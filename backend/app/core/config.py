from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_name: str = "KnowledgeBot"
    app_version: str = "1.0.0"
    debug: bool = False
    frontend_origin: str = "http://localhost:5173"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # LLM
    llm_model_id: str = "microsoft/phi-2"
    embedding_model_id: str = "all-MiniLM-L6-v2"
    max_new_tokens: int = 512
    temperature: float = 0.3
    top_p: float = 0.9

    # Vector Store
    chroma_persist_dir: str = "./knowledge_base/chroma_db"
    collection_name: str = "knowledge_base"

    # Retrieval
    top_k_results: int = 5
    similarity_threshold: float = 0.35
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Logging
    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_rotation: str = "10 MB"
    log_retention: str = "30 days"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
