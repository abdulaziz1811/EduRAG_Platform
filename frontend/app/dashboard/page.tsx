"use client";
import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, AreaChart, Area } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../../components/Navbar";

export default function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedClass, setSelectedClass] = useState("فصل (أ)"); // الميزة الجديدة
  const [stats, setStats] = useState({ avg_score: 0, students_at_risk: 0, total_students: 0, total_quizzes: 0 });
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [studentPerf, setStudentPerf] = useState([]);
  const [chaptersAvg, setChaptersAvg] = useState([]);
  const [classCompare, setClassCompare] = useState([]);
  const [chapterDetails, setChapterDetails] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState("1");
  const [summary, setSummary] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // جلب البيانات بناءً على الفصل المختار
  useEffect(() => {
    const query = `?class_name=${encodeURIComponent(selectedClass)}`;
    fetch(`http://127.0.0.1:8000/teacher/stats${query}`).then(res => res.json()).then(setStats);
    fetch(`http://127.0.0.1:8000/teacher/students${query}`).then(res => res.json()).then(setStudents);
    fetch(`http://127.0.0.1:8000/teacher/analytics/chapters-avg${query}`).then(res => res.json()).then(setChaptersAvg);
    fetch(`http://127.0.0.1:8000/teacher/analytics/classes-compare`).then(res => res.json()).then(setClassCompare);
    loadChapterDetails(selectedChapter, selectedClass);
  }, [selectedClass]);

  const loadChapterDetails = (num: string, className: string) => {
    setSelectedChapter(num);
    fetch(`http://127.0.0.1:8000/teacher/analytics/chapter-details/${num}?class_name=${encodeURIComponent(className)}`)
      .then(res => res.json()).then(setChapterDetails);
  };

  const handleStudentSelect = (id: string) => {
    setSelectedStudent(id);
    if(id) fetch(`http://127.0.0.1:8000/teacher/student/${id}/performance`).then(res => res.json()).then(setStudentPerf);
  };

  const generateRAGReport = () => {
    setIsGenerating(true);
    fetch("http://127.0.0.1:8000/teacher/generate-summary", {
        method:'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ class_name: selectedClass })
    })
    .then(res=>res.json())
    .then(d=>{
        setSummary(d.summary);
        setIsGenerating(false);
    });
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans" dir="rtl">
      <Navbar />
      
      <div className="p-8 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
                <h1 className="text-3xl font-black border-r-4 border-blue-600 pr-4">لوحة تحكم المعلم</h1>
                <p className="text-slate-500 mt-2 pr-4 font-medium">متابعة أداء الطلاب وتحليل الـ RAG</p>
            </div>
            
            {/* الميزة الجديدة: محول الفصول */}
            <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200">
                {["فصل (أ)", "فصل (ب)"].map((cls) => (
                    <button 
                        key={cls}
                        onClick={() => setSelectedClass(cls)}
                        className={`px-6 py-2 rounded-xl font-bold transition-all ${selectedClass === cls ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                    >
                        {cls}
                    </button>
                ))}
            </div>
        </header>

        {/* التبويبات الرئيسية */}
        <div className="flex gap-4 mb-10 bg-slate-100 p-1.5 rounded-2xl w-fit">
          {["overview", "analysis", "factory"].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} 
              className={`px-10 py-2.5 rounded-xl font-bold transition-all ${activeTab === tab ? "bg-white text-blue-600 shadow-md" : "text-slate-500"}`}>
              {tab === "overview" ? "نظرة عامة" : tab === "analysis" ? "التحليل البياني" : "مصنع الاختبارات"}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "overview" && (
            <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} exit={{opacity:0}} className="space-y-10">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard label={`متوسط ${selectedClass}`} value={`${stats.avg_score}%`} color="text-blue-600" />
                <StatCard label="طلاب في حالة حرجة" value={stats.students_at_risk} color="text-red-600" />
                <StatCard label="طلاب الفصل" value={stats.total_students} color="text-slate-800" />
                <StatCard label="فصول المنهج" value={stats.total_quizzes} color="text-purple-600" />
              </div>
              
              <div className="bg-slate-900 text-white p-10 rounded-[40px] shadow-2xl relative overflow-hidden">
                <div className="relative z-10">
                    <h2 className="text-2xl font-bold mb-4 text-blue-400">تحليل RAG الذكي - {selectedClass}</h2>
                    <p className="text-slate-400 mb-8 max-w-2xl text-lg">يقوم النظام بتحليل درجات طلاب {selectedClass} وربطها بمحتوى الكتاب لتقديم خطة علاجية مختصرة.</p>
                    <button 
                        onClick={generateRAGReport}
                        disabled={isGenerating}
                        className={`bg-blue-600 px-12 py-4 rounded-2xl font-bold hover:bg-blue-500 transition-all shadow-lg ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}>
                        {isGenerating ? "جاري التحليل..." : "توليد ملخص المستجدات (RAG)"}
                    </button>
                    
                    {summary && (
                        <motion.div initial={{opacity:0, scale:0.95}} animate={{opacity:1, scale:1}} className="mt-8 p-8 bg-slate-800 rounded-3xl text-xl leading-relaxed border-r-8 border-blue-500 shadow-inner">
                            {summary}
                        </motion.div>
                    )}
                </div>
                <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
              </div>
            </motion.div>
          )}

          {activeTab === "analysis" && (
            <motion.div initial={{opacity:0}} animate={{opacity:1}} className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              
              <div className="bg-slate-50 p-8 rounded-[32px] border border-slate-200">
                <h3 className="text-lg font-black mb-6 text-slate-700">اتقان المهارات في {selectedClass}</h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chaptersAvg}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Area type="monotone" dataKey="score" stroke="#2563eb" fill="#dbeafe" strokeWidth={4} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-slate-50 p-8 rounded-[32px] border border-slate-200">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-black text-slate-700">درجات الطلاب:</h3>
                  <select value={selectedChapter} onChange={(e) => loadChapterDetails(e.target.value, selectedClass)} className="p-2 bg-white rounded-lg border font-bold outline-none">
                    {[1,2,3,4,5].map(n => <option key={n} value={n}>الفصل {n}</option>)}
                  </select>
                </div>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chapterDetails}>
                      <XAxis dataKey="name" hide />
                      <YAxis domain={[0, 100]} />
                      <Tooltip cursor={{fill: '#f1f5f9'}} />
                      <Bar dataKey="score" fill="#0f172a" radius={[6,6,0,0]} barSize={25} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-8 rounded-[32px] border-2 border-blue-100 shadow-sm">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-black text-blue-900">أداء طالب من {selectedClass}</h3>
                  <select value={selectedStudent} onChange={(e) => handleStudentSelect(e.target.value)} className="p-2 bg-blue-50 rounded-lg outline-none font-bold text-blue-700 border border-blue-200 max-w-[200px]">
                    <option value="">اختر طالباً</option>
                    {students.map((s:any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div className="h-[300px]">
                  {selectedStudent ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={studentPerf}>
                        <XAxis dataKey="subject" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Bar dataKey="score" radius={[10, 10, 0, 0]} barSize={40}>
                          {studentPerf.map((entry:any, index) => (
                            <Cell key={index} fill={entry.score < 50 ? "#ef4444" : "#3b82f6"} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : <div className="h-full flex items-center justify-center text-slate-400 italic font-medium">الرجاء اختيار طالب من القائمة أعلاه</div>}
                </div>
              </div>

              <div className="bg-slate-50 p-8 rounded-[32px] border border-slate-200">
                <h3 className="text-lg font-black mb-6 text-slate-700">مقارنة القوة بين الفصول</h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={classCompare}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="score" fill="#6366f1" radius={[15, 15, 0, 0]} barSize={60}>
                         {classCompare.map((entry: any, index: number) => (
                            <Cell key={index} fill={entry.name === selectedClass ? "#2563eb" : "#cbd5e1"} />
                         ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "factory" && (
            <motion.div initial={{opacity:0, scale:0.98}} animate={{opacity:1, scale:1}} className="bg-slate-50 p-12 rounded-[40px] border border-slate-200 text-center">
                <h2 className="text-2xl font-black mb-4">صناعة اختبار لطلاب {selectedClass}</h2>
                <p className="text-slate-500 mb-10 font-medium text-lg">حدد الفصول وسيقوم نظام الـ RAG بتوليد أسئلة من الكتاب المدرسي.</p>
                <div className="max-w-2xl mx-auto space-y-8">
                    <div className="flex items-center gap-4 justify-center">
                        <span className="font-bold text-slate-700">عدد الأسئلة:</span>
                        <input type="number" defaultValue={10} className="w-24 p-3 rounded-xl border-2 border-slate-200 outline-none focus:border-blue-500 font-bold text-center" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {["الكسور الاعتيادية", "الضرب والقسمة", "الأشكال الهندسية", "القياس والوحدات", "الجبر والعمليات"].map((chap, i) => (
                        <div key={i} className="p-6 bg-white rounded-2xl border-2 border-slate-100 flex items-center gap-4 hover:border-blue-400 cursor-pointer transition-all group shadow-sm">
                            <div className="w-10 h-10 bg-slate-200 group-hover:bg-blue-600 group-hover:text-white text-slate-600 rounded-full flex items-center justify-center font-bold transition-colors">{i+1}</div>
                            <span className="font-bold text-slate-800">{chap}</span>
                        </div>
                      ))}
                    </div>
                    <button className="bg-slate-900 text-white px-16 py-5 rounded-3xl font-black text-xl hover:bg-black transition-all shadow-xl transform hover:scale-105 active:scale-95">بدء التوليد الذكي</button>
                </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: any) {
  return (
    <div className="bg-white p-8 rounded-[32px] border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
      <p className="text-slate-500 text-sm font-bold mb-2">{label}</p>
      <p className={`text-4xl font-black ${color}`}>{value}</p>
    </div>
  );
}