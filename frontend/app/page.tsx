import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center bg-gray-50 p-8" dir="rtl">
      
      {/* النصوص الترحيبية */}
      <div className="text-center max-w-3xl mb-12">
        <h1 className="text-6xl font-black text-gray-900 mb-6">
          التعليم بمفهوم <span className="text-blue-600">راقٍ</span>
        </h1>
        <p className="text-xl text-gray-500 leading-relaxed">
          منصة تعليمية ذكية تستخدم الذكاء الاصطناعي لتحليل نقاط ضعف الطلاب 
          وتوليد اختبارات مخصصة من المناهج الدراسية مباشرة.
        </p>
      </div>

      {/* بطاقات الدخول */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
        
        {/* بطاقة الطالب */}
        <Link href="/quiz" className="group">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:border-blue-300 transition-all cursor-pointer h-full text-center">
            <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
              🎓
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-3">أنا طالب</h2>
            <p className="text-gray-500">
              اختبر مستواك في الرياضيات واحصل على تحليل فوري لنقاط ضعفك.
            </p>
          </div>
        </Link>

        {/* بطاقة المعلم */}
        <Link href="/dashboard" className="group">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-xl hover:border-blue-300 transition-all cursor-pointer h-full text-center">
            <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
              👨‍🏫
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-3">أنا معلم</h2>
            <p className="text-gray-500">
              راقب أداء طلابك، واكتشف المفاهيم التي تحتاج لإعادة شرح.
            </p>
          </div>
        </Link>

      </div>
      
      <div className="mt-16 text-gray-400 text-sm">
        تم التطوير بواسطة عبد العزيز © 2026
      </div>
    </div>
  );
}