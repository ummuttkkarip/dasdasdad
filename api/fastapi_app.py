from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import openai
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json
import logging
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from .database import get_db, init_db, ChatSession, ChatMessage as DBChatMessage, UserFeedback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MFT Leather Chatbot API", version="1.0.0")

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Continue without database for backward compatibility

# Mount static files
import os
static_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Azure Search configuration
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_KEY = os.getenv('AZURE_SEARCH_API_KEY')
AZURE_SEARCH_INDEX = os.getenv('AZURE_SEARCH_INDEX', 'mftleather')
POLICY_SEARCH_INDEX = 'policy'

# Configure Azure OpenAI
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Initialize Azure Search clients
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

policy_search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=POLICY_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    products_found: Optional[List[Dict[str, Any]]] = []

class FeedbackRequest(BaseModel):
    rating: str  # 'like' or 'dislike'
    feedback: str
    timestamp: str
    conversationHistory: List[Dict[str, Any]]
    session_id: str

class ChatHistoryRequest(BaseModel):
    timestamp: str
    messages: List[Dict[str, Any]]
    conversationHistory: List[Dict[str, Any]]
    session_id: str

@app.get("/")
async def serve_chatbot():
    """Serve the chatbot HTML interface"""
    return FileResponse('chatbot.html')

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint that processes user messages"""
    try:
        logger.info(f"Received message: {request.message}")
        
        # Search for relevant products
        products = await search_products(request.message)
        
        # Generate response using OpenAI
        response = await generate_chat_response(
            request.message, 
            request.conversation_history, 
            products
        )
        
        # Save message to session if session_id is provided
        if request.session_id:
            message_data = {
                "user_message": request.message,
                "bot_response": response,
                "conversation_history": [msg.dict() for msg in request.conversation_history] if request.conversation_history else []
            }
            save_to_session_db(request.session_id, message_data, 'message')
        
        return ChatResponse(
            response=response,
            products_found=products
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def search_products(query: str) -> List[Dict[str, Any]]:
    """Search for products and policies using Azure Search"""
    try:
        # Enhanced search with multiple strategies
        search_results = []
        query_lower = query.lower()
        
        # Check if query is policy-related (SSS, iade, garanti, etc.)
        policy_keywords = ['sss', 'iade', 'garanti', 'değişim', 'kargo', 'ödeme', 'taksit', 'nakit', 'kredi kartı', 
                          'üretim', 'teslimat', 'bakım', 'temizlik', 'mağaza', 'adres', 'telefon', 'fiyat',
                          'kişiselleştirme', 'isim', 'yazı', 'logo', 'promosyon', 'indirim']
        
        is_policy_query = any(keyword in query_lower for keyword in policy_keywords)
        
        # Strategy -1: Policy search for FAQ and return policy questions
        if is_policy_query:
            try:
                policy_results = policy_search_client.search(
                    search_text=query,
                    top=5,
                    search_mode='any'
                )
                
                for result in policy_results:
                    search_results.append({
                        'id': result.get('id', ''),
                        'title': 'SSS ve İade Politikası',
                        'brand': 'MFT Leather',
                        'description': result.get('chunk', ''),
                        'text': result.get('chunk', ''),
                        'price': '',
                        'color': [],
                        'category': 'policy',
                        'url': '',
                        'score': result.get('@search.score', 1.0),
                        'type': 'policy'
                    })
                
                # If policy results found, return them with higher priority
                if search_results:
                    return search_results[:3]  # Return top 3 policy results
                    
            except Exception as policy_error:
                logger.warning(f"Policy search error: {str(policy_error)}")
                # Continue with product search if policy search fails
        
        # Strategy 0: Specific product ID search for known products
        if 'vineda 5696' in query_lower or 'vineda5696' in query_lower:
            specific_results = search_client.search(
                search_text="",
                filter="id eq 'vineda_5696'",
                top=5
            )
            for result in specific_results:
                search_results.append({
                    'id': result.get('id', ''),
                    'title': result.get('name', ''),
                    'brand': result.get('brand', ''),
                    'description': result.get('description', ''),
                    'text': result.get('text', ''),
                    'price': result.get('price', ''),
                    'color': result.get('color', []),
                    'category': result.get('category', ''),
                    'url': result.get('url', ''),
                    'score': result.get('@search.score', 1.0)
                })
        
        # Strategy 0.1: Product name-based search for common models
        product_mappings = {
            'retro': 'retro_2660',
            'vineda': 'vineda_5696'
        }
        
        for product_name, product_id in product_mappings.items():
            if product_name in query_lower:
                name_results = search_client.search(
                    search_text="",
                    filter=f"id eq '{product_id}'",
                    top=5
                )
                for result in name_results:
                    # Avoid duplicates
                    if not any(r['id'] == result.get('id', '') for r in search_results):
                        search_results.append({
                            'id': result.get('id', ''),
                            'title': result.get('name', ''),
                            'brand': result.get('brand', ''),
                            'description': result.get('description', ''),
                            'text': result.get('text', ''),
                            'price': result.get('price', ''),
                            'color': result.get('color', []),
                            'category': result.get('category', ''),
                            'url': result.get('url', ''),
                            'score': result.get('@search.score', 1.0)
                        })
                break  # Stop after first match to avoid multiple results for same query
        
        # Strategy 0.2: Enhanced partial matching - search in both ID and name fields
        if not search_results:  # Only if no results found yet
            query_words = query_lower.split()
            for word in query_words:
                if len(word) >= 3:  # Only search for words with 3+ characters
                    # Search in both ID and name fields with wildcards
                    partial_results = search_client.search(
                        search_text=f"id:{word}* OR name:{word}*",
                        top=10,
                        search_mode='any'
                    )
                    for result in partial_results:
                        if not any(r['id'] == result.get('id', '') for r in search_results):
                            search_results.append({
                                'id': result.get('id', ''),
                                'title': result.get('name', ''),
                                'brand': result.get('brand', ''),
                                'description': result.get('description', ''),
                                'text': result.get('text', ''),
                                'price': result.get('price', ''),
                                'color': result.get('color', []),
                                'category': result.get('category', ''),
                                'url': result.get('url', ''),
                                'score': result.get('@search.score', 0.8)  # Higher score for partial matches
                            })
                    if search_results:  # Stop after finding results
                        break
            
            # If still no results, try contains search (less strict)
            if not search_results:
                for word in query_words:
                    if len(word) >= 3:
                        contains_results = search_client.search(
                            search_text=f"search.ismatch('{word}', 'id,name')",
                            top=5
                        )
                        for result in contains_results:
                            if not any(r['id'] == result.get('id', '') for r in search_results):
                                search_results.append({
                                    'id': result.get('id', ''),
                                    'title': result.get('name', ''),
                                    'brand': result.get('brand', ''),
                                    'description': result.get('description', ''),
                                    'text': result.get('text', ''),
                                    'price': result.get('price', ''),
                                    'color': result.get('color', []),
                                    'category': result.get('category', ''),
                                    'url': result.get('url', ''),
                                    'score': result.get('@search.score', 0.6)
                                })
                        if search_results:
                            break
        
        # Strategy 1: Simple text search with correct field names
        results = search_client.search(
            search_text=query,
            top=10,
            search_mode='any'
        )
        
        # If no results, try broader search
        if not list(results):
            results = search_client.search(
                search_text="*",
                top=10
            )
        
        for result in results:
            search_results.append({
                'id': result.get('id', ''),
                'title': result.get('name', ''),  # Product name
                'brand': result.get('brand', ''),  # Brand information
                'description': result.get('description', ''),  # Full detailed description
                'text': result.get('text', ''),  # Short summary text
                'price': result.get('price', ''),
                'color': result.get('color', []),
                'category': result.get('category', ''),
                'url': result.get('url', ''),
                'score': result.get('@search.score', 0)
            })
        
        # Strategy 2: Color-specific search if color keywords detected
        color_keywords = {
            'siyah': ['Flother Mat Siyah', 'Napa Siyah', 'Tiguan Siyah', 'Flother Siyah'],
            'pembe': ['Flother Mat Pembe', 'Vineda Pembe', 'Napa Pembe'],
            'kahverengi': ['Flother Mat Kahverengi', 'Napa Kahverengi', 'Tiguan Kahverengi'],
            'beyaz': ['Flother Mat Beyaz', 'Napa Beyaz'],
            'mavi': ['Flother Mat Mavi', 'Napa Mavi']
        }
        
        query_lower = query.lower()
        for color, variants in color_keywords.items():
            if color in query_lower:
                color_filter = ' or '.join([f"color/any(c: c eq '{variant}')" for variant in variants])
                
                color_results = search_client.search(
                    search_text=query,
                    filter=color_filter,
                    top=10
                )
                
                for result in color_results:
                    # Avoid duplicates
                    if not any(r['id'] == result.get('id', '') for r in search_results):
                        search_results.append({
                            'id': result.get('id', ''),
                            'title': result.get('name', ''),  # Fixed: name instead of title
                            'description': result.get('text', ''),  # Fixed: text instead of description
                            'price': result.get('price', ''),
                            'color': result.get('color', []),
                            'category': result.get('category', ''),
                            'url': result.get('url', ''),
                            'score': result.get('@search.score', 0)
                        })
        
        # Sort by relevance score and return top 5
        search_results.sort(key=lambda x: x['score'], reverse=True)
        return search_results[:5]
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

async def generate_chat_response(message: str, history: List[ChatMessage], products: List[Dict[str, Any]]) -> str:
    """Generate chat response using OpenAI"""
    try:
        # Build conversation context
        messages = [
            {
                "role": "system",
                "content": """
