"""
EduRAG - Core Business Logic
============================
منطق الأعمال الرئيسي: RAG Analysis و Quiz Generation
"""

import os
import sqlite3
import pickle
import json
import logging
from typing import Optional, List, Dict, Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# إعداد اللوقر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== إعداد المسارات =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = "/Users/abdulaziz/Desktop/æ/EduRAG_Platform/backend/edurag.db"
RAG_DATA_DIR = os.path.join(BASE_DIR, "rag_data")

# ===== تحميل المتغيرات البيئية =====
load_dotenv()

# ===== إعداد Groq Client =====
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("⚠️ GROQ_API_KEY غير موجود في ملف .env")
    groq_client = None
else:
    groq_client = Groq(api_key=GROQ_API_KEY)
    logger.info("✅ تم تهيئة Groq Client بنجاح")

# ===== تحميل نموذج الـ Embeddings =====
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
try:
    embedding_model = SentenceTransformer(MODEL_NAME)
    logger.info(f"✅ تم تحميل نموذج الـ Embeddings: {MODEL_NAME}")
except Exception as e:
    logger.error(f"❌ فشل تحميل نموذج الـ Embeddings: {e}")
    embedding_model = None


# ===== Helper Functions =====

def extract_chunk_text(chunk: Any) -> str:
    """استخراج النص من chunk سواء كان dict أو string"""
    if isinstance(chunk, dict):
        return chunk.get('content', '')
    return str(chunk) if chunk else ''


def load_rag_index() -> tuple:
    """
    تحميل فهرس FAISS والـ chunks
    Returns: (index, chunks) or (None, None) if failed
    """
    index_path = os.path.join(RAG_DATA_DIR, "index.faiss")
    chunks_path = os.path.join(RAG_DATA_DIR, "chunks.pkl")
    
    if not os.path.exists(index_path):
        logger.warning(f"⚠️ ملف الفهرس غير موجود: {index_path}")
        return None, None
    
    if not os.path.exists(chunks_path):
        logger.warning(f"⚠️ ملف الـ chunks غير موجود: {chunks_path}")
        return None, None
    
    try:
        index = faiss.read_index(index_path)
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)
        logger.info(f"✅ تم تحميل الفهرس ({index.ntotal} vectors) والـ chunks ({len(chunks)} items)")
        return index, chunks
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل RAG: {e}")
        return None, None


def search_rag(query: str, top_k: int = 10) -> List[str]:
    """
    البحث في قاعدة المعرفة RAG
    """
    if not embedding_model:
        logger.error("نموذج الـ Embeddings غير متاح")
        return []
    
    index, chunks = load_rag_index()
    if index is None or chunks is None:
        return []
    
    try:
        # توليد vector للاستعلام
        query_vector = embedding_model.encode([query])
        query_vector = np.array(query_vector).astype('float32')
        
        # البحث
        _, indices = index.search(query_vector, k=top_k)
        
        # جمع النتائج
        results = []
        for i in indices[0]:
            if i != -1 and i < len(chunks):
                text = extract_chunk_text(chunks[i])
                if text and len(text) > 50:
                    results.append(text)
        
        return results
    except Exception as e:
        logger.error(f"❌ خطأ في البحث RAG: {e}")
        return []


# ===== Main Functions =====

