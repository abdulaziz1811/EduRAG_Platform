import os, sqlite3, pickle, faiss, numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")
RAG_DATA_DIR = os.path.join(BASE_DIR, "rag_data")

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_rag_analysis(class_name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. إحصائيات الفصل العامة لضمان عدم نسيان بقية الطلاب
    cursor.execute("SELECT AVG(total_score) as avg, COUNT(*) as total FROM student_stats WHERE class_name = ?", (class_name,))
    class_info = cursor.fetchone()
    class_avg = class_info['avg'] or 0
    total_students = class_info['total']

    # 2. تحديد أضعف مهارة في الفصل وتحديد الأسماء المتعثرة جداً
    cursor.execute("""
        SELECT c.concept, AVG(c.score) as concept_avg 
        FROM concept_stats c JOIN student_stats s ON c.student_id = s.id
        WHERE s.class_name = ? GROUP BY c.concept ORDER BY concept_avg ASC LIMIT 1
    """, (class_name,))
    weak_row = cursor.fetchone()
    
    if not weak_row: return "البيانات غير كافية حالياً."
    
    weak_concept = weak_row['concept']
    
    cursor.execute("""
        SELECT s.name, c.score 
        FROM concept_stats c JOIN student_stats s ON c.student_id = s.id
        WHERE s.class_name = ? AND c.concept = ? AND c.score < 45
        ORDER BY c.score ASC LIMIT 3
    """, (class_name, weak_concept))
    struggling = cursor.fetchall()
    conn.close()

    # 3. استرجاع السياق المنهجي (RAG)
    context = ""
    try:
        index = faiss.read_index(os.path.join(RAG_DATA_DIR, "index.faiss"))
        with open(os.path.join(RAG_DATA_DIR, "chunks.pkl"), "rb") as f:
            chunks = pickle.load(f)
        query_vector = embedding_model.encode([f"معالجة ضعف الطلاب في مهارة {weak_concept}"])
        indices = index.search(np.array([query_vector]).astype('float32'), k=1)[1]
        context = chunks[indices[0][0]] if len(indices[0]) > 0 else ""
    except: pass

    # 4. التوليد باستخدام الموديل الجديد Llama-3.3
    students_names = ", ".join([r['name'] for r in struggling])
    
    system_prompt = "أنت مستشار أكاديمي خبير. ردك باللغة العربية، تقني، مباشر، ومختصر جداً في نقاط."

    user_prompt = f"""
    حلل المستجدات لـ {class_name}:
    - حالة الفصل: متوسط الإتقان {class_avg:.1f}% لـ {total_students} طالب.
    - الفجوة الكبرى: مهارة "{weak_concept}".
    - الحالات الحرجة: {students_names}.
    - المرجع التعليمي: {context[:150]}...

    المطلوب في 3 نقاط مركزة:
    1. (ملخص الفصل): تقييم عام لأداء القاعة وتحديد المهارة التي تستوجب مراجعة جماعية.
    2. (التشخيص): الربط المنطقي لتعثر {students_names} في "{weak_concept}".
    3. (الإجراء): نشاط علاجي سريع (5 دقائق) يطبق غداً لترميم الفجوة.

    * تنبيه: لا تزد عن 70 كلمة. ممنوع الإنجليزية. ابدأ بكلمة "التقرير:".
    """

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile", # الموديل الجديد والمدعوم
            temperature=0.2,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"حدث خطأ في الاتصال بالموديل: {str(e)}"