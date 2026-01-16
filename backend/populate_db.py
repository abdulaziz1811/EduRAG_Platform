import sqlite3
import random
import os

# تحديد المسار الصحيح لقاعدة البيانات
db_path = os.path.join(os.path.dirname(__file__), 'edurag.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("جاري تهيئة قاعدة البيانات وإضافة الطلاب الجدد...")

# 1. إنشاء الجداول بشكل صحيح (استخدام NOT NULL)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        concept TEXT NOT NULL,
        score INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# 2. تنظيف البيانات القديمة
cursor.execute('DELETE FROM scores')
cursor.execute("DELETE FROM users WHERE role = 'student'")

# 3. قائمة أسماء العيال الجديدة (بدون عوايل)
student_names = [
    "فهد", "سلمان", "عبدالرحمن", "فيصل", "خالد", 
    "محمد", "ياسر", "سلطان", "نايف", "سعود", 
    "بندر", "تركي", "مشاري", "طلال", "بدر",
    "صالح", "ناصر", "عمر", "ماجد", "راشد"
]

# 4. إضافة الطلاب وتوليد درجات وهمية
for i, name in enumerate(student_names):
    email = f"student{i+1}@example.com"
    
    try:
        # إضافة الطالب
        cursor.execute('INSERT INTO users (name, email, role) VALUES (?, ?, ?)', (name, email, 'student'))
        user_id = cursor.lastrowid
        
        # إضافة درجات وهمية للمفاهيم
        concepts = ["المشتقات", "التكامل", "المصفوفات"]
        for concept in concepts:
            # محاكاة: 50% من الطلاب اخطأوا في "التكامل"
            if concept == "التكامل" and i < 10: 
                score = random.randint(20, 48)
            else:
                score = random.randint(65, 98)
                
            cursor.execute('INSERT INTO scores (user_id, concept, score) VALUES (?, ?, ?)', (user_id, concept, score))
    except sqlite3.IntegrityError:
        continue 

conn.commit()
conn.close()
print(f"تمت العملية بنجاح! تم تحديث قاعدة البيانات في: {db_path}")