def get_rag_analysis(class_name: str) -> str:
    """
    توليد تقرير تشخيصي بأسلوب إنساني مهني يربط المنهج بالواقع الصفي
    """
    if not groq_client:
        return "⚠️ خدمة توليد التقارير غير متاحة حالياً. يرجى التأكد من إعداد GROQ_API_KEY."
    
    # 1. جلب البيانات من قاعدة البيانات
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # متوسط الفصل
        cursor.execute(
            "SELECT AVG(total_score) as avg FROM student_stats WHERE class_name = ?",
            (class_name,)
        )
        row = cursor.fetchone()
        avg_score = row['avg'] if row and row['avg'] else 0
        
        # المفهوم الأضعف
        cursor.execute("""
            SELECT c.concept, AVG(c.score) as c_avg 
            FROM concept_stats c 
            JOIN student_stats s ON c.student_id = s.id
            WHERE s.class_name = ? 
            GROUP BY c.concept 
            ORDER BY c_avg ASC 
            LIMIT 1
        """, (class_name,))
        weak_row = cursor.fetchone()
        
        if not weak_row:
            conn.close()
            return "أهلاً بك.. حالياً لا توجد بيانات كافية لتحليل أداء الفصل. يرجى التأكد من رصد درجات الطلاب."
        
        weak_concept = weak_row['concept']
        
        # الطلاب المتعثرين
        cursor.execute("""
            SELECT s.name FROM student_stats s 
            JOIN concept_stats c ON s.id = c.student_id
            WHERE s.class_name = ? AND c.concept = ? AND c.score < 50
            LIMIT 4
        """, (class_name, weak_concept))
        struggling_names = [r['name'] for r in cursor.fetchall()]
        
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في قاعدة البيانات: {e}")
        return f"حدث خطأ في جلب البيانات: {str(e)}"
    
    # 2. استرجاع السياق من RAG
    search_query = f"شرح مفصل وتفصيلي لدرس {weak_concept} مع أمثلة ومسائل وطرق الحل"
    retrieved_texts = search_rag(search_query, top_k=15)
    context_text = "\n\n".join(retrieved_texts[:10]) if retrieved_texts else ""
    
    # 3. بناء الـ Prompt
    system_prompt = """أنت مستشار تعليمي وخبير تربوي متخصص في تحليل الأداء الأكاديمي.
يجب عليك كتابة تقرير تحليلي مهني، دقيق، ومنطقي يوجه للمعلم.
قواعد صارمة:
1. استخدم اللغة العربية الفصحى وحروفها فقط. يُمنع منعاً باتاً (تحت أي ظرف) استخدام أي حروف صينية، آسيوية، أو أي لغات أخرى.
2. نسق التقرير باستخدام نقاط وعناوين واضحة (Markdown) لتسهيل القراءة.
3. اربط التحليل بالمحتوى العلمي من الكتاب المدرسي بشكل دقيق.
4. قدم حلولاً تربوية واقعية وقابلة للتطبيق داخل الغرفة الصفية.
5. تجنب المقدمات الطويلة أو التحيات غير الرسمية."""

    struggling_str = '، '.join(struggling_names) if struggling_names else 'لا توجد حالات حرجة حالياً'
    
    user_prompt = f"""إليك بيانات الأداء لفصل "{class_name}":
- متوسط الأداء العام للفصل: {avg_score:.1f}%
- المفهوم الأقل استيعاباً والذي يتطلب تدخلاً: "{weak_concept}"
- الطلاب الذين يحتاجون لدعم مكثف في هذا المفهوم: {struggling_str}
- مقتطفات من المنهج المدرسي المتعلقة بالمفهوم:
{context_text[:2000]}

يرجى كتابة تقرير تحليلي احترافي للمعلم يتضمن:
### 📊 قراءة تحليلية للمستوى العام
تحليل مختصر لمتوسط الفصل ومؤشراته.

### 🔍 تشخيص الفجوة التعليمية
تحليل لأسباب الصعوبة في مفهوم "{weak_concept}" بناءً على السياق المستخرج من المنهج المدرسي.

### 🎯 توجيهات للتدخل المبكر
استراتيجيات محددة لدعم الطلاب ({struggling_str}) وتجاوز التحديات التي يواجهونها.

### 💡 توصية عملية للحصة القادمة
اقتراح نشاط صفي أو طريقة شرح مستوحاة من المنهج لتصحيح هذه المفاهيم.

الرجاء كتابة التقرير بصيغة مهنية ومباشرة، واحرص على جودة اللغة العربية وملاءمتها للبيئة التعليمية المدرسية."""

    # 4. استدعاء Groq API
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ خطأ في Groq API: {e}")
        return f"عذراً يا زميلي، حدث خطأ تقني في توليد التقرير: {str(e)}"


