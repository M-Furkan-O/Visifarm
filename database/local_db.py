import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database.base_db import BaseDatabase
from models.animal import Animal
from config import DB_CONFIG

class LocalDatabase(BaseDatabase):
    """Yerel JSON dosyası kullanan veritabanı (Supabase'e geçiş için geçici)"""
    
    def __init__(self):
        self.file_path = Path(DB_CONFIG["local_file"])
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = []
        self.load_data()
    
    def connect(self) -> bool:
        """Veritabanına bağlan (yerel dosya için her zaman True)"""
        return True
    
    def load_data(self):
        """Verileri dosyadan yükle"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = []
            self.save_data()
        else:
            self.data = []
            self.save_data()
    
    def save_data(self):
        """Verileri dosyaya kaydet"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_all_animals(self) -> List[Animal]:
        """Tüm hayvanları getir"""
        return [Animal(item) for item in self.data]
    
    def get_animal_by_id(self, animal_id: str) -> Optional[Animal]:
        """ID'ye göre hayvan getir"""
        for item in self.data:
            if item.get("id") == animal_id:
                return Animal(item)
        return None
    
    def add_animal(self, animal: Animal) -> bool:
        """Yeni hayvan ekle"""
        try:
            if not animal.id:
                animal.id = str(uuid.uuid4())
            
            animal_dict = animal.to_dict()
            self.data.append(animal_dict)
            self.save_data()
            return True
        except Exception as e:
            print(f"Hata: {e}")
            return False
    
    def update_animal(self, animal_id: str, animal: Animal) -> bool:
        """Hayvan güncelle"""
        try:
            for i, item in enumerate(self.data):
                if item.get("id") == animal_id:
                    animal.id = animal_id
                    self.data[i] = animal.to_dict()
                    self.save_data()
                    return True
            return False
        except Exception as e:
            print(f"Hata: {e}")
            return False
    
    def delete_animal(self, animal_id: str) -> bool:
        """Hayvan sil"""
        try:
            self.data = [item for item in self.data if item.get("id") != animal_id]
            self.save_data()
            return True
        except Exception as e:
            print(f"Hata: {e}")
            return False
    
    def search_animals(self, query: str, filters: Dict[str, Any] = None) -> List[Animal]:
        """Hayvan ara ve filtrele"""
        results = self.data.copy()
        
        # Metin araması (isim, tür, renk ve RFID)
        if query:
            query_lower = query.lower()
            results = [
                item for item in results
                if query_lower in item.get("isim", "").lower() or
                   query_lower in item.get("tur", "").lower() or
                   query_lower in item.get("renk", "").lower() or
                   query_lower in str(item.get("rfid_tag", "")).lower()
            ]
        
        # Filtreleme
        if filters:
            if filters.get("tur"):
                results = [item for item in results if item.get("tur") == filters["tur"]]
            if filters.get("cinsiyet"):
                results = [item for item in results if item.get("cinsiyet") == filters["cinsiyet"]]
            if filters.get("saglik_durumu"):
                results = [item for item in results if item.get("saglik_durumu") == filters["saglik_durumu"]]
        
        return [Animal(item) for item in results]

    # -------- Fotoğraflar (yerel DB için stub implementasyonlar) --------

    def upload_photo(self, animal_id: str, local_file_path: Path, filename: str) -> Optional[str]:
        """
        Yerel veritabanı için yer tutucu: Dosyayı yüklemez, sadece yerel yolu döndürür.
        """
        return str(local_file_path)
    
    def delete_photo(self, animal_id: str, filename: str) -> bool:
        """
        Yerel veritabanı için: Dosya silme işlemi PhotoDialog'da yapılacak.
        """
        return True
    
    def list_photos(self, animal_id: str) -> List[Dict[str, Any]]:
        """
        Yerel veritabanı için: Fotoğraflar yerel dosya sisteminden okunacak.
        """
        return []

    # -------- Sağlık geçmişi (kilo + ateş) - Yerel DB için basit/no-op --------

    def add_health_log(
        self,
        animal_id: str,
        weight: Optional[float],
        temperature: Optional[float],
        measured_at: Optional[datetime] = None,
    ) -> bool:
        """
        Yerel veritabanında sağlık geçmişi tutulmuyor.
        Arayüz uyumluluğu için no-op.
        """
        return True

    def get_health_logs(self, animal_id: str, days: int = 7):
        """Yerel veritabanı için sağlık geçmişi yok, boş liste döner."""
        return []

