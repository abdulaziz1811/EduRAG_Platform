"""
EduRAG - Retrieval Layer
========================
Drop this in as backend/app/retrieval.py, then replace the retrieval parts of
core.py with imports from here.

Fixes vs the current core.py:
  1. load_rag_index() re-read index.faiss and unpickled chunks.pkl on EVERY
     search. Now loaded once and held in memory.
  2. Queries were embedded raw while the index is now normalized Arabic. The
     same normalize_arabic() is applied to both sides.
  3. Embeddings are L2-normalized to match IndexFlatIP (cosine).
  4. explain_error_with_rag() did np.array([query_vector]) on an already-2D
     array -> 3D, which FAISS rejects. Fixed.
  5. Page number was overwritten by the LAST retrieved chunk, so the citation
     pointed at the least relevant hit. Now taken from the top-scoring chunk.
  6. Results carry their similarity score, so weak retrievals can be detected
     instead of silently feeding noise to the LLM.
"""

import os
import pickle
import logging
from functools import lru_cache
from typing import List, Dict, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.build_index import normalize_arabic, MODEL_NAME  # single source of truth

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DATA_DIR = os.path.join(BASE_DIR, "rag_data")
INDEX_PATH = os.path.join(RAG_DATA_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(RAG_DATA_DIR, "chunks.pkl")

# Below this cosine score, a hit is not really about the query.
MIN_SCORE = 0.35


@lru_cache(maxsize=1)
def get_model() -> Optional[SentenceTransformer]:
    try:
        model = SentenceTransformer(MODEL_NAME)
        logger.info(f"Embedding model loaded: {MODEL_NAME}")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return None


@lru_cache(maxsize=1)
def get_index() -> Tuple[Optional[faiss.Index], Optional[list]]:
    """Loaded once per process, not once per request."""
    if not (os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH)):
        logger.warning("RAG index missing. Run: python app/build_index.py")
        return None, None
    try:
        index = faiss.read_index(INDEX_PATH)
        with open(CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)
        logger.info(f"RAG loaded: {index.ntotal} vectors, {len(chunks)} chunks")
        return index, chunks
    except Exception as e:
        logger.error(f"Failed to load RAG index: {e}")
        return None, None


def search(query: str, top_k: int = 10, min_score: float = MIN_SCORE) -> List[Dict]:
    """
    Returns [{content, page, score}] sorted by relevance, weak hits dropped.
    """
    model = get_model()
    index, chunks = get_index()
    if model is None or index is None:
        return []

    try:
        vector = model.encode(
            [normalize_arabic(query)],
            normalize_embeddings=True,
        ).astype("float32")                       # shape (1, dim) — already 2D

        scores, indices = index.search(vector, k=top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(chunks):
                continue
            if score < min_score:
                continue
            chunk = chunks[idx]
            if isinstance(chunk, dict):
                content = chunk.get("content", "")
                page = chunk.get("metadata", {}).get("page")
            else:
                content, page = str(chunk), None
            if content:
                results.append({"content": content, "page": page, "score": float(score)})
        return results
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return []


def build_context(query: str, top_k: int = 10, max_chars: int = 3000) -> Tuple[str, Optional[int]]:
    """
    Convenience wrapper: joined context text + the page of the best hit.
    Returns ("", None) when nothing passes the relevance threshold — the caller
    should then tell the user the textbook has no coverage, not hallucinate.
    """
    hits = search(query, top_k=top_k)
    if not hits:
        return "", None

    parts, total = [], 0
    for hit in hits:
        piece = f"[صفحة {hit['page']}] {hit['content']}" if hit["page"] else hit["content"]
        if total + len(piece) > max_chars:
            break
        parts.append(piece)
        total += len(piece)

    return "\n---\n".join(parts), hits[0]["page"]


# ===================================================================
# Replacement for core.explain_error_with_rag
# ===================================================================

def explain_error_with_rag(question_text: str, correct_answer: str, concept: str,
                           groq_client) -> str:
    """
    Same signature as before plus an injected groq_client (avoids the import
    cycle and makes this testable).
    """
    query = f"شرح درس {concept} وطريقة حل {question_text}"
    context, page = build_context(query, top_k=5, max_chars=1500)

    if not context:
        return (
            f"الإجابة الصحيحة هي: {correct_answer}\n\n"
            "لم أعثر على شرح مطابق في الكتاب المدرسي لهذا السؤال، "
            "يُفضل مراجعة المعلم."
        )

    reference = f"المرجع: الصفحة رقم ({page}) من الكتاب الدراسي." if page else ""

    prompt = f"""أنت معلم رياضيات خبير. اشرح الحل بأسلوب سردي واضح ومختصر.

المفهوم: {concept}
السؤال: {question_text}
الإجابة الصحيحة: {correct_answer}

السياق من الكتاب المدرسي:
{context}

المطلوب:
1. اشرح خطوات الحل رياضياً بأسلوب مباشر.
2. اعتمد على السياق أعلاه فقط، ولا تضف معلومات من خارجه.
3. بدون إيموجي أو عناوين مرقّمة.
4. اختم بعبارة: "{reference}" """

    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return f"الإجابة الصحيحة هي {correct_answer}. {reference}"