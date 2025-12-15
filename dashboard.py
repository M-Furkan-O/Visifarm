import sys
from pathlib import Path
from typing import Dict, Any
from serial_reader import SerialReader
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QListWidget, 
                             QListWidgetItem, QComboBox, QGroupBox, QGridLayout, QTextEdit,
                             QDialog, QDialogButtonBox, QFormLayout, QFileDialog, QDateEdit,
                             QScrollArea)
from PyQt5.QtCore import Qt, QRegExp, QDate
from PyQt5.QtGui import QFont, QRegExpValidator, QPixmap
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
        self.rfid_reader_thread = None  # RFID okuma thread'i için
        
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
        
        # Arama kutusu ve RFID butonu için horizontal layout
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.search_entry = QLineEdit()
        self.search_entry.setFont(QFont("Arial", 11))
        self.search_entry.setPlaceholderText("İsim, tür, renk veya RFID ara...")
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
        search_layout.addWidget(self.search_entry, 1)
        
        # RFID okuma butonu
        self.rfid_search_btn = QPushButton("📡 RFID Oku")
        self.rfid_search_btn.setFont(QFont("Arial", 10))
        self.rfid_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #ecf0f1;
            }
        """)
        self.rfid_search_btn.clicked.connect(self.start_rfid_search)
        search_layout.addWidget(self.rfid_search_btn)
        
        layout.addLayout(search_layout)
        
        # RFID reader thread için değişken
        self.rfid_reader_thread = None
        
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
    
    def start_rfid_search(self):
        """RFID okuma işlemini başlat"""
        # Eğer zaten bir okuma işlemi varsa durdur
        if self.rfid_reader_thread and self.rfid_reader_thread.isRunning():
            self.rfid_reader_thread.stop()
            self.rfid_reader_thread.wait()
        
        # Butonu devre dışı bırak
        self.rfid_search_btn.setEnabled(False)
        self.rfid_search_btn.setText("Okunuyor...")
        
        # Yeni reader thread oluştur
        self.rfid_reader_thread = SerialReader()
        self.rfid_reader_thread.rfid_read.connect(self.on_rfid_search_found)
        self.rfid_reader_thread.error_occurred.connect(self.on_rfid_search_error)
        self.rfid_reader_thread.start()
    
    def on_rfid_search_found(self, rfid_id):
        """RFID okunduğunda arama kutusuna yaz ve ara"""
        # Thread'i durdur
        if self.rfid_reader_thread:
            self.rfid_reader_thread.stop()
            self.rfid_reader_thread.wait()
            self.rfid_reader_thread = None
        
        # Butonu tekrar aktif et
        self.rfid_search_btn.setEnabled(True)
        self.rfid_search_btn.setText("📡 RFID Oku")
        
        # RFID'yi arama kutusuna yaz (otomatik arama yapılacak textChanged signal ile)
        self.search_entry.setText(rfid_id)
        self.search_entry.setFocus()
        
        # Başarı mesajı
        QMessageBox.information(self, "RFID Okundu", f"RFID: {rfid_id}\nArama yapılıyor...")
    
    def on_rfid_search_error(self, error_msg):
        """RFID okuma hatası"""
        # Thread'i durdur
        if self.rfid_reader_thread:
            self.rfid_reader_thread.stop()
            self.rfid_reader_thread.wait()
            self.rfid_reader_thread = None
        
        # Butonu tekrar aktif et
        self.rfid_search_btn.setEnabled(True)
        self.rfid_search_btn.setText("📡 RFID Oku")
        
        # Hata mesajı
        QMessageBox.warning(self, "RFID Okuma Hatası", error_msg)
    
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
        
        photos_btn = QPushButton("Fotoğraflar")
        photos_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7d3c98; }
        """)
        photos_btn.clicked.connect(lambda: self.open_photo_dialog(animal))
        self.detail_layout.addSpacing(10)
        self.detail_layout.addWidget(photos_btn)
        
        self.detail_layout.addStretch()
    
    def open_photo_dialog(self, animal: Animal):
        """Seçili hayvan için fotoğraf yöneticisini aç."""
        dialog = PhotoDialog(self, animal)
        dialog.exec_()
    
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
            # RFID thread'i durdur
            if hasattr(self, "rfid_reader_thread") and self.rfid_reader_thread:
                if self.rfid_reader_thread.isRunning():
                    self.rfid_reader_thread.stop()
                    self.rfid_reader_thread.wait()
            
            if hasattr(self, "db") and self.db:
                self.db.disconnect()
            self.close()
            if callable(self.on_logout):
                self.on_logout()
    



