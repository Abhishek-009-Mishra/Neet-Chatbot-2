"""NEET Book Bot - AI study assistant that answers strictly from your book(s)."""

import os
import logging
from typing import Any

from flask import Flask
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from app.config import AppConfig


def create_app(config_object: Any = None) -> Flask:
    """Application factory for NEET Book Bot."""
    app = Flask(
        __name__,
        static_folder='static',
        static_url_path='/static',
        template_folder='templates'
    )

    if config_object is None:
        app.config.from_object(AppConfig)
    else:
        app.config.from_object(config_object)

    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BOOKS_FOLDER'], exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    register_blueprints(app)
    initialize_services(app)

    return app


def register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    from app.routes.chat import chat_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)


def initialize_services(app: Flask) -> None:
    """Initialize application services and attach to app instance."""
    from app.services.llm_service import LLMService
    from app.services.memory_service import MemoryService
    from app.services.prompt_manager import PromptManager
    from app.services.knowledge_service import KnowledgeService

    app.knowledge_service = KnowledgeService()
    app.prompt_manager = PromptManager()
    app.llm_service = LLMService(prompt_manager=app.prompt_manager)
    app.memory_service = MemoryService()

    if app.knowledge_service.is_ready:
        app.logger.info(
            "Knowledge base loaded: %d chunks from %d book(s).",
            app.knowledge_service.num_chunks,
            app.knowledge_service.num_books,
        )
    else:
        app.logger.warning(
            "No book index found. Add PDFs to '%s' and run "
            "'python scripts/build_index.py' to enable book-based answers.",
            app.config['BOOKS_FOLDER'],
        )

    app.logger.info("All services initialized successfully.")
