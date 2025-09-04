from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    logger.warning("DATABASE_URL not found in environment variables")
    # Fallback to local SQLite for development
    DATABASE_URL = "sqlite:///./chatbot.db"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = Column(JSON, default=list)
    conversation_history = Column(JSON, default=list)

class ChatMessage(Base):
    """Individual chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_id = Column(String, unique=True, index=True)

class UserFeedback(Base):
    """User feedback model"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True)
    rating = Column(String)  # 'like' or 'dislike'
    feedback_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    conversation_history = Column(JSON, default=list)
    feedback_id = Column(String, unique=True, index=True)

# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Initialize database
def init_db():
    """Initialize database"""
    create_tables()