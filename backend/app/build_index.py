"""
EduRAG Pro - RAG Index Builder (v2)
===================================
Rebuilds the knowledge base from the curriculum PDF.

What changed vs v1:
  1. Arabic-ratio validation of the extracted text. The embedded text layer of
     math.pdf contains 0 Arabic characters, so v1 indexed pure noise.
  2. OCR fallback (Tesseract, ara) for any page whose text layer is unusable.
  3. Arabic normalization (alef forms, taa marbuta, diacritics, tatweel)
     applied at index time. The SAME function must be applied to queries.
  4. Word-based chunking with overlap, so a rule stays attached to its example.
  5. L2-normalized embeddings + IndexFlatIP  -> cosine similarity, which is what
     paraphrase-multilingual-MiniLM-L12-v2 was actually trained for.
  6. OCR output is cached to disk; re-running does not re-OCR 224 pages.

Requirements:
    pip install pypdf pypdfium2 pytesseract pillow sentence-transformers faiss-cpu
System dependency:
    Ubuntu/Debian : sudo apt-get install tesseract-ocr tesseract-ocr-ara
    macOS         : brew install tesseract tesseract-lang
    Windows       : install UB-Mannheim build, then add Arabic traineddata

Usage:
    python app/build_index.py              # normal build (uses OCR cache)
    python app/build_index.py --force-ocr  # ignore cache, re-OCR everything
"""

import os
import re
import sys
import json
import pickle
import logging
from typing import List, Dict

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ===== Paths =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAG_DATA_DIR = os.path.join(BASE_DIR, "rag_data")

