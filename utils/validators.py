def validate_animal_data(data: dict) -> tuple[bool, str]:
    """Hayvan verilerini doğrula"""
    required_fields = ["rfid_tag", "isim", "yas", "kilo", "boy", "cinsiyet", "tur"]
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"{field} alanı zorunludur!"
    
    # Sayısal alanları kontrol et
    try:
        yas = int(data["yas"])
        if yas < 0 or yas > 50:
            return False, "Yaş 0-50 arasında olmalıdır!"
    except:
        return False, "Yaş geçerli bir sayı olmalıdır!"
    
    try:
        kilo = float(data["kilo"])
        if kilo < 0 or kilo > 2000:
            return False, "Kilo 0-2000 kg arasında olmalıdır!"
    except:
        return False, "Kilo geçerli bir sayı olmalıdır!"
    
    try:
        boy = float(data["boy"])
        if boy < 0 or boy > 300:
            return False, "Boy 0-300 cm arasında olmalıdır!"
    except:
        return False, "Boy geçerli bir sayı olmalıdır!"
    
    return True, ""

