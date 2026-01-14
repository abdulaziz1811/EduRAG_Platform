import os
import sqlite3
import json
import pandas as pd
from openai import OpenAI
from datetime import datetime

# --- إعداد المسارات بدقة ---
# نحدد المسار بناءً على موقع الملف الحالي لضمان عدم ضياع الملفات
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # داخل app
BACKEND_DIR = os.path.dirname(CURRENT_DIR)               # داخل backend
DATA_DIR = os.path.join(BACKEND_DIR, "data")             # مجلد البيانات
DB_PATH = os.path.join(DATA_DIR, "edurag.db")

# تأكد من وجود المجلد
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------- 1. التعامل مع قاعدة البيانات ----------------------------- #

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تهيئة الجداول إذا لم تكن موجودة"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student TEXT,
                chapter INTEGER,
                score REAL,
                total_questions INTEGER,
                weak_concepts TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS attempt_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER,
                question_text TEXT,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct BOOLEAN,
                concept TEXT,
                FOREIGN KEY(attempt_id) REFERENCES attempts(id)
            )
        ''')
        conn.commit()

# ----------------------------- 2. محرك الذكاء الاصطناعي (توليد الأسئلة) ----------------------------- #

def generate_quiz_logic(api_key: str, chapters: list, num_questions: int):
    """
    دالة تتصل بـ Groq/OpenAI لتوليد أسئلة وتعود ببيانات JSON صافية
    """
    if not api_key:
        return {"error": "API Key is missing"}

    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    
    # صياغة الطلب (Prompt)
    prompt = f"""
    You are a math teacher. Create {num_questions} multiple-choice questions (MCQ) for 2nd Grade Middle School students.
    Focus on Chapters: {chapters}.
    Language: Arabic.
    
    Output MUST be a valid JSON object with this structure:
    {{
        "questions": [
            {{
                "id": 1,
                "text": "Question text here",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "concept": "Math Concept Name"
            }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a JSON generator. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        
        # تحويل النص القادم من الذكاء الاصطناعي إلى قاموس بايثون
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])

    except Exception as e:
        print(f"Error generating quiz: {e}")
        return {"error": str(e)}

# ----------------------------- 3. معالجة النتائج ----------------------------- #

def save_submission(student_name: str, chapter: int, results: dict):
    """حفظ نتيجة الطالب في قاعدة البيانات"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # حساب الدرجة
    correct_count = sum(1 for r in results['details'] if r['is_correct'])
    total = len(results['details'])
    score = (correct_count / total) * 100 if total > 0 else 0
    
    # استخراج المفاهيم الضعيفة
    weak_concepts = list(set([r['concept'] for r in results['details'] if not r['is_correct']]))
    weak_str = ",".join(weak_concepts)

    # 1. حفظ المحاولة الرئيسية
    c.execute('''
        INSERT INTO attempts (student, chapter, score, total_questions, weak_concepts)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_name, chapter, score, total, weak_str))
    
    attempt_id = c.lastrowid

    # 2. حفظ التفاصيل لكل سؤال
    for det in results['details']:
        c.execute('''
            INSERT INTO attempt_details (attempt_id, question_text, user_answer, correct_answer, is_correct, concept)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (attempt_id, det['question'], det['user_answer'], det['correct_answer'], det['is_correct'], det['concept']))

    conn.commit()
    conn.close()
    
    return {"status": "saved", "score": score, "weak_concepts": weak_concepts}

def get_dashboard_stats():
    """جلب إحصائيات للمعلم"""
    conn = get_db_connection()
    
    # مثال: جلب متوسط الدرجات لكل طالب
    df = pd.read_sql("SELECT student, AVG(score) as avg_score FROM attempts GROUP BY student", conn)
    conn.close()
    
    if df.empty:
        return []
    return df.to_dict(orient="records")

# عند تشغيل السيرفر لأول مرة، تأكد من أن قاعدة البيانات جاهزة
init_db()