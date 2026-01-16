import sqlite3
import random
from datetime import datetime, timedelta

# اتصال بقاعدة البيانات (تأكد من المسار الصحيح)
conn = sqlite3.connect('edurag.db')
cursor = conn.cursor()

# إنشاء جداول إذا لم تكن موجودة (لضمان البنية)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'student'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    topic TEXT,
    score INTEGER,
    total_questions INTEGER,
    date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# قائمة أسماء عربية وهمية
names = [
    "أحمد محمد", "سارة خالد", "فهد العنزي", "نورة السبيعي", "محمد العتيبي",
    "ريما عبدالله", "عبدالرحمن الزهراني", "شهد الدوسري", "خالد القحطاني", "مها الشمري",
    "فيصل المطيري", "الهنوف محمد", "سلطان الحربي", "نوف الشهري", "عبدالله السالم",
    "غادة الغامدي", "تركي المالكي", "لجين يوسف", "سلمان الرشيد", "بيان العيسى"
]

# تنظيف البيانات القديمة (اختياري)
# cursor.execute('DELETE FROM users')
# cursor.execute('DELETE FROM quiz_results')

print("جاري إضافة الطلاب والنتائج الوهمية...")

for i, name in enumerate(names):
    email = f"student{i+1}@example.com"
    # إضافة الطالب
    cursor.execute('INSERT INTO users (name, email, role) VALUES (?, ?, ?)', (name, email, 'student'))
    user_id = cursor.lastrowid
    
    # إضافة نتائج عشوائية لكل طالب (من 1 إلى 5 اختبارات)
    num_quizzes = random.randint(1, 5)
    for _ in range(num_quizzes):
        topic = random.choice(["الرياضيات", "الفيزياء", "التاريخ", "الكيمياء"])
        total = 5
        score = random.randint(2, 5) # درجات بين 2 و 5
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO quiz_results (user_id, topic, score, total_questions, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, topic, score, total, date))

conn.commit()
print("تمت إضافة 20 طالب ونتائجهم بنجاح!")
conn.close()