import os
import faiss
import pickle
import PyPDF2
import re
from sentence_transformers import SentenceTransformer

# --- إعدادات المسارات ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "data", "math.pdf")
INDEX_PATH = os.path.join(BASE_DIR, "rag_data", "index.faiss")
CHUNKS_PATH = os.path.join(BASE_DIR, "rag_data", "chunks.pkl")

def extract_text_from_pdf():
    """
    استخراج النص مباشرة من PDF بدون OCR
    أسرع وأدق بكثير من OCR
    """
    print(f"📖 جاري قراءة الكتاب من: {PDF_PATH}")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ خطأ: الملف غير موجود في {PDF_PATH}")
        return []

    text_chunks = []
    
    try:
        with open(PDF_PATH, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            print(f"📄 عدد صفحات الكتاب: {total_pages}")
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text.strip():
                    # تنظيف النص من الأسطر الفارغة والمسافات الزائدة
                    cleaned_text = re.sub(r'\s+', ' ', text).strip()
                    
                    # تقسيم النص إلى فقرات منطقية (كل 500-800 حرف)
                    if len(cleaned_text) > 800:
                        # تقسيم النص لفقرات أصغر
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
                        
                        # إضافة آخر فقرة
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
                
                if (page_num + 1) % 10 == 0:
                    print(f"   ✅ تم معالجة {page_num + 1} صفحة...")
    
    except Exception as e:
        print(f"❌ حدث خطأ أثناء القراءة: {e}")
        return []
    
    return text_chunks

def build_index():
    """
    بناء الفهرس مع تحسينات كبيرة في جودة الاستخراج
    """
    # 1. استخراج النص
    text_chunks = extract_text_from_pdf()
    
    if not text_chunks:
        print("❌ فشل استخراج النصوص من الكتاب")
        return
    
    print(f"⚡ تم استخراج {len(text_chunks)} فقرة نصية")
    
    # عرض عينة من النصوص للتأكد من الجودة
    print("\n📝 عينة من المحتوى المستخرج:")
    print("-" * 70)
    for i, chunk in enumerate(text_chunks[:3], 1):
        preview = chunk['content'][:150] + "..." if len(chunk['content']) > 150 else chunk['content']
        print(f"{i}. صفحة {chunk['page_number']}: {preview}")
    print("-" * 70)
    
    # 2. تحميل نموذج الذكاء الاصطناعي
    print("\n🧠 جاري تحميل نموذج اللغة...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # 3. توليد الـ embeddings
    print("🔄 جاري توليد الـ embeddings...")
    embeddings = model.encode(
        [chunk["content"] for chunk in text_chunks],
        show_progress_bar=True,
        batch_size=32
    )
    
    # 4. بناء الفهرس
    print("🏗️ جاري بناء هيكل البحث (FAISS Index)...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # 5. الحفظ
    print("💾 جاري الحفظ...")
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    
    faiss.write_index(index, INDEX_PATH)
    
    # حفظ chunks كنصوص مباشرة (string) مو dict
    chunks_text = [chunk["content"] for chunk in text_chunks]
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks_text, f)
    
    # حفظ معلومات الصفحات في ملف منفصل
    pages_info = [chunk["page_number"] for chunk in text_chunks]
    pages_path = os.path.join(os.path.dirname(CHUNKS_PATH), "pages.pkl")
    with open(pages_path, "wb") as f:
        pickle.dump(pages_info, f)
    
    print("\n" + "=" * 70)
    print("✅ تم بناء قاعدة المعرفة بنجاح! 🎉")
    print(f"   📊 عدد الفقرات: {len(text_chunks)}")
    print(f"   📍 المسار: {INDEX_PATH}")
    print("=" * 70)

if __name__ == "__main__":
    build_index()