import os
import sqlite3
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# --- إعداد المسارات ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
RAG_DIR = os.path.join(BACKEND_DIR, "rag_data")
DB_PATH = os.path.join(DATA_DIR, "edurag.db")

# تأكد من وجود المجلدات
os.makedirs(DATA_DIR, exist_ok=True)

# --- إعداد OpenAI/Groq ---
# يفضل وضع المفتاح في متغيرات البيئة، لكن يمكن وضعه هنا مؤقتاً
API_KEY = os.environ.get("OPENAI_API_KEY") 
client = OpenAI(
    base_url="https://api.groq.com/openai/v1", # نستخدم Groq للسرعة، أو يمكنك حذف هذا السطر لاستخدام OpenAI الأصلي
    api_key=API_KEY
)

# --- متغيرات RAG العالمية ---
index = None
chunks = []
embedder = None

def load_rag_models():
    """تحميل نماذج البحث (Embedding + FAISS) مرة واحدة عند التشغيل"""
    global index, chunks, embedder
    
    try:
        print("⏳ جاري تحميل نموذج التضمين (SentenceTransformer)...")
        # نستخدم نموذج خفيف ويدعم العربية بشكل جيد
        embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        index_path = os.path.join(RAG_DIR, "index.faiss") # أو math.index حسب التسمية لديك
        chunks_path = os.path.join(RAG_DIR, "chunks.pkl")
        
        if os.path.exists(index_path) and os.path.exists(chunks_path):
            print("📚 تحميل الفهرس وقاعدة البيانات المتجهة...")
            index = faiss.read_index(index_path)
            with open(chunks_path, "rb") as f:
                chunks = pickle.load(f)
            print("✅ تم تحميل نظام RAG بنجاح!")
        else:
            print("⚠️ تحذير: ملفات الفهرس غير موجودة. لن يعمل البحث في الكتاب.")
            
    except Exception as e:
        print(f"❌ خطأ أثناء تحميل النماذج: {e}")

# تحميل النماذج عند استيراد الملف
load_rag_models()

# ----------------------------- دوال قاعدة البيانات ----------------------------- #

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تهيئة جداول قاعدة البيانات"""
    conn = get_db_connection()
    c = conn.cursor()
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')
    # جدول نتائج الاختبارات
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic TEXT,
            score INTEGER,
            total_questions INTEGER,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# ----------------------------- دوال البحث والتوليد (Core Logic) ----------------------------- #

def get_relevant_context(query, k=3):
    """البحث عن النصوص ذات الصلة في الكتاب"""
    global index, chunks, embedder
    
    if index is None or embedder is None:
        return ""
    
    try:
        query_vector = embedder.encode([query])
        # البحث عن أقرب k نصوص
        distances, indices = index.search(query_vector, k)
        
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(chunks):
                # دمج النص مع رقم الصفحة للتوثيق
                text = chunks[idx].get('content', '')
                page = chunks[idx].get('page_number', '?')
                results.append(f"[صفحة {page}]: {text}")
        
        return "\n\n".join(results)
    except Exception as e:
        print(f"Error in RAG search: {e}")
        return ""

def generate_quiz(topic: str):
    """
    توليد اختبار بناءً على الموضوع باستخدام RAG + LLM
    """
    # 1. جلب السياق من الكتاب (RAG)
    print(f"🔍 البحث عن معلومات حول: {topic}")
    context_text = get_relevant_context(topic)
    
    if not context_text:
        context_text = "لا توجد معلومات محددة في الكتاب، قم بتوليد أسئلة عامة صحيحة عن الموضوع."

    # 2. تجهيز البرومبت المحسن (Prompt Engineering)
    # هذا هو المكان الذي نضع فيه البرومبت المطور
    prompt = f"""
    أنت خبير تعليمي متخصص. قم بإنشاء اختبار قصير من 5 أسئلة اختيار من متعدد.
    
    الموضوع المطلوب: {topic}
    
    استخدم المعلومات التالية من الكتاب الدراسي كمرجع أساسي (السياق):
    --- بداية السياق ---
    {context_text}
    --- نهاية السياق ---

    الشروط الصارمة للمخرجات:
    1. المخرج يجب أن يكون **JSON Array** نقي فقط (بدون markdown ```json).
    2. اللغة: العربية الفصحى.
    3. البنية المطلوبة لكل عنصر:
       - "question": نص السؤال.
       - "options": قائمة من 4 خيارات نصية.
       - "answer": الخيار الصحيح (يجب أن يكون مطابقاً حرفياً لأحد الخيارات).
    4. اجعل الخيارات الخاطئة (Distractors) ذكية ومنطقية.

    مثال للمخرج المتوقع:
    [
      {{
        "question": "ما هي وحدة قياس القوة؟",
        "options": ["النيوتن", "الجول", "الواط", "المتر"],
        "answer": "النيوتن"
      }}
    ]
    """

    try:
        # 3. إرسال الطلب للذكاء الاصطناعي
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # نموذج سريع وقوي للعربية
            messages=[
                {"role": "system", "content": "You are a helpful API that returns raw JSON arrays only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5 # تقليل العشوائية لضمان تنسيق JSON
        )

        content = response.choices[0].message.content.strip()
        
        # 4. تنظيف النص من علامات الـ Markdown إذا وجدت
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        elif content.startswith("```"):
            content = content.replace("```", "")
            
        # 5. تحويل النص إلى JSON
        quiz_data = json.loads(content)
        return quiz_data

    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        # إرجاع سؤال وهمي في حال الخطأ لتجنب توقف الواجهة
        return [
            {
                "question": f"لم نتمكن من توليد أسئلة حول {topic}. هل تريد المحاولة مرة أخرى؟",
                "options": ["نعم", "لا", "ربما", "لاحقاً"],
                "answer": "نعم"
            }
        ]

def get_dashboard_data():
    """جلب بيانات الطلاب الوهمية لعرضها في لوحة تحكم المعلم"""
    conn = get_db_connection()
    try:
        # جلب الطلاب ونتائجهم المجمعة
        cursor = conn.cursor()
        
        # نتأكد أولاً أن الجدول ممتلئ (إذا كان فارغاً يمكننا ملؤه ببيانات وهمية هنا أو في سكربت منفصل)
        # الكويري التالي يحسب متوسط الدرجات وعدد الاختبارات لكل طالب
        query = """
        SELECT 
            u.id, 
            u.name, 
            u.email, 
            COUNT(q.id) as quizzes_taken, 
            AVG(CASE WHEN q.total_questions > 0 THEN (CAST(q.score AS FLOAT) / q.total_questions) * 100 ELSE 0 END) as average_score
        FROM users u
        LEFT JOIN quiz_results q ON u.id = q.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        stats = []
        for row in rows:
            stats.append({
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "quizzes_taken": row["quizzes_taken"],
                "average_score": round(row["average_score"] if row["average_score"] else 0, 1)
            })
            
        return stats
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return []
    finally:
        conn.close()

# تهيئة قاعدة البيانات عند استيراد الملف
init_db()