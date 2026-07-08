"""Application Configuration Module.

Centralizes all configuration from environment variables.
"""

import os
from typing import Optional


class AppConfig:
    """Application configuration loaded from environment variables."""

    # Flask
    SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    # Defaults to OFF. Flask's debug mode exposes an interactive
    # in-browser debugger that allows remote code execution if the app
    # is ever reachable publicly with it on — never enable this in
    # production. Set FLASK_DEBUG=true only for local development.
    DEBUG: bool = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BOOKS_FOLDER: str = os.getenv('BOOKS_FOLDER', os.path.join(BASE_DIR, 'books'))
    DATA_FOLDER: str = os.getenv('DATA_FOLDER', os.path.join(BASE_DIR, 'data'))
    INDEX_PATH: str = os.getenv('INDEX_PATH', os.path.join(DATA_FOLDER, 'book_index.pkl'))

    # LLM (Groq)
    GROQ_API_KEY: Optional[str] = os.getenv('GROQ_API_KEY')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'openai/gpt-oss-120b')
    LLM_TEMPERATURE: float = float(os.getenv('LLM_TEMPERATURE', '0.2'))
    LLM_MAX_TOKENS: int = int(os.getenv('LLM_MAX_TOKENS', '2048'))

    # Retrieval / RAG
    RETRIEVAL_TOP_K: int = int(os.getenv('RETRIEVAL_TOP_K', '6'))
    RETRIEVAL_MIN_SCORE: float = float(os.getenv('RETRIEVAL_MIN_SCORE', '0.05'))
    CHUNK_SIZE_WORDS: int = int(os.getenv('CHUNK_SIZE_WORDS', '220'))
    CHUNK_OVERLAP_WORDS: int = int(os.getenv('CHUNK_OVERLAP_WORDS', '40'))

    # Redis (Session Memory)
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_USERNAME: Optional[str] = os.getenv('REDIS_USERNAME', None)
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD', None)
    REDIS_SSL: bool = os.getenv('REDIS_SSL', 'false').lower() == 'true'
    REDIS_SESSION_TTL: int = int(os.getenv('REDIS_SESSION_TTL', '3600'))

    # Session
    SESSION_TYPE: str = 'redis'
    SESSION_PERMANENT: bool = False
    SESSION_USE_SIGNER: bool = True
    SESSION_KEY_PREFIX: str = 'neet_bot:session:'

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
