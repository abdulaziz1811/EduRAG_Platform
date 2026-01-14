'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, BookOpen, RefreshCw, BrainCircuit, Play, Trophy, AlertCircle } from 'lucide-react';
import { generateQuiz, submitQuizResult, explainConcept, Question } from '@/lib/api';

export default function QuizPage() {
  // --- State Variables ---
  const [step, setStep] = useState<'setup' | 'quiz' | 'result'>('setup');
  const [loading, setLoading] = useState(false);
  
  // بيانات الإعداد
  const [apiKey, setApiKey] = useState('');
  const [studentName, setStudentName] = useState('');
  const [selectedChapters, setSelectedChapters] = useState<number[]>([1]);

  // بيانات الاختبار
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  
  // بيانات النتائج والتحسين
  const [score, setScore] = useState(0);
  const [weakConcepts, setWeakConcepts] = useState<string[]>([]);
  const [explanations, setExplanations] = useState<Record<number, string>>({});

  // --- Functions ---

  const handleStartQuiz = async (isRemedial = false) => {
    if (!apiKey || !studentName) return alert('الرجاء إدخال الاسم ومفتاح API');
    if (selectedChapters.length === 0) return alert('اختر فصلاً واحداً على الأقل');

    setLoading(true);
    try {
      const newQuestions = await generateQuiz({
        api_key: apiKey,
        chapters: selectedChapters,
        num_questions: 5,
        focus_concepts: isRemedial ? weakConcepts : [], // هنا يكمن السحر: إرسال نقاط الضعف
      });

      setQuestions(newQuestions);
      setStep('quiz');
      setCurrentQIndex(0);
      setAnswers({});
      setExplanations({});
      if (!isRemedial) setWeakConcepts([]); // تصفير نقاط الضعف في الاختبار الجديد العادي
    } catch (e) {
      alert('فشل الاتصال بالسيرفر. تأكد من تشغيل Backend.');
    }
    setLoading(false);
  };

  const handleOptionClick = (option: string) => {
    setAnswers({ ...answers, [currentQIndex]: option });
  };

  const handleNext = async () => {
    if (currentQIndex < questions.length - 1) {
      setCurrentQIndex(prev => prev + 1);
    } else {
      await finishQuiz();
    }
  };

  const finishQuiz = async () => {
    setLoading(true);
    
    // حساب النتيجة وتحديد نقاط الضعف
    let correctCount = 0;
    const currentWeakConcepts: string[] = [];
    
    const submissionDetails = questions.map((q, idx) => {
      const isCorrect = answers[idx] === q.correct_answer;
      if (isCorrect) correctCount++;
      else if (q.concept) currentWeakConcepts.push(q.concept);

      return {
        question: q.text,
        user_answer: answers[idx] || "",
        correct_answer: q.correct_answer,
        is_correct: isCorrect,
        concept: q.concept
      };
    });

    setScore((correctCount / questions.length) * 100);
    setWeakConcepts([...new Set(currentWeakConcepts)]); // إزالة التكرار

    // إرسال البيانات للسيرفر للحفظ في قاعدة البيانات
    try {
      await submitQuizResult({
        student_name: studentName,
        chapter: selectedChapters[0] || 1, // نسجل الفصل الأول كمرجع
        details: submissionDetails
      });
    } catch (e) {
      console.error("فشل حفظ النتيجة في قاعدة البيانات");
    }

    setStep('result');
    setLoading(false);
  };

  const getExplanation = async (concept: string, qIndex: number) => {
    setExplanations(prev => ({ ...prev, [qIndex]: '...جاري البحث في الكتاب ⏳' }));
    try {
      const data = await explainConcept(concept, apiKey);
      setExplanations(prev => ({ 
        ...prev, 
        [qIndex]: `📖 (صفحة ${data.page}): ${data.text}` 
      }));
    } catch (e) {
      setExplanations(prev => ({ ...prev, [qIndex]: 'تعذر جلب الشرح.' }));
    }
  };

  // --- Renders ---

  // 1. شاشة الإعداد
  if (step === 'setup') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4" dir="rtl">
        <motion.div 
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} 
          className="bg-white p-8 rounded-3xl shadow-xl w-full max-w-lg border border-gray-100"
        >
          <h1 className="text-3xl font-black text-gray-800 mb-2 text-center">EduRAG 🎓</h1>
          <p className="text-gray-500 text-center mb-8">نظام اختبارات ذكي مع شرح من الكتاب</p>
          
          <div className="space-y-4">
            <input 
              type="text" placeholder="اسم الطالب" value={studentName}
              onChange={e => setStudentName(e.target.value)}
              className="w-full p-4 bg-gray-50 rounded-xl border focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all outline-none"
            />
            <input 
              type="password" placeholder="Groq API Key (gsk_...)" value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              className="w-full p-4 bg-gray-50 rounded-xl border focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all outline-none"
            />
            
            <div>
              <label className="text-sm font-bold text-gray-600 mb-2 block">اختر الفصول:</label>
              <div className="flex gap-2 flex-wrap">
                {[1, 2, 3, 4, 5].map(ch => (
                  <button
                    key={ch}
                    onClick={() => setSelectedChapters(prev => prev.includes(ch) ? prev.filter(c => c !== ch) : [...prev, ch])}
                    className={`w-10 h-10 rounded-full font-bold transition-all ${selectedChapters.includes(ch) ? 'bg-blue-600 text-white scale-110 shadow-lg' : 'bg-gray-100 text-gray-400'}`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            <button 
              onClick={() => handleStartQuiz(false)} disabled={loading}
              className="w-full bg-gray-900 text-white py-4 rounded-xl font-bold text-lg hover:bg-black transition-all flex items-center justify-center gap-2 shadow-lg"
            >
              {loading ? <RefreshCw className="animate-spin" /> : <><Play size={20} /> ابدأ الاختبار</>}
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // 2. شاشة الاختبار
  if (step === 'quiz') {
    const q = questions[currentQIndex];
    const progress = ((currentQIndex + 1) / questions.length) * 100;

    return (
      <div className="min-h-screen bg-white flex flex-col p-6" dir="rtl">
        {/* Progress Bar */}
        <div className="w-full max-w-2xl mx-auto h-2 bg-gray-100 rounded-full mb-12 overflow-hidden">
          <motion.div 
            initial={{ width: 0 }} animate={{ width: `${progress}%` }} 
            className="h-full bg-blue-600 rounded-full"
          />
        </div>

        <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center">
          <span className="text-blue-600 font-bold text-sm tracking-widest mb-4 block">
            سؤال {currentQIndex + 1} من {questions.length}
          </span>
          
          <motion.h2 
            key={currentQIndex}
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
            className="text-3xl font-bold text-gray-900 mb-8 leading-relaxed"
          >
            {q.text}
          </motion.h2>

          <div className="grid gap-3 mb-8">
            {q.options.map((opt, i) => (
              <motion.button
                key={`${currentQIndex}-${i}`}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                onClick={() => handleOptionClick(opt)}
                className={`p-5 text-right rounded-2xl border-2 transition-all text-lg font-medium
                  ${answers[currentQIndex] === opt 
                    ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-md' 
                    : 'border-gray-100 hover:border-blue-200 text-gray-600 hover:bg-gray-50'}`}
              >
                {opt}
              </motion.button>
            ))}
          </div>

          <button 
            onClick={handleNext}
            disabled={!answers[currentQIndex]}
            className="self-end bg-gray-900 text-white px-8 py-3 rounded-xl font-bold disabled:opacity-50 hover:scale-105 transition-transform"
          >
            {currentQIndex === questions.length - 1 ? 'إنهاء وتسليم 🏁' : 'التالي ⬅️'}
          </button>
        </div>
      </div>
    );
  }

  // 3. شاشة النتائج
  if (step === 'result') {
    return (
      <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
        <div className="max-w-3xl mx-auto space-y-8">
          {/* بطاقة النتيجة */}
          <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="bg-white p-8 rounded-3xl shadow-lg text-center border border-gray-100">
            <div className="inline-block p-4 rounded-full bg-yellow-100 mb-4">
              <Trophy className="text-yellow-600 w-12 h-12" />
            </div>
            <h2 className="text-2xl font-bold text-gray-800">نتيجتك النهائية</h2>
            <div className={`text-6xl font-black my-4 ${score >= 50 ? 'text-green-500' : 'text-red-500'}`}>
              {Math.round(score)}%
            </div>
            
            {/* قسم التحسين الذكي */}
            {weakConcepts.length > 0 && (
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="bg-orange-50 border border-orange-200 p-6 rounded-2xl mt-6 text-right"
              >
                <h3 className="text-orange-800 font-bold mb-3 flex items-center gap-2">
                  <AlertCircle size={20}/> نقاط تحتاج لتركيز:
                </h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  {weakConcepts.map((c, i) => (
                    <span key={i} className="bg-white text-orange-600 px-3 py-1 rounded-lg text-sm font-bold shadow-sm border border-orange-100">{c}</span>
                  ))}
                </div>
                <button 
                  onClick={() => handleStartQuiz(true)}
                  className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 rounded-xl font-bold transition-colors flex items-center justify-center gap-2"
                >
                  <BrainCircuit size={18}/> إنشاء اختبار تحسين (يركز عليها) 🚀
                </button>
              </motion.div>
            )}
          </motion.div>

          {/* مراجعة الإجابات */}
          <div className="space-y-4">
            <h3 className="font-bold text-gray-500 mr-2">مراجعة التفاصيل:</h3>
            {questions.map((q, idx) => {
              const isCorrect = answers[idx] === q.correct_answer;
              return (
                <div key={idx} className={`bg-white p-6 rounded-2xl border-2 ${isCorrect ? 'border-green-100' : 'border-red-100'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-bold text-gray-800 text-lg">{q.text}</h4>
                    {isCorrect ? <CheckCircle className="text-green-500 shrink-0"/> : <XCircle className="text-red-500 shrink-0"/>}
                  </div>
                  <p className={`text-sm font-bold mb-4 ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                    إجابتك: {answers[idx]}
                  </p>

                  {!isCorrect && (
                    <div className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-green-700 font-bold text-sm">✅ الصحيح: {q.correct_answer}</span>
                        <button 
                          onClick={() => getExplanation(q.concept, idx)}
                          className="text-blue-600 text-sm font-bold underline flex items-center gap-1 hover:text-blue-800"
                        >
                          <BookOpen size={14}/> لماذا؟ (من الكتاب)
                        </button>
                      </div>
                      <AnimatePresence>
                        {explanations[idx] && (
                          <motion.div 
                            initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                            className="text-gray-600 text-sm leading-relaxed border-t pt-2 mt-2"
                          >
                            {explanations[idx]}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <button onClick={() => setStep('setup')} className="text-gray-400 font-bold hover:text-gray-600 block mx-auto">
            خروج للرئيسية
          </button>
        </div>
      </div>
    );
  }

  return null;
}