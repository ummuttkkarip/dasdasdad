# MFT Leather Deployment Steps

## Tamamlanan Adımlar

1. ✅ **mftleather_deploy klasörü oluşturuldu**
   - Ana klasörden gerekli dosyalar kopyalandı
   - .env, requirements.txt, chatbot.html, logo.png dosyaları mevcut

2. ✅ **Logo görünüm sorunu düzeltildi**
   - Logo yolu `/static/logo.png` olarak güncellendi
   - StaticFiles mount'u düzeltildi
   - Logo artık başarıyla görünüyor

3. ✅ **FastAPI uygulaması çalıştırıldı**
   - Port 8002'de başarıyla çalışıyor
   - http://localhost:8002 adresinde erişilebilir
   - Chatbot.html dosya yolu sorunu çözüldü
   - Uygulama hatasız çalışıyor

### 4. Deployment Hazırlığı
- mftleather_deploy klasörü Ubuntu'ya taşınmaya hazır
- Tüm gerekli dosyalar (.env, requirements.txt, logo.png, chatbot.html, fastapi_app.py) mevcut
- Basit JSON veritabanı sistemi entegre edildi

## Çözülen Sorunlar
- Logo görünmeme sorunu çözüldü (statik dosya yolu düzeltildi)
- chatbot.html dosya yolu sorunu giderildi
- Uygulama hatasız çalışıyor
- Sohbet geçmişi otomatik kaydetme özelliği eklendi (her mesaj sonrası)
- Feedback ve beğeni/beğenmeme sistemi mevcut ve çalışıyor
- JSON veritabanı ile sohbet geçmişi ve feedback kayıtları tutuluyor

## Klasör Yapısı
```
mftleather_deploy/
├── .env
├── requirements.txt
├── logo.png
├── chatbot.html
└── api/
    ├── fastapi_app.py
    └── routes/
```

## 5. ✅ **Veritabanı Entegrasyonu Tamamlandı**

### Environment Değişkenleri Eklendi (.env)
- PostgreSQL veritabanı bağlantı URL'si eklendi
- Stack Authentication değişkenleri eklendi:
  - NEXT_PUBLIC_STACK_PROJECT_ID
  - NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY
  - STACK_SECRET_SERVER_KEY

