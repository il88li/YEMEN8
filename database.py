import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        try:
            self.conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            print("✅ تم الاتصال بقاعدة البيانات بنجاح")
        except Exception as e:
            print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
    
    def create_tables(self):
        try:
            with self.conn.cursor() as cur:
                # جدول المستخدمين
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(100),
                        first_name VARCHAR(100),
                        is_admin BOOLEAN DEFAULT FALSE,
                        active_bots INTEGER DEFAULT 0,
                        max_bots INTEGER DEFAULT 3,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # جدول البوتات
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS bots (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        bot_name VARCHAR(100),
                        bot_language VARCHAR(10),
                        bot_token VARCHAR(100),
                        bot_code TEXT,
                        file_path VARCHAR(200),
                        is_active BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # جدول المكتبات
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS libraries (
                        id SERIAL PRIMARY KEY,
                        library_name VARCHAR(100) UNIQUE,
                        installed_by BIGINT,
                        installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (installed_by) REFERENCES users (user_id)
                    )
                ''')
                
                self.conn.commit()
                print("✅ تم إنشاء الجداول بنجاح")
                
                # إضافة المدير
                self.add_admin()
                
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجداول: {e}")
    
    def add_admin(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO users (user_id, username, is_admin, max_bots) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET 
                    is_admin = EXCLUDED.is_admin, max_bots = EXCLUDED.max_bots
                ''', (6689435577, 'admin', True, 10))
                self.conn.commit()
                print("✅ تم إضافة المدير بنجاح")
        except Exception as e:
            print(f"❌ خطأ في إضافة المدير: {e}")
    
    def get_user(self, user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                return cur.fetchone()
        except Exception as e:
            print(f"❌ خطأ في جلب بيانات المستخدم: {e}")
            return None
    
    def add_user(self, user_id, username, first_name):
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO users (user_id, username, first_name) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                ''', (user_id, username, first_name))
                self.conn.commit()
        except Exception as e:
            print(f"❌ خطأ في إضافة المستخدم: {e}")
    
    def can_create_bot(self, user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    SELECT active_bots, max_bots FROM users WHERE user_id = %s
                ''', (user_id,))
                result = cur.fetchone()
                if result:
                    active_bots, max_bots = result
                    return active_bots < max_bots
                return False
        except Exception as e:
            print(f"❌ خطأ في التحقق من إمكانية إنشاء بوت: {e}")
            return False
    
    def add_bot(self, user_id, bot_name, language, token, code, file_path):
        try:
            with self.conn.cursor() as cur:
                # إضافة البوت
                cur.execute('''
                    INSERT INTO bots (user_id, bot_name, bot_language, bot_token, bot_code, file_path, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (user_id, bot_name, language, token, code, file_path, True))
                
                # تحديث عدد البوتات النشطة
                cur.execute('''
                    UPDATE users SET active_bots = active_bots + 1 WHERE user_id = %s
                ''', (user_id,))
                
                self.conn.commit()
                return True
        except Exception as e:
            print(f"❌ خطأ في إضافة البوت: {e}")
            return False
    
    def get_user_bots(self, user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    SELECT id, bot_name, bot_language, is_active, created_at 
                    FROM bots WHERE user_id = %s ORDER BY created_at DESC
                ''', (user_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"❌ خطأ في جلب بوتات المستخدم: {e}")
            return []
    
    def add_library(self, library_name, user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO libraries (library_name, installed_by) 
                    VALUES (%s, %s) ON CONFLICT (library_name) DO NOTHING
                ''', (library_name.strip(), user_id))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"❌ خطأ في إضافة المكتبة: {e}")
            return False
    
    def get_libraries(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT library_name FROM libraries ORDER BY installed_at DESC')
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"❌ خطأ في جلب المكتبات: {e}")
            return []

# إنشاء كائن قاعدة البيانات
db = Database()
