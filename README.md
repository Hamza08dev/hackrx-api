# Email-to-Insights: Hybrid RAG System

A powerful document processing and question-answering system that combines Gemini API for embeddings and entity extraction with OpenRouter API for intelligent responses.

## 🚀 Features

- **Document Processing**: Upload PDF, DOCX, and TXT files
- **Smart Chunking**: Intelligent text splitting for optimal processing
- **Entity Extraction**: Automatic identification of people, organizations, technologies, and skills
- **Hybrid Search**: Combines semantic vector search with graph traversal
- **OpenRouter Integration**: Uses DeepSeek R1 for intelligent question answering
- **Streamlit UI**: Clean, interactive web interface

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

## 📁 Project Structure

```
email-to-insights/
├── app.py                 # Main Streamlit UI
├── requirements.txt       # Python dependencies
├── .env                  # API keys (not in repo)
├── .gitignore           # Git ignore rules
├── api/                 # REST API endpoints
├── ingestion/           # Document loading
├── processing/          # Gemini processing
└── qa/                 # OpenRouter Q&A
```

## 🔧 Configuration

- **Cost Optimization**: Limited API calls and concise responses
- **Rate Limiting**: Built-in delays to respect API quotas
- **Fallback Handling**: Graceful degradation when APIs are unavailable

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License. 