"use client";
import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, AreaChart, Area } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../../components/Navbar";

export default function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedClass, setSelectedClass] = useState("فصل (أ)");
  
  // حالات البيانات والتحليلات
  const [stats, setStats] = useState({ avg_score: 0, students_at_risk: 0, total_students: 0, total_quizzes: 0 });
  const [students, setStudents] = useState<any[]>([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [studentPerf, setStudentPerf] = useState<any[]>([]);
  const [chaptersAvg, setChaptersAvg] = useState<any[]>([]);
  const [classCompare, setClassCompare] = useState<any[]>([]);
  const [chapterDetails, setChapterDetails] = useState<any[]>([]);
  const [selectedChapter, setSelectedChapter] = useState("1");
  const [summary, setSummary] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // حالات مصنع الاختبارات (الميزة المحدثة)
  const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
  const [strugglingStudents, setStrugglingStudents] = useState<any[]>([]);
  const [factoryLoading, setFactoryLoading] = useState(false);

  // إدارة اختيار الفصول في المصنع
  const toggleChapterSelection = (chap: string) => {
    setSelectedChapters(prev => 
      prev.includes(chap) ? prev.filter(c => c !== chap) : [...prev, chap]
    );
  };

  // جلب البيانات عند تغيير الفصل الدراسي
  useEffect(() => {
    const query = `?class_name=${encodeURIComponent(selectedClass)}`;
    
    fetch(`http://127.0.0.1:8000/teacher/stats${query}`).then(res => res.json()).then(data => setStats(data || {}));
    fetch(`http://127.0.0.1:8000/teacher/students${query}`).then(res => res.json()).then(data => setStudents(Array.isArray(data) ? data : []));
    fetch(`http://127.0.0.1:8000/teacher/analytics/chapters-avg${query}`).then(res => res.json()).then(data => setChaptersAvg(Array.isArray(data) ? data : []));
    fetch(`http://127.0.0.1:8000/teacher/analytics/classes-compare`).then(res => res.json()).then(data => setClassCompare(Array.isArray(data) ? data : []));
    
    // جلب المتعثرين حسب المفاهيم (للمصنع)
    fetch(`http://127.0.0.1:8000/api/analytics/struggling${query}`).then(res => res.json()).then(data => setStrugglingStudents(Array.isArray(data) ? data : []));
    
    loadChapterDetails(selectedChapter, selectedClass);
  }, [selectedClass]);

  const loadChapterDetails = (num: string, className: string) => {
    setSelectedChapter(num);
    fetch(`http://127.0.0.1:8000/teacher/analytics/chapter-details/${num}?class_name=${encodeURIComponent(className)}`)
      .then(res => res.json()).then(data => setChapterDetails(Array.isArray(data) ? data : []));
  };

  const handleStudentSelect = (id: string) => {
    setSelectedStudent(id);
    if(id) {
        fetch(`http://127.0.0.1:8000/teacher/student/${id}/performance`)
        .then(res => res.json())
        .then(data => setStudentPerf(Array.isArray(data) ? data : []));
    }
  };

  // توليد اختبار للفصل بناءً على فصول مختارة (من المصنع)
  const generateClassQuiz = async () => {
    if (selectedChapters.length === 0) return alert("يرجى تحديد الفصول من المنهج أولاً");
    setFactoryLoading(true);
    try {
        const res = await fetch("http://127.0.0.1:8000/api/quiz/generate-and-assign", {
            method:'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ class_name: selectedClass, chapters: selectedChapters })
        });
        const data = await res.json();
        alert("تم إنشاء الاختبار ونشره بنجاح لجميع طلاب الفصل");
    } catch(e) { alert("حدث خطأ في الاتصال بالسيرفر"); }
    setFactoryLoading(false);
  };

  // إرسال اختبار دعم مخصص لطالب محدد
  const sendRemedialQuiz = async (studentName: string, concept: string) => {
    alert(`جاري إعداد اختبار دعم مخصص في مفهوم: ${concept}`);
    try {
        await fetch("http://127.0.0.1:8000/api/quiz/generate-and-assign", {
            method:'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ class_name: selectedClass, student_name: studentName, concept: concept })
        });
        alert("تم إرسال الاختبار العلاجي بنجاح");
    } catch(e) { alert("فشل إرسال الاختبار"); }
  };

  const generateRAGReport = () => {
    setIsGenerating(true);
    fetch("http://127.0.0.1:8000/teacher/generate-summary", {
        method:'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ class_name: selectedClass })
    })
    .then(res=>res.json()).then(d=>{
        setSummary(d.summary);
        setIsGenerating(false);
    });
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 font-sans" dir="rtl">
      <Navbar />
      
      <div className="p-8 max-w-7xl mx-auto">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
                <h1 className="text-3xl font-black border-r-8 border-blue-600 pr-4">لوحة تحكم المعلم</h1>
                <p className="text-slate-500 mt-2 pr-4 font-bold text-lg italic">متابعة أداء الطلاب وتحليل المحتوى التعليمي</p>
            </div>
            
            <div className="flex bg-white p-2 rounded-3xl shadow-sm border border-slate-200">
                {["فصل (أ)", "فصل (ب)"].map((cls) => (
                    <button key={cls} onClick={() => setSelectedClass(cls)}
                        className={`px-8 py-2.5 rounded-2xl font-black transition-all ${selectedClass === cls ? "bg-blue-600 text-white shadow-lg" : "text-slate-400 hover:text-slate-600"}`}>
                        {cls}
                    </button>
                ))}
            </div>
        </header>

        {/* التبويبات بدون إيموجيات */}
        <div className="flex gap-6 mb-12 bg-slate-200/50 p-2 rounded-[2rem] w-fit mx-auto">
          {["overview", "analysis", "factory"].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} 
              className={`px-12 py-3 rounded-3xl font-black text-lg transition-all ${activeTab === tab ? "bg-white text-blue-600 shadow-xl scale-105" : "text-slate-500"}`}>
              {tab === "overview" ? "نظرة عامة" : tab === "analysis" ? "التحليل البياني" : "مصنع الاختبارات"}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "overview" && (
            <motion.div key="overview" initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} exit={{opacity:0}} className="space-y-10">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                <StatCard label={`متوسط ${selectedClass}`} value={`${stats.avg_score || 0}%`} color="text-blue-600" />
                <StatCard label="حالات حرجة" value={stats.students_at_risk || 0} color="text-red-600" />
                <StatCard label="طلاب الفصل" value={stats.total_students || 0} color="text-slate-800" />
                <StatCard label="دروس منتهية" value={stats.total_quizzes || 0} color="text-purple-600" />
              </div>
              
              <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-12 rounded-[50px] shadow-2xl relative overflow-hidden border border-slate-700">
                <div className="relative z-10">
                    <h2 className="text-3xl font-black mb-4 text-blue-400">تحليل المحتوى الذكي المنهجي</h2>
                    <p className="text-slate-300 mb-8 max-w-3xl text-xl font-medium leading-relaxed">يقوم النظام بربط الفجوات التعليمية لدى الطلاب بقطع الشرح المستخرجة من الكتاب المدرسي لتقديم توصيات علاجية دقيقة.</p>
                    <button onClick={generateRAGReport} disabled={isGenerating}
                        className={`bg-blue-600 px-16 py-5 rounded-[2rem] font-black text-xl hover:bg-blue-500 transition-all shadow-2xl shadow-blue-500/40 ${isGenerating ? 'opacity-50' : ''}`}>
                        {isGenerating ? "جاري الاسترجاع والتحليل..." : "توليد ملخص المستجدات"}
                    </button>
                    {summary && <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mt-10 p-10 bg-white/5 backdrop-blur-md rounded-[3rem] text-2xl border-r-8 border-blue-500 font-bold">{summary}</motion.div>}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "analysis" && (
            <motion.div key="analysis" initial={{opacity:0}} animate={{opacity:1}} className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              <ChartWrapper title={`مستوى الإتقان للفصل الدراسي`}>
                {chaptersAvg.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chaptersAvg}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                        <XAxis dataKey="name" />
                        <YAxis domain={[0, 100]} />
                        <Tooltip />
                        <Area type="monotone" dataKey="score" stroke="#2563eb" fill="#dbeafe" strokeWidth={5} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : <EmptyState />}
              </ChartWrapper>

              <ChartWrapper title={`توزيع درجات الطلاب حسب الفصل`} 
  action={<select value={selectedChapter} onChange={(e) => loadChapterDetails(e.target.value, selectedClass)} className="p-2 bg-white rounded-xl border font-black outline-none">
      {[1,2,3,4,5].map(n => <option key={n} value={n}>الفصل {n}</option>)}
  </select>}>
  {chapterDetails.length > 0 ? (
      <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chapterDetails} barGap={5}>
            {/* تعريف التدرج اللوني الأزرق */}
            <defs>
              <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={1}/>
                <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.8}/>
              </linearGradient>
               {/* تعريف لون أحمر للراسبين */}
               <linearGradient id="redGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#dc2626" stopOpacity={1}/>
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.8}/>
              </linearGradient>
            </defs>

            {/* خطوط الشبكة خلفية خفيفة */}
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />

            {/* إخفاء الأسماء من المحور الأفقي لمنع التداخل */}
            <XAxis dataKey="name" hide={true} axisLine={false} tickLine={false} />
            
            {/* تنسيق المحور العمودي */}
            <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12, fontWeight: 'bold'}} />
            
            {/* تلميح مخصص وأنيق يظهر عند تمرير الماوس */}
            <Tooltip 
               cursor={{fill: 'transparent'}}
               content={({ active, payload, label }) => {
                   if (active && payload && payload.length) {
                     const score = payload[0].value as number;
                     return (
                       <div className="bg-white p-4 rounded-2xl shadow-xl border border-slate-100 text-center">
                         <p className="font-black text-slate-800 mb-1 text-lg">{label}</p>
                         <div className={`text-xl font-black ${score < 50 ? 'text-red-600' : 'text-blue-600'}`}>
                           {score}% {score < 50 ? '' : ''} 
                         </div>
                       </div>
                     );
                   }
                   return null;
               }}
            />

            {/* الأعمدة بتصميم حديث */}
            <Bar dataKey="score" radius={[20, 20, 0, 0]} barSize={16} animationDuration={1000}>
                {/* شرط لتغيير اللون إذا كانت الدرجة أقل من 50 */}
                {chapterDetails.map((entry:any, index:number) => (
                    <Cell key={`cell-${index}`} fill={entry.score < 50 ? "url(#redGradient)" : "url(#blueGradient)"} />
                ))}
            </Bar>
          </BarChart>
      </ResponsiveContainer>
  ) : <EmptyState />}
