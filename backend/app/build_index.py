import os
import faiss
import pickle
import pytesseract
import gc  # Garbage Collector لتنظيف الذاكرة
from pdf2image import convert_from_path, pdfinfo_from_path
from sentence_transformers import SentenceTransformer

# --- إعدادات المسارات ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "data", "math.pdf")
INDEX_PATH = os.path.join(BASE_DIR, "rag_data", "math.index")
CHUNKS_PATH = os.path.join(BASE_DIR, "rag_data", "chunks.pkl")

def build_index():
    print(f"📖 جاري قراءة الكتاب من: {PDF_PATH}")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ خطأ: الملف غير موجود في {PDF_PATH}")
        return

    text_chunks = []
    
    try:
        # 1. معرفة عدد الصفحات أولاً
        info = pdfinfo_from_path(PDF_PATH)
        total_pages = info["Pages"]
        print(f"📄 عدد صفحات الكتاب: {total_pages}")
        
        # 2. المعالجة بالدفعات (كل 5 صفحات مع بعض عشان الرام ما يمتلي)
        BATCH_SIZE = 5
        
        print("📸 جاري تحويل الصفحات وقراءتها (نظام الدفعات)...")
        
        for start_page in range(1, total_pages + 1, BATCH_SIZE):
            end_page = min(start_page + BATCH_SIZE - 1, total_pages)
            
            # تحويل دفعة صغيرة فقط
            images = convert_from_path(PDF_PATH, dpi=300, first_page=start_page, last_page=end_page)
            
            for i, image in enumerate(images):
                current_page_num = start_page + i
                
                # استخراج النص (OCR)
                text = pytesseract.image_to_string(image, lang='ara')
                
                # تنظيف النص
                if text.strip():
                    clean_lines = [line.strip() for line in text.split('\n') if line.strip()]
                    cleaned_text = " ".join(clean_lines)

                    if len(cleaned_text) > 50:
                        text_chunks.append({
                            "page_number": current_page_num,
                            "content": cleaned_text
                        })
            
            print(f"   ✅ تم الانتهاء من الصفحات {start_page} إلى {end_page}...")
            
            # تنظيف الذاكرة يدوياً بعد كل دفعة
            del images
            gc.collect()

    except Exception as e:
        print(f"❌ حدث خطأ أثناء المعالجة: {e}")
        return

    print(f"⚡ تم استخراج {len(text_chunks)} فقرة/صفحة نصية.")

    # 3. تحميل نموذج الذكاء الاصطناعي
    print("🧠 جاري تحميل نموذج اللغة...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 

    # 4. بناء الفهرس
    print("🏗️ جاري بناء هيكل البحث (FAISS Index)...")
    embeddings = model.encode([chunk["content"] for chunk in text_chunks], show_progress_bar=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 5. الحفظ
    print("💾 جاري الحفظ...")
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(text_chunks, f)

    print("-" * 50)
    print("✅ تم بناء قاعدة المعرفة بنجاح! 🎉")
    print("-" * 50)

if __name__ == "__main__":
    build_index()