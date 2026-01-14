from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from . import core

app = FastAPI(title="EduRAG Platform API")

# ==========================================
# 🚨 منطقة تصريح المرور (CORS) - مهم جداً
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # السماح للجميع (الفرونت إند)
    allow_credentials=True,
    allow_methods=["*"],     # السماح بكل أنواع الطلبات (GET, POST, OPTIONS)
    allow_headers=["*"],     # السماح بكل الهيدرز
)
# ==========================================

# --- نماذج البيانات ---
class QuizRequest(BaseModel):
    api_key: str
    chapters: List[int]
    num_questions: int = 5

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

# --- الروابط (Endpoints) ---

@app.get("/")
def read_root():
    return {"message": "EduRAG System is Running 🚀"}

@app.post("/api/generate-quiz")
def generate_quiz(payload: QuizRequest):
    questions = core.generate_quiz_logic(payload.api_key, payload.chapters, payload.num_questions)
    # التحقق من وجود خطأ في الرد
    if isinstance(questions, dict) and "error" in questions:
        raise HTTPException(status_code=500, detail=questions["error"])
    return {"questions": questions}

@app.post("/api/submit-quiz")
def submit_quiz(payload: SubmissionRequest):
    result = core.save_submission(
        payload.student_name, 
        payload.chapter, 
        payload.model_dump()
    )
    return result

@app.get("/api/dashboard")
def get_dashboard():
    stats = core.get_dashboard_stats()
    return {"stats": stats}