class PhotoDialog(QDialog):
    def __init__(self, parent, animal):
        super().__init__(parent)
        self.animal = animal
        # Parent'tan veritabanı bağlantısını al
        self.db = parent.db if hasattr(parent, 'db') else None
        self.setWindowTitle(f"{animal.isim} - Fotoğraflar")
        self.setMinimumSize(800, 600)
        
        # Fotoğraflar artık sadece Supabase'de tutulacak
        self.photos_by_date = {}
        self._init_ui()
        self.load_photos()

    def _init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Sol panel (tarih listesi)
        left_layout = QVBoxLayout()
        date_label = QLabel("Tarihler:")
        date_label.setFont(QFont("Arial", 11, QFont.Bold))
        left_layout.addWidget(date_label)
        
        self.date_list = QListWidget()
        self.date_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
        """)
        self.date_list.itemClicked.connect(self.on_date_selected)
        left_layout.addWidget(self.date_list, 1)
        
        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)

        # Sağ panel (ekle ve görüntüle)
        right_layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.date_input.setCalendarPopup(True)
        control_layout.addWidget(QLabel("Tarih:"))
        control_layout.addWidget(self.date_input)

        add_btn = QPushButton("Fotoğraf Ekle")
        add_btn.clicked.connect(self.add_photo)
        control_layout.addWidget(add_btn)
        right_layout.addLayout(control_layout)

        self.photos_scroll = QScrollArea()
        self.photos_scroll.setWidgetResizable(True)
        self.photo_container = QWidget()
        self.photo_layout = QVBoxLayout()
        self.photo_layout.setAlignment(Qt.AlignTop)
        self.photo_container.setLayout(self.photo_layout)
        self.photos_scroll.setWidget(self.photo_container)
        right_layout.addWidget(self.photos_scroll, 1)

        main_layout.addLayout(right_layout, 2)

    def add_photo(self):
        """Fotoğraf ekleme dialogunu aç ve sadece Supabase'e yükle"""
        if not self.db or not self.animal.id:
            QMessageBox.warning(self, "Uyarı", "Veritabanı bağlantısı yok veya hayvan ID'si bulunamadı!")
            return
        
        selected_date = self.date_input.date().toString("yyyy-MM-dd")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Fotoğraf Seç",
            "",
            "Resim Dosyaları (*.jpg *.jpeg *.png *.bmp *.gif);;Tüm Dosyalar (*)"
        )
        
        if file_path:
            # Dosya adını oluştur: yyyy-MM-dd_originalname.jpg
            source_path = Path(file_path)
            date_prefix = selected_date
            new_filename = f"{date_prefix}_{source_path.name}"
            
            try:
                # Sadece Supabase'e yükle (yerel dosyaya kaydetme)
                photo_url = self.db.upload_photo(
                    animal_id=str(self.animal.id),
                    local_file_path=source_path,
                    filename=new_filename
                )
                
                if photo_url:
                    QMessageBox.information(self, "Başarılı", f"Fotoğraf Supabase'e yüklendi!")
                    # Fotoğrafları yeniden yükle
                    self.load_photos()
                    # Eklenen tarihi seç
                    self._select_date(selected_date)
                else:
                    QMessageBox.critical(self, "Hata", "Fotoğraf Supabase'e yüklenemedi!")
                    
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Fotoğraf eklenirken hata oluştu: {str(e)}")

    def load_photos(self):
        """Supabase'den fotoğrafları yükle ve tarihe göre grupla."""
        self.photos_by_date = {}
        
        if not self.db or not self.animal.id:
            self._populate_dates()
            return
        
        try:
            # Supabase'den fotoğraf listesini al
            photos = self.db.list_photos(str(self.animal.id))
            
            # Fotoğrafları tarihe göre grupla
            for photo in photos:
                date_iso = photo.get('date') or self._extract_date(photo.get('name', ''))
                if date_iso not in self.photos_by_date:
                    self.photos_by_date[date_iso] = []
                self.photos_by_date[date_iso].append(photo)
            
            # Tarihleri doldur
            self._populate_dates()
        except Exception as e:
            print(f"Fotoğraf yükleme hatası: {e}")
            QMessageBox.warning(self, "Uyarı", f"Fotoğraflar yüklenirken hata oluştu: {str(e)}")
            self._populate_dates()
    
    def _extract_date(self, filename: str) -> str:
        """Dosya adından ISO tarih çıkar (yyyy-MM-dd), yoksa bugünün tarihi."""
        if len(filename) >= 10:
            prefix = filename[:10]
            if QDate.fromString(prefix, "yyyy-MM-dd").isValid():
                return prefix
        return QDate.currentDate().toString("yyyy-MM-dd")
    
    def _populate_dates(self):
        self.date_list.clear()
        for date_iso in sorted(self.photos_by_date.keys()):
            item = QListWidgetItem(QDate.fromString(date_iso, "yyyy-MM-dd").toString("dd.MM.yyyy"))
            item.setData(Qt.UserRole, date_iso)
            self.date_list.addItem(item)
        
        if self.date_list.count() > 0:
            self.date_list.setCurrentRow(self.date_list.count() - 1)
            self.show_photos_for(self.date_list.currentItem().data(Qt.UserRole))
        else:
            self.show_photos_for(None)
    
    def on_date_selected(self, item: QListWidgetItem):
        date_iso = item.data(Qt.UserRole)
        self.show_photos_for(date_iso)
    
    def show_photos_for(self, date_iso: str):
        """Seçili tarihe ait fotoğrafları ekrana bas (Supabase URL'lerinden)."""
        while self.photo_layout.count():
            child = self.photo_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not date_iso or date_iso not in self.photos_by_date:
            empty_label = QLabel("Bu tarihte fotoğraf yok.")
            empty_label.setAlignment(Qt.AlignCenter)
            self.photo_layout.addWidget(empty_label)
            return
        
        for photo_info in self.photos_by_date[date_iso]:
            # Her fotoğraf için bir container widget oluştur
            photo_widget = QWidget()
            photo_container_layout = QVBoxLayout()
            photo_widget.setLayout(photo_container_layout)
            photo_container_layout.setContentsMargins(8, 8, 8, 8)
            photo_container_layout.setSpacing(5)
            
            # Fotoğraf (URL'den yükle)
            img_label = QLabel()
            photo_url = photo_info.get('url', '')
            photo_name = photo_info.get('name', 'Bilinmeyen')
            
            if photo_url:
                try:
                    # URL'den fotoğrafı indir
                    response = requests.get(photo_url, timeout=10)
                    if response.status_code == 200:
                        pixmap = QPixmap()
                        pixmap.loadFromData(response.content)
                        if not pixmap.isNull():
                            img_label.setPixmap(pixmap.scaledToWidth(350, Qt.SmoothTransformation))
                        else:
                            img_label.setText(f"Görüntü yüklenemedi: {photo_name}")
                    else:
                        img_label.setText(f"Fotoğraf indirilemedi: {photo_name}")
                except Exception as e:
                    img_label.setText(f"Hata: {photo_name}\n{str(e)}")
            else:
                img_label.setText(f"URL bulunamadı: {photo_name}")
            
            img_label.setStyleSheet("padding: 4px; background-color: #f0f0f0; border-radius: 4px;")
            img_label.setAlignment(Qt.AlignCenter)
            photo_container_layout.addWidget(img_label)
            
            # Silme butonu
            delete_btn = QPushButton("🗑️ Sil")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 6px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            delete_btn.clicked.connect(lambda checked, info=photo_info: self.delete_photo(info))
            photo_container_layout.addWidget(delete_btn)
            
            # Container'ı ana layout'a ekle
            self.photo_layout.addWidget(photo_widget)
            
    def _select_date(self, date_iso: str):
        for i in range(self.date_list.count()):
            item = self.date_list.item(i)
            if item.data(Qt.UserRole) == date_iso:
                self.date_list.setCurrentRow(i)
                self.show_photos_for(date_iso)
                break
    
    def delete_photo(self, photo_info: Dict[str, Any]):
        """Fotoğrafı sadece Supabase'den sil"""
        if not self.db or not self.animal.id:
            QMessageBox.warning(self, "Uyarı", "Veritabanı bağlantısı yok!")
            return
        
        filename = photo_info.get('name', 'Bilinmeyen')
        
        # Onay mesajı
        reply = QMessageBox.question(
            self,
            "Fotoğraf Sil",
            f"'{filename}' adlı fotoğrafı silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Sadece Supabase'den sil
            success = self.db.delete_photo(
                animal_id=str(self.animal.id),
                filename=filename
            )
            
            if success:
                QMessageBox.information(self, "Başarılı", "Fotoğraf başarıyla silindi!")
                # Fotoğrafları yeniden yükle
                self.load_photos()
            else:
                QMessageBox.critical(self, "Hata", "Fotoğraf silinemedi!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fotoğraf silinirken hata oluştu: {str(e)}")


class AnimalDialog(QDialog):
    """Hayvan ekleme/düzenleme dialog penceresi (RFID Entegreli)"""
    
    def __init__(self, parent, title, data=None):
        super().__init__(parent)
        self.result = None
        self.setWindowTitle(title)
        self.setMinimumSize(500, 600)
        
        # Pencereyi ortala
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 500) // 2, (screen.height() - 600) // 2)
        
        self.init_ui(data or {})
    
    def init_ui(self, data):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        input_style = "padding: 6px; border: 1px solid #ccc; border-radius: 4px;"

        # --- RFID BÖLÜMÜ ---
        rfid_layout = QHBoxLayout()
        self.rfid_entry = QLineEdit()
        self.rfid_entry.setText(data.get("rfid_tag", ""))
        self.rfid_entry.setStyleSheet(input_style)
        self.rfid_entry.setPlaceholderText("Çip ID bekleniyor...")
        rfid_layout.addWidget(self.rfid_entry)
        
        self.scan_btn = QPushButton("Çip Oku")
        self.scan_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 5px;")
        self.scan_btn.clicked.connect(self.start_rfid_scan)
        rfid_layout.addWidget(self.scan_btn)
        
        form_layout.addRow("RFID Tag *:", rfid_layout)
        # -------------------
        
        # Diğer Alanlar
        self.isim_entry = QLineEdit()
        self.isim_entry.setText(data.get("isim", ""))
        self.isim_entry.setStyleSheet(input_style)
        form_layout.addRow("İsim *:", self.isim_entry)
        
        self.tur_combo = QComboBox()
        self.tur_combo.addItems(ANIMAL_TYPES)
        self.tur_combo.setStyleSheet(input_style)
        if data.get("tur"): self.tur_combo.setCurrentText(data.get("tur"))
        form_layout.addRow("Tür *:", self.tur_combo)
        
        self.yas_entry = QLineEdit()
        self.yas_entry.setText(str(data.get("yas", "")))
        self.yas_entry.setStyleSheet(input_style)
        self.yas_entry.setValidator(QRegExpValidator(QRegExp(r'^\d+$')))
        form_layout.addRow("Yaş *:", self.yas_entry)
        
        self.kilo_entry = QLineEdit()
        self.kilo_entry.setText(str(data.get("kilo", "")))
        self.kilo_entry.setStyleSheet(input_style)
        self.kilo_entry.setValidator(QRegExpValidator(QRegExp(r'^\d+\.?\d*$')))
        form_layout.addRow("Kilo (kg) *:", self.kilo_entry)

        self.boy_entry = QLineEdit()
        self.boy_entry.setText(str(data.get("boy", "")))
        self.boy_entry.setStyleSheet(input_style)
        self.boy_entry.setValidator(QRegExpValidator(QRegExp(r'^\d+\.?\d*$')))
        form_layout.addRow("Boy (cm) *:", self.boy_entry)

        self.cinsiyet_combo = QComboBox()
        self.cinsiyet_combo.addItems(GENDERS)
        self.cinsiyet_combo.setStyleSheet(input_style)
        if data.get("cinsiyet"): self.cinsiyet_combo.setCurrentText(data.get("cinsiyet"))
        form_layout.addRow("Cinsiyet *:", self.cinsiyet_combo)

        self.renk_entry = QLineEdit()
        self.renk_entry.setText(data.get("renk", ""))
        self.renk_entry.setStyleSheet(input_style)
        form_layout.addRow("Renk:", self.renk_entry)

        self.dogum_tarihi_entry = QLineEdit()
        self.dogum_tarihi_entry.setText(data.get("dogum_tarihi", ""))
        self.dogum_tarihi_entry.setStyleSheet(input_style)
        self.dogum_tarihi_entry.setPlaceholderText("gg.aa.yyyy")
        form_layout.addRow("Doğum Tarihi:", self.dogum_tarihi_entry)

        self.saglik_durumu_entry = QLineEdit()
        self.saglik_durumu_entry.setText(data.get("saglik_durumu", "İyi"))
        self.saglik_durumu_entry.setStyleSheet(input_style)
        form_layout.addRow("Sağlık Durumu:", self.saglik_durumu_entry)
        
        self.notlar_text = QTextEdit()
        self.notlar_text.setPlainText(data.get("notlar", ""))
        self.notlar_text.setMaximumHeight(80)
        self.notlar_text.setStyleSheet(input_style)
        form_layout.addRow("Notlar:", self.notlar_text)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --- RFID FONKSIYONLARI ---
    def start_rfid_scan(self):
        self.scan_btn.setText("Okunuyor...")
        self.scan_btn.setEnabled(False)
        self.rfid_entry.clear()
        
        self.reader_thread = SerialReader()
        self.reader_thread.rfid_read.connect(self.on_rfid_found)
        self.reader_thread.error_occurred.connect(self.on_rfid_error)
        self.reader_thread.start()

    def on_rfid_found(self, rfid_id):
        self.rfid_entry.setText(rfid_id)
        self.scan_btn.setText("Tekrar Oku")
        self.scan_btn.setEnabled(True)
        QMessageBox.information(self, "Başarılı", f"Kart Okundu: {rfid_id}")
        self.reader_thread.stop()

    def on_rfid_error(self, msg):
        self.scan_btn.setText("Çip Oku")
        self.scan_btn.setEnabled(True)
        QMessageBox.warning(self, "Hata", msg)

    def save(self):
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