Sen MFT Leather'ın satış odaklı müşteri hizmetleri asistanısın. 😊

YANIT STİLİ VE FORMATLAMA:
- Müşterinin SPESIFIK sorusuna odaklan, gereksiz detay verme
- **Başlıkları kalın yaz**, önemli bilgileri **vurgula**
- Markdown formatı kullan: **kalın**, *italik*, başlıklar için ##
- Kısa, net ve satış odaklı yanıtlar ver
- Ürünün değerini ve avantajlarını vurgula
- Satın alma teşvik edici ifadeler kullan

ÜRÜN SORULARI İÇİN:
- **Fiyat soruları**: "Güncel fiyat bilgisi için lütfen web sitemizi ziyaret edin: www.mftleather.com" + ürün avantajlarını vurgula
- **Ürün özellikleri**: Sadece ÖNEMLİ ve ÇARPICI bilgileri ver, tüm detayları değil
- **Renk/model**: Mevcut seçenekleri listele + **en popüler olanını öner**
- Kullanıcı "daha fazla detay" isterse, o zaman ek bilgi ver

POLİTİKA SORULARI İÇİN (SSS, İade, Garanti):
- Verilen policy bilgisini DOĞRUDAN ve NET şekilde aktar
- **Önemli kuralları kalın yaz**
- Müşteriyi rahatlatıcı ton kullan
- Ek sorular için mağaza iletişim bilgilerini öner
- Policy bilgisi yoksa "Detaylı bilgi için mağazamızı arayın" de

