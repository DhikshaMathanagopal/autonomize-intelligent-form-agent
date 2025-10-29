import os
from dotenv import load_dotenv

load_dotenv()

FORCE_LOCAL_ONLY = os.getenv("FORCE_LOCAL_ONLY", "false").lower() == "true"
USE_OPENAI_ONLY = os.getenv("USE_OPENAI_ONLY", "false").lower() == "true"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "")
GOOGLE_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

def can_use_openai():
    return (not FORCE_LOCAL_ONLY) and bool(OPENAI_API_KEY)
