import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from config import USERS, APP_CONFIG

class LoginWindow(QMainWindow):
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success = on_success_callback
        self.setWindowTitle("Giriş Yap")
        self.setMinimumSize(500, 400)
        
        # Pencere boyutunu ayarla
        screen = QApplication.primaryScreen().geometry()
        window_width = max(500, int(screen.width() * 0.35))
        window_height = max(400, int(screen.height() * 0.35))
        self.resize(window_width, window_height)
        
        # Pencereyi ortala
        self.move(
            (screen.width() - window_width) // 2,
            (screen.height() - window_height) // 2
        )
        
        self.init_ui()
    
    def init_ui(self):
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Başlık
        title = QLabel("Ahır Hayvan Yönetim Sistemi")
        title.setFont(QFont("", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Kullanıcı adı label
        username_label = QLabel("Kullanıcı Adı:")
        username_label.setFont(QFont("", 13, QFont.Bold))
        layout.addWidget(username_label)
        
        # Kullanıcı adı input
        self.username_entry = QLineEdit()
        self.username_entry.setFont(QFont("", 14))
        self.username_entry.setMinimumHeight(50)
        self.username_entry.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 3px solid #CCCCCC;
                border-radius: 5px;
                padding: 10px;
            }
            QLineEdit:focus {
                border: 3px solid #4CAF50;
                color: black;
            }
        """)
        layout.addWidget(self.username_entry)
        
        # Şifre label
        password_label = QLabel("Şifre:")
        password_label.setFont(QFont("", 13, QFont.Bold))
        layout.addWidget(password_label)
        
        # Şifre için horizontal layout (input + göster/gizle butonu)
        password_layout = QHBoxLayout()
        password_layout.setSpacing(5)
        
        # Şifre input
        self.password_entry = QLineEdit()
        self.password_entry.setFont(QFont("", 14))
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setMinimumHeight(50)
        self.password_entry.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 3px solid #CCCCCC;
                border-radius: 5px;
                padding: 10px;
            }
            QLineEdit:focus {
                border: 3px solid #4CAF50;
                color: black;
            }
        """)
        password_layout.addWidget(self.password_entry)
        
        # Şifre göster/gizle butonu
        self.show_password_btn = QPushButton("👁️")
        self.show_password_btn.setMinimumWidth(50)
        self.show_password_btn.setMinimumHeight(50)
        self.show_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: 3px solid #CCCCCC;
                border-radius: 5px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
        """)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)
        
        layout.addLayout(password_layout)
        
        layout.addSpacing(20)
        
        # Giriş butonu
        login_btn = QPushButton("Giriş Yap")
        login_btn.setFont(QFont("", 15, QFont.Bold))
        login_btn.setMinimumHeight(50)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)
        
        # Bilgi etiketi
        info_label = QLabel("Varsayılan: admin / admin123")
        info_label.setFont(QFont("", 11))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Enter tuşu ile giriş
        self.password_entry.returnPressed.connect(self.login)
        self.username_entry.returnPressed.connect(lambda: self.password_entry.setFocus())
        
        # İlk focus
        self.username_entry.setFocus()
    
    def toggle_password_visibility(self):
        """Şifre görünürlüğünü değiştir"""
        if self.password_entry.echoMode() == QLineEdit.Password:
            self.password_entry.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_entry.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁️")
    
    def login(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        
        if username in USERS and USERS[username] == password:
            # Callback'i çağır (dashboard açılacak)
            self.on_success(username)
        else:
            QMessageBox.critical(self, "Hata", "Kullanıcı adı veya şifre hatalı!")
            self.password_entry.clear()
    