PDF_PATH = os.path.join(DATA_DIR, "math.pdf")
INDEX_PATH = os.path.join(RAG_DATA_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(RAG_DATA_DIR, "chunks.pkl")
OCR_CACHE_PATH = os.path.join(RAG_DATA_DIR, "ocr_cache.json")

# ===== Tunables =====
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_WORDS = 120          # ~700-800 chars of Arabic
CHUNK_OVERLAP_WORDS = 30   # keeps a rule glued to the example that follows it
MIN_CHUNK_CHARS = 80
OCR_DPI_SCALE = 3          # render scale for OCR; 3 ~= 216 DPI
PAGE_ARABIC_RATIO_MIN = 0.30   # below this, a page's text layer is treated as garbage
BUILD_ARABIC_RATIO_MIN = 0.50  # below this, the whole build is aborted


# ===================================================================
# Text utilities
# ===================================================================

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
DIACRITICS_RE = re.compile(r"[\u064B-\u0652\u0670\u0640]")  # harakat + tatweel


def arabic_ratio(text: str) -> float:
    """Share of letter characters that are Arabic. The core sanity check."""
    letters = re.findall(r"[^\W\d_]", text, flags=re.UNICODE)
    if not letters:
        return 0.0
    arabic = ARABIC_RE.findall(text)
    return len(arabic) / len(letters)


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic for embedding. MUST be applied to queries too, otherwise
    index and query live in slightly different spaces.
    """
    if not text:
        return ""
    text = DIACRITICS_RE.sub("", text)          # strip harakat and tatweel
    text = re.sub(r"[إأآٱ]", "ا", text)          # unify alef forms
    text = text.replace("ى", "ي")                # alef maqsura -> ya
    text = text.replace("ة", "ه")                # taa marbuta -> haa
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    text = re.sub(r"[٠١٢٣٤٥٦٧٨٩]",
                  lambda m: str("٠١٢٣٤٥٦٧٨٩".index(m.group())), text)  # arabic-indic digits
    text = re.sub(r"[^\w\s\u0600-\u06FF=+\-*/×÷^√²³.,()%<>]", " ", text)  # keep math symbols
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ===================================================================
# Extraction
# ===================================================================

def ocr_page(pdf_doc, page_index: int) -> str:
    """Render one page and run Arabic OCR on it."""
    import pytesseract
    page = pdf_doc[page_index]
    image = page.render(scale=OCR_DPI_SCALE).to_pil()
    return pytesseract.image_to_string(image, lang="ara", config="--psm 3")


def extract_pages(force_ocr: bool = False) -> List[Dict]:
    """
    Return [{page: int, text: str, source: 'text-layer'|'ocr'}].
    Uses the embedded text layer when it is genuinely Arabic, OCR otherwise.
    """
    if not os.path.exists(PDF_PATH):
        logger.error(f"PDF not found: {PDF_PATH}")
        return []

    reader = PdfReader(PDF_PATH)
    total = len(reader.pages)
    logger.info(f"Opened PDF with {total} pages")

    # Load OCR cache
    cache: Dict[str, str] = {}
    if os.path.exists(OCR_CACHE_PATH) and not force_ocr:
        try:
            with open(OCR_CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info(f"Loaded OCR cache with {len(cache)} pages")
        except Exception as e:
            logger.warning(f"Could not read OCR cache: {e}")

    pdf_doc = None
    pages: List[Dict] = []
    ocr_used = 0

    for i in range(total):
        raw = reader.pages[i].extract_text() or ""
        if arabic_ratio(raw) >= PAGE_ARABIC_RATIO_MIN and len(raw.strip()) > 100:
            pages.append({"page": i + 1, "text": raw, "source": "text-layer"})
            continue

        # Text layer unusable for this page -> OCR
        key = str(i)
        if key in cache:
            text = cache[key]
        else:
            if pdf_doc is None:
                import pypdfium2 as pdfium
                pdf_doc = pdfium.PdfDocument(PDF_PATH)
                logger.info("Text layer unusable, starting OCR (this is slow the first time)")
            try:
                text = ocr_page(pdf_doc, i)
            except Exception as e:
                logger.error(f"OCR failed on page {i + 1}: {e}")
                text = ""
            cache[key] = text

        ocr_used += 1
        pages.append({"page": i + 1, "text": text, "source": "ocr"})

        if (i + 1) % 20 == 0:
            logger.info(f"Processed {i + 1}/{total} pages")

    # Persist cache
    if ocr_used:
        os.makedirs(RAG_DATA_DIR, exist_ok=True)
        with open(OCR_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        logger.info(f"OCR applied to {ocr_used} pages, cache saved")

    return pages


# ===================================================================
# Chunking
# ===================================================================

def chunk_pages(pages: List[Dict]) -> List[Dict]:
    """
    Word-based sliding window with overlap, per page.
    v1 cut on [.؟!] which almost never appears in a scanned math textbook,
    so most pages became one arbitrary 800-char blob with no overlap.
    """
    chunks: List[Dict] = []

    for page in pages:
        cleaned = normalize_arabic(page["text"])
        if len(cleaned) < MIN_CHUNK_CHARS:
            continue

        words = cleaned.split()
        step = CHUNK_WORDS - CHUNK_OVERLAP_WORDS
        start = 0

        while start < len(words):
            window = words[start:start + CHUNK_WORDS]
            content = " ".join(window)
            if len(content) >= MIN_CHUNK_CHARS:
                chunks.append({
                    "content": content,
                    "metadata": {"page": page["page"], "source": page["source"]},
                })
            if start + CHUNK_WORDS >= len(words):
                break
            start += step

    return chunks


# ===================================================================
# Build
# ===================================================================

def build_index(force_ocr: bool = False) -> None:
    pages = extract_pages(force_ocr=force_ocr)
    if not pages:
        logger.error("No pages extracted. Aborting.")
        return

    # ---- Quality gate: never silently index garbage again ----
    corpus = " ".join(p["text"] for p in pages)
    ratio = arabic_ratio(corpus)
    logger.info(f"Corpus Arabic ratio: {ratio:.1%} ({len(corpus):,} chars)")
    if ratio < BUILD_ARABIC_RATIO_MIN:
        logger.error(
            f"ABORTED: only {ratio:.1%} of the extracted text is Arabic "
            f"(minimum {BUILD_ARABIC_RATIO_MIN:.0%}). "
            "The knowledge base would be noise. Check that Tesseract and the "
            "'ara' language pack are installed, then rerun with --force-ocr."
        )
        return

    chunks = chunk_pages(pages)
    if not chunks:
        logger.error("No usable chunks produced. Aborting.")
        return
    logger.info(f"Built {len(chunks)} chunks from {len(pages)} pages")

    logger.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    logger.info("Encoding chunks...")
    contents = [c["content"] for c in chunks]
    embeddings = model.encode(
        contents,
        show_progress_bar=True,
        batch_size=32,
        normalize_embeddings=True,   # unit vectors -> inner product == cosine
    ).astype("float32")

    logger.info("Building FAISS index (IndexFlatIP / cosine)")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs(RAG_DATA_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    ocr_pages = sum(1 for p in pages if p["source"] == "ocr")
    logger.info("=" * 60)
    logger.info("Knowledge base rebuilt successfully")
    logger.info(f"  chunks     : {len(chunks)}")
    logger.info(f"  vectors    : {index.ntotal}")
    logger.info(f"  OCR pages  : {ocr_pages}/{len(pages)}")
    logger.info(f"  index path : {INDEX_PATH}")
    logger.info("=" * 60)

    # Sample output so you can eyeball retrieval quality immediately
    logger.info("Sample chunk:")
    logger.info(chunks[len(chunks) // 2]["content"][:300])


if __name__ == "__main__":
    build_index(force_ocr="--force-ocr" in sys.argv)