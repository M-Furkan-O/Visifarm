from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from pathlib import Path
from database.base_db import BaseDatabase
from models.animal import Animal
from config import DB_CONFIG

class SupabaseDatabase(BaseDatabase):
    """Supabase veritabanı entegrasyonu"""
    
    def __init__(self):
        self.url = DB_CONFIG["supabase_url"]
        self.key = DB_CONFIG["supabase_key"]
        self.client: Optional[Client] = None
        self.table_name = "farm_animals"
    
    def connect(self) -> bool:
        """Supabase'e bağlan"""
        try:
            if not self.url or not self.key:
                raise ValueError("Supabase URL veya Key bulunamadı!")
            
            self.client = create_client(self.url, self.key)
            return True
        except Exception as e:
            print(f"Supabase bağlantı hatası: {e}")
            return False
    
    def get_all_animals(self) -> List[Animal]:
        """Tüm hayvanları getir"""
        try:
            response = self.client.table(self.table_name).select("*").execute()
            return [self._to_animal(item) for item in response.data]
        except Exception as e:
            print(f"Hata: {e}")
            return []
    
    def get_animal_by_id(self, animal_id: str) -> Optional[Animal]:
        """ID'ye göre hayvan getir"""
        try:
            response = self.client.table(self.table_name).select("*").eq("id", animal_id).execute()
            if response.data:
                return self._to_animal(response.data[0])
            return None
        except Exception as e:
            print(f"Hata: {e}")
            return None
    
    def add_animal(self, animal: Animal) -> bool:
        """Yeni hayvan ekle"""
        try:
            data = self._from_animal(animal)
            # ID Supabase tarafından identity ile üretiliyor, None ise gönderme
            data.pop("id", None)
            self.client.table(self.table_name).insert(data).execute()
            return True
        except Exception as e:
            print(f"Hata: {e}")
            return False
    
    def update_animal(self, animal_id: str, animal: Animal) -> bool:
        """Hayvan güncelle"""
        try:
            data = self._from_animal(animal)
            data.pop("id", None)
            self.client.table(self.table_name).update(data).eq("id", animal_id).execute()
            return True
        except Exception as e:
            print(f"Hata: {e}")
            return False
    
    def delete_animal(self, animal_id: str) -> bool:
        """Hayvan sil"""
        try:
            response = self.client.table(self.table_name).delete().eq("id", animal_id).execute()
            return True
        except Exception as e:
            print(f"Hata: {e}")
            return False
    
    def search_animals(self, query: str, filters: Dict[str, Any] = None) -> List[Animal]:
        """Hayvan ara ve filtrele"""
        try:
            query_builder = self.client.table(self.table_name).select("*")
            
            # Metin araması (Supabase'de ilike kullanılabilir)
            if query:
                query_builder = query_builder.or_(
                    f"name.ilike.%{query}%,animal_type.ilike.%{query}%,rfid_tag.ilike.%{query}%"
                )
            
            # Filtreleme
            if filters:
                if filters.get("tur"):
                    query_builder = query_builder.eq("animal_type", filters["tur"])
                if filters.get("cinsiyet"):
                    query_builder = query_builder.eq("gender", filters["cinsiyet"])
            
            response = query_builder.execute()
            return [self._to_animal(item) for item in response.data]
        except Exception as e:
            print(f"Hata: {e}")
            return []

    def _to_animal(self, item: Dict[str, Any]) -> Animal:
        """Supabase satırını Animal modeline dönüştür."""
        mapped = {
            "id": item.get("id"),
            "rfid_tag": item.get("rfid_tag"),
            "name": item.get("name"),
            "animal_type": item.get("animal_type"),
            "gender": item.get("gender"),
            "age": item.get("age"),
            "height": item.get("height"),
            "weight": item.get("weight"),
            "created_at": item.get("created_at"),
        }
        return Animal(mapped)

    def _from_animal(self, animal: Animal) -> Dict[str, Any]:
        """Animal modelini Supabase alanlarına dönüştür."""
        payload = {
            "id": animal.id,
            "rfid_tag": animal.rfid_tag,
            "name": animal.isim,
            "animal_type": animal.tur,
            "gender": animal.cinsiyet,
            "age": int(animal.yas) if animal.yas not in (None, "") else None,
            "height": float(animal.boy) if animal.boy not in (None, "") else None,
            "weight": float(animal.kilo) if animal.kilo not in (None, "") else None,
        }
        # ID verilmemişse göndermeyelim, Supabase identity üretsin
        if payload.get("id") is None:
            payload.pop("id", None)
        return payload

    def upload_photo(self, animal_id: str, local_file_path: Path, filename: str) -> Optional[str]:
        """
        Fotoğrafı Supabase Storage'a (hayvan_foto bucket'ına) yükler ve genel URL'sini döndürür.
        """
        BUCKET_NAME = "hayvan_foto" # Supabase'te oluşturduğunuz bucket adı
        
        # Dosya yolu: 'hayvan_foto/hayvan_id/foto_adı.jpg'
        storage_path = f"{animal_id}/{filename}"
        
        try:
            # Dosya tipini belirle
            file_ext = local_file_path.suffix.lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp'
            }
            content_type = content_type_map.get(file_ext, 'image/jpeg')
            
            # 1. Dosyayı oku
            with open(local_file_path, 'rb') as f:
                file_data = f.read()
            
            # 2. Dosyayı yükle (upsert kullan - varsa güncelle, yoksa ekle)
            response = self.client.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": "true"  # Aynı dosya varsa üzerine yaz
                }
            )
            
            # 3. Yüklenen dosyanın genel URL'sini al
            public_url = self.client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
            
            return public_url
            
        except Exception as e:
            # Hata detaylarını yazdır
            error_msg = str(e)
            if isinstance(e, dict):
                error_msg = f"{e.get('message', 'Bilinmeyen hata')} - Status: {e.get('statusCode', 'N/A')}"
            
            print(f"Supabase fotoğraf yükleme hatası: {error_msg}")
            print(f"Detay: {e}")
            
            # RLS hatası ise kullanıcıya bilgi ver
            if "row-level security" in error_msg.lower() or "403" in str(e):
                print("\n⚠️  RLS POLİTİKASI HATASI!")
                print("Supabase Dashboard'da Storage > hayvan_foto > Policies bölümünden")
                print("aşağıdaki politikaları eklemeniz gerekiyor:")
                print("\n1. INSERT için: Allow public uploads")
                print("2. SELECT için: Allow public reads")
                print("3. UPDATE için: Allow public updates")
                print("4. DELETE için: Allow public deletes")
                print("\nSQL dosyası: supabase_storage_policies.sql")
            
            return None
    
    def delete_photo(self, animal_id: str, filename: str) -> bool:
        """
        Supabase Storage'dan fotoğrafı siler.
        """
        BUCKET_NAME = "hayvan_foto"
        storage_path = f"{animal_id}/{filename}"
        
        try:
            response = self.client.storage.from_(BUCKET_NAME).remove([storage_path])
            return True
        except Exception as e:
            print(f"Supabase fotoğraf silme hatası: {e}")
            return False
    
    def list_photos(self, animal_id: str) -> List[Dict[str, Any]]:
        """
        Supabase Storage'dan bir hayvana ait tüm fotoğrafları listeler.
        Her fotoğraf için: {'name': dosya_adı, 'url': public_url, 'date': tarih}
        """
        BUCKET_NAME = "hayvan_foto"
        folder_path = f"{animal_id}/"
        
        try:
            # Klasördeki tüm dosyaları listele
            files = self.client.storage.from_(BUCKET_NAME).list(folder_path)
            
            photos = []
            for file_info in files:
                if file_info.get('name'):
                    filename = file_info['name']
                    storage_path = f"{animal_id}/{filename}"
                    public_url = self.client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
                    
                    # Dosya adından tarih çıkar (yyyy-MM-dd_... formatı)
                    date_str = filename[:10] if len(filename) >= 10 else None
                    
                    photos.append({
                        'name': filename,
                        'url': public_url,
                        'date': date_str,
                        'path': storage_path
                    })
            
            return photos
        except Exception as e:
            print(f"Supabase fotoğraf listeleme hatası: {e}")
            return []