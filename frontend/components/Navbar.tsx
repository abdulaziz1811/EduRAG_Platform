import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm" dir="rtl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          {/* الشعار */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="text-2xl font-black text-blue-600 tracking-tighter">
              راقٍ <span className="text-gray-400 text-sm font-normal">EduRAG</span>
            </Link>
          </div>

          {/* الروابط */}
          <div className="hidden sm:ml-6 sm:flex sm:space-x-8 sm:space-x-reverse">
            <Link 
              href="/" 
              className="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              الرئيسية
            </Link>
            
            <Link 
              href="/quiz" 
              className="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              الاختبارات
            </Link>

            <Link 
              href="/dashboard" 
              className="bg-blue-50 text-blue-700 px-4 py-2 rounded-lg text-sm font-bold hover:bg-blue-100 transition-colors"
            >
              بوابة المعلم
            </Link>
          </div>

        </div>
      </div>
    </nav>
  );
}