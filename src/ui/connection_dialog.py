from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QFileDialog)

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новое подключение")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Имя подключения
        name_layout = QHBoxLayout()
        name_label = QLabel("Имя:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        
        # Хост
        host_layout = QHBoxLayout()
        host_label = QLabel("Хост:")
        self.host_input = QLineEdit()
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        
        # Пользователь
        username_layout = QHBoxLayout()
        username_label = QLabel("Пользователь:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        
        # Пароль
        password_layout = QHBoxLayout()
        password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        
        # SSH ключ (опционально)
        key_layout = QHBoxLayout()
        key_label = QLabel("SSH ключ (опционально):")
        self.key_file_input = QLineEdit()
        browse_button = QPushButton("Обзор")
        browse_button.clicked.connect(self.browse_key_file)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_file_input)
        key_layout.addWidget(browse_button)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Отмена")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        
        # Добавляем все в основной layout
        layout.addLayout(name_layout)
        layout.addLayout(host_layout)
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addLayout(key_layout)
        layout.addLayout(buttons_layout)
        
        # Устанавливаем фокус на первое поле
        self.name_input.setFocus()

    def browse_key_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите SSH ключ",
            "",
            "Все файлы (*.*)"
        )
        if file_name:
            self.key_file_input.setText(file_name)

    def get_connection_data(self):
        data = {
            "name": self.name_input.text(),
            "host": self.host_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text()
        }
        
        # Добавляем путь к ключу только если он указан
        key_file = self.key_file_input.text().strip()
        if key_file:
            data["key_file"] = key_file
            
        return data 