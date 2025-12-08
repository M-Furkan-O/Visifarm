from datetime import datetime
from typing import Optional, Dict, Any

class Animal:
    def __init__(self, data: Dict[str, Any] = None):
        # DB (Supabase) alanları ile eski yerel alanları eşle
        self.id = data.get("id") if data else None
        self.rfid_tag = data.get("rfid_tag") if data else data.get("rfid") if data else None
        self.isim = (data.get("isim") if data else "") or (data.get("name") if data else "") or ""
        self.yas = (data.get("yas") if data else 0) or (data.get("age") if data else 0) or 0
        self.kilo = (data.get("kilo") if data else 0.0) or (data.get("weight") if data else 0.0) or 0.0
        self.boy = (data.get("boy") if data else 0.0) or (data.get("height") if data else 0.0) or 0.0
        self.cinsiyet = (data.get("cinsiyet") if data else "") or (data.get("gender") if data else "") or ""
        self.tur = (data.get("tur") if data else "") or (data.get("animal_type") if data else "") or ""
        self.renk = data.get("renk", "") if data else ""
        self.dogum_tarihi = data.get("dogum_tarihi", "") if data else ""
        self.saglik_durumu = data.get("saglik_durumu", "İyi") if data else "İyi"
        self.notlar = data.get("notlar", "") if data else ""
        self.olusturma_tarihi = data.get("olusturma_tarihi") if data else data.get("created_at") if data else datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Hayvan verisini dictionary'ye çevir"""
        return {
            "id": self.id,
            "rfid_tag": self.rfid_tag,
            "isim": self.isim,
            "yas": self.yas,
            "kilo": self.kilo,
            "boy": self.boy,
            "cinsiyet": self.cinsiyet,
            "tur": self.tur,
            "renk": self.renk,
            "dogum_tarihi": self.dogum_tarihi,
            "saglik_durumu": self.saglik_durumu,
            "notlar": self.notlar,
            "olusturma_tarihi": self.olusturma_tarihi
        }
    
    def __str__(self):
        return f"{self.isim} ({self.tur})"