SATIŞ KURALLARI:
- SADECE verilen ürün/policy bilgilerini kullan
- Fiyat sorularında web sitesine yönlendir
- Ürün yoksa alternatif öner
- Her yanıtta satın alma teşviki ekle (ürün sorularında)
- Policy sorularında güven verici ol

DİL VE FORMAT:
- Samimi ama profesyonel
- Kısa cümleler kullan
- 1-2 emoji ekle
- Türkçe konuş
- Müşteriyi "siz" diye hitap et
- **Önemli bilgileri kalın yaz**
- Başlıklar için ## kullan

Müşterinin sorusuna DOĞRUDAN cevap ver, sonra uygun teşviki ekle.
"""
            }
        ]
        
        # Add conversation history (last 5 messages)
        for msg in history[-10:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current message with detailed product/policy context
        product_context = ""
        if products:
            # Check if results contain policy information
            has_policy = any(product.get('type') == 'policy' for product in products)
            
            if has_policy:
                product_context = "\n\nBulunan policy bilgileri:\n"
                for i, product in enumerate(products[:3], 1):
                    if product.get('type') == 'policy':
                        description = product.get('description', product.get('text', 'Bilgi yok'))
                        product_context += f"""{i}. {description}\n\n"""
            else:
                product_context = "\n\nBulunan ürünler (detaylı bilgiler):\n"
                for i, product in enumerate(products[:3], 1):
                    colors = ", ".join(product['color']) if product['color'] else "Renk bilgisi yok"
                    brand = product.get('brand', 'Marka bilgisi yok')
                    category = product.get('category', 'Kategori bilgisi yok')
                    description = product.get('description', product.get('text', 'Açıklama yok'))
                    
                    product_context += f"""{i}. {product['title']}
   Marka: {brand}
   Kategori: {category}
   Renkler: {colors}
   Fiyat: {product['price'] if product['price'] else 'Fiyat bilgisi için mağazamızı arayın'}
   Detaylar: {description[:300]}{'...' if len(description) > 300 else ''}
