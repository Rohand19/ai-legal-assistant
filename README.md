# AI Legal Assistant 🤖⚖️

An AI-powered legal assistant that helps users understand legal procedures and requirements in India. The system uses Google's Gemini model and a multi-agent architecture to process queries, extract relevant information from legal documents, and provide structured, easy-to-understand responses.

🔗 **Try it now**: [https://ai-legal-asst.streamlit.app/](https://ai-legal-asst.streamlit.app/)

## Features 🌟

- Natural language query processing using Google's Gemini model
- Semantic search across legal documents using ChromaDB and Sentence Transformers
- Intelligent query classification (legal vs non-legal queries)
- Streamlit interface with custom styling
- FastAPI backend with efficient async processing
- Structured responses with:
  - Simple explanations in plain language
  - Key points and takeaways
  - Important legal terms and definitions
  - Context-aware warnings and deadlines
  - Step-by-step procedural guides
  - Source references with relevance explanations

## Architecture 🏗️

The project follows a sophisticated multi-agent architecture:

1. **Query Agent**: Handles initial query processing and document retrieval
   - Uses ChromaDB with Sentence Transformers for semantic search
   - Implements intelligent query classification
   - Processes and chunks documents for efficient retrieval
   - Handles document indexing and persistence

2. **Summary Agent**: Processes and structures legal information
   - Simplifies complex legal text into plain language
   - Creates step-by-step procedural guides
   - Extracts key points and important terms
   - Identifies warnings and deadlines
   - Formats source references with relevance explanations

3. **FastAPI Backend**: Coordinates the agents and serves responses
   - Async request processing
   - Comprehensive error handling
   - Health monitoring
   - CORS support for cross-origin requests
   - Structured response formatting

4. **Streamlit Frontend**: Provides an intuitive user interface
   - Custom-styled components
   - Real-time query processing
   - Structured result display with visual hierarchy
   - Error handling and user feedback
   - Responsive design

## Setup 🚀

### Prerequisites

- Python 3.8+
- pip package manager
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Rohand19/ai-legal-assistant.git
cd ai-legal-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

5. Add legal documents:
- Place your PDF legal documents in `data/legal_docs/`
- Documents will be automatically processed and indexed on server start

## Usage 💡

### Online Access
Visit the live application at: [https://ai-legal-asst.streamlit.app/](https://ai-legal-asst.streamlit.app/)

### Local Development
1. Start the FastAPI backend:
```bash
PYTHONPATH=$PYTHONPATH:. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. In a new terminal, start the Streamlit frontend:
```bash
streamlit run app/streamlit_app.py
```

3. Open your browser and navigate to:
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

## API Endpoints 🔌

### POST /process-query
Process a legal query:
```json
{
  "query": "What are the steps involved in filing a lawsuit in India?"
}
```

Response format:
```json
{
  "status": "success",
  "data": {
    "simple_explanation": "Plain language explanation",
    "key_points": ["Important point 1", "Important point 2"],
    "important_terms": [
      {
        "term": "Legal term",
        "definition": "Simple explanation"
      }
    ],
    "warnings_and_deadlines": [
      {
        "warning": "Important warning",
        "deadline": "Associated deadline"
      }
    ],
    "step_by_step_guide": [
      {
        "step": "1",
        "title": "Step title",
        "description": "What to do"
      }
    ],
    "sources": [
      {
        "title": "Document title",
        "description": "Source contribution"
      }
    ]
  }
}
```

### GET /health
Check API health status:
```json
{
  "status": "healthy",
  "agents": {
    "query_agent": true,
    "summary_agent": true
  }
}
```

## Project Structure 📁

```
legal-assistant-ai/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── query_agent.py      # Query processing and document retrieval
│   │   └── summary_agent.py    # Information summarization and structuring
│   ├── __init__.py
│   ├── main.py                 # FastAPI application and endpoints
│   └── streamlit_app.py        # Streamlit frontend interface
├── data/
│   └── legal_docs/             # Legal document storage
│       └── .gitkeep
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## Development 🛠️

### Adding New Documents
1. Add PDF files to `data/legal_docs/`
2. Documents are automatically processed and indexed on server start
3. Supported formats: PDF (additional formats can be added by extending the QueryAgent)

### Customizing Response Format
1. Modify the agent classes in `app/agents/`
2. Update the response models in `app/main.py`
3. Adjust the display in `app/streamlit_app.py`

### Error Handling
The system implements comprehensive error handling:
- Invalid queries
- Document processing errors
- API errors
- Database connection issues
- Model inference errors

### Performance Considerations
- Uses ChromaDB for efficient vector search
- Implements document chunking for better retrieval
- Caches processed documents
- Supports async processing
