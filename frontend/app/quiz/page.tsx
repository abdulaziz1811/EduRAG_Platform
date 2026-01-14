"use client";
import { useState } from 'react';

// تعريف شكل البيانات لترتيب الكود
interface Question {
  id: number;
  text: string;
  options: string[];
  correct_answer: string;
  concept: string;
}

interface Result {
  score: number;
  weak_concepts: string[];
  status: string;
}

export default function QuizPage() {
  // --- المتغيرات (State) ---
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [apiKey, setApiKey] = useState(""); 
  const [studentName, setStudentName] = useState("");
  
  // لحفظ إجابات الطالب { رقم_السؤال: الإجابة }
  const [answers, setAnswers] = useState<{[key: number]: string}>({});
  
  // لحفظ النتيجة النهائية
  const [result, setResult] = useState<Result | null>(null);

  // --- 1. دالة جلب الأسئلة ---
  const generateQuiz = async () => {
    if (!apiKey || !studentName) {
      alert("الرجاء إدخال اسمك ومفتاح API");
      return;
    }

    setLoading(true);
    setResult(null); // تصفير النتيجة القديمة
    setAnswers({});  // تصفير الإجابات القديمة
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/generate-quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          chapters: [1], 
          num_questions: 3
        }),
      });

      const data = await res.json();
      if (data.questions) setQuestions(data.questions);
      else alert("حدث خطأ في جلب البيانات");

    } catch (error) {
      console.error(error);
      alert("فشل الاتصال بالسيرفر");
    } finally {
      setLoading(false);
    }
  };

  // --- 2. دالة إرسال الإجابات للتصحيح ---
  const submitQuiz = async () => {
    if (Object.keys(answers).length < questions.length) {
      alert("الرجاء الإجابة على جميع الأسئلة قبل التسليم!");
      return;
    }

    setLoading(true);
    
    // تجهيز البيانات لتناسب شكل الباك إند (SubmissionRequest)
    const submissionDetails = questions.map((q, index) => ({
      question: q.text,
      user_answer: answers[index] || "",
      correct_answer: q.correct_answer,
      is_correct: answers[index] === q.correct_answer,
      concept: q.concept
    }));

    try {
      const res = await fetch('http://127.0.0.1:8000/api/submit-quiz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_name: studentName,
          chapter: 1,
          details: submissionDetails
        }),
      });

      const data = await res.json();
      setResult(data); // حفظ النتيجة لعرضها
      
    } catch (error) {
      alert("حدث خطأ أثناء التصحيح");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-extrabold text-blue-900 mb-8 text-center">
          منصة راقٍ - الاختبار الذكي 🚀
        </h1>

        {/* --- قسم الإعدادات (يختفي عند ظهور الأسئلة) --- */}
        {questions.length === 0 && (
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 mb-8">
            <div className="grid gap-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">اسم الطالب:</label>
                <input 
                  type="text" 
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  className="w-full p-4 border rounded-xl bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="سجل اسمك هنا..."
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">مفتاح Groq API:</label>
                <input 
                  type="text" 
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full p-4 border rounded-xl bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none text-left"
                  placeholder="gsk_..."
                />
              </div>
              <button 
                onClick={generateQuiz}
                disabled={loading}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all shadow-md mt-4"
              >
                {loading ? "جاري التجهيز..." : "ابدأ الاختبار الآن ✨"}
              </button>
            </div>
          </div>
        )}

        {/* --- عرض النتيجة (تظهر بعد التصحيح) --- */}
        {result && (
          <div className="bg-green-50 border border-green-200 p-8 rounded-2xl shadow-lg mb-8 text-center animate-pulse-once">
            <h2 className="text-3xl font-bold text-green-800 mb-2">🎉 تم التصحيح بنجاح!</h2>
            <p className="text-5xl font-black text-green-600 my-4">{result.score}%</p>
            
            {result.weak_concepts.length > 0 ? (
              <div className="bg-white p-4 rounded-xl mt-4">
                <p className="text-red-500 font-bold mb-2">⚠️ مفاهيم تحتاج مراجعة:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {result.weak_concepts.map((c, i) => (
                    <span key={i} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-blue-600 font-bold mt-4">أداء ممتاز! لا توجد نقاط ضعف. 🌟</p>
            )}
            
            <button 
              onClick={() => { setQuestions([]); setResult(null); }}
              className="mt-6 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              اختبار جديد
            </button>
          </div>
        )}

        {/* --- قائمة الأسئلة --- */}
        {!result && questions.length > 0 && (
          <div className="space-y-6">
            {questions.map((q, index) => (
              <div key={index} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-bold text-gray-800">سؤال {index + 1}</h3>
                  <span className="text-xs bg-blue-50 text-blue-600 px-3 py-1 rounded-full font-bold">
                    {q.concept}
                  </span>
                </div>
                
                <p className="text-lg text-gray-700 mb-6 font-medium leading-relaxed">
                  {q.text}
                </p>

                <div className="grid grid-cols-1 gap-3">
                  {q.options?.map((opt, i) => (
                    <button 
                      key={i} 
                      onClick={() => setAnswers({...answers, [index]: opt})}
                      className={`p-4 text-right border-2 rounded-xl transition-all font-medium
                        ${answers[index] === opt 
                          ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-md' 
                          : 'border-gray-100 hover:border-blue-200 text-gray-600'
                        }
                      `}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}

            <button 
              onClick={submitQuiz}
              disabled={loading}
              className="w-full py-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-black transition-all shadow-lg text-lg"
            >
              {loading ? "جاري التصحيح..." : "تسليم الإجابات ✅"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}