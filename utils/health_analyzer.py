"""
Rule-Based AI Engine for Animal Health Monitoring
Ateş kontrolü ve kilo kaybı analizi yapar
"""
from typing import Dict, Any, Optional
from models.animal import Animal


class HealthAnalyzer:
    """Hayvan sağlık durumunu analiz eden Rule-Based AI Engine"""
    
    # Kritik ateş yüksekliği eşiği (°C)
    CRITICAL_TEMPERATURE_THRESHOLD = 39.5
    # Kritik düşük ateş eşiği (hipotermi) (°C)
    LOW_TEMPERATURE_THRESHOLD = 36.0
    
    # Kilo kaybı uyarı eşiği (%)
    WEIGHT_LOSS_WARNING_THRESHOLD = 0.10  # %10
    
    @staticmethod
    def analyze_health(animal: Animal, current_temperature: Optional[float] = None, 
                       current_weight: Optional[float] = None) -> Dict[str, Any]:
        """
        Hayvan sağlık durumunu analiz eder
        
        Args:
            animal: Analiz edilecek hayvan
            current_temperature: Mevcut vücut sıcaklığı (°C)
            current_weight: Mevcut kilo (kg) - profil kilosuyla karşılaştırılacak
        
        Returns:
            Dict containing:
                - health_status: 'CRITICAL', 'WARNING', veya 'GOOD'
                - alerts: List of alert messages
                - temperature_status: Temperature analysis result
                - weight_status: Weight analysis result
        """
        alerts = []
        health_status = "GOOD"
        
        # 1. Ateş Kontrolü
        temperature_result = HealthAnalyzer._check_temperature(current_temperature)
        if temperature_result["status"] == "CRITICAL":
            health_status = "CRITICAL"
            alerts.append({
                "type": "CRITICAL",
                "message": f"⚠️ KRİTİK: Hayvanın vücut sıcaklığı {current_temperature}°C. Acil müdahale gerekiyor!",
                "icon": "🔥"
            })
        elif temperature_result["status"] == "WARNING":
            if health_status != "CRITICAL":
                health_status = "WARNING"
            alerts.append({
                "type": "WARNING",
                "message": f"⚠️ Uyarı: Hayvanın vücut sıcaklığı yüksek: {current_temperature}°C",
                "icon": "🌡️"
            })
        
        # 2. Kilo Kaybı Analizi
        weight_result = HealthAnalyzer._check_weight_loss(animal, current_weight)
        if weight_result["status"] == "WARNING":
            if health_status != "CRITICAL":
                health_status = "WARNING"
            alerts.append({
                "type": "WARNING",
                "message": f"⚠️ Uyarı: {weight_result['message']}",
                "icon": "⚖️"
            })
        
        return {
            "health_status": health_status,
            "alerts": alerts,
            "temperature_status": temperature_result,
            "weight_status": weight_result
        }
    
    @staticmethod
    def _check_temperature(temperature: Optional[float]) -> Dict[str, Any]:
        """
        Ateş kontrolü yapar
        
        Rules:
            - Temperature < 36.0°C  -> CRITICAL (çok düşük / hipotermi)
            - Temperature > 39.5°C  -> CRITICAL (çok yüksek ateş)
            - Temperature > 38.5°C  -> WARNING (yüksek ama kritik değil)
        """
        if temperature is None:
            return {
                "status": "UNKNOWN",
                "message": "Sıcaklık verisi bulunamadı",
                "temperature": None
            }
        
        # Çok düşük ateş (hipotermi)
        if temperature < HealthAnalyzer.LOW_TEMPERATURE_THRESHOLD:
            return {
                "status": "CRITICAL",
                "message": f"Çok düşük vücut sıcaklığı: {temperature}°C (Eşik: {HealthAnalyzer.LOW_TEMPERATURE_THRESHOLD}°C)",
                "temperature": temperature
            }
        # Çok yüksek ateş
        if temperature > HealthAnalyzer.CRITICAL_TEMPERATURE_THRESHOLD:
            return {
                "status": "CRITICAL",
                "message": f"Kritik ateş: {temperature}°C (Eşik: {HealthAnalyzer.CRITICAL_TEMPERATURE_THRESHOLD}°C)",
                "temperature": temperature
            }
        elif temperature > 38.5:  # Hafif yüksek ama kritik değil
            return {
                "status": "WARNING",
                "message": f"Yüksek sıcaklık: {temperature}°C",
                "temperature": temperature
            }
        else:
            return {
                "status": "GOOD",
                "message": f"Normal sıcaklık: {temperature}°C",
                "temperature": temperature
            }
    
    @staticmethod
    def _check_weight_loss(animal: Animal, current_weight: Optional[float]) -> Dict[str, Any]:
        """
        Kilo kaybı analizi yapar
        
        Rules:
            - Mevcut kilo, profil kilosundan %10 DÜŞÜKSE  -> WARNING
            - Mevcut kilo, profil kilosundan %10 YÜKSEKSE -> WARNING
            - Aksi durumda GOOD
        """
        if current_weight is None:
            return {
                "status": "UNKNOWN",
                "message": "Mevcut kilo verisi bulunamadı",
                "current_weight": None,
                "baseline_weight": None,
                "loss_percentage": None
            }
        
        # Profil kilosunu al (baseline_weight varsa onu kullan, yoksa kilo alanını kullan)
        baseline_weight = getattr(animal, 'baseline_weight', None)
        if baseline_weight is None or baseline_weight == 0:
            # Eğer baseline_weight yoksa, mevcut kilo alanını baseline olarak kullan
            baseline_weight = float(animal.kilo) if animal.kilo else None
        
        if baseline_weight is None or baseline_weight == 0:
            return {
                "status": "UNKNOWN",
                "message": "Profil kilosu bulunamadı",
                "current_weight": current_weight,
                "baseline_weight": None,
                "loss_percentage": None
            }
        
        # Kilo değişim oranını hesapla
        ratio = current_weight / baseline_weight
        change_percentage = (abs(ratio - 1.0)) * 100
        threshold_pct = HealthAnalyzer.WEIGHT_LOSS_WARNING_THRESHOLD * 100

        # Profil kilosundan %10'dan fazla DÜŞÜŞ
        if ratio <= (1.0 - HealthAnalyzer.WEIGHT_LOSS_WARNING_THRESHOLD):
            return {
                "status": "WARNING",
                "message": (
                    f"Kilo kaybı tespit edildi: {current_weight:.1f} kg "
                    f"(Profil: {baseline_weight:.1f} kg, Kayıp: %{change_percentage:.1f})"
                ),
                "current_weight": current_weight,
                "baseline_weight": baseline_weight,
                "change_percentage": change_percentage,
                "direction": "LOSS",
            }

        # Profil kilosundan %10'dan fazla ARTIŞ
        if ratio >= (1.0 + HealthAnalyzer.WEIGHT_LOSS_WARNING_THRESHOLD):
            return {
                "status": "WARNING",
                "message": (
                    f"Kilo artışı tespit edildi: {current_weight:.1f} kg "
                    f"(Profil: {baseline_weight:.1f} kg, Artış: %{change_percentage:.1f})"
                ),
                "current_weight": current_weight,
                "baseline_weight": baseline_weight,
                "change_percentage": change_percentage,
                "direction": "GAIN",
            }

        # Normal aralık
        return {
            "status": "GOOD",
            "message": f"Kilo normal: {current_weight:.1f} kg (Profil: {baseline_weight:.1f} kg)",
            "current_weight": current_weight,
            "baseline_weight": baseline_weight,
            "change_percentage": change_percentage,
            "direction": "STABLE",
        }
    
    @staticmethod
    def update_animal_health_status(animal: Animal, temperature: Optional[float] = None,
                                     current_weight: Optional[float] = None) -> Animal:
        """
        Hayvanın sağlık durumunu analiz edip günceller
        
        Returns:
            Güncellenmiş Animal objesi
        """
        analysis = HealthAnalyzer.analyze_health(animal, temperature, current_weight)
        
        # Health status'u güncelle
        if analysis["health_status"] == "CRITICAL":
            animal.saglik_durumu = "KRİTİK"
        elif analysis["health_status"] == "WARNING":
            if animal.saglik_durumu != "KRİTİK":
                animal.saglik_durumu = "UYARI"
        else:
            # Eğer önceki durum kritik veya uyarı değilse, "İyi" olarak ayarla
            if animal.saglik_durumu not in ["KRİTİK", "UYARI"]:
                animal.saglik_durumu = "İyi"
        
        return animal

