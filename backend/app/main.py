from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from app import core # تأكد من أن ملف core.py في نفس المجلد

app = FastAPI()

# إعداد CORS للسماح للفرونت اند بالاتصال
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# نماذج البيانات
class SummaryRequest(BaseModel):
    teacher_id: int

class QuizRequest(BaseModel):
    topic: str

# --- مسارات المعلم ---

@app.get("/teacher/stats")
async def get_teacher_stats():
    return core.get_stats_logic()

@app.get("/teacher/analytics")
async def get_analytics():
    conn = core.get_db_connection()
    cursor = conn.cursor()
    
    # 1. إحصائيات المفاهيم (للرسم البياني العام)
    concept_data = cursor.execute("""
        SELECT concept, AVG(score) as avg_score, 
        (SUM(CASE WHEN score < 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as failure_rate
        FROM scores GROUP BY concept
    """).fetchall()
    
    # 2. بيانات الطلاب (للقائمة المنسدلة والرسم البياني الخاص)
    student_rows = cursor.execute("""
        SELECT u.id, u.name, AVG(s.score) as average,
        (SELECT GROUP_CONCAT(s2.concept || ':' || s2.score) FROM scores s2 WHERE s2.user_id = u.id) as details
        FROM users u 
        JOIN scores s ON u.id = s.user_id 
        WHERE u.role = 'student' 
        GROUP BY u.id
    """).fetchall()
    
    conn.close()
    return {
        "concepts": [dict(row) for row in concept_data],
        "students": [dict(row) for row in student_rows]
    }

@app.post("/teacher/generate-summary")
async def generate_summary(req: SummaryRequest):
    summary_text = core.generate_summary_logic()
    return {"summary": summary_text}

# --- مسارات الطالب ---

@app.post("/api/quiz")
async def create_quiz(req: QuizRequest):
    questions = core.generate_quiz(req.topic)
    return questions

@app.get("/ask")
def ask_question(query: str):
    return {"answer": core.get_rag_response(query)}