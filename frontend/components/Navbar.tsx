import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm w-full z-50" dir="rtl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              EduRAG Pro
            </Link>
            
            <div className="flex items-center gap-4">
              <Link href="/" className="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md font-medium transition-colors">
                بوابة الطالب          
               </Link>
              
              {/* هذا هو الرابط الذي سيعيدك لواجهة المعلم */}
              <Link href="/dashboard" className="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md font-medium transition-colors">
                بوابة المعلم
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}