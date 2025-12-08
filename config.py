import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Kullanıcı bilgileri
USERS = {
    "admin": "admin123",
    "user": "user123"
}

# Uygulama ayarları
APP_CONFIG = {
    "title": "Ahır Hayvan Yönetim Sistemi",
    "width": 1400,
    "height": 800,
    "login_width": 450,
    "login_height": 350
}

# Veritabanı ayarları
DB_CONFIG = {
    "type": "supabase",  # "local" veya "supabase"
    "local_file": "data/animals.json",
    "supabase_url": os.getenv("SUPABASE_URL", ""),
    "supabase_key": os.getenv("SUPABASE_KEY", "")
}

# Ahır hayvan türleri
ANIMAL_TYPES = [
    "İnek",
    "Koyun",
    "Keçi",
    "At",
    "Eşek",
    "Manda",
    "Tavuk",
    "Ördek",
    "Kaz",
    "Hindi",
    "Boğa"
]

# Cinsiyet seçenekleri
GENDERS = ["Erkek", "Dişi"]

# Hayvan alanları
ANIMAL_FIELDS = {
    "isim": "İsim",
    "yas": "Yaş",
    "kilo": "Kilo (kg)",
    "boy": "Boy (cm)",
    "cinsiyet": "Cinsiyet",
    "tur": "Tür",
    "renk": "Renk",
    "dogum_tarihi": "Doğum Tarihi",
    "saglik_durumu": "Sağlık Durumu",
    "notlar": "Notlar"
}