</ChartWrapper>

              <ChartWrapper title={`تحليل أداء طالب منفرد`}
                action={<select value={selectedStudent} onChange={(e) => handleStudentSelect(e.target.value)} className="p-2 bg-blue-50 rounded-xl border-blue-200 font-black text-blue-700 outline-none">
                    <option value="">اختر طالباً</option>
                    {students.map((s:any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>}>
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
                ) : <div className="h-full flex items-center justify-center text-slate-400 font-bold italic">يرجى تحديد طالب لعرض مهاراته</div>}
              </ChartWrapper>

              <ChartWrapper title={`مقارنة متوسط الفصول الدراسية`}>
                 <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={classCompare}>
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
              </ChartWrapper>
            </motion.div>
          )}

          {activeTab === "factory" && (
            <motion.div key="factory" initial={{opacity:0, scale:0.98}} animate={{opacity:1, scale:1}} className="space-y-12">
                {/* مصنع الاختبارات الدوري */}
                <div className="bg-white p-12 rounded-[4rem] border-2 border-slate-100 shadow-xl shadow-slate-200/50">
                    <h2 className="text-3xl font-black mb-4">مصنع الاختبارات الذكي للفصل</h2>
                    <p className="text-slate-500 mb-12 font-bold text-xl leading-relaxed">اختر موضوعات الكتاب التي ترغب في تضمينها، وسيقوم الذكاء الاصطناعي بصياغة الأسئلة بناءً على المحتوى.</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-12">
                      {["الأعداد النسبية", "القوى والجذور", "التناسب", "المساحات", "الجبر"].map((chap, i) => (
                        <button key={i} onClick={() => toggleChapterSelection(chap)}
                            className={`p-6 rounded-[2rem] border-4 transition-all flex flex-col items-center gap-3 ${selectedChapters.includes(chap) ? "border-blue-600 bg-blue-50 text-blue-700 scale-105" : "border-slate-100 bg-slate-50 hover:border-slate-200"}`}>
                            <span className="text-sm font-black opacity-40">الفصل {i+1}</span>
                            <span className="font-black text-xl text-center">{chap}</span>
                        </button>
                      ))}
                    </div>
                    
                    <button onClick={generateClassQuiz} disabled={factoryLoading}
                        className="bg-slate-900 text-white px-24 py-6 rounded-[2.5rem] font-black text-2xl hover:bg-black transition-all shadow-2xl disabled:opacity-50 active:scale-95">
                        {factoryLoading ? "جاري طبخ الأسئلة..." : "نشر الاختبار لجميع الطلاب"}
                    </button>
                </div>

                {/* متابعة المتعثرين بالمفاهيم */}
                <div className="bg-white p-12 rounded-[4rem] border-4 border-red-50 shadow-2xl">
                    <div className="flex justify-between items-center mb-10">
                        <div>
                            <h2 className="text-3xl font-black text-red-600">رادار الطلاب المتعثرين</h2>
                            <p className="text-slate-500 font-bold mt-2">طلاب بحاجة لدعم في مفاهيم محددة.. ارسل لهم اختبارات تعزيزية</p>
                        </div>
                    </div>
                    
                    <div className="overflow-x-auto">
                        <table className="w-full text-right">
                            <thead>
                                <tr className="text-slate-400 border-b-2 border-slate-100 uppercase text-sm">
                                    <th className="pb-6 font-black tracking-widest">اسم الطالب</th>
                                    <th className="pb-6 font-black tracking-widest">المفهوم الضعيف</th>
                                    <th className="pb-6 font-black text-center tracking-widest">نسبة الإتقان</th>
                                    <th className="pb-6 font-black text-left px-4">الإجراء العلاجي</th>
                                </tr>
                            </thead>
                            <tbody>
                                {strugglingStudents.length > 0 ? strugglingStudents.map((s: any) => (
                                    <tr key={`${s.id}-${s.concept}`} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors group">
                                        <td className="py-6 font-black text-xl text-slate-800">{s.name}</td>
                                        <td className="py-6">
                                            <span className="bg-red-100 text-red-700 px-6 py-2 rounded-full text-lg font-black border border-red-200 uppercase">
                                                {s.concept}
                                            </span>
                                        </td>
                                        <td className="py-6 text-center font-black text-2xl text-red-500">{s.score}%</td>
                                        <td className="py-6 text-left">
                                            <button onClick={() => sendRemedialQuiz(s.name, s.concept)}
                                                className="bg-slate-800 text-white px-8 py-3 rounded-2xl font-black text-sm hover:bg-red-600 transition-all opacity-0 group-hover:opacity-100 shadow-lg">
                                                إرسال اختبار دعم
                                            </button>
                                        </td>
                                    </tr>
                                )) : (
                                    <tr>
                                        <td colSpan={4} className="py-20 text-center text-slate-400 font-bold text-2xl">لا يوجد طلاب متعثرين حالياً، أداء الفصل ممتاز.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
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
    <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm hover:shadow-2xl transition-all">
      <p className="text-slate-400 text-sm font-black uppercase tracking-wider mb-4">{label}</p>
      <p className={`text-5xl font-black ${color}`}>{value}</p>
    </div>
  );
}

function ChartWrapper({ title, children, action }: any) {
    return (
        <div className="bg-white p-10 rounded-[3rem] border border-slate-100 shadow-xl shadow-slate-200/40">
            <div className="flex justify-between items-center mb-8">
                <h3 className="text-2xl font-black text-slate-700">{title}</h3>
                {action}
            </div>
            <div className="h-[350px]">{children}</div>
        </div>
    );
}

function EmptyState() {
    return <div className="h-full flex items-center justify-center text-slate-400 font-bold italic text-lg text-center p-10">لا توجد بيانات كافية للتحليل حالياً</div>;
}