### Gerekli Kütüphaneler Eklendi (requirements.txt)
- psycopg2-binary>=2.9.0 (PostgreSQL bağlantısı için)
- sqlalchemy>=2.0.0 (ORM için)
- alembic>=1.12.0 (veritabanı migration'ları için)

### Veritabanı Modelleri Oluşturuldu (database.py)
- ChatSession modeli: Oturum bilgileri
- ChatMessage modeli: Bireysel mesajlar
- UserFeedback modeli: Kullanıcı geri bildirimleri
- Veritabanı bağlantı ve session yönetimi

### FastAPI Uygulaması Güncellendi
- Veritabanı import'ları eklendi
- Uygulama başlatılırken veritabanı tabloları oluşturuluyor
- save_to_database() fonksiyonu eklendi
- Session tabanlı veri kaydetme sistemi
- API endpoint'leri veritabanından veri okuyacak şekilde güncellendi

### Geriye Uyumluluk Korundu
- Mevcut JSON dosya sistemi korundu
- Veritabanı bağlantısı başarısız olursa JSON dosyalarına kayıt devam ediyor
- API endpoint'leri hem veritabanından hem JSON dosyalarından veri okuyor

## Temizlik İşlemleri ✅

**Silinen gereksiz dosyalar:**
- `api/__pycache__/` - Python cache dosyaları
- `sessions/session_*.json` - Test session dosyası
- `package-lock.json` - Node.js dosyası (bu Python projesi)
- `.github/workflows/` - Boş GitHub Actions klasörü
- `.netlify/` - Boş Netlify klasörü
- `netlify/functions/` - Boş Netlify functions klasörü

## Netlify Deployment Analizi

### ❌ Mevcut Durumda Netlify'a Yüklenemez

**Sorunlar:**
1. **Backend API Sorunu**: `fastapi_app.py` bir Python FastAPI uygulaması ve Netlify'da doğrudan çalışmaz
2. **Veritabanı Bağımlılığı**: PostgreSQL veritabanı bağlantısı var, Netlify'da bu desteklenmez
3. **Python Dependencies**: `requirements.txt` var ama Netlify bu şekilde Python backend'i desteklemez
4. **Environment Variables**: `.env` dosyası var ama production'da farklı şekilde yönetilmeli

### 🔧 Netlify'da Çalıştırmak İçin Gerekli Değişiklikler

**Seçenek 1: Netlify Functions (Önerilen)**
1. `api/fastapi_app.py`'yi Netlify Functions formatına dönüştür
2. Her endpoint için ayrı function dosyası oluştur
3. Veritabanı yerine Netlify'ın desteklediği servisleri kullan (FaunaDB, Supabase)
4. `netlify.toml` dosyası oluştur

**Seçenek 2: Sadece Frontend (Basit)**
1. Backend'i başka bir servise deploy et (Railway, Render, Heroku)
2. Frontend'i Netlify'a yükle
3. API URL'lerini güncelleyerek backend'e bağlan

**Seçenek 3: Serverless Adaptasyon**
1. FastAPI'yi serverless framework'e adapte et
2. Veritabanını cloud servise taşı
3. Static dosyaları CDN'e yükle

### 📋 Önerilen Çözüm: Seçenek 2 (En Kolay)

1. **Backend**: Railway/Render'a deploy et
2. **Frontend**: Netlify'a yükle
3. **Veritabanı**: Railway/Render'ın PostgreSQL'ini kullan
4. **Environment**: Production environment variables ayarla

## GitHub'a Yükleme Hazırlığı Tamamlandı ✅

### Yapılan Değişiklikler:
1. **.env dosyası güncellendi** - PostgreSQL bilgileri eklendi
2. **.gitignore dosyası oluşturuldu** - Hassas dosyaların GitHub'a yüklenmemesi için
3. **requirements.txt güncellendi** - Pydantic bağımlılığı eklendi
4. **start.sh dosyası oluşturuldu** - Render için başlatma scripti
5. **render.yaml dosyası oluşturuldu** - Render otomatik yapılandırması için
6. **GÜVENLİK SORUNU ÇÖZÜLDÜ** - Hardcoded API key'ler environment variable'lara taşındı

### Mevcut Klasör Yapısı:
```
mftleather_deploy/
├── .env (PostgreSQL bilgileri ile güncellenmiş)
├── .gitignore (hassas dosyaları korur)
├── api/
│   ├── database.py
│   └── fastapi_app.py (güvenlik düzeltmesi yapıldı)
├── chatbot.html
├── data/
│   └── feedback.json
├── logo.png
├── render.yaml (Render yapılandırması, env vars eklendi)
├── requirements.txt (Pydantic eklendi)
├── sessions/
├── start.sh (başlatma scripti)
└── steps.md
```

### GitHub'a Yükleme İçin Hazır ✅
Klasör artık GitHub'a yüklenmeye hazır. .env dosyası .gitignore ile korunuyor.

### Güvenlik İyileştirmeleri ✅
- **GitHub Secret Scanning Uyarısı Çözüldü**: API key'ler artık environment variable'lardan alınıyor
- Hardcoded Azure OpenAI API key kaldırıldı
- Hardcoded Azure OpenAI endpoint kaldırıldı
- Production'da güvenli deployment sağlandı
- render.yaml dosyasına environment variables eklendi
- Render dashboard'da manuel olarak girilecek değişkenler tanımlandı

### 🔒 Güvenlik Kontrol Listesi:
- ✅ fastapi_app.py'da hardcoded API key'ler temizlendi
- ✅ Environment variables kullanımına geçildi
- ✅ .env dosyası .gitignore ile korunuyor
- ✅ render.yaml'da güvenli environment variable tanımları
- ✅ Production deployment için güvenlik rehberi eklendi

### ❓ Node_modules Klasörü Hakkında
**Soru**: node_modules klasörü gerekli mi?
**Cevap**: **HAYIR!** Bu bir Python projesi (FastAPI). Node_modules JavaScript/Node.js projeleri için gereklidir.

**Eğer node_modules varsa:**
- Gereksizdir, silebilirsiniz
- .gitignore dosyasında zaten hariç tutulmuştur
- GitHub'a yüklenmez

**Python projesi için gerekli olan:**
- `requirements.txt` (Python paketleri için)
- `pip install` komutu (npm install değil)

**Dosya sayısı sorunu çözümü:**
1. Gereksiz klasörleri silin (data/, sessions/ zaten silindi)
2. .gitignore dosyası hassas dosyaları hariç tutar
3. Sadece gerekli dosyalar GitHub'a yüklenir

## 🚀 Render Deployment Rehberi (Adım Adım)

### 1. Render Hesabı ve Proje Hazırlığı

**Adım 1.1: Render Hesabı Oluştur**
- [render.com](https://render.com) adresine git
- GitHub hesabınla giriş yap
- Ücretsiz plan seç (750 saat/ay ücretsiz)

**Adım 1.2: GitHub Repository Hazırla**
- `mftleather_deploy` klasörünü GitHub'a yükle
- Repository'yi public yap (ücretsiz plan için gerekli)

### 2. PostgreSQL Veritabanı Oluştur

**Adım 2.1: Database Servisi Ekle**
- Render dashboard'da "New +" → "PostgreSQL" seç
- Database Name: `mftleather_db`
- User: `mftleather_user`
- Region: `Frankfurt` (Avrupa'ya yakın)
- Plan: `Free` seç

**Adım 2.2: Database Bilgilerini Kaydet**
- Database URL'ini kopyala (şu formatta olacak):
  ```
  postgresql://username:password@hostname:port/database
  ```

### 3. Web Service (Backend) Deploy Et

**Adım 3.1: Web Service Oluştur**
- Render dashboard'da "New +" → "Web Service" seç
- "Build and deploy from a Git repository" seç
- GitHub hesabınızı bağlayın (ilk kez kullanıyorsanız)
- Repository'nizi seçin: `mftleather_deploy`
- Branch: `main` (veya `master`)

**Adım 3.2: Service Ayarları**
- **Name**: `mftleather-chatbot` (benzersiz olmalı)
- **Root Directory**: boş bırakın
- **Environment**: `Python 3`
- **Region**: `Frankfurt` (veritabanınızla aynı bölge)
- **Branch**: `main`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `bash start.sh` (otomatik tablo oluşturma için)

**Adım 3.3: Environment Variables Ekle**
⚠️ **ÖNEMLİ**: Aşağıdaki environment variables'ları Render dashboard'da manuel olarak ekleyin:

🔒 **GÜVENLİK NOTU**: API key'ler artık kodda hardcoded değil, environment variables'dan alınıyor!

```bash
# PostgreSQL (Render'dan aldığınız bilgiler)
DATABASE_URL=postgresql://[username]:[password]@[host]:[port]/[database]
# Yukarıdaki değeri kendi PostgreSQL bilgilerinizle değiştirin

# Azure OpenAI (Kendi değerlerinizi girin)
AZURE_OPENAI_ENDPOINT=https://[your-resource-name].cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=[your-api-key]
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Azure Search (Kendi değerlerinizi girin)
AZURE_SEARCH_ENDPOINT=https://[your-search-service].search.windows.net
AZURE_SEARCH_API_KEY=[your-search-api-key]
AZURE_SEARCH_INDEX=mftleather
```

**Environment Variables Nasıl Eklenir:**
1. Render dashboard'da web service'inizi seçin
2. "Environment" sekmesine gidin
3. "Add Environment Variable" butonuna tıklayın
4. Her bir değişken için Key ve Value girin
5. "Save Changes" butonuna tıklayın

**Adım 3.4: Deploy Başlat**
- "Create Web Service" butonuna tıkla
- Build sürecini izle (ilk deploy 10-15 dakika sürer)
- Build loglarını takip edin
- Deploy URL'ini kaydet (örn: `https://mftleather-chatbot.onrender.com`)

**Adım 3.5: İlk Deploy Sonrası Kontrol**
- Service URL'ine gidin
- `/health` endpoint'ini test edin
- `/docs` adresinde API dokümantasyonunu kontrol edin
- Logları kontrol edin: "Logs" sekmesinden

### 4. Frontend'i Netlify'a Deploy Et

**Adım 4.1: Frontend Dosyalarını Hazırla**
- `chatbot.html` dosyasını aç
- API URL'lerini Render URL'i ile değiştir:
  ```javascript
  // Eski:
  const API_BASE = 'http://localhost:8000';
  
  // Yeni:
  const API_BASE = 'https://mftleather.onrender.com';
  ```

**Adım 4.2: Netlify'a Yükle**
- [netlify.com](https://netlify.com) adresine git
- "Sites" → "Add new site" → "Deploy manually"
- Sadece `chatbot.html` ve `logo.png` dosyalarını sürükle-bırak
- Site URL'ini kaydet

### 5. Test ve Doğrulama

**Adım 5.1: Backend Testi**
- Render URL'ine git: `https://your-app.onrender.com`
- Health check endpoint'ini test et: `/health`
- API dokümantasyonunu kontrol et: `/docs`

**Adım 5.2: Frontend Testi**
- Netlify URL'ine git
- Chatbot'u test et
- Mesaj gönder ve yanıt al
- Veritabanı kaydını kontrol et

### 6. Sorun Giderme

**Yaygın Sorunlar ve Çözümleri:**

#### 6.1 Build Hataları

**Problem**: `requirements.txt` eksik paket hatası
```
ERROR: Could not find a version that satisfies the requirement...
```
**Çözüm**:
- `requirements.txt` dosyasını kontrol edin
- Eksik paketleri ekleyin
- Paket versiyonlarını güncelleyin

**Problem**: Python versiyonu uyumsuzluğu
**Çözüm**:
- Render'da Python 3.11 kullanın
- `runtime.txt` dosyası oluşturun: `python-3.11.0`

#### 6.2 Database Sorunları

**Problem**: Database bağlantı hatası
```
psycopg2.OperationalError: could not connect to server
```
**Çözüm**:
1. PostgreSQL servisinin çalıştığını kontrol edin
2. DATABASE_URL'in doğru olduğunu kontrol edin
3. Render PostgreSQL panelinden "Internal Database URL" kullanın
4. SSL ayarlarını kontrol edin: `?sslmode=require`

**Problem**: Tablo bulunamadı hatası
**Çözüm**:
- `start.sh` scriptinin çalıştığını kontrol edin
- Manuel olarak tablo oluşturun:
```python
from api.database import create_tables
create_tables()
```

#### 6.3 API Sorunları

**Problem**: CORS hatası
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```
**Çözüm**:
- `fastapi_app.py`'de CORS ayarlarını kontrol edin
- Netlify domain'ini CORS'a ekleyin

**Problem**: 500 Internal Server Error
**Çözüm**:
1. Render loglarını kontrol edin
2. Environment variables'ları kontrol edin
3. Azure API key'lerinin geçerli olduğunu kontrol edin

#### 6.4 Frontend Sorunları

**Problem**: API çağrıları başarısız
**Çözüm**:
- `chatbot.html`'de API_BASE URL'ini kontrol edin
- Render service URL'inin doğru olduğunu kontrol edin
- Network sekmesinde hata mesajlarını kontrol edin

#### 6.5 Performance Sorunları

**Problem**: Yavaş yanıt süreleri
**Çözüm**:
- Render Free plan'da "cold start" sorunu olabilir
- İlk istek 30+ saniye sürebilir
- Paid plan'a geçmeyi düşünün

#### 6.6 Log Kontrolü

**Render Logları Nasıl Kontrol Edilir:**
1. Render dashboard → Service seçin
2. "Logs" sekmesine tıklayın
3. Real-time logları izleyin
4. Hata mesajlarını arayın

**Yararlı Log Komutları:**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Debug mesajı")
```

4. **Cold Start**: İlk istek yavaş (ücretsiz plan)
   - Normal: 30 saniye kadar sürebilir

### 7. Production Optimizasyonları

**Güvenlik:**
- Environment variables'ları Render panelinden ayarla
- `.env` dosyasını GitHub'a yükleme
- HTTPS kullan (Render otomatik sağlar)

**Performans:**
- Paid plan'e geç (cold start yok)
- CDN kullan (static dosyalar için)
- Database connection pooling ekle

### 8. Maliyet Bilgileri

**Ücretsiz Plan Limitleri:**
- Web Service: 750 saat/ay
- PostgreSQL: 1GB storage, 1 milyon row
- Cold start: 30 saniye gecikme

**Paid Plan Avantajları:**
- 24/7 uptime
- Cold start yok
- Daha fazla resource
- Custom domain

### 9. Monitoring ve Logs

**Log İzleme:**
- Render dashboard → Service → Logs
- Real-time log stream
- Error tracking

**Metrics:**
- CPU/Memory kullanımı
- Response time
- Request count

## Ubuntu Deployment için Gerekli Komutlar
```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
python api/fastapi_app.py
```

## Test Sonuçları ✅

### Başarıyla Test Edilenler:
- ✅ Uygulama başlatma ve veritabanı tabloları oluşturma
- ✅ Ana sayfa yükleme
- ✅ Sohbet mesajı gönderme ve yanıt alma
- ✅ Sohbeti bitirme işlevi
- ✅ Beğeni butonu ve geri bildirim formu
- ✅ Geri bildirim gönderme
- ✅ Veritabanına veri kaydetme
- ✅ JSON dosyalarına yedek kaydetme

### Notlar:
- ✅ Pydantic validation hatası düzeltildi (ChatMessage model çakışması çözüldü)
- ✅ Sohbet geçmişi artık düzgün şekilde veritabanına kaydediliyor
- ✅ Her mesaj gönderiminde veritabanına kayıt yapılıyor
- ✅ Tüm temel özellikler çalışıyor
- ✅ Veritabanı entegrasyonu başarılı

## Çözülen Sorunlar

### Sohbet Geçmişi Kaydetme Sorunu ✅
**Sorun**: Sohbet mesajları veritabanına kaydedilmiyordu, sadece feedback kaydediliyordu.

**Sebep**: fastapi_app.py dosyasında iki farklı ChatMessage modeli vardı:
- Pydantic BaseModel (API için): `role` ve `content` alanları ile
- SQLAlchemy modeli (veritabanı için): `user_message` ve `bot_response` alanları ile

İsim çakışması nedeniyle yanlış model kullanılıyordu.

**Çözüm**: 
1. SQLAlchemy ChatMessage modelini `DBChatMessage` olarak import ettik
2. save_to_database fonksiyonunda doğru modeli kullandık
3. Artık her mesaj gönderiminde veritabanına kayıt yapılıyor

## Ubuntu Deployment için Gerekli Komutlar
```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
cd api
python fastapi_app.py
```