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

       {/* --- عرض النتيجة والشرح --- */}
        {result && (
          <div className="space-y-8 animate-fade-in">
            {/* بطاقة الدرجة */}
            <div className={`p-8 rounded-2xl shadow-lg text-center border-2 
              ${result.score >= 60 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <h2 className="text-3xl font-bold mb-2">
                {result.score >= 60 ? '🎉 أحسنت!' : 'حظ أوفر المرة القادمة!'}
              </h2>
              <p className={`text-6xl font-black my-4 ${result.score >= 60 ? 'text-green-600' : 'text-red-600'}`}>
                {result.score.toFixed(1)}%
              </p>
            </div>

            {/* مراجعة الإجابات (الميزة الجديدة) */}
            <h3 className="text-2xl font-bold text-gray-800 border-b pb-2">🔍 مراجعة الأخطاء والشرح</h3>
            
            <div className="space-y-4">
              {questions.map((q, idx) => {
                const isCorrect = answers[idx] === q.correct_answer;
                const userAnswer = answers[idx];
                
                return (
                  <div key={idx} className={`p-6 rounded-xl border-2 ${isCorrect ? 'border-green-100 bg-green-50' : 'border-red-100 bg-white'}`}>
                    <p className="font-bold text-lg mb-2">س{idx+1}: {q.text}</p>
                    
                    <div className="flex gap-4 text-sm mb-4">
                      <span className={isCorrect ? "text-green-700 font-bold" : "text-red-600 font-bold"}>
                        إجابتك: {userAnswer} {isCorrect ? '✅' : '❌'}
                      </span>
                      {!isCorrect && (
                        <span className="text-green-700 font-bold">
                          الصحيح: {q.correct_answer}
                        </span>
                      )}
                    </div>

                    {/* زر الشرح (يظهر فقط عند الخطأ) */}
                    {!isCorrect && (
                      <ExplanationButton concept={q.concept} />
                    )}
                  </div>
                );
              })}
            </div>

            <button 
              onClick={() => { setQuestions([]); setResult(null); }}
              className="w-full py-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-black"
            >
              اختبار جديد 🔄
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
// مكون فرعي لزر الشرح
function ExplanationButton({ concept }: { concept: string }) {
  const [explanation, setExplanation] = useState<{text: string, page: number} | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchExplanation = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concept }),
      });
      const data = await res.json();
      setExplanation(data);
    } catch (e) {
      alert("تعذر جلب الشرح");
    } finally {
      setLoading(false);
    }
  };

  if (explanation) {
    return (
      <div className="mt-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-gray-700">
        <p className="font-bold text-yellow-800 mb-1">📖 من الكتاب المدرسي (صفحة {explanation.page}):</p>
        <p>{explanation.text}</p>
      </div>
    );
  }

  return (
    <button 
      onClick={fetchExplanation}
      disabled={loading}
      className="mt-2 text-blue-600 text-sm font-bold underline hover:text-blue-800 flex items-center gap-1"
    >
      {loading ? "جاري البحث في الكتاب..." : "لماذا إجابتي خاطئة؟ (شاهد الشرح)"}
    </button>
  );
}