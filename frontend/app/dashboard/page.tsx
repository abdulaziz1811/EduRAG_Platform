"use client";
import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // جلب البيانات من الباك إند
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/dashboard');
        const data = await res.json();
        setStats(data.stats);
      } catch (error) {
        console.error("فشل جلب البيانات");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  // ألوان الرسم البياني
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  if (loading) return <div className="p-10 text-center">جاري تحميل البيانات... ⏳</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8" dir="rtl">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">لوحة تحكم المعلم 👨‍🏫</h1>
          <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full font-bold text-sm">
             عدد الطلاب: {stats.length}
          </span>
        </div>

        {/* --- بطاقات الملخص السريع --- */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm border-r-4 border-blue-500">
            <p className="text-gray-500 mb-1">متوسط درجات الفصل</p>
            <h2 className="text-4xl font-bold text-gray-800">
              {stats.length > 0 
                ? (stats.reduce((acc, curr) => acc + curr.avg_score, 0) / stats.length).toFixed(1) 
                : 0}%
            </h2>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border-r-4 border-green-500">
            <p className="text-gray-500 mb-1">أعلى درجة</p>
            <h2 className="text-4xl font-bold text-gray-800">
              {stats.length > 0 ? Math.max(...stats.map(s => s.avg_score)).toFixed(1) : 0}%
            </h2>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border-r-4 border-red-500">
            <p className="text-gray-500 mb-1">طلاب بحاجة لدعم</p>
            <h2 className="text-4xl font-bold text-gray-800">
              {stats.filter(s => s.avg_score < 60).length}
            </h2>
          </div>
        </div>

        {/* --- الرسوم البيانية --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* رسم بياني 1: درجات الطلاب (أعمدة) */}
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-xl font-bold mb-6 text-gray-700">📊 تحليل درجات الطلاب</h3>
            <div className="h-[300px] w-full" dir="ltr"> {/* dir=ltr مهم للرسوم البيانية */}
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="student" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="avg_score" name="المعدل" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* رسم بياني 2: جدول تفصيلي */}
          <div className="bg-white p-6 rounded-xl shadow-lg overflow-hidden">
            <h3 className="text-xl font-bold mb-6 text-gray-700">📋 سجل الطلاب</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-right">
                <thead className="bg-gray-50 text-gray-600 font-medium">
                  <tr>
                    <th className="p-4 rounded-r-lg">الطالب</th>
                    <th className="p-4">المعدل</th>
                    <th className="p-4 rounded-l-lg">الحالة</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {stats.map((s, idx) => (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td className="p-4 font-bold text-gray-800">{s.student}</td>
                      <td className="p-4 text-blue-600 font-bold">{s.avg_score.toFixed(1)}%</td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold
                          ${s.avg_score >= 80 ? 'bg-green-100 text-green-700' : 
                            s.avg_score >= 60 ? 'bg-yellow-100 text-yellow-700' : 
                            'bg-red-100 text-red-700'}`}>
                          {s.avg_score >= 80 ? 'ممتاز' : s.avg_score >= 60 ? 'جيد' : 'ضعيف'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}