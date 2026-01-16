import os
import sqlite3
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# --- إعداد المسارات وبيئة العمل ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # مجلد app
BACKEND_DIR = os.path.dirname(CURRENT_DIR) # مجلد backend الرئيسي

# تحميل ملف .env من مجلد backend
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

RAG_DIR = os.path.join(BACKEND_DIR, "rag_data")
DB_PATH = os.path.join(BACKEND_DIR, "edurag.db")

# --- إعداد Groq API ---
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    # ملاحظة: إذا استمر الخطأ يمكنك وضع المفتاح يدوياً هنا للتجربة: API_KEY = "gsk_..."
    print("⚠️ تحذير: لم يتم العثور على GROQ_API_KEY في ملف .env")

client = Groq(api_key=API_KEY)

# --- متغيرات RAG العالمية ---
index = None
chunks = []
embedder = None

def load_rag_models():
    """تحميل نماذج البحث (Embedding + FAISS) مرة واحدة عند التشغيل"""
    global index, chunks, embedder
    try:
        print("⏳ جاري تحميل نموذج التضمين (SentenceTransformer)...")
        embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        index_path = os.path.join(RAG_DIR, "index.faiss")
        chunks_path = os.path.join(RAG_DIR, "chunks.pkl")
        
        if os.path.exists(index_path) and os.path.exists(chunks_path):
            print("📚 تحميل الفهرس وقاعدة البيانات المتجهة...")
            index = faiss.read_index(index_path)
            with open(chunks_path, "rb") as f:
                chunks = pickle.load(f)
            print("✅ تم تحميل نظام RAG بنجاح!")
        else:
            print("⚠️ تحذير: ملفات الفهرس (FAISS/Pickle) غير موجودة.")
    except Exception as e:
        print(f"❌ خطأ أثناء تحميل النماذج: {e}")

# تحميل النماذج عند استيراد الملف
load_rag_models()

# ----------------------------- دوال قاعدة البيانات ----------------------------- #

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------- دوال البحث والتوليد (Core Logic) ----------------------------- #

def get_relevant_context(query, k=3):
    """البحث عن النصوص ذات الصلة في الكتاب"""
    global index, chunks, embedder
    if index is None or embedder is None:
        return ""
    try:
        query_vector = embedder.encode([query])
        distances, indices = index.search(query_vector, k)
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(chunks):
                text = chunks[idx].get('content', '')
                page = chunks[idx].get('page_number', '?')
                results.append(f"[صفحة {page}]: {text}")
        return "\n\n".join(results)
    except Exception as e:
        print(f"Error in RAG search: {e}")
        return ""

def get_rag_response(prompt: str):
    """
    الدالة الرئيسية لتوليد الإجابات باستخدام Groq مع سياق الـ RAG
    (تم تسميتها get_rag_response لتطابق استدعاء main.py)
    """
    context = get_relevant_context(prompt)
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"أنت مساعد تعليمي ذكي. استخدم السياق المستخرج من الكتاب الدراسي للإجابة: {context}"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ خطأ في الاتصال بـ Groq: {str(e)}"

def generate_summary_logic():
    """المنطق الخاص بزر 'اصنع ملخص' - تحليل الطلاب والمفاهيم"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. جلب الطلاب المتعثرين (متوسط درجاتهم أقل من 50)
    cursor.execute("""
        SELECT u.name FROM users u 
        JOIN scores s ON u.id = s.user_id 
        GROUP BY u.id HAVING AVG(s.score) < 50
    """)
    low_students = ", ".join([r['name'] for r in cursor.fetchall()])

    # 2. جلب المفاهيم الصعبة (التي رسب فيها 40% من الطلاب أو أكثر)
    cursor.execute("""
        SELECT concept FROM scores 
        GROUP BY concept 
        HAVING (SUM(CASE WHEN score < 50 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) >= 0.4
    """)
    hard_concepts = ", ".join([r['concept'] for r in cursor.fetchall()])
    conn.close()

    # 3. صياغة التقرير باستخدام الـ LLM
    prompt = f"""
    بصفتك مساعد تعليمي خبير، قم بكتابة تقرير موجز للمعلم بناءً على النتائج التالية المستخلصة من قاعدة البيانات:
    - الطلاب الذين يحتاجون لتدخل عاجل: {low_students if low_students else "لا يوجد طلاب في منطقة الخطر حالياً"}
    - المفاهيم الدراسية التي تعثر بها أكثر من 40% من الطلاب: {hard_concepts if hard_concepts else "جميع المفاهيم تم استيعابها بشكل جيد"}
    
    اكتب التقرير بأسلوب مهني، مباشر، وباللغة العربية الفصحى. اقترح نصيحة سريعة للمعلم لكيفية معالجة هذه الفجوات.
    """
    return get_rag_response(prompt)

def get_stats_logic():
    """جلب الأرقام الحقيقية للمربعات العلوية في Dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # إجمالي الطلاب
        total_students = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
        
        # متوسط الدرجات
        avg_score = cursor.execute("SELECT AVG(score) FROM scores").fetchone()[0] or 0
        
        # طلاب في خطر (متوسطهم < 50)
        risk_count = cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT user_id FROM scores GROUP BY user_id HAVING AVG(score) < 50
            )
        """).fetchone()[0]
        
        # عدد الاختبارات (المفاهيم الفريدة)
        total_quizzes = cursor.execute("SELECT COUNT(DISTINCT concept) FROM scores").fetchone()[0]
        
        conn.close()
        return {
            "avg_score": f"{round(avg_score)}%",
            "risk_students": risk_count,
            "total_students": total_students,
            "total_quizzes": total_quizzes
        }
    except Exception as e:
        print(f"Error in stats: {e}")
        return {"avg_score": "0%", "risk_students": 0, "total_students": 0, "total_quizzes": 0}

def generate_quiz(topic: str, num_q=5):
    """توليد اختبار JSON نقي بناءً على الـ RAG"""
    context_text = get_relevant_context(topic)
    prompt = f"""
    أنشئ اختباراً تعليمياً بصيغة JSON مكون من {num_q} أسئلة عن موضوع: {topic}.
    استخدم السياق التالي كمصدر وحيد للمعلومات: {context_text}
    
    يجب أن يكون الرد عبارة عن JSON Array فقط يحتوي على:
    - question: نص السؤال
    - options: مصفوفة من 4 خيارات
    - answer: الخيار الصحيح مطابق تماماً لأحد الخيارات.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a specialized API that returns only raw JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        return []