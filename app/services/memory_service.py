"""Conversation Memory Service.

Uses Redis if configured; otherwise falls back to a simple in-memory
dict, so the bot still remembers a conversation within the same process
even without Redis set up.
"""

import json
import logging
import threading
from typing import Dict, List, Optional

import redis
from redis import Redis as RedisClient

from app.config import AppConfig

logger = logging.getLogger(__name__)


class MemoryService:
    """Manages conversation memory with Redis primary and in-memory fallback."""

    def __init__(self) -> None:
        self.config = AppConfig
        self._client: Optional[RedisClient] = None
        self._fallback: Dict[str, List[Dict[str, str]]] = {}
        self._lock = threading.Lock()
        self._redis_available = False
        self._connect()

    def _connect(self) -> None:
        try:
            connection_params = {
                'host': self.config.REDIS_HOST,
                'port': self.config.REDIS_PORT,
                'decode_responses': True,
                'socket_connect_timeout': 2,
            }
            if self.config.REDIS_USERNAME:
                connection_params['username'] = self.config.REDIS_USERNAME
            if self.config.REDIS_PASSWORD:
                connection_params['password'] = self.config.REDIS_PASSWORD
            if self.config.REDIS_SSL:
                connection_params['ssl'] = True

            self._client = redis.Redis(**connection_params)
            self._client.ping()
            self._redis_available = True
            logger.info("Connected to Redis at %s:%s", self.config.REDIS_HOST, self.config.REDIS_PORT)
        except Exception as exc:
            logger.info("Redis unavailable, using in-memory conversation storage: %s", exc)
            self._client = None
            self._redis_available = False

    def _get_session_key(self, session_id: str) -> str:
        return f"neet_bot:conversation:{session_id}"

    def get_conversation_history(self, session_id: str, max_turns: int = 8) -> List[Dict[str, str]]:
        if self._redis_available and self._client is not None:
            try:
                key = self._get_session_key(session_id)
                raw = self._client.lrange(key, 0, -1)
                messages = [json.loads(item) for item in raw]
                return messages[-(max_turns * 2):]
            except Exception as exc:
                logger.error("Redis read error [%s]: %s", session_id, exc)

        with self._lock:
            messages = self._fallback.get(session_id, [])
        return messages[-(max_turns * 2):]

    def add_to_conversation(self, session_id: str, role: str, content: str) -> None:
        message = {"role": role, "content": content}

        with self._lock:
            self._fallback.setdefault(session_id, []).append(message)

        if self._redis_available and self._client is not None:
            try:
                key = self._get_session_key(session_id)
                self._client.rpush(key, json.dumps(message))
                self._client.expire(key, self.config.REDIS_SESSION_TTL)
            except Exception as exc:
                logger.error("Redis write error [%s]: %s", session_id, exc)
                self._redis_available = False

    def clear_conversation(self, session_id: str) -> None:
        with self._lock:
            self._fallback.pop(session_id, None)

        if self._redis_available and self._client is not None:
            try:
                self._client.delete(self._get_session_key(session_id))
            except Exception as exc:
                logger.error("Redis delete error [%s]: %s", session_id, exc)

    def health_check(self) -> bool:
        if not self._redis_available or self._client is None:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            return False
