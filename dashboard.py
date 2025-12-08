import sys
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QListWidget, 
                             QListWidgetItem, QComboBox, QGroupBox, QGridLayout, QTextEdit,
                             QDialog, QDialogButtonBox, QFormLayout, QFileDialog, QDateEdit,
                             QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp, QDate
from PyQt5.QtGui import QFont, QColor, QRegExpValidator, QPixmap
from database import get_database
from models.animal import Animal
from config import APP_CONFIG, ANIMAL_TYPES, GENDERS
from utils.validators import validate_animal_data

class Dashboard(QMainWindow):
    def __init__(self, username, on_logout=None):
        super().__init__()
        self.username = username
        self.on_logout = on_logout
        self.db = get_database()
        self.db.connect()
        self.selected_animal_id = None
        
        self.setWindowTitle(f"{APP_CONFIG['title']} - Admin Dashboard")
        self.setMinimumSize(APP_CONFIG['width'], APP_CONFIG['height'])
        
        # Pencereyi ortala
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - APP_CONFIG['width']) // 2,
            (screen.height() - APP_CONFIG['height']) // 2
        )
        
        self.init_ui()
        self.load_animal_list()
    
    def init_ui(self):
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #2c3e50;")
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title_label = QLabel(APP_CONFIG['title'])
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        user_label = QLabel(f"Hoş geldiniz, {self.username}")
        user_label.setFont(QFont("Arial", 12))
        user_label.setStyleSheet("color: white; margin-right: 15px;")
        header_layout.addWidget(user_label)

        logout_btn = QPushButton("Çıkış Yap")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        
        main_layout.addWidget(header)
        
        # Ana içerik
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # Sol panel
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 0)
        
        # Sağ panel
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(content_layout)
    
    def create_left_panel(self):
        """Sol paneli oluştur"""
        panel = QWidget()
        panel.setStyleSheet("background-color: white; border: 2px solid #ddd; border-radius: 5px;")
        panel.setFixedWidth(350)
        layout = QVBoxLayout()
        panel.setLayout(layout)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Arama bölümü
        search_label = QLabel("Ara:")
        search_label.setFont(QFont("Arial", 11, QFont.Bold))
        search_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(search_label)
        
        self.search_entry = QLineEdit()
        self.search_entry.setFont(QFont("Arial", 11))
        self.search_entry.setPlaceholderText("İsim, tür veya renk ara...")
        self.search_entry.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                color: black;
            }
        """)
        self.search_entry.textChanged.connect(self.on_search)
        layout.addWidget(self.search_entry)
        
        # Filtreler
        filter_group = QGroupBox("Filtreler")
        filter_group.setFont(QFont("Arial", 11, QFont.Bold))
        filter_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ecf0f1;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        filter_layout = QVBoxLayout()
        filter_group.setLayout(filter_layout)
        filter_layout.setSpacing(8)
        
        # Tür filtresi
        type_label = QLabel("Tür:")
        type_label.setFont(QFont("Arial", 10))
        type_label.setStyleSheet("color: #34495e;")
        filter_layout.addWidget(type_label)
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Tümü"] + ANIMAL_TYPES)
        self.filter_type.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.filter_type.currentTextChanged.connect(self.on_filter)
        filter_layout.addWidget(self.filter_type)
        
        # Cinsiyet filtresi
        gender_label = QLabel("Cinsiyet:")
        gender_label.setFont(QFont("Arial", 10))
        gender_label.setStyleSheet("color: #34495e;")
        filter_layout.addWidget(gender_label)
        
        self.filter_gender = QComboBox()
        self.filter_gender.addItems(["Tümü"] + GENDERS)
        self.filter_gender.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.filter_gender.currentTextChanged.connect(self.on_filter)
        filter_layout.addWidget(self.filter_gender)
        
        layout.addWidget(filter_group)
        
        # Liste başlığı
        list_label = QLabel("Hayvan Listesi")
        list_label.setFont(QFont("Arial", 14, QFont.Bold))
        list_label.setStyleSheet("color: #2c3e50; padding-top: 5px;")
        layout.addWidget(list_label)
        
        # Hayvan listesi
        self.animal_list = QListWidget()
        self.animal_list.setFont(QFont("Arial", 11))
        self.animal_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ecf0f1;
                border-radius: 4px;
                background-color: #fafafa;
                color: black;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
                color: black;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
                color: black;
            }
        """)
        self.animal_list.itemClicked.connect(self.on_animal_select)
        layout.addWidget(self.animal_list, 1)
        
        # Butonlar
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        
        add_btn = QPushButton("+ Yeni Hayvan")
        add_btn.setFont(QFont("Arial", 11, QFont.Bold))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        add_btn.clicked.connect(self.add_animal)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Düzenle")
        edit_btn.setFont(QFont("Arial", 11))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        # Buton metnini düzelt
        edit_btn.setText("Düzenle")
        edit_btn.clicked.connect(self.edit_animal)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Sil")
        delete_btn.setFont(QFont("Arial", 11))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.clicked.connect(self.delete_animal)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_right_panel(self):
        """Sağ paneli oluştur"""
        panel = QWidget()
        panel.setStyleSheet("background-color: white; border: 2px solid #ddd;")
        layout = QVBoxLayout()
        panel.setLayout(layout)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        # Başlık
        detail_label = QLabel("Hayvan Detayları")
        detail_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(detail_label)
        
        # Detay alanı (scrollable)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout()
        self.detail_widget.setLayout(self.detail_layout)
        
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(self.detail_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        layout.addWidget(scroll, 1)
        
        self.show_welcome_message()
        
        return panel
    
    def load_animal_list(self, animals=None):
        """Hayvan listesini yükle"""
        if animals is None:
            animals = self.db.get_all_animals()
        
        self.animal_list.clear()
        for animal in animals:
            item_text = f"{animal.isim} - {animal.tur} ({animal.cinsiyet})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, animal.id)
            self.animal_list.addItem(item)
    
    def on_search(self):
        """Arama yap"""
        query = self.search_entry.text()
        filters = self.get_filters()
        results = self.db.search_animals(query, filters)
        self.load_animal_list(results)
    
    def on_filter(self):
        """Filtre uygula"""
        self.on_search()
    
    def get_filters(self):
        """Aktif filtreleri döndür"""
        filters = {}
        if self.filter_type.currentText() != "Tümü":
            filters["tur"] = self.filter_type.currentText()
        if self.filter_gender.currentText() != "Tümü":
            filters["cinsiyet"] = self.filter_gender.currentText()
        return filters
    
    def on_animal_select(self, item):
        """Hayvan seçildiğinde"""
        animal_id = item.data(Qt.UserRole)
        self.selected_animal_id = animal_id
        animal = self.db.get_animal_by_id(animal_id)
        if animal:
            self.show_animal_details(animal)
    
    def show_welcome_message(self):
        """Hoş geldin mesajı"""
        self.clear_details()
        
        welcome_label = QLabel("Lütfen listeden bir hayvan seçin veya yeni hayvan ekleyin")
        welcome_label.setFont(QFont("Arial", 12))
        welcome_label.setStyleSheet("color: #7f8c8d;")
        welcome_label.setAlignment(Qt.AlignCenter)
        self.detail_layout.addWidget(welcome_label)
        self.detail_layout.addStretch()
    
    def clear_details(self):
        """Detay alanını temizle"""
        while self.detail_layout.count():
            child = self.detail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_animal_details(self, animal: Animal):
        """Hayvan detaylarını göster"""
        self.clear_details()
        
        # Hayvan adı
        name_label = QLabel(animal.isim)
        name_label.setFont(QFont("Arial", 20, QFont.Bold))
        name_label.setStyleSheet("color: #2c3e50;")
        self.detail_layout.addWidget(name_label)
        
        # Detay bilgileri
        info_grid = QGridLayout()
        info_grid.setSpacing(10)
        
        info_items = [
            ("RFID", animal.rfid_tag or "Belirtilmemiş"),
            ("Tür", animal.tur),
            ("Yaş", f"{animal.yas} yaşında"),
            ("Kilo", f"{animal.kilo} kg"),
            ("Boy", f"{animal.boy} cm"),
            ("Cinsiyet", animal.cinsiyet),
            ("Renk", animal.renk),
            ("Doğum Tarihi", animal.dogum_tarihi or "Belirtilmemiş"),
            ("Sağlık Durumu", animal.saglik_durumu),
        ]
        
        for i, (label, value) in enumerate(info_items):
            # Label
            label_widget = QLabel(label + ":")
            label_widget.setFont(QFont("Arial", 10))
            label_widget.setStyleSheet("color: #7f8c8d;")
            info_grid.addWidget(label_widget, i // 2, (i % 2) * 2)
            
            # Value
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Arial", 14, QFont.Bold))
            value_widget.setStyleSheet("color: #2c3e50; background-color: #ecf0f1; padding: 10px; border-radius: 5px;")
            info_grid.addWidget(value_widget, i // 2, (i % 2) * 2 + 1)
        
        info_widget = QWidget()
        info_widget.setLayout(info_grid)
        self.detail_layout.addWidget(info_widget)
        
        # Notlar
        if animal.notlar:
            notes_label = QLabel("Notlar:")
            notes_label.setFont(QFont("Arial", 11, QFont.Bold))
            notes_label.setStyleSheet("color: #2c3e50;")
            self.detail_layout.addWidget(notes_label)
            
            notes_text = QLabel(animal.notlar)
            notes_text.setFont(QFont("Arial", 10))
            notes_text.setWordWrap(True)
            notes_text.setStyleSheet("background-color: #fafafa; color: black; padding: 10px; border-radius: 5px;")
            self.detail_layout.addWidget(notes_text)
    
    def add_animal(self):
        """Yeni hayvan ekle"""
        dialog = AnimalDialog(self, "Yeni Hayvan Ekle")
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            animal = Animal(dialog.result)
            if self.db.add_animal(animal):
                QMessageBox.information(self, "Başarılı", "Hayvan başarıyla eklendi!")
                self.on_search()
            else:
                QMessageBox.critical(self, "Hata", "Hayvan eklenirken bir hata oluştu!")
    
    def edit_animal(self):
        """Hayvan düzenle"""
        if not self.selected_animal_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için bir hayvan seçin!")
            return
        
        animal = self.db.get_animal_by_id(self.selected_animal_id)
        if not animal:
            QMessageBox.critical(self, "Hata", "Hayvan bulunamadı!")
            return
        
        dialog = AnimalDialog(self, "Hayvan Düzenle", animal.to_dict())
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            updated_animal = Animal(dialog.result)
            if self.db.update_animal(self.selected_animal_id, updated_animal):
                QMessageBox.information(self, "Başarılı", "Hayvan başarıyla güncellendi!")
                self.on_search()
                updated_animal = self.db.get_animal_by_id(self.selected_animal_id)
                if updated_animal:
                    self.show_animal_details(updated_animal)
            else:
                QMessageBox.critical(self, "Hata", "Hayvan güncellenirken bir hata oluştu!")
    
    def delete_animal(self):
        """Hayvan sil"""
        if not self.selected_animal_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir hayvan seçin!")
            return
        
        animal = self.db.get_animal_by_id(self.selected_animal_id)
        if not animal:
            QMessageBox.critical(self, "Hata", "Hayvan bulunamadı!")
            return
        
        reply = QMessageBox.question(
            self, "Onay", 
            f"'{animal.isim}' adlı hayvanı silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.delete_animal(self.selected_animal_id):
                QMessageBox.information(self, "Başarılı", "Hayvan başarıyla silindi!")
                self.selected_animal_id = None
                self.on_search()
                self.show_welcome_message()
            else:
                QMessageBox.critical(self, "Hata", "Hayvan silinirken bir hata oluştu!")

    def logout(self):
        """Oturumu kapat ve pencereyi kapat."""
        reply = QMessageBox.question(
            self,
            "Çıkış",
            "Uygulamadan çıkmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if hasattr(self, "db") and self.db:
                self.db.disconnect()
            self.close()
            if callable(self.on_logout):
                self.on_logout()
    
    def run(self):
        self.show()     
class AnimalDialog(QDialog):
    """Hayvan ekleme/düzenleme dialog penceresi"""
    
    def __init__(self, parent, title, data=None):
        super().__init__(parent)
        self.result = None
        self.setWindowTitle(title)
        self.setMinimumSize(500, 600)
        
        # Pencereyi ortala
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 500) // 2,
            (screen.height() - 600) // 2
        )
        
        self.init_ui(data or {})
    
    def init_ui(self, data):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Ortak stil
        input_style = """
            QLineEdit, QComboBox, QTextEdit {
                color: black;
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #3498db;
                color: black;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        
        form_layout = QFormLayout()

        # RFID Tag
        self.rfid_entry = QLineEdit()
        self.rfid_entry.setText(data.get("rfid_tag", ""))
        self.rfid_entry.setStyleSheet(input_style)
        form_layout.addRow("RFID Tag *:", self.rfid_entry)
        
        # İsim
        self.isim_entry = QLineEdit()
        self.isim_entry.setText(data.get("isim", ""))
        self.isim_entry.setStyleSheet(input_style)
        form_layout.addRow("İsim *:", self.isim_entry)
        
        # Tür
        self.tur_combo = QComboBox()
        self.tur_combo.addItems(ANIMAL_TYPES)
        self.tur_combo.setStyleSheet(input_style)
        if data.get("tur"):
            index = self.tur_combo.findText(data.get("tur"))
            if index >= 0:
                self.tur_combo.setCurrentIndex(index)
        form_layout.addRow("Tür *:", self.tur_combo)
        
        # Yaş - sadece sayı
        self.yas_entry = QLineEdit()
        self.yas_entry.setText(str(data.get("yas", "")))
        self.yas_entry.setStyleSheet(input_style)
        # Sadece sayı kabul et
        yas_validator = QRegExpValidator(QRegExp(r'^\d+$'))
        self.yas_entry.setValidator(yas_validator)
        form_layout.addRow("Yaş *:", self.yas_entry)
        
        # Kilo - sadece sayı (ondalıklı)
        self.kilo_entry = QLineEdit()
        self.kilo_entry.setText(str(data.get("kilo", "")))
        self.kilo_entry.setStyleSheet(input_style)
        # Sadece sayı kabul et (ondalıklı olabilir)
        kilo_validator = QRegExpValidator(QRegExp(r'^\d+\.?\d*$'))
        self.kilo_entry.setValidator(kilo_validator)
        form_layout.addRow("Kilo (kg) *:", self.kilo_entry)
        
        # Boy - sadece sayı (ondalıklı)
        self.boy_entry = QLineEdit()
        self.boy_entry.setText(str(data.get("boy", "")))
        self.boy_entry.setStyleSheet(input_style)
        # Sadece sayı kabul et (ondalıklı olabilir)
        boy_validator = QRegExpValidator(QRegExp(r'^\d+\.?\d*$'))
        self.boy_entry.setValidator(boy_validator)
        form_layout.addRow("Boy (cm) *:", self.boy_entry)
        
        # Cinsiyet
        self.cinsiyet_combo = QComboBox()
        self.cinsiyet_combo.addItems(GENDERS)
        self.cinsiyet_combo.setStyleSheet(input_style)
        if data.get("cinsiyet"):
            index = self.cinsiyet_combo.findText(data.get("cinsiyet"))
            if index >= 0:
                self.cinsiyet_combo.setCurrentIndex(index)
        form_layout.addRow("Cinsiyet *:", self.cinsiyet_combo)
        
        # Renk - sadece harf (sayı kabul etme)
        self.renk_entry = QLineEdit()
        self.renk_entry.setText(data.get("renk", ""))
        self.renk_entry.setStyleSheet(input_style)
        # Sadece harf ve boşluk kabul et (sayı yok)
        renk_validator = QRegExpValidator(QRegExp(r'^[a-zA-ZğüşıöçĞÜŞİÖÇ\s]+$'))
        self.renk_entry.setValidator(renk_validator)
        form_layout.addRow("Renk:", self.renk_entry)
        
        # Doğum Tarihi - gün.ay.yıl formatı
        self.dogum_tarihi_entry = QLineEdit()
        self.dogum_tarihi_entry.setText(data.get("dogum_tarihi", ""))
        self.dogum_tarihi_entry.setStyleSheet(input_style)
        self.dogum_tarihi_entry.setPlaceholderText("gg.aa.yyyy (örn: 15.03.2020)")
        # Tarih formatı: gün.ay.yıl (sadece sayı değil, nokta ile ayrılmış)
        tarih_validator = QRegExpValidator(QRegExp(r'^\d{1,2}\.\d{1,2}\.\d{4}$'))
        self.dogum_tarihi_entry.setValidator(tarih_validator)
        form_layout.addRow("Doğum Tarihi (gg.aa.yyyy):", self.dogum_tarihi_entry)
        
        # Sağlık Durumu
        self.saglik_durumu_entry = QLineEdit()
        self.saglik_durumu_entry.setText(data.get("saglik_durumu", "İyi"))
        self.saglik_durumu_entry.setStyleSheet(input_style)
        form_layout.addRow("Sağlık Durumu:", self.saglik_durumu_entry)
        
        # Notlar
        self.notlar_text = QTextEdit()
        self.notlar_text.setPlainText(data.get("notlar", ""))
        self.notlar_text.setMaximumHeight(100)
        self.notlar_text.setStyleSheet(input_style)
        form_layout.addRow("Notlar:", self.notlar_text)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def save(self):
        """Form verilerini kaydet"""
        data = {
            "rfid_tag": self.rfid_entry.text(),
            "isim": self.isim_entry.text(),
            "yas": self.yas_entry.text(),
            "kilo": self.kilo_entry.text(),
            "boy": self.boy_entry.text(),
            "cinsiyet": self.cinsiyet_combo.currentText(),
            "tur": self.tur_combo.currentText(),
            "renk": self.renk_entry.text(),
            "dogum_tarihi": self.dogum_tarihi_entry.text(),
            "saglik_durumu": self.saglik_durumu_entry.text(),
            "notlar": self.notlar_text.toPlainText()
        }
        
        is_valid, error_msg = validate_animal_data(data)
        if not is_valid:
            QMessageBox.critical(self, "Hata", error_msg)
            return
        
        self.result = data
        self.accept()
