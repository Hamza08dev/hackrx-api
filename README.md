# Email-to-Insights: Hybrid RAG System

A powerful document processing and question-answering system that combines Gemini API for embeddings and entity extraction with OpenRouter API for intelligent responses.

## 🚀 Features

- **Document Processing**: Upload PDF, DOCX, and TXT files
- **Smart Chunking**: Intelligent text splitting for optimal processing
- **Entity Extraction**: Automatic identification of people, organizations, technologies, and skills
- **Hybrid Search**: Combines semantic vector search with graph traversal
- **OpenRouter Integration**: Uses DeepSeek R1 for intelligent question answering
- **Streamlit UI**: Clean, interactive web interface
- **FastAPI Backend**: REST API for hackathon submissions

## 🏗️ Architecture

- **Gemini API**: Text embeddings and entity/relationship extraction
- **OpenRouter API**: Final answer generation using DeepSeek R1
- **In-Memory Storage**: Fast vector storage and graph data
- **Modular Design**: Clean separation of concerns

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shiva666666/email-to-insights.git
   cd email-to-insights
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with your API keys:
   ```env
   # Gemini API (for embeddings and graph creation)
   GOOGLE_API_KEY=your_gemini_api_key_here

   # OpenRouter API (for final answer generation)
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # Optional: Site info for OpenRouter rankings
   OPENROUTER_SITE_URL=http://localhost:8511
   OPENROUTER_SITE_NAME=Hybrid RAG System
   ```

## 🎯 Usage

### Streamlit UI (Local Development)

1. **Start the application**
   ```bash
   streamlit run app.py --server.port 8511
   ```

2. **Open your browser**
   Navigate to: http://localhost:8511

3. **Upload documents**
   - Supported formats: PDF, DOCX, TXT
   - Documents are automatically processed and stored

4. **Ask questions**
   - Use the Q&A interface to query your documents
   - Get intelligent answers based on document content

### FastAPI Backend (Hackathon Submission)

1. **Run the API locally**
   ```bash
   cd api
   python main.py
   ```

2. **Test the API**
   ```bash
   python test_api.py
   ```

3. **Deploy to platform**
   - Follow instructions in `DEPLOYMENT.md`
   - Recommended: Railway (free and easy)

## 🔌 API Endpoints

### Main Endpoint: `/hackrx/run`

**Request Format:**
```bash
POST /hackrx/run
Content-Type: application/json
Accept: application/json
Authorization: Bearer <api_key>

{
    "documents": "https://example.com/policy.pdf",
    "questions": [
        "What is the grace period for premium payment?",
        "What is the waiting period for pre-existing diseases?"
    ]
}
```

**Response Format:**
```json
{
    "answers": [
        "A grace period of thirty days is provided...",
        "There is a waiting period of thirty-six months..."
    ]
}
```

### Health Check: `/health`
```bash
GET /health
```

## 📁 Project Structure

```
email-to-insights/
├── app.py                 # Main Streamlit UI
├── api/
│   └── main.py           # FastAPI backend
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md         # Deployment instructions
├── test_api.py           # API testing script
├── ingestion/            # Document loading
├── processing/           # Gemini processing
└── qa/                  # OpenRouter Q&A
```

## 🌐 Deployment

### Quick Deployment (Railway - Recommended)

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** repository
3. **Set environment variables**:
   - `GOOGLE_API_KEY`
   - `OPENROUTER_API_KEY`
4. **Deploy** - Railway auto-detects FastAPI
5. **Get your URL** - Use for hackathon submission

### Other Platforms

See `DEPLOYMENT.md` for detailed instructions on:
- Render
- Heroku
- Vercel
- AWS/GCP/Azure

## 🔧 Configuration

- **Cost Optimization**: Limited API calls and concise responses
- **Rate Limiting**: Built-in delays to respect API quotas
- **Fallback Handling**: Graceful degradation when APIs are unavailable

## 🧪 Testing

### Local Testing
```bash
# Test Streamlit UI
streamlit run app.py

# Test API
python test_api.py
```

### Production Testing
```bash
# Update API_URL in test_api.py
python test_api.py
```

## 📋 Hackathon Submission

1. **Deploy your API** (see `DEPLOYMENT.md`)
2. **Test thoroughly** with sample data
3. **Submit webhook URL**: `https://your-url.com/hackrx/run`
4. **Add description**: "FastAPI + Gemini + OpenRouter RAG system"

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License. 