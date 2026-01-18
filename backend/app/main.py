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
        GROUP BY c.concept""", (class_name,)).fetchall()
    conn.close()
    return [dict(r) for r in data]

@app.get("/teacher/analytics/chapter-details/{chap_num}")
async def get_chapter_details(chap_num: int, class_name: str = "فصل (أ)"):
    conn = get_db_connection()
    
    # خريطة لربط رقم الفصل بالمسمى الموجود في قاعدة البيانات عندك
    chapter_map = {
        1: "الأعداد النسبية",
        2: "القوى والجذور",
        3: "التناسب",
        4: "المساحات",
        5: "الجبر"
    }
    
    target_concept = chapter_map.get(chap_num, "")
    
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
    conn = get_db_connection()
    # جلب درجات الطالب في كل المفاهيم
    data = conn.execute("""
        SELECT concept as subject, score 
        FROM concept_stats 
        WHERE student_id = ?
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in data]

# --- 3. نقاط نهاية مصنع الاختبارات والطلاب المتعثرين ---

@app.get("/api/analytics/struggling")
async def get_struggling_students(class_name: str):
    conn = get_db_connection()
    query = """
        SELECT s.name, c.concept, c.score, s.id 
        FROM concept_stats c JOIN student_stats s ON c.student_id = s.id
        WHERE s.class_name = ? AND c.score < 50
    """
    rows = conn.execute(query, (class_name,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/quiz/generate-and-assign")
async def generate_and_assign(req: QuizGenerateRequest):
    quiz_json = generate_dynamic_quiz(req.class_name, req.chapters, req.concept)
    conn = get_db_connection()
    if req.concept and req.student_name:
        conn.execute("INSERT INTO custom_quizzes (student_name, quiz_data, status) VALUES (?, ?, 'pending')",
                     (req.student_name, json.dumps(quiz_json)))
    else:
        conn.execute("DELETE FROM class_quizzes WHERE class_name = ?", (req.class_name,))
        conn.execute("INSERT INTO class_quizzes (class_name, quiz_data) VALUES (?, ?)",
                     (req.class_name, json.dumps(quiz_json)))
    conn.commit()
    conn.close()
    return {"message": "تم بنجاح", "quiz": quiz_json}

# --- 4. نقاط نهاية الطالب والـ RAG ---

@app.get("/api/student/quiz")
async def get_student_quiz(name: str, class_name: str):
    quiz = get_student_quiz_logic(name, class_name)
    if not quiz:
        raise HTTPException(status_code=404, detail="لا يوجد اختبار متاح حالياً لفصلك")
    return quiz

@app.post("/teacher/generate-summary")
async def generate_summary(req: RagRequest):
    analysis_result = get_rag_analysis(req.class_name)
    return {"summary": analysis_result}

# تشغيل السيرفر (يجب أن يكون في نهاية الملف)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)