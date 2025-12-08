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
python main.py
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

## Supabase Entegrasyonu

Supabase veritabanına geçiş yapmak için:

1. `.env` dosyası oluşturun (`.env.example` dosyasını kopyalayın)
2. Supabase URL ve Key bilgilerinizi ekleyin
3. `config.py` dosyasında `DB_CONFIG["type"]` değerini `"supabase"` olarak değiştirin
4. Supabase'de `animals` tablosunu oluşturun:

```sql
CREATE TABLE animals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  isim TEXT NOT NULL,
  yas INTEGER NOT NULL,
  kilo DECIMAL NOT NULL,
  boy DECIMAL NOT NULL,
  cinsiyet TEXT NOT NULL,
  tur TEXT NOT NULL,
  renk TEXT,
  dogum_tarihi TEXT,
  saglik_durumu TEXT,
  notlar TEXT,
  olusturma_tarihi TIMESTAMP DEFAULT NOW()
);
```

## Proje Yapısı

```
Baslangic/
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
└── data/                   # Veri dosyaları
    └── animals.json        # Yerel veritabanı
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

