"""Main route blueprint. Serves the chat page."""

import logging

from flask import Blueprint, current_app, render_template

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Render the main chat interface."""
    knowledge_service = current_app.knowledge_service
    return render_template(
        'index.html',
        book_ready=knowledge_service.is_ready,
        book_names=knowledge_service.book_names,
    )
