import sys
import os
from PyQt6.QtWidgets import QApplication

# Добавляем путь к src в PYTHONPATH
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(src_path)

from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Загрузка стилей
    with open('src/ui/styles.qss', 'r') as f:
        app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 