from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app"
    ]
    
    CHROMA_DB_PATH: str = str(Path(__file__).parent.parent.parent / "chroma_db")
    DATA_DIR: str = str(Path(__file__).parent.parent.parent / "data")
    SCRAPED_FILES_DIR: str = str(Path(__file__).parent.parent.parent / "scraped_files" / "documents")
    
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    
    TOP_K_DEFAULT: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
