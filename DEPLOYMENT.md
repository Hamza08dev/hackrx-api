# HackRx API Deployment Guide

This guide will help you deploy your HackRx API to various platforms for the hackathon submission.

## 🚀 Quick Start

### 1. Local Testing First

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the API locally
cd api
python main.py

# Test the API
python ../test_api.py
```

### 2. Environment Variables

Create a `.env` file with your API keys:

```env
# Gemini API (for embeddings and entity extraction)
GOOGLE_API_KEY=your_gemini_api_key_here

# OpenRouter API (for answer generation)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Site info for OpenRouter
OPENROUTER_SITE_URL=https://your-deployed-url.com
OPENROUTER_SITE_NAME=HackRx API
```

## 🌐 Deployment Options

### Option 1: Railway (Recommended - Free & Easy)

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** repository
3. **Create new project** from GitHub repo
4. **Set environment variables** in Railway dashboard:
   - `GOOGLE_API_KEY`
   - `OPENROUTER_API_KEY`
   - `PORT` (Railway sets this automatically)
5. **Deploy** - Railway will automatically detect and deploy your FastAPI app
6. **Get your URL** - Railway provides HTTPS URL automatically

### Option 2: Render (Free Tier Available)

1. **Sign up** at [render.com](https://render.com)
2. **Create new Web Service**
3. **Connect your GitHub** repository
4. **Configure service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host=0.0.0.0 --port=$PORT`
   - **Environment**: Python 3
5. **Set environment variables**:
   - `GOOGLE_API_KEY`
   - `OPENROUTER_API_KEY`
6. **Deploy** and get your HTTPS URL

### Option 3: Heroku (Paid)

1. **Install Heroku CLI** and sign up
2. **Login to Heroku**:
   ```bash
   heroku login
   ```
3. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```
4. **Set environment variables**:
   ```bash
   heroku config:set GOOGLE_API_KEY=your_key
   heroku config:set OPENROUTER_API_KEY=your_key
   ```
5. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

### Option 4: Vercel (Free Tier)

1. **Sign up** at [vercel.com](https://vercel.com)
2. **Import your GitHub** repository
3. **Configure build settings**:
   - **Framework Preset**: Other
   - **Build Command**: `pip install -r requirements.txt`
   - **Output Directory**: `api`
   - **Install Command**: `pip install -r requirements.txt`
4. **Set environment variables** in Vercel dashboard
5. **Deploy** and get your URL

## 🧪 Testing Your Deployment

### 1. Update Test Script

Edit `test_api.py` and update the `API_URL`:

```python
API_URL = "https://your-deployed-url.com/hackrx/run"
```

### 2. Run Tests

```bash
python test_api.py
```

### 3. Manual Testing

Test with curl:

```bash
curl -X POST "https://your-deployed-url.com/hackrx/run" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": ["What is the grace period for premium payment?"]
  }'
```

## 📋 Pre-Submission Checklist

Before submitting to the hackathon:

- [ ] API is deployed and accessible via HTTPS
- [ ] `/hackrx/run` endpoint responds correctly
- [ ] API accepts requests without authentication
- [ ] Response time is under 30 seconds
- [ ] Returns JSON format with `answers` array
- [ ] Tested with sample hackathon data
- [ ] Environment variables are set correctly

## 🔧 Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **API Key Issues**: Verify your API keys are set correctly
3. **Timeout Errors**: Check if your API is processing within 30 seconds
4. **CORS Issues**: FastAPI handles CORS automatically
5. **Port Issues**: Most platforms set `PORT` environment variable automatically

### Debug Commands:

```bash
# Check if API is running
curl https://your-url.com/health

# Check logs (platform-specific)
# Railway: railway logs
# Render: Check dashboard logs
# Heroku: heroku logs --tail
```

## 🎯 Submission Format

When submitting to the hackathon platform:

- **Webhook URL**: `https://your-deployed-url.com/hackrx/run`
- **Description**: "FastAPI + Gemini + OpenRouter RAG system for document Q&A"
- **Tech Stack**: FastAPI, Gemini API, OpenRouter API, Vector Search

## 📞 Support

If you encounter issues:

1. Check the platform's documentation
2. Verify environment variables are set
3. Test locally first
4. Check API logs for errors
5. Ensure all dependencies are installed

Good luck with your hackathon submission! 🚀 