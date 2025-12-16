import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

from serial_reader import SerialReader
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QMessageBox, QListWidget, 
                             QListWidgetItem, QComboBox, QGroupBox, QGridLayout, QTextEdit,
                             QDialog, QDialogButtonBox, QFormLayout, QFileDialog, QDateEdit,
                             QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp, QDate
from PyQt5.QtGui import QFont, QColor, QRegExpValidator, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

from database import get_database
from models.animal import Animal
from config import APP_CONFIG, ANIMAL_TYPES, GENDERS
from utils.validators import validate_animal_data
from utils.health_analyzer import HealthAnalyzer

class Dashboard(QMainWindow):
    def __init__(self, username, on_logout=None):
        super().__init__()
        self.username = username
        self.on_logout = on_logout
        self.db = get_database()
        self.db.connect()
        self.selected_animal_id = None
        self.rfid_reader_thread = None  # RFID okuma thread'i için
        # Hayvan listesindeki tür gruplarının (inek, koyun vs.) açık/kapalı durumları
        self.group_states: Dict[str, bool] = {}
        
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
        # Ana widget (login sayfası ile uyumlu arka plan)
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E9FCE9,   /* açık yeşil */
                    stop:1 #FDFBF7    /* krem */
                );
            }
        """)
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header (login teması ile uyumlu)
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet("""
            background-color: #FFFFFF;
            border-bottom: 1px solid #E4DDCF;
        """)
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Sol üstte menü (hamburger) butonu için yer bırakalım (şimdilik sadece başlık)
        title_label = QLabel("VisiFarm")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setStyleSheet("color: #3E2C1C;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        user_label = QLabel(f"Hoş geldiniz, {self.username}")
        user_label.setFont(QFont("Arial", 11))
        user_label.setStyleSheet("color: #887766; margin-right: 15px;")
        header_layout.addWidget(user_label)

        logout_btn = QPushButton("Çıkış Yap")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFE0E0;
                color: #B03A2E;
                border: none;
                padding: 6px 16px;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFC4C4;
            }
            QPushButton:pressed {
                background-color: #FFAAAA;
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
        panel.setStyleSheet("""
            QWidget {
                background-color: #F6F9F5;
                border-radius: 24px;
                border: 1px solid #D4E4D4;
            }
        """)
        panel.setFixedWidth(360)
        layout = QVBoxLayout()
        panel.setLayout(layout)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Arama başlığı
        search_label = QLabel("Hayvan ara")
        search_label.setFont(QFont("Arial", 11, QFont.Bold))
        search_label.setFrameShape(QFrame.NoFrame)
        search_label.setStyleSheet("color: #3E2C1C; background: transparent; border: none;")
        layout.addWidget(search_label)
        
        # Arama kutusu ve RFID butonu için horizontal layout
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.search_entry = QLineEdit()
        self.search_entry.setFont(QFont("Arial", 11))
        self.search_entry.setPlaceholderText("İsim, tür, renk veya RFID ara...")
        self.search_entry.setStyleSheet("""
            QLineEdit {
                background-color: #FFFDF8;
                color: #3E2C1C;
                border: 1px solid #E4DDCF;
                border-radius: 999px;
                padding: 8px 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2E7D32;
                background-color: #FFFFFF;
            }
        """)
        self.search_entry.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_entry, 1)
        
        # RFID okuma butonu
        self.rfid_search_btn = QPushButton("📡 RFID Oku")
        self.rfid_search_btn.setFont(QFont("Arial", 10))
        self.rfid_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #CDEBD3;
                color: #215732;
                padding: 8px 18px;
                border: none;
                border-radius: 999px;
                font-weight: 600;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #B7DFC1;
            }
            QPushButton:pressed {
                background-color: #A2D3AF;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #A0A0A0;
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
                border: 1px solid #D4E4D4;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: transparent;
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
        type_label.setFrameShape(QFrame.NoFrame)
        type_label.setStyleSheet("color: #34495e; background: transparent; border: none;")
        filter_layout.addWidget(type_label)
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Tümü"] + ANIMAL_TYPES)
        self.filter_type.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #E4DDCF;
                border-radius: 8px;
                background-color: white;
                color: #3E2C1C;
            }
            QComboBox:hover {
                border: 1px solid #2E7D32;
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
        gender_label.setFrameShape(QFrame.NoFrame)
        gender_label.setStyleSheet("color: #34495e; background: transparent; border: none;")
        filter_layout.addWidget(gender_label)
        
        self.filter_gender = QComboBox()
        self.filter_gender.addItems(["Tümü"] + GENDERS)
        self.filter_gender.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #E4DDCF;
                border-radius: 8px;
                background-color: white;
                color: #3E2C1C;
            }
            QComboBox:hover {
                border: 1px solid #2E7D32;
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
        list_label.setFrameShape(QFrame.NoFrame)
        list_label.setStyleSheet("color: #3E2C1C; padding-top: 5px; background: transparent; border: none;")
        layout.addWidget(list_label)
        
        # Hayvan listesi
        self.animal_list = QListWidget()
        self.animal_list.setFont(QFont("Arial", 11))
        self.animal_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #D4E4D4;
                border-radius: 20px;
                background-color: #FAFCFA;
                color: black;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #E8F0E8;
                color: black;
            }
            QListWidget::item:selected {
                background-color: transparent;
                border: 2px solid #2E7D32;
            }
            QListWidget::item:hover {
                background-color: #F0F7F0;
                color: #3E2C1C;
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
                background-color: #CDEBD3;
                color: #215732;
                padding: 12px;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #B7DFC1;
            }
            QPushButton:pressed {
                background-color: #A2D3AF;
            }
        """)
        add_btn.clicked.connect(self.add_animal)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Düzenle")
        edit_btn.setFont(QFont("Arial", 11))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #D7E8F8;
                color: #1F4E79;
                padding: 12px;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #C3DBF2;
            }
            QPushButton:pressed {
                background-color: #AFCFEC;
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
                background-color: #FFE0E0;
                color: #B03A2E;
                padding: 12px;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #FFC4C4;
            }
            QPushButton:pressed {
                background-color: #FFAAAA;
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
        detail_label.setFrameShape(QFrame.NoFrame)
        detail_label.setStyleSheet("color: #3E2C1C; background: transparent; border: none;")
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
        """Hayvan listesini yükle ve türlere göre grupla"""
        if animals is None:
            animals = self.db.get_all_animals()

        # Tür ve isimlere göre sırala ki gruplar düzgün gelsin
        animals_sorted = sorted(
            animals,
            key=lambda a: ((a.tur or "").lower(), (a.isim or "").lower()),
        )

        # Listeyi temizle
        self.animal_list.clear()
        current_type = None

        for animal in animals_sorted:
            animal_type = animal.tur or "Diğer"

            # Yeni bir tür grubuna geçiyorsak başlık ekle
            if animal_type != current_type:
                current_type = animal_type

                # Başlangıçta tüm gruplar kapalı: ok sağa bakan (▶)
                header_item = QListWidgetItem(f"▶ {current_type}")
                header_font = header_item.font()
                header_font.setBold(True)
                header_item.setFont(header_font)
                # Başlık seçilebilir ama tıklanınca sadece grubu aç/kapa yapar
                header_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                # Başlık olduğunu ve hangi tür olduğunu işaretle
                header_item.setData(Qt.UserRole, "HEADER")
                header_item.setData(Qt.UserRole + 1, animal_type)  # Tür bilgisi
                header_item.setBackground(QColor("#F5F5F5"))
                header_item.setForeground(QColor("#3E2C1C"))
                self.animal_list.addItem(header_item)

            # Önce sağlık analizini yap
            try:
                temp = getattr(animal, "temperature", None)
                current_weight = float(animal.kilo) if animal.kilo else None
                analysis = HealthAnalyzer.analyze_health(animal, temp, current_weight)
                status = analysis.get("health_status", "GOOD")
            except Exception:
                status = "GOOD"

            # İkonu durumuna göre belirle
            prefix_icon = ""
            if status == "CRITICAL":
                prefix_icon = "🔴 "
            elif status == "WARNING":
                prefix_icon = "🟡 "

            # Liste metnini oluştur
            item_text = f"{prefix_icon}{animal.isim} - {animal_type} ({animal.cinsiyet})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, animal.id)  # Hayvan ID'si
            item.setData(Qt.UserRole + 1, animal_type)  # Hangi türe ait
            item.setData(Qt.UserRole + 2, "CHILD")  # Bu bir çocuk öğe (hayvan)

            # Satır rengini de durumuna göre ayarla
            if status == "CRITICAL":
                item.setBackground(QColor("#ffebee"))   # çok açık kırmızı
                item.setForeground(QColor("#ea4335"))   # koyu kırmızı yazı
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif status == "WARNING":
                item.setBackground(QColor("#fff8e1"))   # açık sarı
                item.setForeground(QColor("#ea4335"))   # turuncu yazı
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            # İlk yüklemede tüm gruplar kapalı: tüm hayvanları gizle
            item.setHidden(True)

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
        role = item.data(Qt.UserRole)

        # Eğer bu bir BAŞLIK ise (UserRole = "HEADER")
        if role == "HEADER":
            group_type = item.data(Qt.UserRole + 1)  # Hangi tür? (Örn: İnek)
            current_text = item.text()

            # Durumu belirle: Şu an kapalı mı? (▶ ile mi başlıyor?)
            is_collapsed = current_text.strip().startswith("▶")

            # OKU GÜNCELLE
            if is_collapsed:
                # Kapalıymış, AÇACAĞIZ
                new_text = current_text.replace("▶", "▼")
                item.setText(new_text)
                should_hide = False  # Gizleme, GÖSTER
            else:
                # Açıkmış, KAPATACAĞIZ
                new_text = current_text.replace("▼", "▶")
                item.setText(new_text)
                should_hide = True  # GİZLE

            # LİSTEDEKİ DİĞER ELEMANLARI BUL VE GİZLE/GÖSTER
            # ListWidget'taki tüm satırları tek tek geziyoruz
            for i in range(self.animal_list.count()):
                loop_item = self.animal_list.item(i)

                # Sadece bu grubun çocuklarını etkile
                # (UserRole+1'i 'tur', UserRole+2'yi 'CHILD' olarak kaydetmiştik)
                if (loop_item.data(Qt.UserRole + 1) == group_type and
                    loop_item.data(Qt.UserRole + 2) == "CHILD"):
                    loop_item.setHidden(should_hide)
            return

        # Eğer başlığa değil de hayvana tıklandıysa normal işlemleri yap
        animal_id = role
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
        
        # AI Health Analysis - Sağlık durumunu analiz et
        current_temperature = getattr(animal, 'temperature', None)
        current_weight = float(animal.kilo) if animal.kilo else None
        health_analysis = HealthAnalyzer.analyze_health(animal, current_temperature, current_weight)
        
        # Hayvan adı - daha soft, login paletine uygun kart
        name_container = QWidget()
        name_container.setStyleSheet("""
            QWidget {
                background-color: #E3F3E8;
                border-radius: 18px;
                padding: 20px;
                border: none;
            }
        """)

        # Üst satır: isim + sağlık rozeti
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(f"🐄 {animal.isim}")
        name_label.setFont(QFont("Arial", 26, QFont.Bold))
        name_label.setFrameShape(QFrame.NoFrame)
        name_label.setStyleSheet("color: #3E2C1C; background: transparent; border: none;")
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        # Sağlık durumu badge'i (sağ üstte)
        health_badge = QLabel()
        health_badge.setFont(QFont("Arial", 13, QFont.Bold))
        health_badge.setAlignment(Qt.AlignCenter)
        # Boyutu Qt'ya bırak, sadece minimum genişlik ver
        health_badge.setMinimumWidth(110)

        if health_analysis["health_status"] == "CRITICAL":
            health_badge.setText("KRİTİK")
            # Çerçeveyi kaldır, sadece yumuşak arka plan kalsın
            health_badge.setStyleSheet("""
                QLabel {
                    background-color: #FCE4E4;
                    color: #C62828;
                    border-radius: 18px;
                    padding: 6px 20px;
                    border: none;
                }
            """)
        elif health_analysis["health_status"] == "WARNING":
            health_badge.setText("UYARI")
            health_badge.setStyleSheet("""
                QLabel {
                    background-color: #FFF2DD;
                    color: #E65100;
                    border-radius: 18px;
                    padding: 6px 20px;
                    border: none;
                }
            """)
        else:
            health_badge.setText("İYİ")
            health_badge.setStyleSheet("""
                QLabel {
                    background-color: #E3F3E8;
                    color: #2E7D32;
                    border-radius: 18px;
                    padding: 6px 20px;
                    border: none;
                }
            """)
        header_layout.addWidget(health_badge)

        # Alt satır: tür / cinsiyet / yaş özeti
        summary_label = QLabel(
            f"{animal.tur or 'Tür belirtilmemiş'} • "
            f"{animal.cinsiyet or 'Cinsiyet belirtilmemiş'} • "
            f"{animal.yas} yaşında"
        )
        summary_label.setFrameShape(QFrame.NoFrame)
        summary_label.setStyleSheet(
            "color: #5D4B3A; background: transparent; border: none; font-size: 15px;"
        )

        name_main_layout = QVBoxLayout()
        name_main_layout.setContentsMargins(15, 10, 15, 5)
        name_main_layout.setSpacing(6)
        name_main_layout.addLayout(header_layout)
        name_main_layout.addWidget(summary_label)

        name_container.setLayout(name_main_layout)
        self.detail_layout.addWidget(name_container)
        
        # Spacing
        self.detail_layout.addSpacing(10)
        
        # AI Uyarıları Göster (CRITICAL ve WARNING) - daha soft kart tasarımı
        if health_analysis["alerts"]:
            # Başlık - Daha belirgin
            alerts_title = QLabel("⚠️ Sağlık Uyarıları")
            alerts_title.setFont(QFont("Arial", 18, QFont.Bold))
            alerts_title.setStyleSheet("color: #2c3e50; padding: 10px 0px 5px 0px;")
            self.detail_layout.addWidget(alerts_title)
            
            # Her uyarı için sade kart tasarımı
            for alert in health_analysis["alerts"]:
                is_critical = alert["type"] == "CRITICAL"

                bg_color = "#FCE4E4" if is_critical else "#FFF2DD"
                text_color = "#C62828" if is_critical else "#E65100"
                border_color = "#F5B7B1" if is_critical else "#F8C471"

                # Ana container (arka plan kalsın, çerçeve çizgisi olmasın)
                alert_container = QWidget()
                alert_container.setStyleSheet(f"""
                    QWidget {{
                        background-color: {bg_color};
                        border: none;
                        border-radius: 8px;
                        padding: 0px;
                    }}
                """)
                alert_layout = QHBoxLayout()
                alert_container.setLayout(alert_layout)
                alert_layout.setContentsMargins(12, 8, 12, 8)
                alert_layout.setSpacing(12)
                
                # İkon (sol tarafta, sade)
                icon_label = QLabel()
                icon_label.setStyleSheet("background: transparent;")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedWidth(28)

                icon_text = alert.get("icon", "⚠️")
                # Ateş uyarılarında termometre ikonunu kullan
                if icon_text in ("🔥", "🌡️"):
                    pix = QPixmap("assets/termometre.png")
                    if not pix.isNull():
                        icon_label.setPixmap(
                            pix.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )
                    else:
                        icon_label.setText("🌡️")
                        icon_label.setFont(QFont("Arial", 18))
                # Kilo kaybı uyarılarında özel ikon kullan
                elif icon_text in ("⚖️",):
                    pix = QPixmap("assets/kilo_kayip.png")
                    if not pix.isNull():
                        icon_label.setPixmap(
                            pix.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )
                    else:
                        icon_label.setText("⚖️")
                        icon_label.setFont(QFont("Arial", 18))
                else:
                    icon_label.setText(icon_text)
                    icon_label.setFont(QFont("Arial", 18))

                alert_layout.addWidget(icon_label)
                
                # Mesaj (sağ tarafta, tek satır kalın metin)
                message_label = QLabel(alert["message"])
                message_label.setFont(QFont("Arial", 15, QFont.Bold))
                message_label.setStyleSheet(f"color: {text_color}; background: transparent;")
                message_label.setWordWrap(True)
                message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                alert_layout.addWidget(message_label, 1)
                
                alert_container.setMinimumHeight(40)
                self.detail_layout.addWidget(alert_container)
                self.detail_layout.addSpacing(6)
        
        # Detay bilgileri - Modern kart tasarımı
        details_title = QLabel("📋 Hayvan Bilgileri")
        details_title.setFont(QFont("Arial", 18, QFont.Bold))
        details_title.setStyleSheet("color: #2c3e50; padding: 15px 0px 10px 0px;")
        self.detail_layout.addWidget(details_title)
        
        # Ana bilgi container'ı
        info_container = QWidget()
        info_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        info_grid = QGridLayout()
        info_container.setLayout(info_grid)
        info_grid.setSpacing(15)
        info_grid.setContentsMargins(15, 15, 15, 15)
        
        # Sağlık durumunu renklendir - Analiz sonucuna göre dinamik göster
        health_status_color = "#3E2C1C"
        if health_analysis["health_status"] == "CRITICAL":
            health_status_display = "🔴 KRİTİK"
            health_status_color = "#C62828"
        elif health_analysis["health_status"] == "WARNING":
            health_status_display = "🟡 UYARI"
            health_status_color = "#E65100"
        else:
            health_status_display = "✅ İYİ"
            health_status_color = "#2E7D32"
        
        info_items = [
            ("🏷️ RFID", animal.rfid_tag or "Belirtilmemiş"),
            ("⚖️ Kilo", f"{animal.kilo} kg"),
            ("📏 Boy", f"{animal.boy} cm"),
            ("💊 Sağlık Durumu", health_status_display),
        ]
        
        # Temperature göster (varsa)
        if current_temperature is not None:
            temp_display = f"{current_temperature}°C"
            if health_analysis["temperature_status"]["status"] == "CRITICAL":
                temp_display = f"🔴 {temp_display}"
            elif health_analysis["temperature_status"]["status"] == "WARNING":
                temp_display = f"🟡 {temp_display}"
            else:
                temp_display = f"🌡️ {temp_display}"
            info_items.append(("🌡️ Vücut Sıcaklığı", temp_display))
        
        # Baseline weight göster (varsa)
        if hasattr(animal, 'baseline_weight') and animal.baseline_weight:
            info_items.append(("📊 Profil Kilosu", f"{animal.baseline_weight} kg"))
        
        for i, (label, value) in enumerate(info_items):
            # Her bilgi için kart tasarımı
            item_container = QWidget()
            item_container.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 8px;
                    padding: 12px;
                    border: 1px solid #e0e0e0;
                }
            """)
            item_layout = QVBoxLayout()
            item_container.setLayout(item_layout)
            item_layout.setContentsMargins(10, 8, 10, 8)
            item_layout.setSpacing(5)
            
            # Label
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 12))
            label_widget.setStyleSheet("color: #7f8c8d; background: transparent;")
            item_layout.addWidget(label_widget)
            
            # Value
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Arial", 16, QFont.Bold))
            # Sağlık durumu için özel renk
            if "Sağlık Durumu" in label:
                value_widget.setStyleSheet(f"""
                    QLabel {{
                        color: {health_status_color};
                        background: transparent;
                        padding: 5px 0px;
                    }}
                """)
            elif "Vücut Sıcaklığı" in label:
                # Sıcaklık için özel renk
                if "🔴" in value:
                    value_widget.setStyleSheet("color: #d32f2f; background: transparent; padding: 5px 0px;")
                elif "🟡" in value:
                    value_widget.setStyleSheet("color: #f57c00; background: transparent; padding: 5px 0px;")
                else:
                    value_widget.setStyleSheet("color: #2c3e50; background: transparent; padding: 5px 0px;")
            else:
                value_widget.setStyleSheet("color: #2c3e50; background: transparent; padding: 5px 0px;")
            item_layout.addWidget(value_widget)
            
            # Grid'e ekle (2 sütunlu)
            info_grid.addWidget(item_container, i // 2, i % 2)
        
        self.detail_layout.addWidget(info_container)
        
        # Notlar - Modern kart tasarımı
        if animal.notlar:
            self.detail_layout.addSpacing(15)
            notes_title = QLabel("📝 Notlar")
            notes_title.setFont(QFont("Arial", 14, QFont.Bold))
            notes_title.setStyleSheet("color: #2c3e50; padding: 10px 0px 5px 0px;")
            self.detail_layout.addWidget(notes_title)
            
            notes_container = QWidget()
            notes_container.setStyleSheet("""
                QWidget {
                    background-color: #fff9e6;
                    border-left: 4px solid #f39c12;
                    border-radius: 10px;
                    padding: 15px;
                }
            """)
            notes_layout = QVBoxLayout()
            notes_container.setLayout(notes_layout)
            notes_layout.setContentsMargins(10, 10, 10, 10)
            
            notes_text = QLabel(animal.notlar)
            notes_text.setFont(QFont("Arial", 11))
            notes_text.setWordWrap(True)
            notes_text.setStyleSheet("color: #2c3e50; background: transparent; padding: 5px;")
            notes_layout.addWidget(notes_text)
            
            self.detail_layout.addWidget(notes_container)
        
        # Fotoğraf ve sağlık butonları - daha yumuşak tasarım
        self.detail_layout.addSpacing(20)
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_container.setLayout(button_layout)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        photos_btn = QPushButton("📷 Fotoğrafları Görüntüle")
        photos_btn.setFont(QFont("Arial", 12, QFont.Bold))
        photos_btn.setCursor(Qt.PointingHandCursor)
        photos_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3E2C1C;
                padding: 14px 22px;
                border: 1px solid #E4DDCF;
                border-radius: 16px;
                font-weight: bold;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #FDFBF7;
            }
            QPushButton:pressed {
                background-color: #F3EEE3;
            }
        """)
        photos_btn.clicked.connect(lambda: self.open_photo_dialog(animal))
        button_layout.addWidget(photos_btn)

        # 7 günlük sağlık grafiği butonu (popup)
        trend_btn = QPushButton("📈 7 Günlük Sağlık Grafiği")
        trend_btn.setFont(QFont("Arial", 12, QFont.Bold))
        trend_btn.setCursor(Qt.PointingHandCursor)
        trend_btn.setStyleSheet("""
            QPushButton {
                background-color: #E4F0FB;
                color: #1F4E79;
                padding: 14px 22px;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #D4E6F7;
            }
            QPushButton:pressed {
                background-color: #C5DCF3;
            }
        """)
        trend_btn.clicked.connect(lambda: self.open_health_trend_dialog(animal))
        button_layout.addWidget(trend_btn)

        # Manuel ölçüm ekleme butonu
        log_btn = QPushButton("➕ Ölçüm Ekle")
        log_btn.setFont(QFont("Arial", 12, QFont.Bold))
        log_btn.setCursor(Qt.PointingHandCursor)
        log_btn.setStyleSheet("""
            QPushButton {
                background-color: #D7E8F8;
                color: #1F4E79;
                padding: 14px 22px;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #C3DBF2;
            }
            QPushButton:pressed {
                background-color: #AFCFEC;
            }
        """)
        log_btn.clicked.connect(lambda: self.open_health_log_dialog(animal))
        button_layout.addWidget(log_btn)
        
        self.detail_layout.addWidget(button_container)
        self.detail_layout.addStretch()
    
    def open_photo_dialog(self, animal: Animal):
        """Seçili hayvan için fotoğraf yöneticisini aç."""
        dialog = PhotoDialog(self, animal)
        dialog.exec_()
    
    def open_health_trend_dialog(self, animal: Animal):
        """
        Seçili hayvan için 7 günlük kilo + ateş grafiğini göster.
        Supabase'den sağlık geçmişi verilerini okur; yoksa bilgi mesajı gösterir.
        """
        if not animal.id:
            QMessageBox.information(
                self,
                "Bilgi",
                "Bu hayvan henüz kaydedilmemiş, sağlık geçmişi bulunmuyor.",
            )
            return

        # Veritabanından son 7 günün sağlık geçmişini oku
        if hasattr(self.db, "get_health_logs"):
            history_data = self.db.get_health_logs(animal.id, days=7)
        else:
            history_data = []

        dialog = HealthTrendDialog(self, animal, history_data)
        dialog.exec_()

    def open_health_log_dialog(self, animal: Animal):
        """Seçili hayvan için manuel kilo + ateş ölçümü ekle."""
        if not animal.id:
            QMessageBox.information(
                self,
                "Bilgi",
                "Bu hayvan henüz kaydedilmemiş, ölçüm eklenemez.",
            )
            return

        dialog = HealthLogDialog(self, animal)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            data = dialog.result
            try:
                # Yeni ölçümü sağlık geçmişine kaydet
                self.db.add_health_log(
                    animal.id,
                    data.get("weight"),
                    data.get("temperature"),
                    data.get("measured_at"),
                )
                # Hayvanın anlık kilo / ateş ve sağlık durumunu da güncelle
                weight = data.get("weight")
                temperature = data.get("temperature")

                if weight is not None:
                    animal.kilo = weight
                if temperature is not None:
                    animal.temperature = temperature

                # Rule-based AI ile sağlık durumunu yeniden hesapla
                updated_animal = HealthAnalyzer.update_animal_health_status(
                    animal,
                    temperature,
                    weight if weight is not None else (float(animal.kilo) if animal.kilo else None),
                )

                # Veritabanındaki hayvan kaydını da güncelle
                try:
                    self.db.update_animal(animal.id, updated_animal)
                except Exception:
                    # DB güncellemesi başarısız olsa bile UI'ı güncellemeye devam et
                    pass

                # Liste ve detay panelini tazele (son ölçüm ve durumlar hemen görünsün)
                self.on_search()
                # Seçili hayvanı yeniden DB'den çekmeye çalış; olmazsa elimizdeki updated_animal'ı kullan
                refreshed = None
                try:
                    refreshed = self.db.get_animal_by_id(animal.id)
                except Exception:
                    refreshed = None
                self.show_animal_details(refreshed or updated_animal)

                QMessageBox.information(self, "Başarılı", "Yeni ölçüm başarıyla kaydedildi ve detaylar güncellendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ölçüm kaydedilirken bir hata oluştu:\n{e}")
    
    def add_animal(self):
        """Yeni hayvan ekle"""
        dialog = AnimalDialog(self, "Yeni Hayvan Ekle")
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            animal = Animal(dialog.result)
            
            # AI Health Analysis - Sağlık durumunu otomatik güncelle
            temperature = getattr(animal, 'temperature', None)
            current_weight = float(animal.kilo) if animal.kilo else None
            animal = HealthAnalyzer.update_animal_health_status(animal, temperature, current_weight)
            
            # Eğer baseline_weight yoksa, mevcut kiloyu baseline olarak ayarla
            if not animal.baseline_weight and animal.kilo:
                animal.baseline_weight = float(animal.kilo)
            
            if self.db.add_animal(animal):
                # İlk kayıt için sağlık geçmişine de bir ölçüm ekle
                try:
                    self.db.add_health_log(
                        animal.id,
                        float(animal.kilo) if animal.kilo else None,
                        getattr(animal, "temperature", None),
                    )
                except Exception:
                    pass
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
            
            # Eğer baseline_weight girilmediyse, mevcut baseline_weight'i koru
            if not updated_animal.baseline_weight and hasattr(animal, 'baseline_weight') and animal.baseline_weight:
                updated_animal.baseline_weight = animal.baseline_weight
            # Eğer hiç baseline_weight yoksa ve yeni kilo girildiyse, onu baseline yap
            elif not updated_animal.baseline_weight and updated_animal.kilo:
                updated_animal.baseline_weight = float(updated_animal.kilo)
            
            # AI Health Analysis - Sağlık durumunu otomatik güncelle
            temperature = getattr(updated_animal, 'temperature', None)
            current_weight = float(updated_animal.kilo) if updated_animal.kilo else None
            updated_animal = HealthAnalyzer.update_animal_health_status(updated_animal, temperature, current_weight)
            
            if self.db.update_animal(self.selected_animal_id, updated_animal):
                # Güncellenen ölçümleri sağlık geçmişine ekle
                try:
                    self.db.add_health_log(
                        self.selected_animal_id,
                        float(updated_animal.kilo) if updated_animal.kilo else None,
                        getattr(updated_animal, "temperature", None),
                    )
                except Exception:
                    pass
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
                color: #2c3e50;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
                color: #2c3e50;
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
                    background-color: #FFE0E0;
                    color: #B03A2E;
                    padding: 6px;
                    border: none;
                    border-radius: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FFC4C4;
                }
                QPushButton:pressed {
                    background-color: #FFAAAA;
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


class HealthTrendDialog(QDialog):
    """Seçili hayvan için 7 günlük kilo + ateş grafiği"""

    def __init__(self, parent, animal: Animal, history_data):
        """
        history_data: [
            {"date": datetime, "weight": float, "temperature": float},
            ...
        ]
        """
        super().__init__(parent)
        self.animal = animal
        self.history_data = history_data or []

        self.setWindowTitle(f"{animal.isim} - Sağlık Trendi (7 Gün)")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Matplotlib Figure
        # (Bazı ortamlarda global import sorun çıkarmasın diye lokal import da yapıyoruz)
        from matplotlib.figure import Figure as _Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as _FigureCanvas

        self.figure = _Figure(figsize=(8, 4))
        self.canvas = _FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        self.plot_trend()

    def plot_trend(self):
        if not self.history_data:
            msg = QLabel("Son 7 gün için kayıtlı kilo / ateş verisi bulunamadı.")
            msg.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(msg)
            return

        df = pd.DataFrame(self.history_data)
        df["date_str"] = df["date"].dt.strftime("%d %b")

        dates = df["date_str"]
        weights = df["weight"]
        temps = df["temperature"]

        # Sol eksen: kilo
        self.ax1.clear()
        color_w = "tab:blue"
        self.ax1.set_xlabel("Tarih")
        self.ax1.set_ylabel("Kilo (kg)", color=color_w, fontsize=11)
        self.ax1.plot(dates, weights, color=color_w, marker="o", label="Kilo", linewidth=2)
        self.ax1.tick_params(axis="y", labelcolor=color_w)
        self.ax1.grid(True, linestyle="--", alpha=0.5)

        # Sağ eksen: ateş
        self.ax2.clear()
        color_t = "tab:red"
        # Sağ eksen etiketini grafiğin SAĞ tarafına al
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()
        self.ax2.set_ylabel("Ateş (°C)", color=color_t, fontsize=11, labelpad=12)
        self.ax2.plot(dates, temps, color=color_t, marker="s", linestyle="--", label="Ateş", linewidth=2)
        self.ax2.tick_params(axis="y", labelcolor=color_t)
        self.ax2.set_ylim(35, 42)

        self.figure.tight_layout()
        self.canvas.draw()


class HealthLogDialog(QDialog):
    """Seçili hayvan için manuel kilo + ateş ölçümü ekleme."""

    def __init__(self, parent, animal: Animal):
        super().__init__(parent)
        self.animal = animal
        self.result = None

        self.setWindowTitle(f"{animal.isim} - Yeni Ölçüm")
        self.setMinimumSize(320, 230)

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        input_style = "padding: 6px; border: 1px solid #ccc; border-radius: 4px;"

        # Tarih seçimi
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(input_style)
        form.addRow("Tarih:", self.date_edit)

        self.weight_entry = QLineEdit()
        self.weight_entry.setStyleSheet(input_style)
        self.weight_entry.setPlaceholderText("Örn: 750.0")
        self.weight_entry.setValidator(QRegExpValidator(QRegExp(r'^\d+\.?\d*$')))
        # Mevcut kiloyu varsayılan yap
        if getattr(animal, "kilo", None):
            self.weight_entry.setText(str(animal.kilo))
        form.addRow("Kilo (kg):", self.weight_entry)

        self.temp_entry = QLineEdit()
        self.temp_entry.setStyleSheet(input_style)
        self.temp_entry.setPlaceholderText("Örn: 38.5")
        self.temp_entry.setValidator(QRegExpValidator(QRegExp(r'^\d+\.?\d*$')))
        if getattr(animal, "temperature", None):
            self.temp_entry.setText(str(animal.temperature))
        form.addRow("Vücut Sıcaklığı (°C):", self.temp_entry)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        weight_text = self.weight_entry.text().strip()
        temp_text = self.temp_entry.text().strip()

        weight = float(weight_text) if weight_text else None
        temperature = float(temp_text) if temp_text else None

        # Tarihi datetime'a çevir (saat 00:00)
        selected_date = self.date_edit.date().toPyDate()
        measured_at = datetime.combine(selected_date, datetime.min.time())

        if weight is None and temperature is None:
            QMessageBox.warning(self, "Uyarı", "En azından kilo veya vücut sıcaklığından birini girmelisiniz.")
            return

        self.result = {
            "weight": weight,
            "temperature": temperature,
            "measured_at": measured_at,
        }
        self.accept()


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
        
        # Tüm label'larda çerçeve olmasın
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        
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
        self.tur_combo.setEnabled(True)  # Açıkça aktif et
        if data.get("tur"): 
            self.tur_combo.setCurrentText(data.get("tur"))
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
        self.cinsiyet_combo.setEnabled(True)  # Açıkça aktif et
        if data.get("cinsiyet"): 
            self.cinsiyet_combo.setCurrentText(data.get("cinsiyet"))
        form_layout.addRow("Cinsiyet *:", self.cinsiyet_combo)

        self.saglik_durumu_entry = QLineEdit()
        self.saglik_durumu_entry.setText(data.get("saglik_durumu", "İyi"))
        self.saglik_durumu_entry.setStyleSheet(input_style)
        form_layout.addRow("Sağlık Durumu:", self.saglik_durumu_entry)
        
        # Vücut Sıcaklığı (°C) - AI Health Monitoring için
        self.temperature_entry = QLineEdit()
        temp_value = data.get("temperature", "")
        self.temperature_entry.setText(str(temp_value) if temp_value else "")
        self.temperature_entry.setStyleSheet(input_style)
        self.temperature_entry.setPlaceholderText("Örn: 38.5")
        # Sadece sayı kabul et (ondalıklı olabilir)
        temp_validator = QRegExpValidator(QRegExp(r'^\d+\.?\d*$'))
        self.temperature_entry.setValidator(temp_validator)
        form_layout.addRow("Vücut Sıcaklığı (°C):", self.temperature_entry)
        
        # Profil Kilosu (kg) - AI Health Monitoring için
        self.baseline_weight_entry = QLineEdit()
        baseline_value = data.get("baseline_weight", "")
        self.baseline_weight_entry.setText(str(baseline_value) if baseline_value else "")
        self.baseline_weight_entry.setStyleSheet(input_style)
        self.baseline_weight_entry.setPlaceholderText("Kilo kaybı analizi için referans kilo")
        # Sadece sayı kabul et (ondalıklı olabilir)
        baseline_validator = QRegExpValidator(QRegExp(r'^\d+\.?\d*$'))
        self.baseline_weight_entry.setValidator(baseline_validator)
        form_layout.addRow("Profil Kilosu (kg):", self.baseline_weight_entry)
        
        # Notlar
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
        """Form verilerini kaydet"""
        # Temperature ve baseline_weight değerlerini parse et
        temperature_text = self.temperature_entry.text().strip()
        temperature = float(temperature_text) if temperature_text else None
        
        baseline_weight_text = self.baseline_weight_entry.text().strip()
        baseline_weight = float(baseline_weight_text) if baseline_weight_text else None
        
        data = {
            "rfid_tag": self.rfid_entry.text(),
            "isim": self.isim_entry.text(),
            "yas": self.yas_entry.text(),
            "kilo": self.kilo_entry.text(),
            "boy": self.boy_entry.text(),
            "cinsiyet": self.cinsiyet_combo.currentText(),
            "tur": self.tur_combo.currentText(),
            "saglik_durumu": self.saglik_durumu_entry.text(),
            "notlar": self.notlar_text.toPlainText(),
            "temperature": temperature,
            "baseline_weight": baseline_weight
        }
        
        is_valid, error_msg = validate_animal_data(data)
        if not is_valid:
            QMessageBox.critical(self, "Hata", error_msg)
            return
        
        self.result = data
        self.accept()
