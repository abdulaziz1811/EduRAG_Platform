import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core import get_rag_analysis

app = FastAPI()

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

# موديل لاستقبال اسم الفصل في طلب الـ RAG
class RagRequest(BaseModel):
    class_name: str

@app.get("/teacher/stats")
async def get_teacher_stats(class_name: str = "فصل (أ)"):
    conn = get_db_connection()
    # تصفية الإحصائيات بناءً على الفصل
    avg = conn.execute("SELECT AVG(total_score) FROM student_stats WHERE class_name = ?", (class_name,)).fetchone()[0] or 0
    risk = conn.execute("SELECT COUNT(*) FROM student_stats WHERE total_score < 50 AND class_name = ?", (class_name,)).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM student_stats WHERE class_name = ?", (class_name,)).fetchone()[0]
    conn.close()
    return {"avg_score": round(avg, 1), "students_at_risk": risk, "total_students": total, "total_quizzes": 5}

@app.get("/teacher/students")
async def get_students(class_name: str = "فصل (أ)"):
    conn = get_db_connection()
    # جلب طلاب الفصل المختار فقط
    res = [dict(r) for r in conn.execute("SELECT id, name FROM student_stats WHERE class_name = ?", (class_name,)).fetchall()]
    conn.close()
    return res

@app.get("/teacher/analytics/chapters-avg")
async def get_chapters_avg(class_name: str = "فصل (أ)"):
    conn = get_db_connection()
    # متوسط الفصل المختار لكل مهارة
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
    chap_name = f"الفصل {chap_num}"
    # خرائط الدرجات لطلاب فصل محدد في فصل دراسي معين
    data = conn.execute("""
        SELECT s.name, c.score 
        FROM student_stats s JOIN concept_stats c ON s.id = c.student_id 
        WHERE c.concept LIKE ? AND s.class_name = ? ORDER BY c.score DESC""", (f"%{chap_num}%", class_name)).fetchall()
    conn.close()
    return [dict(r) for r in data]

@app.get("/teacher/analytics/classes-compare")
async def get_classes_compare():
    conn = get_db_connection()
    data = conn.execute("SELECT class_name as name, AVG(total_score) as score FROM student_stats GROUP BY class_name").fetchall()
    conn.close()
    return [dict(r) for r in data]

@app.get("/teacher/student/{student_id}/performance")
async def get_student_perf(student_id: int):
    conn = get_db_connection()
    data = conn.execute("SELECT concept as subject, score FROM concept_stats WHERE student_id = ?", (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in data]

@app.post("/teacher/generate-summary")
async def generate_summary(req: RagRequest):
    try:
        # إرسال الفصل المختار للدالة لعمل تحليل مخصص
        analysis_result = get_rag_analysis(req.class_name)
        return {"summary": analysis_result}
    except Exception as e:
        return {"summary": f"خطأ في الـ RAG: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)