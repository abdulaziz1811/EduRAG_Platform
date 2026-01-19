"""
EduRAG Pro - RAG Index Builder
==============================
بناء قاعدة المعرفة الموثقة من كتاب PDF لنظام الإشراف الأكاديمي
"""

import os
import faiss
import pickle
import PyPDF2
import re
import logging
from sentence_transformers import SentenceTransformer

# إعداد اللوقر (Logging) لنسخة Pro
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- إعدادات المسارات ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAG_DATA_DIR = os.path.join(BASE_DIR, "rag_data")

# تأكد من أن ملف math.pdf موجود في مجلد backend/data
PDF_PATH = os.path.join(DATA_DIR, "math.pdf")
INDEX_PATH = os.path.join(RAG_DATA_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(RAG_DATA_DIR, "chunks.pkl")

def extract_text_from_pdf():
    """
    استخراج النص من PDF وتقسيمه لفقرات منطقية مع حفظ رقم الصفحة لكل فقرة
    """
    logger.info(f"جاري قراءة المحتوى العلمي من المسار: {PDF_PATH}")
    
    if not os.path.exists(PDF_PATH):
        logger.error(f"فشل العثور على ملف المرجع: {PDF_PATH}")
        return []

    text_chunks = []
    
    try:
        with open(PDF_PATH, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"إجمالي عدد صفحات المستند المستهدفة: {total_pages}")
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text and text.strip():
                    # تنظيف النص ومعالجته برمجياً
                    cleaned_text = re.sub(r'\s+', ' ', text).strip()
                    
                    # تقسيم النص إلى فقرات (Chunks) بطول 800 حرف لضمان جودة الاسترجاع
                    if len(cleaned_text) > 800:
                        sentences = re.split(r'[.؟!]\s+', cleaned_text)
                        current_chunk = ""
                        
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) < 800:
                                current_chunk += sentence + ". "
                            else:
                                if current_chunk.strip():
                                    text_chunks.append({
                                        "page_number": page_num + 1,
                                        "content": current_chunk.strip()
                                    })
                                current_chunk = sentence + ". "
                        
                        # إضافة الفقرة الأخيرة المتبقية
                        if current_chunk.strip():
                            text_chunks.append({
                                "page_number": page_num + 1,
                                "content": current_chunk.strip()
                            })
                    else:
                        text_chunks.append({
                            "page_number": page_num + 1,
                            "content": cleaned_text
                        })
                
                if (page_num + 1) % 20 == 0:
                    logger.info(f"تمت معالجة {page_num + 1} صفحة بنجاح...")
    
    except Exception as e:
        logger.error(f"حدث خطأ غير متوقع أثناء استخراج البيانات: {e}")
        return []
    
    return text_chunks

def build_index():
    """
    بناء الفهرس الرقمي وربط النصوص بالمراجع الصفحية
    """
    # 1. استخراج النص والميتا داتا
    text_chunks = extract_text_from_pdf()
    
    if not text_chunks:
        logger.error("فشل عملية بناء قاعدة المعرفة: لم يتم استخراج أي بيانات صالحة.")
        return
    
    logger.info(f"تم استخراج {len(text_chunks)} فقرة تعليمية موثقة برقم الصفحة.")
    
    # 2. تحميل نموذج الذكاء الاصطناعي (Embeddings)
    logger.info("جاري تحميل مفسر اللغة (paraphrase-multilingual-MiniLM-L12-v2)...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # 3. توليد الـ Vector Embeddings لنصوص الكتاب
    logger.info("جاري تحويل الفقرات التعليمية إلى متجهات رقمية...")
    contents = [chunk["content"] for chunk in text_chunks]
    embeddings = model.encode(contents, show_progress_bar=True, batch_size=32)
    
    # 4. بناء هيكل البحث السريع (FAISS Index)
    logger.info("إنشاء الفهرس الرقمي للبحث الدلالي (FAISS Index)...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    
    # 5. حفظ قاعدة المعرفة المحدثة
    logger.info("جاري حفظ الفهرس والبيانات الوصفية الموثقة...")
    os.makedirs(RAG_DATA_DIR, exist_ok=True)
    
    # حفظ الفهرس (index.faiss)
    faiss.write_index(index, INDEX_PATH)
    
    # التعديل الهام: حفظ النص مع رقم الصفحة في كائن واحد لضمان دقة المراجع
    chunks_with_metadata = []
    for chunk in text_chunks:
        chunks_with_metadata.append({
            "content": chunk["content"],
            "metadata": {"page": chunk["page_number"]}
        })
    
    # حفظ النصوص مع مراجعها (chunks.pkl)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks_with_metadata, f)
    
    logger.info("=" * 60)
    logger.info("✅ تم تحديث قاعدة معرفة EduRAG Pro بنجاح")
    logger.info(f"إجمالي الوحدات النصية الموثقة: {len(chunks_with_metadata)}")
    logger.info(f"مسار الفهرس: {INDEX_PATH}")
    logger.info("=" * 60)

if __name__ == "__main__":
    build_index()