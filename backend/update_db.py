import sqlite3
import random
import os

# تحديد مسار قاعدة البيانات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")

def refresh_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- جاري تصفية وتحديث قاعدة البيانات بالكامل ---")

    # 1. حذف الجداول القديمة (لضمان نظافة البيانات)
    cursor.execute("DROP TABLE IF EXISTS concept_stats")
    cursor.execute("DROP TABLE IF EXISTS student_stats")
    cursor.execute("DROP TABLE IF EXISTS class_quizzes")
    cursor.execute("DROP TABLE IF EXISTS custom_quizzes")
    
    # 2. إنشاء جداول الإحصائيات (الطلاب والمهارات)
    cursor.execute("""
        CREATE TABLE student_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            class_name TEXT, 
            total_score REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE concept_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            student_id INTEGER, 
            concept TEXT, 
            score REAL, 
            FOREIGN KEY(student_id) REFERENCES student_stats(id)
        )
    """)

    # 3. إنشاء جدول الاختبارات العامة للفصول (مصنع الاختبارات)
    cursor.execute("""
        CREATE TABLE class_quizzes (
            class_name TEXT PRIMARY KEY,
            quiz_data TEXT
        )
    """)

    # 4. إنشاء جدول الاختبارات المخصصة (للمتعثرين - دعم مخصص)
    cursor.execute("""
        CREATE TABLE custom_quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            quiz_data TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- توليد بيانات تجريبية (الأسماء والدرجات) ---
    first_names = ["خالد", "خلف", "فهد", "سلطان", "فيصل", "سلمان", "نايف", "مشاري", "بندر", "تركي", "يزيد", "سعود", "نواف", "راكان", "طلال", "عمر", "سعد", "محمد", "عبدالله", "بدر"]
    father_names = ["الشمري", "التميمي", "العنزي", "الرشيدي", "الحايلي", "العتيبي", "القحطاني", "الحربي"]
    
    classes = ["فصل (أ)", "فصل (ب)"]
    concepts = ["الأعداد النسبية", "القوى والجذور", "التناسب", "المساحات", "الجبر"]

    for class_name in classes:
        for i in range(20):
            # اسم ثنائي بلمسة حائلية
            full_name = f"{random.choice(first_names)} {random.choice(father_names)}"
            
            # محاكاة درجات حقيقية للتحليل
            if class_name == "فصل (ب)":
                total_avg = random.randint(35, 75)
            else:
                total_avg = random.randint(60, 95)
                
            cursor.execute("INSERT INTO student_stats (name, class_name, total_score) VALUES (?, ?, ?)", 
                           (full_name, class_name, total_avg))
            s_id = cursor.lastrowid
            
            for c in concepts:
                # توليد درجات متفاوتة لإظهار حالات تعثر في الداشبورد
                score = random.randint(20, 100)
                cursor.execute("INSERT INTO concept_stats (student_id, concept, score) VALUES (?, ?, ?)", 
                               (s_id, c, score))
    
    conn.commit()
    conn.close()
    print(f"✅ تم بنجاح:")
    print(f"   - إنشاء جداول الإحصائيات مع 40 طالب.")
    print(f"   - إضافة جداول 'class_quizzes' و 'custom_quizzes' للميزات الجديدة.")
    print(f"📍 المسار: {DB_PATH}")

if __name__ == "__main__":
    refresh_database()