def generate_dynamic_quiz(
    class_name: str,
    selected_chapters: Optional[List[str]] = None,
    target_concept: Optional[str] = None
) -> Dict[str, Any]:
    """
    توليد اختبارات عالية الجودة مع أسئلة تطبيقية من محتوى الكتاب
    """
    # تحديد عنوان الاختبار ونص البحث
    if target_concept:
        search_query = f"تمارين ومسائل وأمثلة محلولة وتطبيقات عملية عن {target_concept}"
        quiz_title = f"اختبار علاجي - {target_concept}"
        mode = f"علاجي لمفهوم {target_concept}"
    elif selected_chapters:
        chapters_str = ", ".join(selected_chapters)
        search_query = f"أسئلة ومسائل وتمارين وتطبيقات عن {chapters_str}"
        quiz_title = f"اختبار دوري - {chapters_str}"
        mode = f"دوري للفصول {chapters_str}"
    else:
        search_query = "أسئلة ومسائل رياضيات الصف الثاني متوسط"
        quiz_title = "اختبار عام"
        mode = "عام للمنهج"
    
    # التحقق من توفر Groq
    if not groq_client:
        return {
            "error": "خدمة توليد الاختبارات غير متاحة. يرجى التأكد من إعداد GROQ_API_KEY.",
            "quiz_name": quiz_title,
            "questions": []
        }
    
    # استرجاع السياق من RAG
    retrieved_chunks = search_rag(search_query, top_k=20)
    context = "\n---\n".join(retrieved_chunks[:15]) if retrieved_chunks else "اعتمد على مفاهيم الكتاب العامة."
    
    # بناء الـ Prompt
    system_prompt = """أنت خبير في تصميم اختبارات الرياضيات للمرحلة المتوسطة.

قواعد صارمة:
1. كل سؤال يجب أن يكون واضح ومباشر ومرتبط بالمحتوى المعطى
2. نوّع بين: حسابات مباشرة، مسائل كلامية، تطبيقات عملية، مفاهيم أساسية
3. الخيارات يجب أن تكون معقولة ومتقاربة في المستوى (ليست سهلة جداً)
4. الإجابة الصحيحة يجب أن تكون واحدة فقط ومذكورة بالضبط كما في options
5. تجنب الأسئلة الغامضة أو النظرية البحتة
6. استخدم أرقام وأمثلة واقعية من المحتوى

ردك يجب أن يكون JSON فقط بدون أي نص إضافي."""

    user_prompt = f"""صمم اختبار اختيار من متعدد (MCQ) لطلاب الصف الثاني متوسط في {class_name}.

**الهدف:** {mode}

**المحتوى الدراسي المرجعي من الكتاب:**
{context[:3000]}

**المطلوب:**
- عدد الأسئلة: 5 أسئلة
- كل سؤال له 4 خيارات
- الأسئلة يجب أن تكون متنوعة (30% حسابات، 40% مسائل كلامية، 30% مفاهيم)

**صيغة JSON المطلوبة حصراً:**
{{
  "quiz_name": "{quiz_title}",
  "questions": [
    {{
      "question": "نص السؤال بوضوح",
      "options": ["الخيار الأول", "الخيار الثاني", "الخيار الثالث", "الخيار الرابع"],
      "answer": "الإجابة الصحيحة المطابقة تماماً لأحد الخيارات",
      "concept": "المفهوم المستهدف"
    }}
  ]
}}

**مهم جداً:**
- الإجابة يجب أن تكون نسخة طبق الأصل من أحد الخيارات
- لا تضع أرقام أو حروف في بداية الخيارات
- اجعل الأسئلة تطبيقية قدر الإمكان"""

    # استدعاء Groq API
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=2500,
            response_format={"type": "json_object"}
        )
        
        quiz_data = json.loads(response.choices[0].message.content)
        
        # التحقق من صحة البيانات
        if "questions" not in quiz_data or len(quiz_data["questions"]) == 0:
            return {
                "error": "فشل توليد الأسئلة",
                "quiz_name": quiz_title,
                "questions": []
            }
        
        # تنظيف وتحسين البيانات
        valid_questions = []
        for q in quiz_data["questions"]:
            # التأكد من وجود جميع الحقول
            if not all(key in q for key in ["question", "options", "answer", "concept"]):
                continue
            
            # التأكد من 4 خيارات
            if len(q["options"]) != 4:
                continue
            
            # التأكد من أن الإجابة موجودة في الخيارات
            if q["answer"] not in q["options"]:
                q["answer"] = q["options"][0]
            
            # إضافة المفهوم الافتراضي
            if not q.get("concept"):
                q["concept"] = target_concept or "مفاهيم عامة"
            
            valid_questions.append(q)
        
        quiz_data["questions"] = valid_questions
        
        if len(valid_questions) == 0:
            return {
                "error": "لم يتم توليد أسئلة صالحة",
                "quiz_name": quiz_title,
                "questions": []
            }
        
        logger.info(f"✅ تم توليد اختبار بـ {len(valid_questions)} أسئلة")
        return quiz_data
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطأ في تحليل JSON: {e}")
        return {
            "error": "فشل في تحويل الرد إلى JSON",
            "quiz_name": quiz_title,
            "questions": []
        }
    except Exception as e:
        logger.error(f"❌ خطأ عام في توليد الاختبار: {e}")
        return {
            "error": str(e),
            "quiz_name": quiz_title,
            "questions": []
        }


