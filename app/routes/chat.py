"""Chat route blueprint.

Handles text chat: retrieves relevant book passages, asks the LLM to
answer grounded in them, and returns the answer plus its sources.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict

from flask import Blueprint, current_app, jsonify, request, session

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


def _get_session_id() -> str:
    if not session.get('user_id'):
        session['user_id'] = str(uuid.uuid4())
        session.permanent = True
    return session['user_id']


def _get_services():
    return (
        current_app.llm_service,
        current_app.memory_service,
        current_app.knowledge_service,
    )


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle a text chat message and answer it from the book."""
    session_id = _get_session_id()
    llm_service, memory_service, knowledge_service = _get_services()

    text = request.form.get('text')
    if not text and request.is_json:
        text = (request.json or {}).get('text')
    if not text or not text.strip():
        return jsonify({'error': 'No text provided.'}), 400
    text = text.strip()

    response_data = _process_text_query(session_id, text, llm_service, memory_service, knowledge_service)
    return jsonify(response_data)


@chat_bp.route('/chat/clear', methods=['POST'])
def clear_conversation():
    """Clear the conversation history for the current session."""
    session_id = _get_session_id()
    current_app.memory_service.clear_conversation(session_id)
    logger.info("Conversation cleared for session %s", session_id)
    return jsonify({'status': 'ok', 'message': 'Conversation cleared.'})


@chat_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    memory_service = current_app.memory_service
    knowledge_service = current_app.knowledge_service

    return jsonify({
        'status': 'healthy',
        'redis': 'connected' if memory_service.health_check() else 'in-memory fallback',
        'book_index': {
            'ready': knowledge_service.is_ready,
            'books': knowledge_service.book_names,
            'chunks': knowledge_service.num_chunks,
        },
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


def _process_text_query(
    session_id: str,
    user_text: str,
    llm_service,
    memory_service,
    knowledge_service,
) -> Dict:
    """Retrieve book context, generate a grounded answer, and save to memory."""
    # 1. Retrieve relevant passages from the book
    retrieval = knowledge_service.retrieve(user_text)

    # 2. Get conversation history
    history = memory_service.get_conversation_history(session_id)

    # 3. Generate LLM response grounded in retrieved context
    llm_result = llm_service.generate(
        user_query=user_text,
        context_text=retrieval.as_context_text(),
        found_relevant=retrieval.found_relevant,
        conversation_history=history,
        session_id=session_id,
    )

    # 4. Save to memory
    memory_service.add_to_conversation(session_id, 'user', user_text)
    memory_service.add_to_conversation(session_id, 'assistant', llm_result.text)

    result: Dict = {
        'text': llm_result.text,
        'sources': retrieval.as_source_list(),
        'book_ready': knowledge_service.is_ready,
        'cache': {
            'prompt_tokens': llm_result.prompt_tokens,
            'cached_tokens': llm_result.cached_tokens,
            'hit_rate': round(llm_result.cache_hit_rate, 1),
            'completion_tokens': llm_result.completion_tokens,
        },
    }
    return result