\n"""
        
        messages.append({
            "role": "user",
            "content": f"{message}{product_context}"
        })
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=800,  # Increased to prevent cut-off responses
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return "Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin. 😔"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/chatbot.html")
async def get_chatbot():
    """Serve chatbot HTML file"""
    import os
    # Get the absolute path to chatbot.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    file_path = os.path.join(parent_dir, "chatbot.html")
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        logger.error(f"Chatbot HTML file not found at: {file_path}")
        return {"error": f"File not found: {file_path}"}

@app.get("/debug")
async def debug_paths():
    """Debug file paths"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    file_path = os.path.join(parent_dir, "chatbot.html")
    
    return {
        "current_file": __file__,
        "current_dir": current_dir,
        "parent_dir": parent_dir,
        "file_path": file_path,
        "file_exists": os.path.exists(file_path),
        "cwd": os.getcwd(),
        "listdir_parent": os.listdir(parent_dir) if os.path.exists(parent_dir) else "parent_dir_not_exists"
    }

@app.get("/")
async def root():
    """Redirect to chatbot"""
    import os
    # Get the absolute path to chatbot.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    file_path = os.path.join(parent_dir, "chatbot.html")
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        logger.error(f"Chatbot HTML file not found at: {file_path}")
        return {"error": f"File not found: {file_path}", "current_dir": os.getcwd(), "file_path": file_path, "parent_dir": parent_dir}

# Database functions
def save_to_database(session_id: str, data: dict, data_type: str, db: Session = None):
    """Save data to PostgreSQL database"""
    try:
        if db is None:
            # Create a new session if none provided
            from database import SessionLocal
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
            
        try:
            if data_type == 'message':
                # Save or update chat session
                session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
                if not session:
                    session = ChatSession(
                        session_id=session_id,
                        messages=[],
                        conversation_history=data.get('conversation_history', [])
                    )
                    db.add(session)
                else:
                    session.last_updated = datetime.utcnow()
                    session.conversation_history = data.get('conversation_history', [])
                
                # Save individual message
                message = DBChatMessage(
                    session_id=session_id,
                    user_message=data.get('user_message', ''),
                    bot_response=data.get('bot_response', ''),
                    message_id=str(uuid.uuid4())
                )
                db.add(message)
                
            elif data_type == 'feedback':
                # Save feedback
                feedback = UserFeedback(
                    session_id=session_id,
                    rating=data.get('rating', ''),
                    feedback_text=data.get('feedback', ''),
                    conversation_history=data.get('conversation_history', []),
                    feedback_id=str(uuid.uuid4())
                )
                db.add(feedback)
            
            db.commit()
            logger.info(f"Data saved to database for session {session_id}")
            return True
            
        finally:
            if close_db:
                db.close()
                
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        if db:
            db.rollback()
        return False

