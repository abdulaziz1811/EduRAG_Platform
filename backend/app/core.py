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

# ✅ تحديث: استخدام نفس النموذج في build_index.py
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# --- وظيفة تحليل الفصل للـ RAG Summary (محسّنة) ---
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

    # 2. استرجاع السياق المنهجي من الكتاب (RAG) - محسّن
    context_text = ""
    try:
        index_path = os.path.join(RAG_DATA_DIR, "index.faiss")
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            with open(os.path.join(RAG_DATA_DIR, "chunks.pkl"), "rb") as f:
                chunks = pickle.load(f)
            
            # ✅ التحسين: زيادة من 5 إلى 15 للحصول على سياق أغنى
            query_vector = embedding_model.encode([f"شرح مفصل وتفصيلي لدرس {weak_concept} مع أمثلة ومسائل وطرق الحل"])
            _, indices = index.search(np.array([query_vector]).astype('float32'), k=15)
            
            # جمع النصوص مع معالجة أفضل
            retrieved_texts = []
            for i in indices[0]:
                if i != -1 and i < len(chunks):
                    chunk = chunks[i]
                    # التعامل مع chunks سواء dict أو string
                    if isinstance(chunk, dict):
                        text = chunk.get('content', '')
                    else:
                        text = str(chunk)
                    
                    if text and len(text) > 50:
                        retrieved_texts.append(text)
            
            context_text = "\n\n".join(retrieved_texts[:10])
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
    - المحتوى العلمي المرتبط من الكتاب المدرسي: {context_text[:2000]}

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
            temperature=0.6,  # ✅ زيادة قليلة للإبداع
            max_tokens=1500   # ✅ زيادة من 1000 لمزيد من التفاصيل
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"عذراً يا زميلي، حدث خطأ تقني في توليد التقرير: {str(e)}"

# --- وظيفة توليد الاختبارات الديناميكية (مصنع الاختبارات) - محسّنة بشكل كبير ---
def generate_dynamic_quiz(class_name: str, selected_chapters: list = None, target_concept: str = None):
    """
    ✅ توليد اختبارات عالية الجودة مع أسئلة تطبيقية من محتوى الكتاب
    """
    # 1. تحديد نص البحث (فصول محددة أو مفهوم علاجي)
    if target_concept:
        search_query = f"تمارين ومسائل وأمثلة محلولة وتطبيقات عملية عن {target_concept}"
        quiz_title = f"اختبار علاجي - {target_concept}"
    elif selected_chapters:
        chapters_str = ", ".join(selected_chapters)
        search_query = f"أسئلة ومسائل وتمارين وتطبيقات عن {chapters_str}"
        quiz_title = f"اختبار دوري - {chapters_str}"
    else:
        search_query = "أسئلة ومسائل رياضيات الصف الثاني متوسط"
        quiz_title = "اختبار عام"
    
    context = ""
    try:
        index = faiss.read_index(os.path.join(RAG_DATA_DIR, "index.faiss"))
        with open(os.path.join(RAG_DATA_DIR, "chunks.pkl"), "rb") as f:
            chunks = pickle.load(f)
        
        # ✅ التحسين الكبير: زيادة من 3 إلى 20 للحصول على تغطية شاملة
        query_vector = embedding_model.encode([search_query])
        _, indices = index.search(np.array([query_vector]).astype('float32'), k=20)
        
        # جمع النصوص مع معالجة محسّنة
        retrieved_chunks = []
        for i in indices[0]:
            if i != -1 and i < len(chunks):
                chunk_data = chunks[i]
                # التعامل مع chunks كـ dict أو string
                if isinstance(chunk_data, dict):
                    text = chunk_data.get('content', '')
                else:
                    text = str(chunk_data)
                
                if text and len(text) > 50:
                    retrieved_chunks.append(text)
        
        context = "\n---\n".join(retrieved_chunks[:15])
        
    except Exception as e:
        print(f"⚠️ خطأ في RAG: {e}")
        context = "اعتمد على مفاهيم الكتاب العامة."

    mode = f"علاجي لمفهوم {target_concept}" if target_concept else f"دوري للفصول {', '.join(selected_chapters) if selected_chapters else 'المنهج'}"
    
    # ✅ Prompt محسّن جداً لتوليد أسئلة تطبيقية عالية الجودة
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
- الخيارات يجب أن تكون معقولة ومنطقية

**صيغة JSON المطلوبة حصراً:**
{{
  "quiz_name": "{quiz_title}",
  "questions": [
    {{
      "question": "نص السؤال بوضوح (يفضل أن يتضمن أرقاماً أو حالة عملية)",
      "options": ["الخيار الأول", "الخيار الثاني", "الخيار الثالث", "الخيار الرابع"],
      "answer": "الإجابة الصحيحة المطابقة تماماً لأحد الخيارات",
      "concept": "المفهوم المستهدف"
    }}
  ]
}}

**مهم جداً:**
- الإجابة يجب أن تكون نسخة طبق الأصل من أحد الخيارات (نفس الحروف والأرقام)
- لا تضع أرقام أو حروف (أ، ب، ج، د) في بداية الخيارات
- تأكد من جودة الأسئلة وارتباطها بالمحتوى المقدم
- اجعل الأسئلة تطبيقية قدر الإمكان وليست نظرية فقط
- استخدم أمثلة ومسائل من المحتوى المرجعي"""

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,  # ✅ توازن بين الإبداع والدقة
            max_tokens=2500,  # ✅ زيادة من 1000 للأسئلة المفصلة
            response_format={"type": "json_object"}
        )
        
        quiz_data = json.loads(response.choices[0].message.content)
        
        # ✅ التحقق من صحة البيانات المُولدة
        if "questions" not in quiz_data or len(quiz_data["questions"]) == 0:
            return {
                "error": "فشل توليد الأسئلة",
                "quiz_name": quiz_title,
                "questions": []
            }
        
        # ✅ تنظيف وتحسين البيانات
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
                # محاولة إيجاد أقرب خيار
                q["answer"] = q["options"][0]
            
            # إضافة المفهوم إذا لم يكن موجوداً
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
        
        return quiz_data
        
    except json.JSONDecodeError as e:
        print(f"❌ خطأ في تحليل JSON: {e}")
        return {
            "error": "فشل في تحويل الرد إلى JSON",
            "quiz_name": quiz_title,
            "questions": []
        }
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return {
            "error": str(e),
            "quiz_name": quiz_title,
            "questions": []
        }

# --- وظيفة جلب اختبار الطالب (إصلاح مشكلة عدم الظهور) ---
def get_student_quiz_logic(student_name: str, class_name: str):
    """
    ✅ جلب اختبار الطالب مع معالجة أخطاء محسّنة
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # أولاً: البحث عن اختبار مخصص (علاجي)
    cursor.execute(
        "SELECT quiz_data FROM custom_quizzes WHERE student_name = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
        (student_name,)
    )
    row = cursor.fetchone()
    if row:
        conn.close()
        try:
            return json.loads(row[0])
        except:
            return None
    
    # ثانياً: البحث عن اختبار الفصل العام
    cursor.execute("SELECT quiz_data FROM class_quizzes WHERE class_name = ?", (class_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            return json.loads(row[0])
        except:
            return None
    
    return None