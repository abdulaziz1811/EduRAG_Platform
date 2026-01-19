"""
EduRAG Platform - Main API Server
=================================
FastAPI Backend for Educational RAG System
"""

import os
import json
import logging
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# استيراد من الـ app package
from app.core import get_rag_analysis, generate_dynamic_quiz, get_student_quiz_logic, explain_error_with_rag
from app.database import get_db_connection, initialize_database, check_tables_exist

# ===== إعداد اللوقر =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== إنشاء التطبيق =====
app = FastAPI(
    title="EduRAG Platform API",
    description="منصة تعليمية ذكية باستخدام RAG",
    version="1.0.0"
)

# ===== إعدادات CORS =====
# في الإنتاج، غيّر هذي القيم للدومينات المسموحة فقط
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# ===== مسار قاعدة البيانات =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")


# ===== النماذج (Pydantic Models) =====

class QuizGenerateRequest(BaseModel):
    """طلب توليد اختبار"""
    class_name: str = Field(..., description="اسم الفصل")
    chapters: List[str] = Field(default=[], description="الفصول المختارة")
    student_name: Optional[str] = Field(default=None, description="اسم الطالب (للاختبار المخصص)")
    concept: Optional[str] = Field(default=None, description="المفهوم المستهدف (للاختبار العلاجي)")


class RagRequest(BaseModel):
    """طلب تحليل RAG"""
    class_name: str = Field(..., description="اسم الفصل")


# ===== Startup Event =====

@app.on_event("startup")
async def startup_event():
    """تنفيذ عند بدء التطبيق"""
    logger.info("🚀 جاري بدء تشغيل EduRAG Platform...")
    
    # التحقق من قاعدة البيانات
    status = check_tables_exist()
    if not status['is_valid']:
        logger.warning(f"⚠️ جداول مفقودة: {status['missing']}")
        logger.info("جاري إنشاء الجداول...")
        initialize_database()
    
    logger.info("✅ EduRAG Platform جاهز!")


# ===== 1. نقاط نهاية المعلم (Teacher Endpoints) =====

@app.get("/teacher/stats")
async def get_teacher_stats(class_name: str = "فصل (أ)"):
    """جلب المؤشرات العامة لأداء الفصل الدراسي"""
    try:
        with get_db_connection() as conn:
            # متوسط درجات الفصل
            avg = conn.execute(
                "SELECT AVG(total_score) FROM student_stats WHERE class_name = ?", 
                (class_name,)
            ).fetchone()[0] or 0
            
            # عدد الحالات الحرجة
            risk = conn.execute(
                "SELECT COUNT(*) FROM student_stats WHERE total_score < 50 AND class_name = ?", 
                (class_name,)
            ).fetchone()[0]
            
            # إجمالي الطلاب
            total_students = conn.execute(
                "SELECT COUNT(*) FROM student_stats WHERE class_name = ?", 
                (class_name,)
            ).fetchone()[0]
            
            # حساب الوحدات المقيمة (الدروس المنجزة)
            query_finished = """
                SELECT COUNT(DISTINCT c.concept) 
                FROM concept_stats c 
                JOIN student_stats s ON c.student_id = s.id 
                WHERE s.class_name = ?
            """
            finished_chapters = conn.execute(query_finished, (class_name,)).fetchone()[0] or 0
            
        return {
            "avg_score": round(avg, 1), 
            "students_at_risk": risk, 
            "total_students": total_students,
            "total_quizzes": finished_chapters
        }
    except Exception as e:
        logger.error(f"خطأ في جلب إحصائيات النظام: {e}")
        raise HTTPException(status_code=500, detail="فشل في جلب البيانات الإحصائية")

