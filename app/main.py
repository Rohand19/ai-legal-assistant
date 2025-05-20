from fastapi import FastAPI, HTTPException
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

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI(
    title="Legal Multi-Agent Chatbot",
    description="A sophisticated multi-agent system for legal information retrieval and summarization",
    version="1.0.0"
)

# Initialize agents
query_agent = QueryAgent()
summary_agent = SummaryAgent()

# Predefined conversational responses
CONVERSATIONAL_RESPONSES = {
    "hello": "Hello! I'm a legal assistant bot. How can I help you with legal information today?",
    "hi": "Hi there! I'm here to help you with legal questions and information. What would you like to know?",
    "how are you": "I'm functioning well and ready to help you with legal questions! What legal matter can I assist you with?",
    "bye": "Goodbye! If you have more legal questions in the future, feel free to ask.",
    "thanks": "You're welcome! Let me know if you need any more help with legal matters.",
    "thank you": "You're welcome! Feel free to ask any legal questions you may have."
}

def is_conversational_query(query: str) -> tuple[bool, str]:
    """
    Determine if a query is conversational and return appropriate response.
    
    Args:
        query (str): The user's query
        
    Returns:
        tuple[bool, str]: (is_conversational, response_if_conversational)
    """
    query_lower = query.lower().strip()
    
    # Check for exact matches
    if query_lower in CONVERSATIONAL_RESPONSES:
        return True, CONVERSATIONAL_RESPONSES[query_lower]
    
    # Check for greetings
    greetings = ["hey", "good morning", "good afternoon", "good evening"]
    if any(greeting in query_lower for greeting in greetings):
        return True, "Hello! I'm your legal assistant bot. How can I help you with legal information today?"
    
    # Check for gratitude
    gratitude = ["appreciate", "grateful", "thank"]
    if any(word in query_lower for word in gratitude):
        return True, "You're welcome! Feel free to ask any legal questions you may have."
    
    return False, ""

class Query(BaseModel):
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/query")
async def process_query(query: Query) -> Dict[Any, Any]:
    try:
        logger.info(f"Processing query: {query.query}")
        
        # Check if it's a conversational query
        is_conversational, conv_response = is_conversational_query(query.query)
        if is_conversational:
            return {
                "simple_explanation": conv_response,
                "key_points": [],
                "important_terms": [],
                "warnings_and_deadlines": [],
                "sources": []
            }
        
        # Get response from query agent for legal queries
        query_result = query_agent.process_query(query.query)
        logger.debug(f"Query agent response: {query_result}")
        
        # Clean and parse any JSON responses
        simple_explanation = clean_json_response(query_result.get("simple_explanation", ""))
        if isinstance(simple_explanation, dict) and "simplified_text" in simple_explanation:
            simple_explanation = simple_explanation["simplified_text"]
        logger.debug(f"Cleaned simple explanation: {simple_explanation}")
            
        key_points = query_result.get("key_points", [])
        if isinstance(key_points, str):
            # Try to parse as JSON if it's a string
            try:
                key_points = clean_json_response(key_points)
            except:
                key_points = [key_points]
        elif isinstance(key_points, list):
            # If it's a list, check if any item needs JSON parsing
            cleaned_points = []
            for point in key_points:
                if isinstance(point, str):
                    try:
                        parsed = clean_json_response(point)
                        if isinstance(parsed, list):
                            cleaned_points.extend(parsed)
                        else:
                            cleaned_points.append(parsed)
                    except:
                        cleaned_points.append(point)
                else:
                    cleaned_points.append(str(point))
            key_points = cleaned_points
        logger.debug(f"Cleaned key points: {key_points}")
        
        # Format the response according to our schema
        response = {
            "simple_explanation": simple_explanation,
            "key_points": key_points,
            "important_terms": query_result.get("important_terms", []),
            "warnings_and_deadlines": query_result.get("warnings_and_deadlines", []),
            "sources": query_result.get("sources", [])
        }
        
        # Add step-by-step guide if available
        if "step_by_step_guide" in query_result:
            response["step_by_step_guide"] = query_result["step_by_step_guide"]
        
        logger.info("Successfully processed query")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 