import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "../components/Navbar"; // استيراد الشريط

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "EduRAG Platform",
  description: "AI-Powered Education System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar">
      <body className={inter.className}>
        <Navbar /> {/* الشريط يظهر هنا في كل الصفحات */}
        <main>
          {children}
        </main>
      </body>
    </html>
  );
}