# Session-based JSON database functions (for backward compatibility)
def save_to_session_db(session_id: str, data: dict, data_type: str):
    """Save data to both database and JSON file for backward compatibility"""
    try:
        # Try to save to database first
        db_success = save_to_database(session_id, data, data_type)
        
        # Also save to JSON file for backward compatibility
        # Create sessions directory if it doesn't exist
        os.makedirs('sessions', exist_ok=True)
        
        file_path = os.path.join('sessions', f'session_{session_id}.json')
        
        # Load existing session data
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "messages": [],
            "feedbacks": [],
            "conversation_history": []
        }
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        
        # Update last_updated timestamp
        session_data['last_updated'] = datetime.now().isoformat()
        
        # Add data based on type
        if data_type == 'message':
            session_data['messages'].append({
                "timestamp": datetime.now().isoformat(),
                "user_message": data.get('user_message', ''),
                "bot_response": data.get('bot_response', ''),
                "id": str(uuid.uuid4())
            })
            # Update conversation history
            if 'conversation_history' in data:
                session_data['conversation_history'] = data['conversation_history']
        elif data_type == 'feedback':
            session_data['feedbacks'].append({
                "timestamp": datetime.now().isoformat(),
                "rating": data.get('rating', ''),
                "feedback": data.get('feedback', ''),
                "id": str(uuid.uuid4())
            })
        
        # Save back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Session data saved to {file_path}")
        return db_success or True  # Return success if either database or file save worked
    except Exception as e:
        logger.error(f"Error saving to session DB: {e}")
        return False

