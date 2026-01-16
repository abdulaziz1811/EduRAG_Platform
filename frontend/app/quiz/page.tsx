'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, BookOpen, RefreshCw, Trophy, ArrowLeft, BrainCircuit, Play } from 'lucide-react';
import Navbar from '../../components/Navbar';
import axios from 'axios';

interface Question {
  question: string;
  options: string[];
  answer: string;
}

export default function QuizPage() {
  const [topic, setTopic] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResult, setShowResult] = useState(false);
  
  // حالات التفاعل مع الإجابة
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [answerSubmitted, setAnswerSubmitted] = useState(false);

  const startQuiz = async () => {
    if (!topic) return;
    setLoading(true);
    setQuestions([]);
    setScore(0);
    setCurrentQuestion(0);
    setShowResult(false);
    setAnswerSubmitted(false);
    setSelectedAnswer(null);

    try {
      const res = await axios.post('http://localhost:8000/api/quiz', { topic });
      let data = res.data;
      if (typeof data === 'string') {
        try {
          // تم تعديل هذا السطر ليعمل مع إعدادات ES القديمة
          // بدلاً من استخدام flag /s نستخدم [\s\S] لمطابقة الأسطر الجديدة
          const jsonMatch = data.match(/\[[\s\S]*\]/);
          data = jsonMatch ? JSON.parse(jsonMatch[0]) : JSON.parse(data);
        } catch (e) {
          console.error("Error parsing JSON", e);
          data = [];
        }
      }
      setQuestions(data);
    } catch (error) {
      console.error(error);
      alert('حدث خطأ أثناء توليد الاختبار، حاول موضوعاً آخر');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (option: string) => {
    if (answerSubmitted) return;

    const correct = questions[currentQuestion].answer;
    const isAnswerCorrect = option === correct;
    
    setSelectedAnswer(option);
    setIsCorrect(isAnswerCorrect);
    setAnswerSubmitted(true);

    if (isAnswerCorrect) {
      setScore(score + 1);
    }
  };

  const nextQuestion = () => {
    if (currentQuestion + 1 < questions.length) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer(null);
      setAnswerSubmitted(false);
      setIsCorrect(null);
    } else {
      setShowResult(true);
    }
  };

  const restartQuiz = () => {
    setQuestions([]);
    setTopic('');
    setShowResult(false);
    setScore(0);
    setCurrentQuestion(0);
    setAnswerSubmitted(false);
  };

  const progress = questions.length > 0 ? ((currentQuestion + 1) / questions.length) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-50 text-right font-sans" dir="rtl">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 py-12">
        {/* شاشة البداية */}
        {questions.length === 0 && !loading && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl shadow-xl p-10 text-center border border-gray-100"
          >
            <div className="w-20 h-20 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <BrainCircuit size={40} />
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-4">اختبر معلوماتك</h1>
            <p className="text-gray-500 mb-8 text-lg">أدخل أي موضوع وسيقوم الذكاء الاصطناعي بإنشاء اختبار مخصص لك فوراً.</p>
            
            <div className="flex gap-4">
              <button
                onClick={startQuiz}
                disabled={!topic}
                className="bg-blue-600 text-white px-8 py-4 rounded-xl hover:bg-blue-700 transition-all font-bold text-lg shadow-lg disabled:opacity-50 flex items-center gap-2"
              >
                <Play size={20} fill="currentColor" />
                 بدء الاختبار
              </button>
              <input
                type="text"
                placeholder="عن ماذا تريد أن تتعلم اليوم؟"
                className="flex-1 p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-50 transition-all outline-none text-lg"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && startQuiz()}
              />
            </div>
          </motion.div>
        )}

        {/* شاشة التحميل */}
        {loading && (
          <div className="text-center py-20">
            <div className="animate-spin w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-6"></div>
            <h3 className="text-2xl font-bold text-gray-700">جاري إعداد الأسئلة الذكية...</h3>
            <p className="text-gray-500 mt-2">نبحث في المراجع لضمان دقة المعلومات</p>
          </div>
        )}

        {/* الأسئلة */}
        {questions.length > 0 && !showResult && (
          <div className="w-full">
            <div className="mb-8">
              <div className="flex justify-between text-sm text-gray-500 mb-2 font-medium">
                <span>السؤال {currentQuestion + 1} من {questions.length}</span>
                <span>التقدم {Math.round(progress)}%</span>
              </div>
              <div className="h-3 w-full bg-gray-200 rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-blue-600 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            <AnimatePresence mode='wait'>
              <motion.div
                key={currentQuestion}
                initial={{ x: 50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -50, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100"
              >
                <h2 className="text-2xl font-bold text-gray-800 mb-8 leading-relaxed">
                  {questions[currentQuestion].question}
                </h2>

                <div className="space-y-4">
                  {questions[currentQuestion].options.map((option, idx) => {
                    let buttonStyle = "border-gray-200 hover:border-blue-300 hover:bg-blue-50";
                    if (answerSubmitted) {
                      if (option === questions[currentQuestion].answer) {
                        buttonStyle = "border-green-500 bg-green-50 text-green-700";
                      } else if (option === selectedAnswer) {
                        buttonStyle = "border-red-500 bg-red-50 text-red-700";
                      } else {
                        buttonStyle = "border-gray-100 opacity-50";
                      }
                    }

                    return (
                      <button
                        key={idx}
                        onClick={() => handleAnswer(option)}
                        disabled={answerSubmitted}
                        className={`w-full p-5 text-right rounded-2xl border-2 transition-all duration-200 flex items-center justify-between group ${buttonStyle}`}
                      >
                        <span className="text-lg font-medium">{option}</span>
                        {answerSubmitted && option === questions[currentQuestion].answer && (
                          <CheckCircle className="text-green-600" />
                        )}
                        {answerSubmitted && option === selectedAnswer && option !== questions[currentQuestion].answer && (
                          <XCircle className="text-red-600" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            </AnimatePresence>

            <div className="mt-8 flex justify-end h-16">
              {answerSubmitted && (
                <motion.button
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={nextQuestion}
                  className="bg-gray-900 text-white px-8 py-3 rounded-xl hover:bg-black transition-colors font-bold text-lg flex items-center gap-2 shadow-lg"
                >
                  {currentQuestion + 1 === questions.length ? "إنهاء الاختبار" : "السؤال التالي"}
                  <ArrowLeft size={20} />
                </motion.button>
              )}
            </div>
          </div>
        )}

        {/* النتائج */}
        {showResult && (
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-3xl shadow-xl p-12 text-center max-w-2xl mx-auto border border-gray-100"
          >
            <div className="w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Trophy size={48} className="text-yellow-600" />
            </div>
            
            <h2 className="text-3xl font-bold text-gray-900 mb-2">اكتمل الاختبار!</h2>
            <p className="text-gray-500 mb-8">إليك ملخص أدائك في {topic}</p>

            <div className="bg-gray-50 rounded-2xl p-8 mb-8">
              <div className="text-5xl font-black text-blue-600 mb-2">{score} / {questions.length}</div>
              <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">النتيجة النهائية</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={restartQuiz}
                className="w-full bg-white border-2 border-gray-200 text-gray-700 p-4 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-all font-bold flex items-center justify-center gap-2"
              >
                <RefreshCw size={20} />
                موضوع آخر
              </button>
              <button
                onClick={() => {
                    setScore(0);
                    setCurrentQuestion(0);
                    setShowResult(false);
                    setAnswerSubmitted(false);
                }}
                className="w-full bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-all font-bold flex items-center justify-center gap-2 shadow-lg shadow-blue-200"
              >
                <BookOpen size={20} />
                إعادة الاختبار
              </button>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}