import os
import sqlite3
import json
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core import get_rag_analysis, generate_dynamic_quiz, get_student_quiz_logic

app = FastAPI()

# إعدادات CORS للسماح للفرونت إند بالوصول للباك إند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "edurag.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- النماذج (Models) ---
class QuizGenerateRequest(BaseModel):
    class_name: str
    chapters: list = []
    student_name: str = None
    concept: str = None

class RagRequest(BaseModel):
    class_name: str

# --- 1. نقاط نهاية المعلم الأساسية (Teacher Stats) ---

@app.get("/teacher/stats")
async def get_teacher_stats(class_name: str = "فصل (أ)"):
    conn = get_db_connection()
    avg = conn.execute("SELECT AVG(total_score) FROM student_stats WHERE class_name = ?", (class_name,)).fetchone()[0] or 0
    risk = conn.execute("SELECT COUNT(*) FROM student_stats WHERE total_score < 50 AND class_name = ?", (class_name,)).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM student_stats WHERE class_name = ?", (class_name,)).fetchone()[0]
    conn.close()
    return {"avg_score": round(avg, 1), "students_at_risk": risk, "total_students": total}

@app.get("/teacher/students")
async def get_students(class_name: str = "فصل (أ)"):
    """جلب قائمة الطلاب للفصل المختار لتعبئة القائمة المنسدلة"""
    conn = get_db_connection()
    res = [dict(r) for r in conn.execute("SELECT id, name FROM student_stats WHERE class_name = ?", (class_name,)).fetchall()]
    conn.close()
    return res

# ✅ Endpoint جديد لجلب جميع الفصول (يحل مشكلة ظهور فصلين فقط)
@app.get("/api/chapters")
async def get_all_chapters():
    """
    جلب قائمة جميع الفصول/المفاهيم المتاحة في المنهج مع إحصائياتها
    """
    conn = get_db_connection()
    
    # جلب كل المفاهيم مع احصائياتها
    query = """
        SELECT 
            c.concept,
            COUNT(DISTINCT c.student_id) as student_count,
            AVG(c.score) as avg_score
        FROM concept_stats c
        GROUP BY c.concept
        ORDER BY c.concept
    """
    concepts = conn.execute(query).fetchall()
    conn.close()
    
    # الترتيب الصحيح للفصول (حسب المنهج)
    chapter_order = [
        "الأعداد النسبية",
        "القوى والجذور", 
        "التناسب",
        "المساحات",
        "الجبر"
    ]
    
    # إنشاء قائمة مرتبة
    chapters_list = []
    for idx, chapter_name in enumerate(chapter_order, 1):
        # البحث عن الفصل في النتائج
        found = False
        for row in concepts:
            if row['concept'] == chapter_name:
                chapters_list.append({
                    "id": idx,
                    "name": chapter_name,
                    "display_name": chapter_name,
                    "avg_score": round(row['avg_score'], 1),
                    "student_count": row['student_count']
                })
                found = True
                break
        
        # إذا الفصل مو موجود في البيانات، نضيفه فاضي
        if not found:
            chapters_list.append({
                "id": idx,
                "name": chapter_name,
                "display_name": chapter_name,
                "avg_score": 0,
                "student_count": 0
            })
    
    return chapters_list

# --- 2. نقاط نهاية التحليل البياني (Charts) ---

@app.get("/teacher/analytics/chapters-avg")
async def get_chapters_avg(class_name: str = "فصل (أ)"):
    """الرسم البياني الأول: متوسط الفصل لكل مهارة"""
    conn = get_db_connection()
    data = conn.execute("""
        SELECT c.concept as name, AVG(c.score) as score 
        FROM concept_stats c 
        JOIN student_stats s ON c.student_id = s.id 
        WHERE s.class_name = ? 
        GROUP BY c.concept
        ORDER BY c.concept""", (class_name,)).fetchall()
    conn.close()
    return [dict(r) for r in data]

@app.get("/teacher/analytics/chapter-details/{chap_num}")
async def get_chapter_details(chap_num: int, class_name: str = "فصل (أ)"):
    """
    ✅ تحسين: دعم جلب تفاصيل أي فصل ديناميكياً
    """
    conn = get_db_connection()
    
    # خريطة لربط رقم الفصل بالمسمى الموجود في قاعدة البيانات
    chapter_map = {
        1: "الأعداد النسبية",
        2: "القوى والجذور",
        3: "التناسب",
        4: "المساحات",
        5: "الجبر"
    }
    
    target_concept = chapter_map.get(chap_num)
    
    if not target_concept:
        # إذا الرقم مو موجود، نجيب كل المفاهيم ونحاول نطابق
        all_concepts = conn.execute("SELECT DISTINCT concept FROM concept_stats").fetchall()
        concepts_list = [r['concept'] for r in all_concepts]
        
        if chap_num <= len(concepts_list):
            target_concept = concepts_list[chap_num - 1]
        else:
            conn.close()
            raise HTTPException(status_code=404, detail="رقم الفصل غير موجود")
    
    # البحث بالاسم المباشر أو بالنمط الرقمي لضمان جلب البيانات
    query = """
        SELECT s.name, c.score 
        FROM student_stats s 
        JOIN concept_stats c ON s.id = c.student_id 
        WHERE (c.concept = ? OR c.concept LIKE ?) AND s.class_name = ? 
        ORDER BY c.score DESC
    """
    search_pattern = f"{chap_num}.%"
    data = conn.execute(query, (target_concept, search_pattern, class_name)).fetchall()
    conn.close()
    
    if not data:
        return []
    
    return [dict(r) for r in data]

