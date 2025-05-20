from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Legal Multi-Agent Chatbot"
    
    # Google Gemini Settings
    GOOGLE_API_KEY: str
    
    # Document Settings
    DOCS_DIR: Path = Path("data/legal_docs")
    CHUNK_SIZE: int = 1000
    
    # Vector Store Settings
    COLLECTION_NAME: str = "legal_documents"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 