# Legal Assistant AI 🤖⚖️

An AI-powered legal assistant that helps users understand legal procedures and requirements in India. The system uses a multi-agent architecture to process queries, extract relevant information from legal documents, and provide structured, easy-to-understand responses.

## Features 🌟

- Natural language query processing
- Semantic search across legal documents
- Structured responses with:
  - Simple explanations in plain language
  - Key points and takeaways
  - Important legal terms and definitions
  - Warnings and deadlines
  - Step-by-step guides for procedures
  - Source references with relevance explanations
- User-friendly Streamlit interface
- FastAPI backend for efficient processing
- ChromaDB for document storage and retrieval
- Google's Gemini model for advanced language processing

## Architecture 🏗️

The project follows a multi-agent architecture:

1. **Query Agent**: Handles initial query processing and document retrieval
   - Uses ChromaDB for semantic search
   - Extracts relevant passages from documents
   - Determines if queries are procedural

2. **Summary Agent**: Processes and structures the information
   - Simplifies complex legal text
   - Creates step-by-step guides
   - Extracts key points and warnings

3. **FastAPI Backend**: Coordinates the agents and serves responses
   - RESTful API endpoints
   - Error handling and logging
   - Response formatting

4. **Streamlit Frontend**: Provides the user interface
   - Clean, intuitive design
   - Real-time query processing
   - Structured result display

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
- Documents will be automatically processed and indexed

## Usage 💡

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

### POST /api/query
Submit a legal query:
```json
{
  "query": "What are the steps involved in filing a lawsuit in India?"
}
```

### GET /api/health
Check API health status.

## Project Structure 📁

```
legal-assistant-ai/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── query_agent.py
│   │   └── summary_agent.py
│   ├── __init__.py
│   ├── main.py
│   └── streamlit_app.py
├── data/
│   └── legal_docs/
│       └── .gitkeep
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## Development 🛠️

### Adding New Documents
1. Add PDF files to `data/legal_docs/`
2. Restart the FastAPI server to reindex documents

### Customizing Response Format
1. Modify the agent classes in `app/agents/`
2. Update the response models in `app/main.py`
3. Adjust the display in `app/streamlit_app.py`

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
