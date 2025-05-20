from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os
from pathlib import Path
import json
import logging

from app.agents.query_agent import QueryAgent
from app.agents.summary_agent import SummaryAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Configure Gemini
genai.configure(api_key=api_key)

app = FastAPI(
    title="Legal Assistant API",
    description="API for processing legal queries using a multi-agent system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
query_agent = QueryAgent(api_key)
summary_agent = SummaryAgent(api_key)

# Predefined conversational responses
class Query(BaseModel):
    """Request model for legal queries."""
    query: str

class Source(BaseModel):
    text: str
    document: str
    relevance: str

class Step(BaseModel):
    title: str
    description: str
    requirements: List[str]

class LegalResponse(BaseModel):
    simple_explanation: str
    key_points: List[str]
    important_terms: List[str]
    warnings_and_deadlines: List[str]
    step_by_step_guide: Optional[List[Step]] = None
    sources: List[Source]

def clean_json_response(text: str) -> Any:
    """Clean and parse JSON response."""
    try:
        # If the text starts with ```json, extract just the JSON part
        if text.startswith('```json'):
            text = text[7:].strip()  # Remove ```json prefix
            if text.endswith('```'):
                text = text[:-3].strip()  # Remove ``` suffix
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        logger.debug(f"Original text: {text}")
        return text

@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"status": "ok", "message": "Legal Assistant API is running"}

@app.post("/process-query")
async def process_query(query: Query) -> Dict[str, Any]:
    """Process a legal query and return structured information."""
    try:
        # Search for relevant legal information
        query_results = query_agent.search_legal_documents(query.query)
        
        # Summarize and structure the information
        response = summary_agent.summarize_legal_information(query_results)
        
        return {
            "status": "success",
            "data": response
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "data": {
                    "simple_explanation": "An error occurred while processing your query. Please try again.",
                    "key_points": [],
                    "important_terms": [],
                    "warnings_and_deadlines": [],
                    "step_by_step_guide": [],
                    "sources": []
                }
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": {
            "query_agent": query_agent is not None,
            "summary_agent": summary_agent is not None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 