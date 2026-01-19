"""
EduRAG - Database Seeder
========================
سكربت لتهيئة قاعدة البيانات وإضافة بيانات تجريبية
"""

import sqlite3
import random
import os
from datetime import datetime

# تحديد مسار قاعدة البيانات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")


def create_tables(cursor: sqlite3.Cursor):
    """إنشاء الجداول المطلوبة"""
    
    # جدول إحصائيات الطلاب
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            total_score REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول إحصائيات المفاهيم
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concept_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            concept TEXT NOT NULL,
            score REAL DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES student_stats(id) ON DELETE CASCADE
        )
    """)
    
    # جدول اختبارات الفصول
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_quizzes (
            class_name TEXT PRIMARY KEY,
            quiz_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول الاختبارات المخصصة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            quiz_data TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # إنشاء indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_class ON student_stats(class_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concept_student ON concept_stats(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_quiz_student ON custom_quizzes(student_name)")


def seed_sample_data(cursor: sqlite3.Cursor):
    """إضافة بيانات تجريبية"""
    
    # الأسماء
    first_names = [
        "خالد", "خلف", "فهد", "سلطان", "فيصل", "سلمان", "نايف", "مشاري",
        "بندر", "تركي", "يزيد", "سعود", "نواف", "راكان", "طلال", "عمر",
        "سعد", "محمد", "عبدالله", "بدر", "عبدالرحمن", "أحمد", "حمد", "ماجد"
    ]
    
    last_names = [
        "الشمري", "التميمي", "العنزي", "الرشيدي", "الحايلي",
        "العتيبي", "القحطاني", "الحربي", "الدوسري", "المطيري"
    ]
    
    classes = ["فصل (أ)", "فصل (ب)"]
    concepts = ["الأعداد النسبية", "القوى والجذور", "التناسب", "المساحات", "الجبر"]
    
    students_created = 0
    
    for class_name in classes:
        # 20 طالب لكل فصل
        for i in range(20):
            # اسم عشوائي
            full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # درجات متفاوتة حسب الفصل (فصل ب أضعف)
            if class_name == "فصل (ب)":
                total_avg = random.randint(35, 75)
            else:
                total_avg = random.randint(60, 95)
            
            cursor.execute(
                "INSERT INTO student_stats (name, class_name, total_score) VALUES (?, ?, ?)",
                (full_name, class_name, total_avg)
            )
            student_id = cursor.lastrowid
            students_created += 1
            
            # درجات لكل مفهوم
            for concept in concepts:
                # درجات متفاوتة لإظهار نقاط الضعف
                if class_name == "فصل (ب)" and concept in ["القوى والجذور", "الجبر"]:
                    score = random.randint(20, 55)  # درجات ضعيفة
                else:
                    score = random.randint(40, 100)
                
                cursor.execute(
                    "INSERT INTO concept_stats (student_id, concept, score) VALUES (?, ?, ?)",
                    (student_id, concept, score)
                )
    
    return students_created


def refresh_database(drop_existing: bool = True):
    """
    تحديث قاعدة البيانات
    
    Args:
        drop_existing: حذف الجداول الموجودة وإعادة إنشائها
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔄 جاري تحديث قاعدة البيانات...")
    print("=" * 60)
    
    if drop_existing:
        print("\n📦 حذف الجداول القديمة...")
        cursor.execute("DROP TABLE IF EXISTS concept_stats")
        cursor.execute("DROP TABLE IF EXISTS student_stats")
        cursor.execute("DROP TABLE IF EXISTS class_quizzes")
        cursor.execute("DROP TABLE IF EXISTS custom_quizzes")
    
    print("📦 إنشاء الجداول...")
    create_tables(cursor)
    
    print("📦 إضافة البيانات التجريبية...")
    students_count = seed_sample_data(cursor)
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ تم التحديث بنجاح!")
    print(f"   📊 عدد الطلاب: {students_count}")
    print(f"   📍 المسار: {DB_PATH}")
    print("=" * 60)


def check_database():
    """فحص قاعدة البيانات الحالية"""
    if not os.path.exists(DB_PATH):
        print("❌ قاعدة البيانات غير موجودة!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📋 فحص قاعدة البيانات")
    print("=" * 60)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        if table_name.startswith('sqlite_'):
            continue
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   📁 {table_name}: {count} صف")
    
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_database()
    else:
        refresh_database()