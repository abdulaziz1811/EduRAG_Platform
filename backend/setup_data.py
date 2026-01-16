import sqlite3, random, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'edurag.db')

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS student_stats')
    cursor.execute('DROP TABLE IF EXISTS concept_stats')
    
    cursor.execute('CREATE TABLE student_stats (id INTEGER PRIMARY KEY, name TEXT, class TEXT, total_score INTEGER)')
    cursor.execute('CREATE TABLE concept_stats (student_id INTEGER, concept TEXT, score INTEGER)')

    names = ["فهد", "سلمان", "عبدالرحمن", "فيصل", "خالد", "محمد", "ياسر", "سلطان", "نايف", "سعود", 
             "بندر", "تركي", "مشاري", "طلال", "بدر", "صالح", "ناصر", "عمر", "ماجد", "راشد"]
    
    chapters = ["الفصل 1", "الفصل 2", "الفصل 3", "الفصل 4", "الفصل 5"]
    classes = ["أ", "ب"]

    for i, name in enumerate(names):
        class_name = classes[i % 2]
        
        # تحديد 3 طلاب بحالة حرجة (سلمان، نايف، طلال مثلاً)
        if name in ["سلمان", "نايف", "طلال"]:
            total_avg = random.randint(30, 45) # درجات حرجة
        else:
            total_avg = random.randint(70, 95) # درجات ممتازة
            
        cursor.execute('INSERT INTO student_stats (name, class, total_score) VALUES (?, ?, ?)', (name, class_name, total_avg))
        student_id = cursor.lastrowid
        
        for chap in chapters:
            if name in ["سلمان", "نايف", "طلال"]:
                score = random.randint(20, 50)
            else:
                score = random.randint(65, 100)
            cursor.execute('INSERT INTO concept_stats VALUES (?, ?, ?)', (student_id, chap, score))

    conn.commit()
    conn.close()
    print("✅ تم تجهيز 20 طالباً: 17 متفوقون و 3 في حالة حرجة.")

if __name__ == "__main__":
    setup_database()