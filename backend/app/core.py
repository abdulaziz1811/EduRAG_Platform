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
    """
    توليد تقرير تشخيصي بأسلوب إنساني مهني يربط المنهج بالواقع الصفي.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. تحليل الأداء الرقمي
    cursor.execute("SELECT AVG(total_score) as avg FROM student_stats WHERE class_name = ?", (class_name,))
    avg_score = cursor.fetchone()['avg'] or 0

    cursor.execute("""
        SELECT c.concept, AVG(c.score) as c_avg 
        FROM concept_stats c JOIN student_stats s ON c.student_id = s.id
        WHERE s.class_name = ? GROUP BY c.concept ORDER BY c_avg ASC LIMIT 1
    """, (class_name,))
    weak_row = cursor.fetchone()
    
    if not weak_row:
        conn.close()
        return "أهلاً بك.. حالياً لا توجد بيانات كافية لتحليل أداء الفصل. يرجى التأكد من رصد درجات الطلاب."

    weak_concept = weak_row['concept']
    
    # تحديد الطلاب المتعثرين
    cursor.execute("""
        SELECT s.name FROM student_stats s 
        JOIN concept_stats c ON s.id = c.student_id
        WHERE s.class_name = ? AND c.concept = ? AND c.score < 50
        LIMIT 4
    """, (class_name, weak_concept))
    struggling_names = [r['name'] for r in cursor.fetchall()]
    conn.close()

    # 2. استرجاع السياق المنهجي من الكتاب (RAG)
    context_text = ""
    try:
        index_path = os.path.join(RAG_DATA_DIR, "index.faiss")
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            with open(os.path.join(RAG_DATA_DIR, "chunks.pkl"), "rb") as f:
                chunks = pickle.load(f)
            
            # بحث مكثف (جلب أفضل 5 قطع لشرح المفهوم)
            query_vector = embedding_model.encode([f"شرح مفصل لدرس {weak_concept} وكيفية حل مسائله"])
            _, indices = index.search(np.array([query_vector]).astype('float32'), k=5)
            context_text = "\n".join([chunks[i] for i in indices[0] if i != -1])
    except Exception as e:
        print(f"RAG Retrieval Notice: {e}")

    # 3. بناء الـ Prompt الإنساني (Colleague Style)
    system_prompt = (
        "أنت مستشار أكاديمي خبير. اكتب بأسلوب إنساني، دافئ، ومهني كأنك تخاطب المعلم مباشرة كزميل. "
        "تجنب العناوين الجامدة مثل (أولاً، ثانياً) أو كثرة النقاط. "
        "ادمج المادة العلمية المستخرجة من الكتاب في صلب حديثك التشخيصي أو العلاجي بشكل طبيعي."
    )
    
    user_prompt = f"""
    يا هلا بك.. هذا ملخص لمستوى طلاب فصل "{class_name}":
    - متوسط الفصل العام حالياً هو {avg_score:.1f}%.
    - المهارة التي تحتاج وقفة هي "{weak_concept}".
    - الطلاب الذين يواجهون تحديات واضحة في هذا المفهوم: {', '.join(struggling_names) if struggling_names else 'لا توجد حالات حرجة'}.
    - المحتوى العلمي المرتبط من الكتاب المدرسي: {context_text[:1200]}

    المطلوب كتابة تقرير (بأسلوب السرد المهني المباشر):
    1. ابدأ بتحية زميلك المعلم وشاركه قراءتك لمستوى الفصل بشكل عام.
    2. وضح أين تكمن الصعوبة في "{weak_concept}" بناءً على ما ورد في الكتاب المدرسي (ادمج القواعد العلمية هنا بلا قسم مستقل).
    3. وجه تركيز المعلم نحو الطلاب ({', '.join(struggling_names)}) وكيف يمكن مساعدتهم.
    4. اختم بتوصية عملية ومبتكرة للحصة القادمة لترميم هذه الفجوة.

    مهم جداً: خفف من الرموز والنقاط، واجعل الكلام يتدفق كأنه نصائح إنسانية مهنية.
    ابدأ بعبارة: "مرحباً يا زميلي.. إليك نظرة على مستجدات فصلك:"
    """

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5, # زيادة طفيفة للإبداع في اللغة
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"عذراً يا زميلي، حدث خطأ تقني في توليد التقرير: {str(e)}"

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