"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar"; // إضافة الاستيراد

export default function StudentLoginPage() {
  const [name, setName] = useState("");
  const [chapter, setChapter] = useState("");
  const router = useRouter();

  const handleStart = () => {
    if (name && chapter) {
      localStorage.setItem("student_name", name);
      localStorage.setItem("selected_chapter", chapter);
      router.push("/quiz"); // تأكد أن مجلد quiz موجود إذا كنت ستحذف الواجهة كما طلبت سابقاً
    } else {
      alert("يرجى إكمال البيانات المطلوبة");
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] font-sans">
      <Navbar /> {/* إضافة شريط التنقل هنا ليظهر رابط واجهة المعلم */}
      
      <div className="flex items-center justify-center p-6 pt-20">
        <motion.div initial={{scale:0.9, opacity:0}} animate={{scale:1, opacity:1}} className="max-w-md w-full bg-white rounded-[40px] p-10 shadow-2xl">
          <div className="text-center mb-10">
            <h1 className="text-3xl font-black text-slate-900 mb-4">منصة الرياضيات الذكية</h1>
            <p className="text-blue-600 font-bold">مرحباً بك يا بطل في مادة الرياضيات للصف الثاني المتوسط</p>
          </div>

          <div className="space-y-6 text-right">
            <div>
              <label className="block text-slate-700 font-bold mb-2">اسم الطالب:</label>
              <input type="text" value={name} onChange={(e)=>setName(e.target.value)} placeholder="أدخل اسمك الثلاثي"
                className="w-full p-4 rounded-2xl bg-slate-50 border-2 border-slate-100 focus:border-blue-500 outline-none transition-all font-bold text-slate-800" />
            </div>

            <div>
              <label className="block text-slate-700 font-bold mb-2">اختر فصل الاختبار:</label>
              <select value={chapter} onChange={(e)=>setChapter(e.target.value)}
                className="w-full p-4 rounded-2xl bg-slate-50 border-2 border-slate-100 focus:border-blue-500 outline-none font-bold text-slate-800">
                <option value="">-- حدد الفصل --</option>
                <option value="1">الفصل الأول: الكسور الاعتيادية</option>
                <option value="2">الفصل الثاني: الضرب والقسمة</option>
                <option value="3">الفصل الثالث: الهندسة والأشكال</option>
                <option value="4">الفصل الرابع: القياس والوحدات</option>
                <option value="5">الفصل الخامس: الجبر والعمليات</option>
              </select>
            </div>

            <button onClick={handleStart} className="w-full bg-blue-600 text-white py-5 rounded-2xl font-black text-xl hover:bg-blue-700 shadow-lg shadow-blue-100 transition-all active:scale-95">
              بدء الاختبار التفاعلي
            </button>
          </div>

          <p className="text-center text-slate-400 text-xs mt-8 font-medium">نظام EduRAG التعليمي المطور</p>
        </motion.div>
      </div>
    </div>
  );
}