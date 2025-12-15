import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QFont

from login import LoginWindow
from dashboard import Dashboard

# Global değişkenler
login_window = None
dashboard_window = None

def start_dashboard(username):
    """Giriş başarılı olduğunda dashboard'u başlat"""
    global login_window, dashboard_window
    
    # Login penceresini gizle
    if login_window:
        login_window.hide()
    
    # Dashboard'u oluştur ve göster
    dashboard_window = Dashboard(username, on_logout=return_to_login)
    dashboard_window.show()


def return_to_login():
    """Dashboard kapanınca giriş ekranına dön"""
    global login_window, dashboard_window
    
    if dashboard_window:
        dashboard_window.close()
        dashboard_window = None
    
    if login_window is None:
        login_window = LoginWindow(start_dashboard)
    else:
        # Alanları temizle ve yeniden odakla
        login_window.username_entry.clear()
        login_window.password_entry.clear()
        login_window.username_entry.setFocus()
    
    login_window.show()
    login_window.raise_()

def main():
    """Ana uygulama"""
    global login_window
    
    app = QApplication(sys.argv)

    # Uygulama genelinde Roboto Slab fontunu kullan
    try:
        font_path = Path("assets/fonts/RobotoSlab.ttf")
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                roboto_family = families[0]
                app.setFont(QFont(roboto_family, 11))
    except Exception as e:
        # Font yüklenemezse sessizce geç, varsayılan font kullanılır
        print(f"Font yükleme hatası: {e}")
    
    login_window = LoginWindow(start_dashboard)
    login_window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
