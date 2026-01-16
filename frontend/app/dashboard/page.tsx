"use client";
import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, AreaChart, Area } from "recharts";
import { motion } from "framer-motion";

export default function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState({ avg_score: 0, students_at_risk: 0, total_students: 0, total_quizzes: 0 });
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [studentPerf, setStudentPerf] = useState([]);
  const [chaptersAvg, setChaptersAvg] = useState([]);
  const [classCompare, setClassCompare] = useState([]);
  const [chapterDetails, setChapterDetails] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState("1");
  const [summary, setSummary] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/teacher/stats").then(res => res.json()).then(setStats);
    fetch("http://127.0.0.1:8000/teacher/students").then(res => res.json()).then(setStudents);
    fetch("http://127.0.0.1:8000/teacher/analytics/chapters-avg").then(res => res.json()).then(setChaptersAvg);
    fetch("http://127.0.0.1:8000/teacher/analytics/classes-compare").then(res => res.json()).then(setClassCompare);
    loadChapterDetails("1");
  }, []);

  const loadChapterDetails = (num: string) => {
    setSelectedChapter(num);
    fetch(`http://127.0.0.1:8000/teacher/analytics/chapter-details/${num}`).then(res => res.json()).then(setChapterDetails);
  };

  const handleStudentSelect = (id: string) => {
    setSelectedStudent(id);
    if(id) fetch(`http://127.0.0.1:8000/teacher/student/${id}/performance`).then(res => res.json()).then(setStudentPerf);
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 p-8 font-sans" dir="rtl">
      <h1 className="text-3xl font-black mb-8 border-r-4 border-blue-600 pr-4">لوحة تحكم معلم الرياضيات</h1>

      {/* التبويبات - ثابتة كما هي */}
      <div className="flex gap-4 mb-10 bg-slate-100 p-1.5 rounded-2xl w-fit">
        {["overview", "analysis", "factory"].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} 
            className={`px-10 py-2.5 rounded-xl font-bold transition-all ${activeTab === tab ? "bg-white text-blue-600 shadow-md" : "text-slate-500"}`}>
            {tab === "overview" ? "نظرة عامة" : tab === "analysis" ? "التحليل البياني" : "مصنع الاختبارات"}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="space-y-10">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatCard label="متوسط درجات المادة" value={`${stats.avg_score}%`} color="text-blue-600" />
            <StatCard label="طلاب في حالة حرجة" value={stats.students_at_risk} color="text-red-600" />
            <StatCard label="إجمالي الطلاب" value={stats.total_students} color="text-slate-800" />
            <StatCard label="عدد فصول المنهج" value={stats.total_quizzes} color="text-purple-600" />
          </div>
          <div className="bg-slate-900 text-white p-10 rounded-[32px]">
            <h2 className="text-2xl font-bold mb-4 text-blue-400">تحليل RAG للطلاب المتعثرين</h2>
            <p className="text-slate-400 mb-8 max-w-2xl">يستخدم النظام الذكاء الاصطناعي لربط نتائج الفصول وتحديد أسماء الطلاب الذين يحتاجون خطة علاجية فورية.</p>
            <button onClick={() => fetch("http://127.0.0.1:8000/teacher/generate-summary", {method:'POST'}).then(res=>res.json()).then(d=>setSummary(d.summary))}
              className="bg-blue-600 px-12 py-4 rounded-2xl font-bold hover:bg-blue-500 transition-all shadow-lg shadow-blue-900/20">توليد التقرير الأكاديمي</button>
            {summary && <div className="mt-8 p-8 bg-slate-800 rounded-3xl text-xl leading-relaxed border-r-8 border-red-500">{summary}</div>}
          </div>
        </div>
      )}

      {activeTab === "analysis" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          
          {/* 1. متوسط أداء المادة عبر الفصول (المنهج كامل) */}
          <div className="bg-slate-50 p-8 rounded-[32px] border border-slate-200">
            <h3 className="text-lg font-black mb-6 text-slate-700">متوسط الإتقان لكل فصل (جميع الطلاب)</h3>
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

          {/* 2. توزيع درجات الطلاب في فصل محدد */}
          <div className="bg-slate-50 p-8 rounded-[32px] border border-slate-200">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-black text-slate-700">توزيع درجات الطلاب في:</h3>
              <select onChange={(e) => loadChapterDetails(e.target.value)} className="p-2 bg-white rounded-lg border font-bold">
                {[1,2,3,4,5].map(n => <option key={n} value={n}>الفصل {n}</option>)}
              </select>
            </div>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chapterDetails}>
                  <XAxis dataKey="name" hide />
                  <YAxis domain={[0, 100]} />
                  <Tooltip labelStyle={{color:'black'}} />
                  <Bar dataKey="score" fill="#0f172a" radius={[5,5,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 3. تتبع أداء طالب محدد (بجميع الفصول) */}
          <div className="bg-white p-8 rounded-[32px] border-2 border-blue-100 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-black text-blue-900">مستوى طالب محدد عبر الفصول</h3>
              <select onChange={(e) => handleStudentSelect(e.target.value)} className="p-2 bg-blue-50 rounded-lg outline-none font-bold text-blue-700 border border-blue-200">
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
              ) : <div className="h-full flex items-center justify-center text-slate-400 italic">اختر طالباً لمشاهدة تفاصيل أدائه</div>}
            </div>
          </div>

          {/* 4. مقارنة الفصول الدراسية */}
          <div className="bg-slate-50 p-8 rounded-[32px] border border-slate-200">
            <h3 className="text-lg font-black mb-6 text-slate-700">مقارنة متوسط أداء الفصول (أ ضد ب)</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={classCompare}>
                  <XAxis dataKey="name" label={{value: 'الفصل الدراسي', position: 'insideBottom', offset: -5}} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="score" fill="#6366f1" radius={[15, 15, 0, 0]} barSize={80} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      )}

      {activeTab === "factory" && (
        /* مصنع الاختبارات المعتمد لديك */
        <div className="bg-slate-50 p-12 rounded-[40px] border border-slate-200 text-center">
            <h2 className="text-2xl font-black mb-4">صناعة اختبار رياضيات مخصص</h2>
            <p className="text-slate-500 mb-10 font-medium text-lg text-center">حدد الفصول وعدد الأسئلة وسيقوم نظام الـ RAG بتوليد اختبار مخصص للطلاب.</p>
            <div className="max-w-2xl mx-auto space-y-8">
                <div className="flex items-center gap-4 justify-center">
                    <span className="font-bold">عدد الأسئلة:</span>
                    <input type="number" defaultValue={10} className="w-24 p-3 rounded-xl border-2 border-slate-200 outline-none focus:border-blue-500 font-bold" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {["الكسور الاعتيادية", "الضرب والقسمة", "الأشكال الهندسية", "القياس والوحدات", "الجبر والعمليات"].map((chap, i) => (
                    <div key={i} className="p-6 bg-white rounded-2xl border-2 border-slate-100 flex items-center gap-4 hover:border-blue-400 cursor-pointer transition-all">
                        <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">{i+1}</div>
                        <span className="font-bold text-slate-800">{chap}</span>
                    </div>
                  ))}
                </div>
                <button className="bg-slate-900 text-white px-16 py-5 rounded-3xl font-black text-xl hover:bg-black transition-all shadow-xl">إنشاء الاختبار الآن</button>
            </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }: any) {
  return (
    <div className="bg-white p-8 rounded-[28px] border border-slate-100 shadow-sm">
      <p className="text-slate-500 text-sm font-bold mb-2">{label}</p>
      <p className={`text-4xl font-black ${color}`}>{value}</p>
    </div>
  );
}