"use client";
import { useState, useEffect } from 'react';
import { 
  LayoutDashboard, BarChart3, FilePlus, 
  Users, AlertCircle, GraduationCap, ClipboardCheck,
  TrendingDown, RefreshCw, Send
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, LineChart, Line, Legend 
} from 'recharts';

export default function TeacherDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    avg_score: "0%",
    risk_students: 0,
    total_students: 0,
    total_quizzes: 0
  });
  const [analytics, setAnalytics] = useState({ concepts: [], students: [] });
  const [summary, setSummary] = useState("");
  const [loadingSummary, setLoadingSummary] = useState(false);

  // جلب الإحصائيات عند تحميل الصفحة
  useEffect(() => {
    fetch('http://localhost:8000/teacher/stats')
      .then(res => res.json())
      .then(data => setStats(data));

    fetch('http://localhost:8000/teacher/analytics')
      .then(res => res.json())
      .then(data => setAnalytics(data));
  }, []);

  const generateAIReport = async () => {
    setLoadingSummary(true);
    try {
      const res = await fetch('http://localhost:8000/teacher/generate-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ teacher_id: 1 })
      });
      const data = await res.json();
      setSummary(data.summary);
    } catch (error) {
      console.error("Error fetching summary:", error);
    }
    setLoadingSummary(false);
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans" dir="rtl">
      {/* Sidebar - القائمة الجانبية */}
      <div className="w-72 bg-slate-900 text-white p-6 shadow-2xl transition-all">
        <div className="flex items-center space-x-3 mb-12 border-b border-slate-700 pb-6">
          <GraduationCap className="text-indigo-400 w-10 h-10 ml-3" />
          <h1 className="text-2xl font-bold">EduRAG <span className="text-indigo-400 text-sm">PRO</span></h1>
        </div>
        
        <nav className="space-y-2">
          <SidebarLink 
            active={activeTab === 'overview'} 
            onClick={() => setActiveTab('overview')}
            icon={<LayoutDashboard />} 
            label="نظرة عامة" 
          />
          <SidebarLink 
            active={activeTab === 'analytics'} 
            onClick={() => setActiveTab('analytics')}
            icon={<BarChart3 />} 
            label="تحليل بياني" 
          />
          <SidebarLink 
            active={activeTab === 'quizzes'} 
            onClick={() => setActiveTab('quizzes')}
            icon={<FilePlus />} 
            label="صنع اختبارات الراق" 
          />
        </nav>
      </div>

      {/* Main Content - المحتوى الرئيسي */}
      <div className="flex-1 overflow-y-auto p-10">
        
        {/* --- قسم نظرة عامة --- */}
        {activeTab === 'overview' && (
          <div className="animate-in fade-in duration-500">
            <header className="mb-10">
              <h2 className="text-3xl font-bold text-slate-800">مرحباً بك أيها المعلم</h2>
              <p className="text-slate-500 mt-2">إليك ملخص سريع لأداء طلابك اليوم.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
              <StatCard title="متوسط الدرجات" value={stats.avg_score} icon={<GraduationCap />} color="text-blue-600" bg="bg-blue-100" />
              <StatCard title="طلاب في خطر" value={stats.risk_students} icon={<AlertCircle />} color="text-red-600" bg="bg-red-100" />
              <StatCard title="إجمالي الطلاب" value={stats.total_students} icon={<Users />} color="text-green-600" bg="bg-green-100" />
              <StatCard title="الاختبارات المعطاة" value={stats.total_quizzes} icon={<ClipboardCheck />} color="text-yellow-600" bg="bg-yellow-100" />
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-slate-800 flex items-center">
                  <RefreshCw className="ml-2 text-indigo-500" /> الملخص الذكي (RAG Analysis)
                </h3>
                <button 
                  onClick={generateAIReport}
                  disabled={loadingSummary}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-xl transition flex items-center disabled:opacity-50"
                >
                  {loadingSummary ? "جاري التحليل..." : "اصنع ملخص"}
                </button>
              </div>
              
              {summary ? (
                <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-100 text-slate-700 leading-relaxed whitespace-pre-line shadow-inner">
                  {summary}
                </div>
              ) : (
                <div className="text-center py-10 border-2 border-dashed border-slate-100 rounded-xl text-slate-400">
                  انقر على الزر لتوليد تقرير ذكي عن الطلاب المتعثرين والمفاهيم الصعبة.
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- قسم التحليل البياني --- */}
        {activeTab === 'analytics' && (
          <div className="animate-in slide-in-from-bottom-4 duration-500 space-y-8">
            <h2 className="text-3xl font-bold text-slate-800 mb-8 text-center">لوحة البيانات التحليلية</h2>
            
            <div className="grid grid-cols-2 gap-8">
              {/* رسم بياني للمفاهيم */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-bold mb-6 text-slate-700">أداء المفاهيم التعليمية</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics.concepts}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="concept" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="avg_score" fill="#6366f1" radius={[4, 4, 0, 0]} name="متوسط الدرجة" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {analytics.concepts.some((c: any) => c.failure_rate > 40) && (
                   <div className="mt-4 p-4 bg-orange-50 text-orange-700 rounded-lg flex items-start text-sm">
                      <TrendingDown className="ml-2 w-5 h-5 flex-shrink-0" />
                      <p>
                        تنبيه: أعد شرح مفهوم <b>{analytics.concepts.find((c: any) => c.failure_rate > 40)?.['concept']}</b> لأن نسبة الخطأ تجاوزت 40% بين الطلاب.
                      </p>
                   </div>
                )}
              </div>

              {/* رسم بياني للطلاب */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-bold mb-6 text-slate-700">توزيع درجات الطلاب</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={analytics.students}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="average" stroke="#10b981" strokeWidth={3} dot={{r: 6}} name="الدرجة" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- قسم صنع الاختبارات --- */}
        {activeTab === 'quizzes' && (
          <div className="bg-white p-10 rounded-2xl shadow-sm border border-slate-100 max-w-2xl mx-auto mt-10 text-center animate-in zoom-in duration-500">
            <div className="bg-indigo-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 text-indigo-600">
              <FilePlus size={40} />
            </div>
            <h2 className="text-3xl font-bold text-slate-800 mb-4">مولد اختبارات الراق</h2>
            <p className="text-slate-500 mb-8 px-10">اختر الملفات المرجعية، وسيقوم الذكاء الاصطناعي بصياغة أسئلة دقيقة بناءً على المحتوى.</p>
            
            <div className="space-y-4 text-right">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">اختر المستند التعليمي</label>
                <select className="w-full p-3 bg-gray-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500">
                  <option>math.pdf</option>
                  <option>science_unit1.pdf</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">عدد الأسئلة</label>
                  <input type="number" defaultValue={5} className="w-full p-3 bg-gray-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">مستوى الصعوبة</label>
                  <select className="w-full p-3 bg-gray-50 border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500">
                    <option>سهل</option>
                    <option>متوسط</option>
                    <option>صعب</option>
                  </select>
                </div>
              </div>
              <button className="w-full mt-6 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-indigo-200 transition flex items-center justify-center">
                <Send className="ml-2 w-5 h-5" /> ابدأ توليد الأسئلة
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

// مكونات صغيرة (Sub-components) لترتيب الكود
function SidebarLink({ active, icon, label, onClick }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center w-full p-4 rounded-xl transition-all duration-200 group ${
        active ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
      }`}
    >
      <span className={`ml-4 transition-transform group-hover:scale-110 ${active ? 'text-white' : 'text-indigo-400'}`}>
        {icon}
      </span>
      <span className="font-medium text-lg">{label}</span>
    </button>
  );
}

function StatCard({ title, value, icon, color, bg }: any) {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between hover:border-indigo-200 transition cursor-default group">
      <div className="flex justify-between items-start mb-4">
        <span className={`p-3 rounded-xl ${bg} ${color} transition group-hover:scale-110`}>{icon}</span>
      </div>
      <div>
        <p className="text-slate-500 text-sm font-medium">{title}</p>
        <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
      </div>
    </div>
  );
}