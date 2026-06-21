"""
One-time ingestion: BPHSv1.pdf + BPHSv2.pdf → chapter-aware chunks → ChromaDB.

Run:
    python -m bphs_agent.knowledge.ingest
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz  # pymupdf
import chromadb
from openai import OpenAI

from bphs_agent import config

CHUNK_TOKENS = 600
OVERLAP_TOKENS = 100
BATCH_SIZE = 100  # OpenAI embedding batch limit

# Patterns that signal a new chapter/adhyaya heading in BPHS translations
_CHAPTER_RE = re.compile(
    r"(?i)(chapter\s+\d+|adhyaya\s+\d+|ch\.\s*\d+)",
)
# Sloka/verse range pattern in text (e.g. "1-3.", "Sl. 4", "verse 5")
_SLOKA_RE = re.compile(r"(?i)(sl(?:oka)?\.?\s*\d+[-–]?\d*|verse\s+\d+)")


def _extract_pages(pdf_path: Path) -> list[dict]:
    """Return list of {page, text} dicts from a PDF."""
    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages


def _detect_chapter(text: str) -> str | None:
    m = _CHAPTER_RE.search(text[:200])
    return m.group(0).strip() if m else None


def _detect_sloka_range(text: str) -> str | None:
    m = _SLOKA_RE.search(text[:300])
    return m.group(0).strip() if m else None


def _simple_tokenize(text: str) -> list[str]:
    """Very cheap whitespace tokeniser — good enough for chunking heuristics."""
    return text.split()


def _chunk_pages(pages: list[dict], source: str) -> list[dict]:
    """
    Slide a window over concatenated page text, respecting chapter boundaries.
    Returns list of {text, chapter, sloka_range, source, page_start}.
    """
    chunks: list[dict] = []
    current_chapter = "Unknown"
    buffer_words: list[str] = []
    buffer_page_start = 1

    def flush(words: list[str], chapter: str, page: int) -> None:
        text = " ".join(words).strip()
        if len(text) < 50:
            return
        sloka = _detect_sloka_range(text)
        chunks.append(
            {
                "text": text,
                "chapter": chapter,
                "sloka_range": sloka or "",
                "source": source,
                "page_start": page,
            }
        )

    for page_info in pages:
        page_text = page_info["text"]
        page_num = page_info["page"]

        # Detect chapter heading change
        detected = _detect_chapter(page_text)
        if detected:
            current_chapter = detected

        words = _simple_tokenize(page_text)

        # If adding this page would overflow, flush with overlap
        while len(buffer_words) + len(words) > CHUNK_TOKENS:
            flush(buffer_words[:CHUNK_TOKENS], current_chapter, buffer_page_start)
            buffer_words = buffer_words[CHUNK_TOKENS - OVERLAP_TOKENS :]
            buffer_page_start = page_num

        buffer_words.extend(words)

    if buffer_words:
        flush(buffer_words, current_chapter, buffer_page_start)

    return chunks


def _embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=config.EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def ingest(pdf_paths: list[Path] | None = None) -> int:
    """Ingest PDFs into ChromaDB. Returns total chunks written."""
    if pdf_paths is None:
        pdf_paths = [
            config.DATA_PATH / "BPHSv1.pdf",
            config.DATA_PATH / "BPHSv2.pdf",
        ]

    oai = OpenAI(api_key=config.OPENAI_API_KEY)
    db = chromadb.PersistentClient(path=str(config.CHROMA_PATH))

    # Drop + recreate so re-runs are idempotent
    try:
        db.delete_collection(config.CHROMA_COLLECTION)
    except Exception:
        pass
    col = db.create_collection(
        config.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks: list[dict] = []
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            print(f"[WARN] {pdf_path} not found — skipping", file=sys.stderr)
            continue
        print(f"[ingest] Extracting {pdf_path.name}…")
        pages = _extract_pages(pdf_path)
        chunks = _chunk_pages(pages, pdf_path.name)
        all_chunks.extend(chunks)
        print(f"         → {len(chunks)} chunks")

    if not all_chunks:
        print("[ingest] No chunks produced — check PDF paths.", file=sys.stderr)
        return 0

    print(f"[ingest] Embedding {len(all_chunks)} chunks with {config.EMBEDDING_MODEL}…")
    total = 0
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        embeddings = _embed_batch(oai, texts)
        col.add(
            ids=[f"chunk_{i + j}" for j in range(len(batch))],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "chapter": c["chapter"],
                    "sloka_range": c["sloka_range"],
                    "source": c["source"],
                    "page_start": c["page_start"],
                }
                for c in batch
            ],
        )
        total += len(batch)
        print(f"         {total}/{len(all_chunks)}", end="\r")

    print(f"\n[ingest] Done. {total} chunks in ChromaDB at {config.CHROMA_PATH}")
    return total


if __name__ == "__main__":
    ingest()
