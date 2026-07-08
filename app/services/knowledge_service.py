"""Knowledge Service — retrieval over your NEET book(s).

This is the piece that makes the bot answer from YOUR book instead of
its general training knowledge. At startup it loads a pre-built index
(created by scripts/build_index.py from the PDFs in the books/ folder)
and, for every question, retrieves the most relevant passages using
TF-IDF + cosine similarity. Those passages are then handed to the LLM
as context, along with an instruction to answer only from them.

Why TF-IDF instead of a vector/embedding model? It needs no external
API, no GPU, and no extra service — it runs anywhere Python runs, and
works well for keyword-heavy textbook content (chemical names, laws,
formulas, biological terms). If you later want deeper semantic search,
swap this module for an embeddings-based index; the rest of the app
does not need to change.
"""

import logging
import pickle
from dataclasses import dataclass, field
from typing import List, Optional

from app.config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A single retrieved passage from the book, with its source."""
    text: str
    book: str
    page: int
    score: float


@dataclass
class RetrievalResult:
    """Bundle of retrieved chunks plus a flag for whether anything useful was found."""
    chunks: List[RetrievedChunk] = field(default_factory=list)

    @property
    def found_relevant(self) -> bool:
        return len(self.chunks) > 0

    def as_context_text(self) -> str:
        """Format retrieved chunks into a single context block for the LLM prompt."""
        parts = []
        for i, c in enumerate(self.chunks, 1):
            parts.append(
                f"[Source {i} | {c.book}, page {c.page}]\n{c.text.strip()}"
            )
        return "\n\n".join(parts)

    def as_source_list(self) -> List[dict]:
        """Format sources for the API response (used by the frontend to show citations)."""
        seen = set()
        sources = []
        for c in self.chunks:
            key = (c.book, c.page)
            if key in seen:
                continue
            seen.add(key)
            sources.append({"book": c.book, "page": c.page})
        return sources


class KnowledgeService:
    """Loads the book index and retrieves relevant passages for a query."""

    def __init__(self) -> None:
        self.config = AppConfig
        self._vectorizer = None
        self._matrix = None
        self._chunks: List[dict] = []
        self._books: set = set()
        self._load_index()

    def _load_index(self) -> None:
        """Load the pre-built TF-IDF index from disk, if it exists."""
        try:
            with open(self.config.INDEX_PATH, 'rb') as f:
                data = pickle.load(f)
            self._vectorizer = data['vectorizer']
            self._matrix = data['matrix']
            self._chunks = data['chunks']
            self._books = {c['book'] for c in self._chunks}
        except FileNotFoundError:
            logger.warning("No index file at %s.", self.config.INDEX_PATH)
        except Exception as exc:
            logger.error("Failed to load book index: %s", exc)

    @property
    def is_ready(self) -> bool:
        """Whether a book index has been successfully loaded."""
        return self._vectorizer is not None and self._matrix is not None and len(self._chunks) > 0

    @property
    def num_chunks(self) -> int:
        return len(self._chunks)

    @property
    def num_books(self) -> int:
        return len(self._books)

    @property
    def book_names(self) -> List[str]:
        return sorted(self._books)

    def reload(self) -> None:
        """Reload the index from disk (e.g. after running build_index.py again)."""
        self._load_index()

    def retrieve(self, query: str, top_k: Optional[int] = None) -> RetrievalResult:
        """Retrieve the most relevant book passages for a query.

        Args:
            query: The student's question.
            top_k: Number of chunks to retrieve (defaults to config value).

        Returns:
            RetrievalResult with ranked chunks above the similarity threshold.
        """
        if not self.is_ready:
            return RetrievalResult(chunks=[])

        top_k = top_k or self.config.RETRIEVAL_TOP_K

        # Import here so the module can still be imported (e.g. for docs)
        # even if scikit-learn isn't installed yet.
        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix).flatten()

        ranked_idx = scores.argsort()[::-1][:top_k]

        chunks: List[RetrievedChunk] = []
        for idx in ranked_idx:
            score = float(scores[idx])
            if score < self.config.RETRIEVAL_MIN_SCORE:
                continue
            c = self._chunks[idx]
            chunks.append(RetrievedChunk(
                text=c['text'],
                book=c['book'],
                page=c['page'],
                score=score,
            ))

        return RetrievalResult(chunks=chunks)
