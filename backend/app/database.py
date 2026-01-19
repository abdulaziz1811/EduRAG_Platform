"""
EduRAG - Database Connection Manager
====================================
إدارة اتصالات قاعدة البيانات بشكل آمن ومنظم
"""

import os
import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional

# إعداد اللوقر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مسار قاعدة البيانات
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "edurag.db")


@contextmanager
def get_db_connection():
    """
    Context manager للاتصال بقاعدة البيانات بشكل آمن
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"خطأ في قاعدة البيانات: {e}")
        raise
    finally:
        if conn:
            conn.close()

def initialize_database():
    """
    إنشاء الجداول المطلوبة إذا لم تكن موجودة
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
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
        
        # جدول الاختبارات المخصصة (العلاجية)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                quiz_data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("✅ تم إنشاء/التحقق من جداول قاعدة البيانات")

def check_tables_exist() -> dict:
    """
    فحص الجداول المطلوبة في قاعدة البيانات وإعادة حالة النظام كقاموس
    """
    required_tables = [
        'student_stats',
        'concept_stats', 
        'class_quizzes',
        'custom_quizzes'
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
    
    # التحقق مما إذا كانت جميع الجداول المطلوبة موجودة
    missing_tables = [t for t in required_tables if t not in existing_tables]
    is_valid = len(missing_tables) == 0
    
    return {
        "existing": existing_tables,
        "required": required_tables,
        "missing": missing_tables,
        "is_valid": is_valid
    }

if __name__ == "__main__":
    print("جاري فحص قاعدة البيانات...")
    initialize_database()
    tables = check_tables_exist()
    print(f"الجداول الحالية: {tables}")