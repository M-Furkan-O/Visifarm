from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.animal import Animal
from pathlib import Path

class BaseDatabase(ABC):
    """Veritabanı için abstract base class - Supabase entegrasyonu için hazır"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Veritabanına bağlan"""
        pass
    
    @abstractmethod
    def get_all_animals(self) -> List[Animal]:
        """Tüm hayvanları getir"""
        pass
    
    @abstractmethod
    def get_animal_by_id(self, animal_id: str) -> Optional[Animal]:
        """ID'ye göre hayvan getir"""
        pass
    
    @abstractmethod
    def add_animal(self, animal: Animal) -> bool:
        """Yeni hayvan ekle"""
        pass
    
    @abstractmethod
    def update_animal(self, animal_id: str, animal: Animal) -> bool:
        """Hayvan güncelle"""
        pass
    
    @abstractmethod
    def delete_animal(self, animal_id: str) -> bool:
        """Hayvan sil"""
        pass
    
    @abstractmethod
    def search_animals(self, query: str, filters: Dict[str, Any] = None) -> List[Animal]:
        """Hayvan ara ve filtrele"""
        pass

    @abstractmethod
    def upload_photo(self, animal_id: str, local_file_path: Path, filename: str) -> Optional[str]:
        """Yerel dosyayı buluta yükle ve genel URL'sini döndür."""
        pass
    
    @abstractmethod
    def delete_photo(self, animal_id: str, filename: str) -> bool:
        """Buluttan fotoğrafı sil."""
        pass
    
    @abstractmethod
    def list_photos(self, animal_id: str) -> List[Dict[str, Any]]:
        """Bir hayvana ait tüm fotoğrafları listele."""
        pass