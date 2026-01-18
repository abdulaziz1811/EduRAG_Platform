import sqlite3, random, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")

def refresh_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS concept_stats")
    cursor.execute("DROP TABLE IF EXISTS student_stats")
    
    cursor.execute("CREATE TABLE student_stats (id INTEGER PRIMARY KEY, name TEXT, class_name TEXT, total_score REAL)")
    cursor.execute("CREATE TABLE concept_stats (id INTEGER PRIMARY KEY, student_id INTEGER, concept TEXT, score REAL, FOREIGN KEY(student_id) REFERENCES student_stats(id))")

    first_names = ["خالد", "فهد", "سلطان", "فيصل", "سلمان", "نايف", "مشاري", "بندر", "تركي", "يزيد", "سعود", "نواف", "راكان", "طلال", "عمر", "سعد", "محمد", "عبدالله", "بدر", "منصور"]
    father_names = ["أحمد", "علي", "سليمان", "إبراهيم", "صالح", "ناصر", "عبدالرحمن", "سعيد", "فواز", "حمد"]
    
    classes = ["فصل (أ)", "فصل (ب)"]
    concepts = ["الكسور", "الضرب والقسمة", "الهندسة", "القياس", "الجبر"]

    for class_name in classes:
        for i in range(20):
            # اسم ثنائي عشوائي
            full_name = f"{random.choice(first_names)} {random.choice(father_names)}"
            # درجات متفاوتة: فصل ب دائماً أضعف قليلاً لغرض التحليل
            if class_name == "فصل (ب)":
                total_avg = random.randint(35, 75)
            else:
                total_avg = random.randint(60, 95)
                
            cursor.execute("INSERT INTO student_stats (name, class_name, total_score) VALUES (?, ?, ?)", (full_name, class_name, total_avg))
            s_id = cursor.lastrowid
            
            for c in concepts:
                # توليد درجات تجعل مهارة معينة ضعيفة عمداً للتحليل
                score = random.randint(20, 100)
                cursor.execute("INSERT INTO concept_stats (student_id, concept, score) VALUES (?, ?, ?)", (s_id, c, score))
    
    conn.commit()
    conn.close()
    print(f"✅ تم تحديث قاعدة البيانات بأسماء ثنائية في: {DB_PATH}")

if __name__ == "__main__":
    refresh_database()