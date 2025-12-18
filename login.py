import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from config import USERS, APP_CONFIG


class LoginWindow(QMainWindow):
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success = on_success_callback
        self.setWindowTitle("Giriş Yap")
        self.setMinimumSize(700, 500)

        # Pencere boyutunu ayarla (ekrana göre daha geniş olsun)
        screen = QApplication.primaryScreen().geometry()
        window_width = max(800, int(screen.width() * 0.5))
        window_height = max(550, int(screen.height() * 0.5))
        self.resize(window_width, window_height)

        # Pencereyi ortala
        self.move(
            (screen.width() - window_width) // 2,
            (screen.height() - window_height) // 2,
        )

        self.init_ui()

    def init_ui(self):
        # Ana widget (arkaplan: açık yeşilden kreme gradient)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Tüm label'larda arka plan/çerçeve olmasın
        self.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                border: none;
            }
        """
        )
        central_widget.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E9FCE9,   /* açık yeşil */
                    stop:1 #FDFBF7    /* krem */
                );
            }
        """
        )

        # Dış layout (kartı ortalamak için)
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(40, 40, 40, 40)
        outer_layout.setSpacing(0)
        outer_layout.setAlignment(Qt.AlignCenter)
        central_widget.setLayout(outer_layout)
        self.outer_layout = outer_layout

        # Kart
        card = QWidget()
        card.setStyleSheet(
            """
            QWidget {
                /* Daha nötr, hafif yeşilimsi krem ton */
                background-color: #F6F9F5;
                border-radius: 24px;
                border: 1px solid #D4E4D4;
            }
        """
        )
        # Kart, pencere genişledikçe yatayda daha geniş görünsün
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card.setMinimumWidth(520)
        self.card = card

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(40, 40, 40, 32)
        card_layout.setSpacing(24)
        card.setLayout(card_layout)
        outer_layout.addWidget(card, 0, Qt.AlignCenter)

        # Logo / ikon (yaprak görseli - ortalanmış, responsive boyut)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFrameShape(QFrame.NoFrame)
        self.logo_label.setStyleSheet("background-color: transparent; border: none;")
        self.logo_pixmap = QPixmap("assets/yaprak.png")
        if not self.logo_pixmap.isNull():
            self.logo_label.setPixmap(self.logo_pixmap)
        card_layout.addWidget(self.logo_label, 0, Qt.AlignHCenter)

        # Başlık
        title = QLabel("VisiFarm")
        title.setFont(QFont("Arial", 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setFrameShape(QFrame.NoFrame)
        title.setStyleSheet(
            """
            QLabel {
                color: #3E2C1C;
                background-color: transparent;
                border: none;
            }
        """
        )
        card_layout.addWidget(title)

        # Alt başlık
        subtitle = QLabel("Ahır Hayvan Yönetim Sistemi")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFrameShape(QFrame.NoFrame)
        subtitle.setStyleSheet(
            """
            QLabel {
                color: #887766;
                background-color: transparent;
                border: none;
            }
        """
        )
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(16)

        # Kullanıcı adı label
        username_label = QLabel("Kullanıcı Adı")
        username_label.setFont(QFont("Arial", 11, QFont.Bold))
        username_label.setFrameShape(QFrame.NoFrame)
        username_label.setStyleSheet(
            """
            QLabel {
                color: #3E2C1C;
                background-color: transparent;
                border: none;
            }
        """
        )
        card_layout.addWidget(username_label)

        # Kullanıcı adı input
        self.username_entry = QLineEdit()
        self.username_entry.setFont(QFont("Arial", 12))
        self.username_entry.setMinimumHeight(44)
        self.username_entry.setPlaceholderText("Kullanıcı adınızı girin")
        self.username_entry.setStyleSheet(
            """
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
        """
        )
        # macOS odak halkasını gizle (pembe çerçeve olmasın)
        self.username_entry.setAttribute(Qt.WA_MacShowFocusRect, False)
        card_layout.addWidget(self.username_entry)

        # Şifre label
        password_label = QLabel("Şifre")
        password_label.setFont(QFont("Arial", 11, QFont.Bold))
        password_label.setFrameShape(QFrame.NoFrame)
        password_label.setStyleSheet(
            """
            QLabel {
                color: #3E2C1C;
                background-color: transparent;
                border: none;
            }
        """
        )
        card_layout.addWidget(password_label)

        # Şifre için horizontal layout (input + göster/gizle butonu)
        password_layout = QHBoxLayout()
        password_layout.setSpacing(8)

        # Şifre input
        self.password_entry = QLineEdit()
        self.password_entry.setFont(QFont("Arial", 12))
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setMinimumHeight(44)
        self.password_entry.setPlaceholderText("Şifrenizi girin")
        self.password_entry.setStyleSheet(
            """
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
        """
        )
        self.password_entry.setAttribute(Qt.WA_MacShowFocusRect, False)
        password_layout.addWidget(self.password_entry, 1)

        # Şifre göster/gizle butonu
        self.show_password_btn = QPushButton("👁️")
        self.show_password_btn.setMinimumWidth(44)
        self.show_password_btn.setMinimumHeight(44)
        self.show_password_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #F0E9DD;
                border: 1px solid #E4DDCF;
                border-radius: 22px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #E6DECF;
            }
            QPushButton:pressed {
                background-color: #DCD3C3;
            }
        """
        )
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)

        card_layout.addLayout(password_layout)

        card_layout.addSpacing(12)

        # Giriş butonu
        login_btn = QPushButton("Giriş Yap")
        login_btn.setFont(QFont("Arial", 13, QFont.Bold))
        login_btn.setMinimumHeight(44)
        login_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 999px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #27652A;
            }
            QPushButton:pressed {
                background-color: #1F4D21;
            }
        """
        )
        login_btn.clicked.connect(self.login)
        card_layout.addWidget(login_btn)

        # Bilgi etiketi
        info_label = QLabel("Demo: admin / admin123")
        info_label.setFont(QFont("Arial", 10))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFrameShape(QFrame.NoFrame)
        info_label.setStyleSheet(
            """
            QLabel {
                color: #887766;
                background-color: transparent;
                border: none;
            }
        """
        )
        card_layout.addWidget(info_label)

    def resizeEvent(self, event):
        """Pencere boyutuna göre kart genişliğini ve kenar boşluklarını uyumlu hale getir."""
        super().resizeEvent(event)

        if hasattr(self, "card") and hasattr(self, "outer_layout"):
            w = self.width()
            h = self.height()

            # Pencere küçüldükçe kenar boşluklarını azalt
            margin = 40
            if w < 900 or h < 650:
                margin = 24
            if w < 700 or h < 550:
                margin = 16
            self.outer_layout.setContentsMargins(margin, margin, margin, margin)

            # Kart genişliği: pencere genişliğinin yaklaşık %60'ı, ama 520'den küçük olmasın
            target_width = max(520, int(w * 0.6))
            self.card.setMaximumWidth(target_width)

            # Logo boyutunu da kart genişliğine göre ölçekle
            if hasattr(self, "logo_label") and hasattr(self, "logo_pixmap") and not self.logo_pixmap.isNull():
                card_width = self.card.width()
                # Kart genişliğinin ~%18'i kadar bir max genişlik
                max_logo_width = max(48, int(card_width * 0.18))
                # Orijinal pixmap'i bu genişliğe kadar küçült, büyütürken bozmamak için min al
                target_w = min(max_logo_width, self.logo_pixmap.width())
                scaled = self.logo_pixmap.scaledToWidth(target_w, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled)

    def toggle_password_visibility(self):
        if self.password_entry.echoMode() == QLineEdit.Password:
            self.password_entry.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_entry.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁️")

    def login(self):
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen kullanıcı adı ve şifreyi girin.")
            return

        if username in USERS and USERS[username] == password:
            # Başarılı girişte direkt dashboard'a geç
            try:
                self.on_success(username)
            except TypeError:
                # Geriye dönük uyumluluk: parametre beklemeyen callback'ler için
                self.on_success()
            self.close()
        else:
            QMessageBox.critical(self, "Hata", "Kullanıcı adı veya şifre hatalı.")


def run_login(on_success_callback):
    app = QApplication(sys.argv)

    # macOS odak çerçevelerini azaltmak için Fusion stilini kullan
    app.setStyle("Fusion")

    window = LoginWindow(on_success_callback)
    window.show()
    app.exec_()
