from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional  # أضفنا Optional
from . import core

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