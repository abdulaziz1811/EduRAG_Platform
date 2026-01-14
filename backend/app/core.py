import os
import sqlite3
import json
import pandas as pd
import faiss
import pickle
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
os.makedirs(RAG_DIR, exist_ok=True)

# --- متغيرات عالمية ---
index = None
chunks = []
embedder = None

def load_rag_models():
    """تحميل فهرس البحث والذكاء الاصطناعي عند بدء التشغيل"""
    global index, chunks, embedder
    
    if embedder is None:
        print("⏳ جاري تحميل نموذج اللغة (SentenceTransformer)...")
        embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
    
    index_path = os.path.join(RAG_DIR, "math.index")
    chunks_path = os.path.join(RAG_DIR, "chunks.pkl")
    
    if os.path.exists(index_path) and os.path.exists(chunks_path):
        if index is None:
            print("📚 تحميل الفهرس الدلالي...")
            index = faiss.read_index(index_path)
            with open(chunks_path, "rb") as f:
                chunks = pickle.load(f)
            print("✅ تم تحميل بيانات RAG بنجاح!")
    else:
        print("⚠️ تحذير: ملفات الفهرس غير موجودة. يجب تشغيل build_index.py أولاً.")

load_rag_models()

# ----------------------------- 1. البحث والشرح (RAG + Generative AI) ----------------------------- #

def get_explanation_from_book(concept: str, api_key: str = None):
    """
    1. يبحث في الكتاب عن النص الخام (Retrieval).
    2. يرسل النص للذكاء الاصطناعي لتنظيفه وشرحه (Generation).
    """
    global index, chunks, embedder
    
    if index is None or not chunks:
        load_rag_models()
        if index is None:
            return {"text": "عذراً، الفهرس غير جاهز أو الملفات مفقودة.", "page": 0}

    # 1. البحث الدلالي (Retrieval)
    query_vector = embedder.encode([concept])
    D, I = index.search(query_vector, 1) # نأخذ أفضل نتيجة
    top_idx = I[0][0]
    
    if top_idx == -1:
        return {"text": "لم يتم العثور على معلومة مشابهة في الكتاب.", "page": 0}
        
    result_chunk = chunks[top_idx]
    raw_text = result_chunk.get('content', '')
    page_number = result_chunk.get('page_number', 0)

    # إذا لم يتوفر مفتاح API، نرجع النص الخام كما هو
    if not api_key:
        return {
            "text": f"⚠️ (نص خام من الكتاب - لتنظيفه وفر API Key):\n{raw_text[:500]}...",
            "page": page_number
        }

    # 2. التوليد والصياغة (Generation) باستخدام Groq
    try:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
        
        prompt = f"""
        لديك نص مستخرج بتقنية OCR من كتاب مدرسي (يحتوي على أخطاء ورموز).
        
        النص المستخرج (صفحة {page_number}):
        {raw_text}
        
        سؤال الطالب: {concept}
        
        المطلوب:
        1. تجاهل الرموز الغريبة والأخطاء الإملائية الناتجة عن الـ OCR.
        2. اشرح المفهوم للطالب باللغة العربية بوضوح وبساطة بناءً على النص فقط.
        3. ابدأ إجابتك بعبارة: "بناءً على الصفحة {page_number} من الكتاب، فإن..."
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "أنت معلم رياضيات مساعد. تشرح المفاهيم بناء على محتوى الكتاب بدقة."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        cleaned_explanation = response.choices[0].message.content
        return {"text": cleaned_explanation, "page": page_number}

    except Exception as e:
        return {"text": f"حدث خطأ أثناء معالجة الذكاء الاصطناعي: {str(e)}", "page": page_number}

# ----------------------------- 2. بقية الدوال (قاعدة البيانات والكويزات) ----------------------------- #
# (لم نغير فيها شيئاً للحفاظ على عمل النظام السابق)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, student TEXT, chapter INTEGER, score REAL, total_questions INTEGER, weak_concepts TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attempt_details (id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER, question_text TEXT, user_answer TEXT, correct_answer TEXT, is_correct BOOLEAN, concept TEXT, FOREIGN KEY(attempt_id) REFERENCES attempts(id))''')
        conn.commit()

# في ملف backend/app/core.py

def generate_quiz_logic(api_key: str, chapters: list, num_questions: int, focus_concepts: list = []):
    if not api_key: return {"error": "API Key Required"}
    
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    
    # منطق التوجيه (Prompt Engineering)
    if focus_concepts:
        # إذا كان اختبار تحسين
        topic_desc = f"Focus 70% of the questions on these weak concepts: {', '.join(focus_concepts)}. The remaining 30% should be general review of Chapters {chapters}."
        quiz_type = "Remedial/Improvement Quiz"
    else:
        # إذا كان اختبار عادي
        topic_desc = f"Cover key concepts from Math Book Chapters: {chapters}."
        quiz_type = "Standard Assessment Quiz"

    prompt = f"""
    You are a math teacher. Create {num_questions} multiple-choice questions (MCQ) for Middle School level.
    Context: {quiz_type}.
    Instructions: {topic_desc}
    Language: Arabic.
    
    Output JSON ONLY in this exact format:
    {{ "questions": [ 
        {{ 
            "id": 1, 
            "text": "Question text here?", 
            "options": ["Option A", "Option B", "Option C", "Option D"], 
            "correct_answer": "Option A", 
            "concept": "Name of the math concept tested (e.g., Pythagoras, Algebra)" 
        }} 
    ] }}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Return valid JSON only. No markdown."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("questions", [])
    except Exception as e:
        return {"error": str(e)}

def save_submission(student_name: str, chapter: int, results: dict):
    conn = get_db_connection()
    c = conn.cursor()
    correct = sum(1 for r in results['details'] if r['is_correct'])
    total = len(results['details'])
    score = (correct / total) * 100 if total > 0 else 0
    weak_concepts = list(set([r['concept'] for r in results['details'] if not r['is_correct']]))
    c.execute('INSERT INTO attempts (student, chapter, score, total_questions, weak_concepts) VALUES (?,?,?,?,?)', (student_name, chapter, score, total, ",".join(weak_concepts)))
    attempt_id = c.lastrowid
    for det in results['details']:
        c.execute('INSERT INTO attempt_details (attempt_id, question_text, user_answer, correct_answer, is_correct, concept) VALUES (?,?,?,?,?,?)', (attempt_id, det['question'], det['user_answer'], det['correct_answer'], det['is_correct'], det['concept']))
    conn.commit()
    conn.close()
    return {"status": "saved", "score": score, "weak_concepts": weak_concepts}

def get_dashboard_stats():
    conn = get_db_connection()
    try:
        df = pd.read_sql("SELECT student, AVG(score) as avg_score FROM attempts GROUP BY student", conn)
        return df.to_dict(orient="records") if not df.empty else []
    finally:
        conn.close()

init_db()