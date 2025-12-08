from typing import List, Optional, Dict, Any
from supabase import create_client, Client

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

