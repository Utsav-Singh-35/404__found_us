# SatyaMatrix LLM API

AI-powered fact-checking microservice with 8-agent pipeline and 4 innovation modules.

## 🚀 Quick Deploy to Render

### Prerequisites
- MongoDB Atlas account (free tier)
- Upstash Redis account (free tier)
- API Keys: Google Fact Check, OCR.space, OpenRouter

### Deploy Steps

1. **Push to GitHub**
2. **Create Render Web Service**
   - Connect GitHub repo
   - Build Command: `pip install --no-cache-dir -r requirements.txt`
   - Start Command: `python start.py`
   - Instance Type: Free

3. **Add Environment Variables**
   ```
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB=factchecker
   REDIS_URL=your_upstash_redis_url
   GOOGLE_FACTCHECK_KEY=your_key
   OCR_SPACE_KEY=your_key
   OPENROUTER_API_KEY=your_key
   OPENROUTER_MODEL=openai/gpt-4o-mini:free
   SECRET_KEY=random-32-char-string
   ALLOWED_ORIGINS=https://satyamatrix.onrender.com
   ```

4. **Deploy!**

## 📡 API Endpoints

- `GET /health` - Health check
- `POST /check` - Submit claim (text/url/image)
- `GET /result/{id}` - Get fact-check result
- `GET /report/{id}` - Download report
- `GET /dashboard/*` - Real-time monitoring

## 🏗️ Architecture

- **FastAPI** - Async Python web framework
- **MongoDB** - Document storage
- **Redis** - Job queue
- **Worker** - Background processing (45-60s per claim)

## 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env

# Run locally
python start.py
```

## 📊 Features

- 8-Agent fact-checking pipeline
- OCR for images
- URL scraping
- Google Fact Check API integration
- AI-powered analysis
- HTML/PDF reports
- Real-time dashboard

---

**Status**: Production Ready ✅
