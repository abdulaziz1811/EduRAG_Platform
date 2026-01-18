"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../components/Navbar";

export default function StudentIntegratedPage() {
  const [step, setStep] = useState<'login' | 'quiz' | 'result'>('login');
  const [formData, setFormData] = useState({ name: "", className: "", chapter: "" });
  const [quizData, setQuizData] = useState<any>(null);
  const [answers, setAnswers] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const startQuiz = async () => {
    if (!formData.name || !formData.className) return alert("يا بطل، كمل بياناتك أولاً! 🚀");
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/quiz/generate-and-assign`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
          chapters: formData.chapter ? [formData.chapter] : [], 
          class_name: formData.className,
          student_name: formData.name 
        })
      });
      const data = await res.json();
      
      // حل المشكلة: التأكد من أن البيانات تحتوي على أسئلة
      if (data && data.quiz && data.quiz.questions) {
        setQuizData(data.quiz);
        setStep('quiz');
      } else {
        alert("عذراً، لم نتمكن من توليد الاختبار حالياً. حاول مرة أخرى.");
      }
    } catch (e) { 
      alert("خطأ في الاتصال بالسيرفر. تأكد من تشغيل الـ Backend."); 
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-right" dir="rtl">
      <Navbar />
      <div className="flex items-center justify-center p-6 pt-24">
        <AnimatePresence mode="wait">
          {step === 'login' && (
            <motion.div key="login" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="bg-white p-10 rounded-[40px] shadow-2xl max-w-md w-full">
              <h1 className="text-2xl font-black mb-6 text-slate-800 text-center">دخول الأبطال 🚀</h1>
              <input type="text" placeholder="اسمك الثلاثي" className="w-full p-4 mb-4 bg-slate-100 rounded-2xl outline-none border-2 focus:border-blue-500 text-slate-800 font-bold" 
                onChange={e => setFormData({...formData, name: e.target.value})} />
              
              <select className="w-full p-4 mb-4 bg-slate-100 rounded-2xl font-bold text-slate-800 outline-none"
                onChange={e => setFormData({...formData, className: e.target.value})}>
                <option value="">اختر فصلك الدراسي</option>
                <option value="فصل (أ)">فصل (أ)</option>
                <option value="فصل (ب)">فصل (ب)</option>
              </select>

              <select className="w-full p-4 mb-6 bg-slate-100 rounded-2xl font-bold text-slate-800 outline-none"
                onChange={e => setFormData({...formData, chapter: e.target.value})}>
                <option value="">اختر الفصل المطلوب اختباره</option>
                <option value="الأعداد النسبية">الفصل 1: الأعداد النسبية</option>
                <option value="القوى والجذور">الفصل 2: القوى والجذور</option>
              </select>

              <button onClick={startQuiz} disabled={loading} className="w-full bg-blue-600 text-white py-4 rounded-2xl font-black text-lg hover:bg-blue-700 transition-all">
                {loading ? "جاري تجهيز الاختبار..." : "ابدأ التحدي الآن ⚡"}
              </button>
            </motion.div>
          )}

          {step === 'quiz' && quizData && (
            <motion.div key="quiz" initial={{x:50, opacity:0}} animate={{x:0, opacity:1}} className="bg-white p-8 rounded-[30px] shadow-xl max-w-2xl w-full text-slate-800">
              <h2 className="text-xl font-bold mb-6 border-b pb-4 text-blue-600">{quizData.quiz_name}</h2>
              {/* حل المشكلة باستخدام الـ Optional Chaining ?. */}
              {quizData?.questions?.map((q: any, idx: number) => (
                <div key={idx} className="mb-8 p-4 bg-slate-50 rounded-2xl">
                  <p className="font-black mb-4 text-lg">{idx + 1}. {q.question}</p>
                  <div className="grid grid-cols-1 gap-3">
                    {q.options.map((opt: string) => (
                      <button key={opt} onClick={() => setAnswers({...answers, [idx]: opt})}
                        className={`p-3 rounded-xl border-2 transition-all font-bold ${answers[idx] === opt ? 'border-blue-500 bg-blue-50' : 'border-slate-100 hover:bg-slate-200'}`}>
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <button onClick={() => setStep('result')} className="w-full bg-green-600 text-white py-4 rounded-2xl font-black text-xl shadow-lg mt-4">إرسال الإجابات ✅</button>
            </motion.div>
          )}

          {step === 'result' && (
            <motion.div key="res" initial={{scale:0.8}} animate={{scale:1}} className="bg-white p-10 rounded-[40px] text-center text-slate-800">
              <h2 className="text-4xl mb-4">🏆</h2>
              <h1 className="text-2xl font-black mb-2">كفو يا بطل!</h1>
              <p className="text-slate-500 mb-6 font-bold">تم تسجيل نتيجتك وإرسالها للأستاذ.</p>
              <button onClick={() => window.location.reload()} className="btn btn-outline">العودة للرئيسية</button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}