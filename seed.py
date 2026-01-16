import sqlite3
import random
from datetime import datetime, timedelta

# المسار الصحيح لقاعدة البيانات بناءً على ملفاتك
DB_PATH = "backend/data/edurag.db"

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # أسماء طلاب وهمية
    names = [
        "سلطان الحربي", "نورة السبيعي", "أحمد الزهراني", "سارة خالد", "فيصل المطيري",
        "ريم القحطاني", "خالد العتيبي", "ليلى الشهري", "عبدالرحمن الدوسري", "شهد العنزي",
        "محمد البقمي", "فاطمة الغامدي", "ياسر الشمري", "مها الرويلي", "تركي السالم",
        "هيا الفهد", "سلمان الرشيد", "بيان العيسى", "فهد المنصور", "منى التميمي"
    ]

    print("جاري إضافة 20 طالب ونتائجهم...")

    for name in names:
        # إضافة الطالب (إيميل وهمي بسيط)
        email = f"{name.split()[0]}@example.com"
        try:
            cursor.execute('INSERT INTO users (name, email, role) VALUES (?, ?, ?)', (name, email, 'student'))
            user_id = cursor.lastrowid
        except:
            # إذا كان الطالب موجوداً مسبقاً
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user_id = cursor.fetchone()[0]

        # إضافة من 2 إلى 4 اختبارات لكل طالب لملء الإحصائيات
        for _ in range(random.randint(2, 4)):
            score = random.randint(3, 5) # درجات من 5
            date = (datetime.now() - timedelta(days=random.randint(0, 15))).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO quiz_results (user_id, topic, score, total_questions, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, "الرياضيات - الفصل الأول", score, 5, date))

    conn.commit()
    conn.close()
    print("✅ تمت إضافة البيانات بنجاح!")

if __name__ == "__main__":
    seed_data()