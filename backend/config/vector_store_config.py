from pathlib import Path
import os
from pydantic_settings import BaseSettings
from typing import Optional

class VectorStoreSettings(BaseSettings):
    VECTOR_STORE_DIR: str = "./vector_store"
    COLLECTION_NAME: str = "code_chunks"
    DISTANCE_METRIC: str = "cosine"
    
    class Config:
        env_file = ".env"
        
    def get_persist_directory(self) -> Path:
        """Get and create the vector store directory if it doesn't exist."""
        persist_dir = Path(self.VECTOR_STORE_DIR).resolve()
        persist_dir.mkdir(parents=True, exist_ok=True)
        return persist_dir

# Create a global instance
settings = VectorStoreSettings() 