@app.get("/teacher/students")
async def get_students(class_name: str = Query(default="فصل (أ)", description="اسم الفصل")):
    """جلب قائمة طلاب الفصل"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM student_stats WHERE class_name = ?",
                (class_name,)
            )
            students = [dict(row) for row in cursor.fetchall()]
        return students
    except Exception as e:
        logger.error(f"خطأ في جلب قائمة الطلاب: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 2. نقاط نهاية الفصول والمفاهيم =====

@app.get("/api/chapters")
async def get_all_chapters():
    """جلب جميع الفصول/المفاهيم مع إحصائياتها"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.concept,
                    COUNT(DISTINCT c.student_id) as student_count,
                    AVG(c.score) as avg_score
                FROM concept_stats c
                GROUP BY c.concept
                ORDER BY c.concept
            """)
            concepts = cursor.fetchall()
        
        # الترتيب الصحيح للفصول
        chapter_order = [
            "الأعداد النسبية",
            "القوى والجذور",
            "التناسب",
            "المساحات",
            "الجبر"
        ]
        
        chapters_list = []
        for idx, chapter_name in enumerate(chapter_order, 1):
            found = False
            for row in concepts:
                if row['concept'] == chapter_name:
                    chapters_list.append({
                        "id": idx,
                        "name": chapter_name,
                        "display_name": chapter_name,
                        "avg_score": round(row['avg_score'], 1) if row['avg_score'] else 0,
                        "student_count": row['student_count']
                    })
                    found = True
                    break
            
            if not found:
                chapters_list.append({
                    "id": idx,
                    "name": chapter_name,
                    "display_name": chapter_name,
                    "avg_score": 0,
                    "student_count": 0
                })
        
        return chapters_list
    except Exception as e:
        logger.error(f"خطأ في جلب الفصول: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 3. نقاط نهاية التحليلات (Analytics) =====

@app.get("/teacher/analytics/chapters-avg")
async def get_chapters_avg(class_name: str = Query(default="فصل (أ)")):
    """متوسط درجات كل مفهوم في الفصل"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.concept as name, AVG(c.score) as score 
                FROM concept_stats c 
                JOIN student_stats s ON c.student_id = s.id 
                WHERE s.class_name = ? 
                GROUP BY c.concept
                ORDER BY c.concept
            """, (class_name,))
            data = [dict(row) for row in cursor.fetchall()]
        return data
    except Exception as e:
        logger.error(f"خطأ في جلب متوسطات الفصول: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teacher/analytics/chapter-details/{chap_num}")
async def get_chapter_details(chap_num: int, class_name: str = Query(default="فصل (أ)")):
    """تفاصيل درجات الطلاب في فصل معين"""
    chapter_map = {
        1: "الأعداد النسبية",
        2: "القوى والجذور",
        3: "التناسب",
        4: "المساحات",
        5: "الجبر"
    }
    
    target_concept = chapter_map.get(chap_num)
    if not target_concept:
        raise HTTPException(status_code=404, detail="رقم الفصل غير موجود")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.name, c.score 
                FROM student_stats s 
                JOIN concept_stats c ON s.id = c.student_id 
                WHERE c.concept = ? AND s.class_name = ? 
                ORDER BY c.score DESC
            """, (target_concept, class_name))
            data = [dict(row) for row in cursor.fetchall()]
        return data
    except Exception as e:
        logger.error(f"خطأ في جلب تفاصيل الفصل: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teacher/analytics/classes-compare")
async def get_classes_compare():
    """مقارنة أداء الفصول"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT class_name as name, AVG(total_score) as score 
                FROM student_stats 
                GROUP BY class_name
            """)
            data = [dict(row) for row in cursor.fetchall()]
        return data
    except Exception as e:
        logger.error(f"خطأ في مقارنة الفصول: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/teacher/student/{student_id}/performance")
async def get_student_performance(student_id: int):
    """أداء طالب معين في كل المفاهيم"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT concept as subject, score 
                FROM concept_stats 
                WHERE student_id = ?
                ORDER BY concept
            """, (student_id,))
            data = [dict(row) for row in cursor.fetchall()]
        
        if not data:
            raise HTTPException(status_code=404, detail="الطالب غير موجود")
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في جلب أداء الطالب: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 4. نقاط نهاية الطلاب المتعثرين =====