@app.get("/teacher/analytics/classes-compare")
async def get_classes_compare():
    """الرسم البياني الرابع: مقارنة أداء الفصول"""
    conn = get_db_connection()
    data = conn.execute("SELECT class_name as name, AVG(total_score) as score FROM student_stats GROUP BY class_name").fetchall()
    conn.close()
    return [dict(r) for r in data]

@app.get("/teacher/student/{student_id}/performance")
async def get_student_perf(student_id: int):
    """جلب أداء طالب محدد في كل المفاهيم"""
    conn = get_db_connection()
    data = conn.execute("""
        SELECT concept as subject, score 
        FROM concept_stats 
        WHERE student_id = ?
        ORDER BY concept
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in data]

# --- 3. نقاط نهاية مصنع الاختبارات والطلاب المتعثرين ---

@app.get("/api/analytics/struggling")
async def get_struggling_students(class_name: str):
    """جلب قائمة الطلاب المتعثرين في الفصل"""
    conn = get_db_connection()
    query = """
        SELECT s.name, c.concept, c.score, s.id 
        FROM concept_stats c JOIN student_stats s ON c.student_id = s.id
        WHERE s.class_name = ? AND c.score < 50
        ORDER BY c.score ASC
    """
    rows = conn.execute(query, (class_name,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/quiz/generate-and-assign")
async def generate_and_assign(req: QuizGenerateRequest):
    """
    ✅ تحسين: توليد وحفظ الاختبارات مع معالجة أخطاء شاملة
    """
    try:
        # توليد الاختبار
        quiz_json = generate_dynamic_quiz(req.class_name, req.chapters, req.concept)
        
        # ✅ التحقق من نجاح التوليد
        if "error" in quiz_json or not quiz_json.get("questions"):
            raise HTTPException(
                status_code=500, 
                detail=f"فشل توليد الاختبار: {quiz_json.get('error', 'خطأ غير معروف')}"
            )
        
        # حفظ الاختبار في قاعدة البيانات
        conn = get_db_connection()
        
        if req.concept and req.student_name:
            # اختبار علاجي مخصص
            conn.execute(
                "INSERT INTO custom_quizzes (student_name, quiz_data, status) VALUES (?, ?, 'pending')",
                (req.student_name, json.dumps(quiz_json, ensure_ascii=False))
            )
        else:
            # اختبار عام للفصل
            conn.execute("DELETE FROM class_quizzes WHERE class_name = ?", (req.class_name,))
            conn.execute(
                "INSERT INTO class_quizzes (class_name, quiz_data) VALUES (?, ?)",
                (req.class_name, json.dumps(quiz_json, ensure_ascii=False))
            )
        
        conn.commit()
        conn.close()
        
        return {
            "message": "تم توليد وحفظ الاختبار بنجاح ✅",
            "quiz": quiz_json,
            "questions_count": len(quiz_json.get("questions", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في المعالجة: {str(e)}")

# --- 4. نقاط نهاية الطالب والـ RAG ---

@app.get("/api/student/quiz")
async def get_student_quiz(name: str, class_name: str):
    """
    ✅ جلب اختبار الطالب مع تفاصيل أفضل للأخطاء
    """
    quiz = get_student_quiz_logic(name, class_name)
    
    if not quiz:
        raise HTTPException(
            status_code=404, 
            detail=f"لا يوجد اختبار متاح حالياً للطالب '{name}' في {class_name}. يرجى التواصل مع المعلم."
        )
    
    # ✅ التحقق من وجود أسئلة
    if not quiz.get("questions"):
        raise HTTPException(
            status_code=404,
            detail="الاختبار فارغ أو تالف. يرجى التواصل مع المعلم لإعادة توليد الاختبار."
        )
    
    return quiz

@app.post("/teacher/generate-summary")
async def generate_summary(req: RagRequest):
    """
    توليد تقرير تحليلي للفصل باستخدام RAG (محسّن)
    """
    try:
        analysis_result = get_rag_analysis(req.class_name)
        return {"summary": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في توليد التقرير: {str(e)}")

# ✅ Endpoint للتحقق من صحة النظام
@app.get("/health")
async def health_check():
    """فحص صحة النظام والاتصال بقاعدة البيانات"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # فحص الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # فحص عدد الطلاب
        cursor.execute("SELECT COUNT(*) FROM student_stats")
        students_count = cursor.fetchone()[0]
        
        # فحص عدد المفاهيم
        cursor.execute("SELECT COUNT(DISTINCT concept) FROM concept_stats")
        concepts_count = cursor.fetchone()[0]
        
        # فحص الاختبارات
        cursor.execute("SELECT COUNT(*) FROM class_quizzes")
        class_quizzes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM custom_quizzes")
        custom_quizzes_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables": tables,
            "students": students_count,
            "concepts": concepts_count,
            "class_quizzes": class_quizzes_count,
            "custom_quizzes": custom_quizzes_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# تشغيل السيرفر (يجب أن يكون في نهاية الملف)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)