from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional  # أضفنا Optional
from . import core
import sqlite3
import os
app = FastAPI(title="EduRAG Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- نماذج البيانات ---
class QuizRequest(BaseModel):
    api_key: str
    chapters: List[int]       # أرقام الفصول
    num_questions: int = 10   # الافتراضي 10 أسئلة
    focus_concepts: List[str] = [] # قائمة المفاهيم اللي الطالب ضعيف فيها (للتحسين)

class SubmissionDetail(BaseModel):
    question: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    concept: str

class SubmissionRequest(BaseModel):
    student_name: str
    chapter: int
    details: List[SubmissionDetail]

# ✅ تعديل نموذج طلب الشرح لإضافة مفتاح API
class ExplainRequest(BaseModel):
    concept: str
    api_key: Optional[str] = None 

# --- الروابط (Endpoints) ---

@app.get("/")
def read_root():
    return {"message": "EduRAG System is Running 🚀"}

@app.post("/api/generate-quiz")
def generate_quiz(payload: QuizRequest):
    # التعديل هنا: تمرير focus_concepts
    questions = core.generate_quiz_logic(
        payload.api_key, 
        payload.chapters, 
        payload.num_questions, 
        payload.focus_concepts
    )
    if isinstance(questions, dict) and "error" in questions:
        raise HTTPException(status_code=500, detail=questions["error"])
    return {"questions": questions}

@app.post("/api/submit-quiz")
def submit_quiz(payload: SubmissionRequest):
    result = core.save_submission(payload.student_name, payload.chapter, payload.model_dump())
    return result

@app.get("/api/dashboard")
def get_dashboard():
    stats = core.get_dashboard_stats()
    return {"stats": stats}

@app.post("/api/explain")
def explain_concept(payload: ExplainRequest):
    """يقوم بالبحث في الكتاب ثم توليد شرح نظيف باستخدام AI"""
    explanation = core.get_explanation_from_book(payload.concept, payload.api_key)
    return explanation
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جلب جميع الطلاب
    cursor.execute("SELECT id, name, email FROM users WHERE role = 'student'")
    students = cursor.fetchall()
    
    dashboard_data = []
    
    for student in students:
        s_id, name, email = student
        # جلب نتائج الطالب
        cursor.execute("SELECT score, total_questions, topic FROM quiz_results WHERE user_id = ?", (s_id,))
        results = cursor.fetchall()
        
        quizzes_taken = len(results)
        average_score = 0
        if quizzes_taken > 0:
            # حساب المعدل كنسبة مئوية
            total_percent = sum([(r[0]/r[1])*100 for r in results])
            average_score = round(total_percent / quizzes_taken, 1)
            
        dashboard_data.append({
            "id": s_id,
            "name": name,
            "email": email,
            "quizzes_taken": quizzes_taken,
            "average_score": average_score,
            "last_active": "منذ يومين" # قيمة افتراضية أو يمكن جلبها من التاريخ
        })
    
    conn.close()
    return {"students": dashboard_data}
# دالة مساعدة للاتصال بقاعدة البيانات
def get_db_connection():
    # تحديد مسار قاعدة البيانات بشكل ديناميكي لضمان عملها من أي مجلد
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "edurag.db")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # للوصول للبيانات بأسماء الأعمدة
    return conn