def get_student_quiz_logic(student_name: str, class_name: str) -> Optional[Dict[str, Any]]:
    """
    جلب اختبار الطالب (مخصص أو عام)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # أولاً: البحث عن اختبار مخصص (علاجي)
        cursor.execute(
            """SELECT quiz_data FROM custom_quizzes 
               WHERE student_name = ? AND status = 'pending' 
               ORDER BY created_at DESC LIMIT 1""",
            (student_name,)
        )
        row = cursor.fetchone()
        if row:
            conn.close()
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                logger.error(f"خطأ في تحليل اختبار الطالب {student_name}")
                return None
        
        # ثانياً: البحث عن اختبار الفصل العام
        cursor.execute(
            "SELECT quiz_data FROM class_quizzes WHERE class_name = ?",
            (class_name,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                logger.error(f"خطأ في تحليل اختبار الفصل {class_name}")
                return None
        
        return None
        
    except sqlite3.Error as e:
        logger.error(f"❌ خطأ في جلب اختبار الطالب: {e}")
        return None

# تحديث الدالة في ملف backend/app/core.py

def explain_error_with_rag(question_text: str, correct_answer: str, concept: str):
    """
    توليد شرح أكاديمي رصين واستخراج رقم الصفحة من المرجع (نسخة Pro)
    """
    context_text = ""
    page_number = "غير محدد"
    
    try:
        index_path = os.path.join(RAG_DATA_DIR, "index.faiss")
        chunks_path = os.path.join(RAG_DATA_DIR, "chunks.pkl")
        
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            with open(chunks_path, "rb") as f:
                chunks = pickle.load(f)
            
            query = f"شرح مفصل لدرس {concept} وقواعد حل {question_text}"
            query_vector = embedding_model.encode([query])
            _, indices = index.search(np.array([query_vector]).astype('float32'), k=5)
            
            retrieved_chunks = []
            for i in indices[0]:
                if i != -1 and i < len(chunks):
                    chunk_data = chunks[i]
                    # التحقق من وجود الميتا داتا (رقم الصفحة)
                    if isinstance(chunk_data, dict):
                        retrieved_chunks.append(chunk_data.get('content', ''))
                        meta = chunk_data.get('metadata', {})
                        # قراءة مفتاح 'page' الذي قمنا بتعريفه في build_index.py
                        page_number = meta.get('page') or page_number
                    else:
                        retrieved_chunks.append(str(chunk_data))
            
            context_text = "\n\n".join(retrieved_chunks)
    except Exception as e:
        print(f"RAG Error: {e}")

    prompt = f"""
    أنت معلم خبير في EduRAG Pro. قدم شرحاً دقيقاً ومختصراً.
    المفهوم: {concept}
    السؤال: {question_text}
    الإجابة الصحيحة: {correct_answer}
    
    السياق من الكتاب: {context_text[:1500]}
    
    المطلوب:
    1. اشرح الحل رياضياً بأسلوب سردي رصين.
    2. لا تكرر الكلام ولا تستخدم لغات غريبة أو إيموجيات.
    3. اختم بعبارة: "المرجع: الصفحة رقم ({page_number}) من الكتاب الدراسي."
    """

    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception:
        return f"الإجابة الصحيحة هي {correct_answer}. يرجى مراجعة صفحة {page_number}."

# (احتفظ بباقي الدوال: get_rag_analysis, generate_dynamic_quiz كما هي)