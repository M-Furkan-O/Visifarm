from config import DB_CONFIG
from database.local_db import LocalDatabase
from database.supabase_db import SupabaseDatabase

def get_database():
    """Veritabanı tipine göre uygun veritabanı instance'ı döndür"""
    db_type = DB_CONFIG["type"]
    
    if db_type == "supabase":
        db = SupabaseDatabase()
        if db.connect():
            return db
        else:
            print("Supabase bağlantısı başarısız, yerel veritabanına geçiliyor...")
            return LocalDatabase()
    else:
        return LocalDatabase()

