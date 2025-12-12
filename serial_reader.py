from PyQt5.QtCore import QThread, pyqtSignal
import serial
import serial.tools.list_ports
import time

class SerialReader(QThread):
    rfid_read = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_running = True
        self.port = self.find_arduino()

    def find_arduino(self):
        print("--- PORT TARAMASI BAŞLADI ---")
        ports = list(serial.tools.list_ports.comports())
        found_port = None
        
        # Tüm portları yazdır (Görmemiz için)
        for p in ports:
            print(f"Bulunan Cihaz: {p.device} - {p.description}")
            
            # Mac için usbserial veya usbmodem
            if "usbmodem" in p.device or "usbserial" in p.device or \
               "Arduino" in p.description or "CH340" in p.description:
                found_port = p.device
        
        if found_port:
            print(f"--> SEÇİLEN PORT: {found_port}")
        else:
            print("--> HİÇBİR UYGUN PORT BULUNAMADI!")
            
        print("-------------------------------")
        return found_port

    def run(self):
        if not self.port:
            self.error_occurred.emit("Arduino bulunamadı! Kabloyu kontrol edin.")
            print("HATA: Port yok, işlem iptal edildi.")
            return

        print(f"BAĞLANTI BAŞLATILIYOR: {self.port} @ 9600 baud")
        try:
            with serial.Serial(self.port, 9600, timeout=1) as ser:
                time.sleep(2) # Reset için bekle
                print("BAĞLANTI BAŞARILI! Veri bekleniyor...")
                
                ser.reset_input_buffer()
                
                while self.is_running:
                    if ser.in_waiting > 0:
                        try:
                            # Gelen ham veriyi oku
                            raw_data = ser.readline()
                            line = raw_data.decode('utf-8', errors='ignore').strip()
                            
                            # Terminale ne duyduğunu yazsın
                            print(f"GELEN VERİ: '{line}'")
                            
                            # Filtreleme (Boş veya gereksiz verileri atla)
                            if not line or len(line) < 4:
                                continue
                                
                            print(f"--> GEÇERLİ ID BULUNDU: {line}")
                            self.rfid_read.emit(line)
                            break 
                        except Exception as e:
                            print(f"Okuma Hatası: {e}")
                            continue
                    time.sleep(0.1)
        except Exception as e:
            error_msg = f"Bağlantı Hatası: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
    
    def stop(self):
        self.is_running = False
        print("Okuyucu durduruldu.")
        self.wait()