# Ahır Hayvan Yönetim Sistemi

Ahır hayvanlarını yönetmek için geliştirilmiş Python tabanlı masaüstü uygulaması.

## Özellikler

- 🔐 Kullanıcı giriş sistemi
- 📊 Admin dashboard
- 🐄 Hayvan listesi ve detay görüntüleme
- ➕ Yeni hayvan ekleme
- ✏️ Hayvan bilgilerini düzenleme
- 🗑️ Hayvan silme
- 🔍 Arama ve filtreleme
- 💾 Yerel JSON veritabanı (Supabase'e geçiş için hazır)

## Kurulum

1. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:
```bash
python3 main.py
```

## Varsayılan Giriş Bilgileri

- **Kullanıcı Adı:** `admin`
- **Şifre:** `admin123`

## .exe Oluşturma

Windows için çalıştırılabilir dosya oluşturmak için:

```bash
pyinstaller --onefile --windowed --name "AhirHayvanYonetim" main.py
```

Oluşturulan `.exe` dosyası `dist/` klasöründe bulunacaktır.



## Proje Yapısı

```
Baslangic/
├── .env                    # Supabase Bağlantı
├── main.py                 # Ana uygulama
├── login.py                # Giriş ekranı
├── dashboard.py            # Admin dashboard
├── config.py               # Yapılandırma
├── database/               # Veritabanı katmanı
│   ├── base_db.py         # Abstract base class
│   ├── local_db.py        # Yerel JSON veritabanı
│   └── supabase_db.py     # Supabase entegrasyonu
├── models/                 # Veri modelleri
│   └── animal.py          # Hayvan modeli
├── utils/                  # Yardımcı fonksiyonlar
│   └── validators.py      # Validasyon fonksiyonları

```

## Desteklenen Hayvan Türleri

- İnek
- Koyun
- Keçi
- At
- Eşek
- Manda
- Tavuk
- Ördek
- Kaz
- Hindi

## Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