# Legacy function for backward compatibility
def save_to_json_db(filename: str, data: dict):
    """Save data to JSON file database (legacy)"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        file_path = os.path.join('data', filename)
        
        # Load existing data
        existing_data = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # Add new data with unique ID
        data['id'] = str(uuid.uuid4())
        existing_data.append(data)
        
        # Save back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Data saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to JSON DB: {e}")
        return False

@app.post("/api/feedback")
async def save_feedback(request: FeedbackRequest):
    """Save user feedback to session-based JSON database"""
    try:
        feedback_data = {
            "rating": request.rating,
            "feedback": request.feedback,
            "timestamp": request.timestamp,
            "conversation_history": request.conversationHistory
        }
        
        # Save to session-based database
        success = save_to_session_db(request.session_id, feedback_data, 'feedback')
        
        # Also save to legacy database for backward compatibility
        feedback_data["created_at"] = datetime.now().isoformat()
        save_to_json_db('feedback.json', feedback_data)
        
        if success:
            return {"status": "success", "message": "Feedback saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
            
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat-history")
async def save_chat_history(request: ChatHistoryRequest):
    """Save chat history to JSON database"""
    try:
        chat_data = {
            "timestamp": request.timestamp,
            "messages": request.messages,
            "conversation_history": request.conversationHistory,
            "created_at": datetime.now().isoformat()
        }
        
        success = save_to_json_db('chat_history.json', chat_data)
        
        if success:
            return {"status": "success", "message": "Chat history saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save chat history")
            
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback")
async def get_feedback(db: Session = Depends(get_db)):
    """Get all feedback data from database"""
    try:
        # Get feedback from database
        db_feedbacks = db.query(UserFeedback).order_by(UserFeedback.timestamp.desc()).all()
        feedback_list = []
        
        for fb in db_feedbacks:
            feedback_list.append({
                "id": fb.feedback_id,
                "session_id": fb.session_id,
                "rating": fb.rating,
                "feedback": fb.feedback_text,
                "timestamp": fb.timestamp.isoformat(),
                "conversation_history": fb.conversation_history,
                "created_at": fb.timestamp.isoformat()
            })
        
        # Also include JSON file feedback for backward compatibility
        file_path = os.path.join('data', 'feedback.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            # Add source indicator for JSON data
            for item in json_data:
                item['source'] = 'json_file'
            feedback_list.extend(json_data)
        
        return {"feedback": feedback_list}
    except Exception as e:
        logger.error(f"Error reading feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat-history")
async def get_chat_history(db: Session = Depends(get_db)):
    """Get all chat history data from database"""
    try:
        # Get messages from database
        db_messages = db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).all()
        chat_history = []
        
        for msg in db_messages:
            chat_history.append({
                "id": msg.message_id,
                "session_id": msg.session_id,
                "user_message": msg.user_message,
                "bot_response": msg.bot_response,
                "timestamp": msg.timestamp.isoformat(),
                "created_at": msg.timestamp.isoformat()
            })
        
        # Also include JSON file chat history for backward compatibility
        file_path = os.path.join('data', 'chat_history.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            # Add source indicator for JSON data
            for item in json_data:
                item['source'] = 'json_file'
            chat_history.extend(json_data)
        
        return {"chat_history": chat_history}
    except Exception as e:
        logger.error(f"Error reading chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session_data(session_id: str, db: Session = Depends(get_db)):
    """Get session-specific data from database"""
    try:
        # Try to get from database first
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()
        feedbacks = db.query(UserFeedback).filter(UserFeedback.session_id == session_id).order_by(UserFeedback.timestamp).all()
        
        if session:
            return {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
                "messages": [{
                    "id": msg.message_id,
                    "timestamp": msg.timestamp.isoformat(),
                    "user_message": msg.user_message,
                    "bot_response": msg.bot_response
                } for msg in messages],
                "feedbacks": [{
                    "id": fb.feedback_id,
                    "timestamp": fb.timestamp.isoformat(),
                    "rating": fb.rating,
                    "feedback": fb.feedback_text
                } for fb in feedbacks],
                "conversation_history": session.conversation_history
            }
        
        # Fallback to JSON file if not found in database
        file_path = os.path.join('sessions', f'session_{session_id}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        else:
            return {"error": "Session not found"}
    except Exception as e:
        logger.error(f"Error reading session data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def get_all_sessions(db: Session = Depends(get_db)):
    """Get list of all sessions from database"""
    try:
        # Get sessions from database
        db_sessions = db.query(ChatSession).all()
        sessions = []
        
        for session in db_sessions:
            message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session.session_id).count()
            feedback_count = db.query(UserFeedback).filter(UserFeedback.session_id == session.session_id).count()
            
            sessions.append({
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
                "message_count": message_count,
                "feedback_count": feedback_count
            })
        
        # Also include JSON file sessions for backward compatibility
        sessions_dir = 'sessions'
        if os.path.exists(sessions_dir):
            existing_session_ids = {s["session_id"] for s in sessions}
            
            for filename in os.listdir(sessions_dir):
                if filename.startswith('session_') and filename.endswith('.json'):
                    session_id = filename.replace('session_', '').replace('.json', '')
                    
                    # Skip if already in database
                    if session_id in existing_session_ids:
                        continue
                        
                    file_path = os.path.join(sessions_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    sessions.append({
                        "session_id": session_id,
                        "created_at": session_data.get('created_at'),
                        "last_updated": session_data.get('last_updated'),
                        "message_count": len(session_data.get('messages', [])),
                        "feedback_count": len(session_data.get('feedbacks', [])),
                        "source": "json_file"
                    })
        
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error reading sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