@app.get("/api/analytics/struggling")
async def get_struggling_students(class_name: str = Query(..., description="اسم الفصل")):
    """قائمة الطلاب المتعثرين في الفصل"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.name, c.concept, c.score, s.id 
                FROM concept_stats c 
                JOIN student_stats s ON c.student_id = s.id
                WHERE s.class_name = ? AND c.score < 50
                ORDER BY c.score ASC
            """, (class_name,))
            data = [dict(row) for row in cursor.fetchall()]
        return data
    except Exception as e:
        logger.error(f"خطأ في جلب الطلاب المتعثرين: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 5. نقاط نهاية الاختبارات =====

@app.post("/api/quiz/explain-error")
async def explain_error(data: dict):
    explanation = explain_error_with_rag(
        data['question'], 
        data['correct_answer'], 
        data['concept']
    )
    return {"explanation": explanation}
@app.post("/api/quiz/generate-and-assign")
async def generate_and_assign_quiz(req: QuizGenerateRequest):
    """توليد وحفظ اختبار"""
    try:
        # توليد الاختبار
        quiz_json = generate_dynamic_quiz(req.class_name, req.chapters, req.concept)
        
        # التحقق من نجاح التوليد
        if "error" in quiz_json or not quiz_json.get("questions"):
            raise HTTPException(
                status_code=500,
                detail=f"فشل توليد الاختبار: {quiz_json.get('error', 'خطأ غير معروف')}"
            )
        
        # حفظ الاختبار
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if req.concept and req.student_name:
                # اختبار علاجي مخصص
                cursor.execute(
                    "INSERT INTO custom_quizzes (student_name, quiz_data, status) VALUES (?, ?, 'pending')",
                    (req.student_name, json.dumps(quiz_json, ensure_ascii=False))
                )
            else:
                # اختبار عام للفصل
                cursor.execute("DELETE FROM class_quizzes WHERE class_name = ?", (req.class_name,))
                cursor.execute(
                    "INSERT INTO class_quizzes (class_name, quiz_data) VALUES (?, ?)",
                    (req.class_name, json.dumps(quiz_json, ensure_ascii=False))
                )
            
            conn.commit()
        
        return {
            "message": "تم توليد وحفظ الاختبار بنجاح ✅",
            "quiz": quiz_json,
            "questions_count": len(quiz_json.get("questions", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"خطأ في توليد الاختبار: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في المعالجة: {str(e)}")


@app.get("/api/student/quiz")
async def get_student_quiz(
    name: str = Query(..., description="اسم الطالب"),
    class_name: str = Query(..., description="اسم الفصل")
):
    """جلب اختبار الطالب"""
    quiz = get_student_quiz_logic(name, class_name)
    
    if not quiz:
        raise HTTPException(
            status_code=404,
            detail=f"لا يوجد اختبار متاح حالياً للطالب '{name}' في {class_name}. يرجى التواصل مع المعلم."
        )
    
    if not quiz.get("questions"):
        raise HTTPException(
            status_code=404,
            detail="الاختبار فارغ أو تالف. يرجى التواصل مع المعلم لإعادة توليد الاختبار."
        )
    
    return quiz


# ===== 6. نقاط نهاية RAG =====

@app.post("/teacher/generate-summary")
async def generate_summary(req: RagRequest):
    """توليد تقرير تحليلي للفصل باستخدام RAG"""
    try:
        analysis_result = get_rag_analysis(req.class_name)
        return {"summary": analysis_result}
    except Exception as e:
        logger.error(f"خطأ في توليد التقرير: {e}")
        raise HTTPException(status_code=500, detail=f"خطأ في توليد التقرير: {str(e)}")


# ===== 7. نقاط نهاية النظام =====

@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            stats = {}
            for table in ['student_stats', 'concept_stats', 'class_quizzes', 'custom_quizzes']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                else:
                    stats[table] = "❌ غير موجود"
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables": tables,
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "message": "مرحباً بك في EduRAG Platform API 🎓",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ===== تشغيل السيرفر =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )