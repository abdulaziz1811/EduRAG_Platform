"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../components/Navbar";

// --- مكون فرعي لجلب الشرح من الباك إند بشكل آمن ---
function RAGExplanation({ q }: { q: any }) {
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchExplanation = async () => {
    if (explanation) return; // لا تطلب الشرح إذا كان موجوداً
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/quiz/explain-error', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q.question,
          correct_answer: q.answer,
          concept: q.concept
        })
      });
      const data = await res.json();
      setExplanation(data.explanation);
    } catch (e) {
      setExplanation("عذراً، تعذر جلب الشرح حالياً من الكتاب المدرسي.");
    }
    setLoading(false);
  };

  return (
    <details 
      className="mt-4 bg-white rounded-2xl border border-red-200 overflow-hidden" 
      onToggle={(e: any) => e.target.open && fetchExplanation()}
    >
      <summary className="p-4 cursor-pointer font-black text-red-700 hover:bg-red-50 transition-all flex justify-between items-center">
        <span>تحليل الخطأ واسترجاع الشرح من الكتاب (RAG Pro)</span>
        {loading && <span className="animate-spin text-red-500 text-xl">⏳</span>}
      </summary>
      <div className="p-4 text-slate-700 leading-relaxed border-t border-red-100 bg-slate-50 whitespace-pre-wrap font-medium">
        {loading ? "جاري استرجاع البيانات والتحليل من الكتاب المدرسي..." : explanation}
      </div>
    </details>
  );
}

// --- المكون الرئيسي لواجهة الطالب ---
export default function StudentIntegratedPage() {
  const [step, setStep] = useState<'login' | 'quiz' | 'result'>('login');
  const [formData, setFormData] = useState({ name: "", className: "", chapter: "" });
  const [quizData, setQuizData] = useState<any>(null);
  const [answers, setAnswers] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const startQuiz = async () => {
    if (!formData.name || !formData.className) return alert("يرجى إكمال البيانات المطلوبة أولاً.");
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/quiz/generate-and-assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chapters: formData.chapter ? [formData.chapter] : [],
          class_name: formData.className,
          student_name: formData.name
        })
      });
      const data = await res.json();

      if (data && data.quiz && data.quiz.questions) {
        setQuizData(data.quiz);
        setStep('quiz');
      } else {
        alert("عذراً، لم نتمكن من توليد التقييم حالياً. يرجى المحاولة لاحقاً.");
      }
    } catch (e) {
      alert("خطأ في الاتصال بالسيرفر. تأكد من تشغيل نظام الـ Backend.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-right" dir="rtl">
      <Navbar />
      
      <div className="flex items-center justify-center p-6 pt-24">
        <AnimatePresence mode="wait">
          
          {/* شاشة تسجيل الدخول */}
          {step === 'login' && (
            <motion.div 
              key="login" 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }} 
              exit={{ opacity: 0, y: -20 }} 
              className="bg-white p-10 rounded-[40px] shadow-2xl max-w-md w-full"
            >
              <h1 className="text-2xl font-black mb-6 text-slate-800 text-center">تسجيل دخول الطالب - EduRAG Pro</h1>
              
              <input 
                type="text" 
                placeholder="الاسم الثلاثي للطالب" 
                className="w-full p-4 mb-4 bg-slate-100 rounded-2xl outline-none border-2 focus:border-blue-500 text-slate-800 font-bold" 
                onChange={e => setFormData({ ...formData, name: e.target.value })} 
              />
              
              <select 
                className="w-full p-4 mb-4 bg-slate-100 rounded-2xl font-bold text-slate-800 outline-none"
                onChange={e => setFormData({ ...formData, className: e.target.value })}
              >
                <option value="">تحديد الفصل الدراسي</option>
                <option value="فصل (أ)">فصل (أ)</option>
                <option value="فصل (ب)">فصل (ب)</option>
              </select>

              <select 
                className="w-full p-4 mb-6 bg-slate-100 rounded-2xl font-bold text-slate-800 outline-none"
                onChange={e => setFormData({ ...formData, chapter: e.target.value })}
              >
                <option value="">تحديد الوحدة الدراسية للتقييم</option>
                <option value="الأعداد النسبية">الوحدة 1: الأعداد النسبية</option>
                <option value="القوى والجذور">الوحدة 2: القوى والجذور</option>
                <option value="التناسب">الوحدة 3: التناسب</option>
                <option value="المساحات">الوحدة 4: المساحات</option>
                <option value="الجبر">الوحدة 5: الجبر</option>
              </select>

              <button 
                onClick={startQuiz} 
                disabled={loading} 
                className="w-full bg-blue-600 text-white py-4 rounded-2xl font-black text-lg hover:bg-blue-700 transition-all shadow-lg"
              >
                {loading ? "جاري تحميل التقييم..." : "بدء التقييم الدراسي"}
              </button>
            </motion.div>
          )}

          {/* شاشة الاختبار */}
          {step === 'quiz' && quizData && (
            <motion.div 
              key="quiz" 
              initial={{ x: 50, opacity: 0 }} 
              animate={{ x: 0, opacity: 1 }} 
              className="bg-white p-8 rounded-[30px] shadow-xl max-w-2xl w-full text-slate-800"
            >
              <h2 className="text-xl font-black mb-6 border-b pb-4 text-blue-600">{quizData.quiz_name}</h2>
              
              <div className="max-h-[60vh] overflow-y-auto pr-2">
                {quizData?.questions?.map((q: any, idx: number) => (
                  <div key={idx} className="mb-8 p-6 bg-slate-50 rounded-2xl border border-slate-100">
                    <p className="font-black mb-4 text-lg leading-relaxed">{idx + 1}. {q.question}</p>
                    <div className="grid grid-cols-1 gap-3">
                      {q.options.map((opt: string) => (
                        <button 
                          key={opt} 
                          onClick={() => setAnswers({ ...answers, [idx]: opt })}
                          className={`p-4 rounded-xl border-2 transition-all font-bold text-right ${
                            answers[idx] === opt 
                              ? 'border-blue-500 bg-blue-50 text-blue-700' 
                              : 'border-white bg-white hover:bg-slate-100 text-slate-600'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              
              <button 
                onClick={() => setStep('result')} 
                className="w-full bg-green-600 text-white py-4 rounded-2xl font-black text-xl shadow-lg mt-6 hover:bg-green-700 transition-all"
              >
                إنهاء الاختبار واعتماد الإجابات
              </button>
            </motion.div>
          )}

          {/* شاشة النتائج والتحليل (EduRAG Pro) */}
          {step === 'result' && (
            <motion.div 
              key="res" 
              initial={{ opacity: 0, scale: 0.95 }} 
              animate={{ opacity: 1, scale: 1 }} 
              className="bg-white p-8 rounded-[40px] max-w-4xl w-full text-slate-800 shadow-2xl overflow-y-auto max-h-[85vh]"
            >
              <div className="text-center mb-10 border-b pb-6">
                <h1 className="text-3xl font-black text-slate-900">تقرير الأداء الأكاديمي - EduRAG Pro</h1>
                <p className="text-slate-500 font-bold mt-2">تحليل دقيق للاستجابات بناءً على المحتوى المنهجي</p>
              </div>

              {quizData.questions.map((q: any, idx: number) => {
                const isCorrect = answers[idx] === q.answer;
                return (
                  <div key={idx} className={`mb-8 p-6 rounded-3xl border-2 ${isCorrect ? 'border-green-100 bg-green-50/50' : 'border-red-100 bg-red-50/50'}`}>
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="font-black text-xl text-slate-800 leading-snug w-4/5">{idx + 1}. {q.question}</h3>
                      <span className={`px-4 py-1 rounded-full text-sm font-black ${isCorrect ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                        {isCorrect ? 'إتقان' : 'غير متقن'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div className="p-4 bg-white rounded-2xl shadow-sm border border-slate-100">
                        <span className="block text-slate-400 text-xs font-black mb-1 uppercase tracking-wider">إجابة الطالب</span>
                        <span className={`text-lg font-black ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                          {answers[idx] || "لم يتم تقديم إجابة"}
                        </span>
                      </div>
                      <div className="p-4 bg-white rounded-2xl shadow-sm border border-slate-100">
                        <span className="block text-slate-400 text-xs font-black mb-1 uppercase tracking-wider">الإجابة النموذجية</span>
                        <span className="text-lg font-black text-blue-700">{q.answer}</span>
                      </div>
                    </div>

                    {!isCorrect && <RAGExplanation q={q} />}
                  </div>
                );
              })}

              <div className="flex gap-4 mt-10">
                <button 
                  onClick={() => window.location.reload()} 
                  className="flex-1 bg-slate-900 text-white py-5 rounded-[2rem] font-black text-xl shadow-xl hover:bg-black transition-all"
                >
                  إغلاق التقرير والعودة للرئيسية
                </button>
                <button 
                  onClick={() => window.print()} 
                  className="px-10 bg-blue-100 text-blue-700 rounded-[2rem] font-black hover:bg-blue-200 transition-all"
                >
                  طباعة التقرير
                </button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
}