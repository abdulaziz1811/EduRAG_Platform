import os
import sqlite3
import pickle
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# إعداد المسارات
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")
RAG_DATA_DIR = os.path.join(BASE_DIR, "rag_data")

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- وظيفة تحليل الفصل للـ RAG Summary ---
def get_rag_analysis(class_name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT AVG(total_score) as avg FROM student_stats WHERE class_name = ?", (class_name,))
    avg_score = cursor.fetchone()['avg'] or 0

    cursor.execute("""
        SELECT c.concept, AVG(c.score) as c_avg 
        FROM concept_stats c JOIN student_stats s ON c.student_id = s.id
        WHERE s.class_name = ? GROUP BY c.concept ORDER BY c_avg ASC LIMIT 1
    """, (class_name,))
    weak_row = cursor.fetchone()
    conn.close()

    weak_concept = weak_row['concept'] if weak_row else "المفاهيم العامة"
    
    # استرجاع سياق من الكتاب حول المفهوم الضعيف
    context = ""
    try:
        index = faiss.read_index(os.path.join(RAG_DATA_DIR, "index.faiss"))
        with open(os.path.join(RAG_DATA_DIR, "chunks.pkl"), "rb") as f:
            chunks = pickle.load(f)
        query_vector = embedding_model.encode([f"شرح عن {weak_concept}"])
        _, indices = index.search(np.array([query_vector]).astype('float32'), k=1)
        context = chunks[indices[0][0]]
    except: context = "لا يوجد سياق متوفر."

    prompt = f"التقرير: الفصل {class_name} يعاني في {weak_concept}. المتوسط {avg_score:.1f}%. السياق المنهجي: {context[:200]}"
    return prompt

# --- وظيفة توليد الاختبارات الديناميكية (مصنع الاختبارات) ---
def generate_dynamic_quiz(class_name: str, selected_chapters: list = None, target_concept: str = None):
    # 1. تحديد نص البحث (فصول محددة أو مفهوم علاجي)
    search_query = target_concept if target_concept else " ".join(selected_chapters) if selected_chapters else "المنهج العام"
    
    context = ""
    try:
        index = faiss.read_index(os.path.join(RAG_DATA_DIR, "index.faiss"))
        with open(os.path.join(RAG_DATA_DIR, "chunks.pkl"), "rb") as f:
            chunks = pickle.load(f)
        query_vector = embedding_model.encode([f"أسئلة ومفاهيم عن {search_query}"])
        _, indices = index.search(np.array([query_vector]).astype('float32'), k=3)
        context = "\n".join([chunks[i] for i in indices[0] if i != -1])
    except: context = "اعتمد على مفاهيم الكتاب العامة."

    mode = f"علاجي لمفهوم {target_concept}" if target_concept else f"دوري للفصول {selected_chapters}"
    
    system_prompt = "أنت مصمم اختبارات خبير. ردك يجب أن يكون JSON فقط."
    user_prompt = f"""
    صمم اختبار MCQ لطلاب {class_name}.
    الهدف: {mode}.
    السياق من الكتاب: {context[:1200]}
    
    المطلوب JSON بهذا الشكل حصراً:
    {{
      "quiz_name": "اسم الاختبار",
      "questions": [
        {{
          "question": "نص السؤال",
          "options": ["أ", "ب", "ج", "د"],
          "answer": "الخيار الصحيح المطابق",
          "concept": "المفهوم"
        }}
      ]
    }}
    """
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- وظيفة جلب اختبار الطالب (إصلاح مشكلة عدم الظهور) ---
def get_student_quiz_logic(student_name: str, class_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # أولاً: البحث عن اختبار مخصص (علاجي)
    cursor.execute("SELECT quiz_data FROM custom_quizzes WHERE student_name = ? AND status = 'pending'", (student_name,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return json.loads(row[0])
    
    # ثانياً: البحث عن اختبار الفصل العام
    cursor.execute("SELECT quiz_data FROM class_quizzes WHERE class_name = ?", (class_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None