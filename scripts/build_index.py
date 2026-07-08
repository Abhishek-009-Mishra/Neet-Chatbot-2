#!/usr/bin/env python3
"""Build the searchable book index.

Run this whenever you add or change PDFs in the books/ folder:

    python scripts/build_index.py

It reads every .pdf in books/, splits it into overlapping chunks
(keeping track of which page each chunk came from), builds a TF-IDF
index over those chunks, and saves everything to data/book_index.pkl.
The Flask app loads that file at startup to answer questions.
"""

import os
import pickle
import sys

# Make the project root importable when running this script directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AppConfig


def extract_pages(pdf_path: str) -> list:
    """Extract text per page from a PDF file.

    Returns a list of (page_number, text) tuples, 1-indexed pages.
    """
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            print(f"  Warning: could not extract page {i}: {exc}")
            text = ""
        text = " ".join(text.split())  # collapse whitespace
        if text.strip():
            pages.append((i, text))
    return pages


def chunk_pages(pages: list, book_name: str, chunk_size: int, overlap: int) -> list:
    """Turn (page_number, text) pairs into overlapping word chunks.

    Each chunk records the page it started on, so answers can cite a
    page number. Chunking by words (not characters) keeps chunks
    readable and roughly consistent in size regardless of layout.
    """
    chunks = []
    for page_num, text in pages:
        words = text.split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "book": book_name,
                    "page": page_num,
                })
            if end >= len(words):
                break
            start = end - overlap  # overlap keeps context continuous across chunk edges
    return chunks


def main() -> None:
    config = AppConfig
    books_folder = config.BOOKS_FOLDER
    index_path = config.INDEX_PATH

    os.makedirs(config.DATA_FOLDER, exist_ok=True)

    pdf_files = [
        f for f in os.listdir(books_folder)
        if f.lower().endswith('.pdf')
    ]

    if not pdf_files:
        print(f"No PDF files found in '{books_folder}'.")
        print("Add your NEET book PDF(s) there and re-run this script.")
        sys.exit(1)

    all_chunks = []
    for filename in pdf_files:
        pdf_path = os.path.join(books_folder, filename)
        book_name = os.path.splitext(filename)[0]
        print(f"Reading '{filename}'...")
        pages = extract_pages(pdf_path)
        print(f"  Extracted text from {len(pages)} page(s).")
        chunks = chunk_pages(
            pages, book_name,
            chunk_size=config.CHUNK_SIZE_WORDS,
            overlap=config.CHUNK_OVERLAP_WORDS,
        )
        print(f"  Created {len(chunks)} chunk(s).")
        all_chunks.extend(chunks)

    if not all_chunks:
        print("No extractable text found in any PDF. If these are scanned")
        print("image-only pages, they will need OCR before this will work.")
        sys.exit(1)

    print(f"\nBuilding TF-IDF index over {len(all_chunks)} chunks from "
          f"{len(pdf_files)} book(s)...")

    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = [c['text'] for c in all_chunks]
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_features=60000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts)

    with open(index_path, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'matrix': matrix,
            'chunks': all_chunks,
        }, f)

    print(f"Saved index to '{index_path}'.")
    print("Done. Start (or restart) the app to use the updated book.")


if __name__ == '__main__':
    main()
