"use client";
import { useEffect, useState } from 'react';
import Navbar from '../../components/Navbar';
import { motion } from 'framer-motion';

interface Student {
  id: number;
  name: string;
  email: string;
  quizzes_taken: number;
  average_score: number;
}

export default function Dashboard() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // محاكاة جلب البيانات من الـ API الذي أنشأناه
    fetch('http://localhost:8000/api/dashboard/stats')
      .then(res => res.json())
      .then(data => {
        setStudents(data.students);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch stats", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-right" dir="rtl">
      <Navbar />
      
      <main className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">لوحة تحكم المعلم</h1>
          <p className="mt-2 text-gray-600">متابعة أداء الطلاب وتقدمهم في الاختبارات</p>
        </div>

        {/* بطاقات إحصائيات سريعة */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-gray-500 text-sm">إجمالي الطلاب</h3>
            <p className="text-3xl font-bold text-blue-600">{students.length}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
             <h3 className="text-gray-500 text-sm">متوسط الأداء العام</h3>
             <p className="text-3xl font-bold text-green-600">
               {students.length > 0 
                 ? Math.round(students.reduce((acc, curr) => acc + curr.average_score, 0) / students.length) + '%' 
                 : '0%'}
             </p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-gray-500 text-sm">الاختبارات المنجزة</h3>
            <p className="text-3xl font-bold text-purple-600">
              {students.reduce((acc, curr) => acc + curr.quizzes_taken, 0)}
            </p>
          </div>
        </div>

        {/* جدول الطلاب */}
        <div className="bg-white shadow-lg rounded-2xl overflow-hidden border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
            <h2 className="text-lg font-semibold text-gray-800">قائمة الطلاب</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center text-gray-500">جاري تحميل البيانات...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-right">
                <thead className="bg-gray-50 text-gray-600 text-sm uppercase">
                  <tr>
                    <th className="px-6 py-4 font-medium">اسم الطالب</th>
                    <th className="px-6 py-4 font-medium">البريد الإلكتروني</th>
                    <th className="px-6 py-4 font-medium">عدد الاختبارات</th>
                    <th className="px-6 py-4 font-medium">مستوى الأداء</th>
                    <th className="px-6 py-4 font-medium">الحالة</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {students.map((student, index) => (
                    <motion.tr 
                      key={student.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="hover:bg-blue-50/30 transition-colors"
                    >
                      <td className="px-6 py-4 font-medium text-gray-900">{student.name}</td>
                      <td className="px-6 py-4 text-gray-500">{student.email}</td>
                      <td className="px-6 py-4 text-gray-900">{student.quizzes_taken}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${
                                student.average_score >= 80 ? 'bg-green-500' :
                                student.average_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${student.average_score}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">{student.average_score}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          نشط
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}