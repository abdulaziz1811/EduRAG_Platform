import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// تعريف أنواع البيانات
export interface Question {
  id: number;
  text: string;
  options: string[];
  correct_answer: string;
  concept: string;
}

export interface QuizPayload {
  api_key: string;
  chapters: number[];
  num_questions: number;
  focus_concepts?: string[];
}

export interface SubmissionDetail {
  question: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  concept: string;
}

export interface SubmitPayload {
  student_name: string;
  chapter: number;
  details: SubmissionDetail[];
}

// دوال الاتصال
export const generateQuiz = async (payload: QuizPayload) => {
  const res = await api.post('/generate-quiz', payload);
  return res.data.questions;
};

export const submitQuizResult = async (payload: SubmitPayload) => {
  const res = await api.post('/submit-quiz', payload);
  return res.data;
};

export const explainConcept = async (concept: string, apiKey: string) => {
  const res = await api.post('/explain', { concept, api_key: apiKey });
  return res.data;
};