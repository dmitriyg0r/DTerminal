from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QFileDialog)

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новое подключение")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Название подключения
        name_layout = QHBoxLayout()
        name_label = QLabel("Название:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        
        # Хост
        host_layout = QHBoxLayout()
        host_label = QLabel("Хост:")
        self.host_input = QLineEdit()
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        
        # Порт
        port_layout = QHBoxLayout()
        port_label = QLabel("Порт:")
        self.port_input = QLineEdit("22")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        
        # Имя пользователя
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
        
        # SSH ключ
        key_layout = QHBoxLayout()
        key_label = QLabel("SSH ключ:")
        self.key_input = QLineEdit()
        self.key_browse = QPushButton("Обзор")
        self.key_browse.clicked.connect(self.browse_key)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        key_layout.addWidget(self.key_browse)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        # Добавляем все в основной layout
        layout.addLayout(name_layout)
        layout.addLayout(host_layout)
        layout.addLayout(port_layout)
        layout.addLayout(username_layout)
        layout.addLayout(password_layout)
        layout.addLayout(key_layout)
        layout.addLayout(buttons_layout)

    def browse_key(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите SSH ключ",
            "",
            "Все файлы (*.*)"
        )
        if filename:
            self.key_input.setText(filename)

    def get_connection_data(self):
        return {
            "name": self.name_input.text(),
            "host": self.host_input.text(),
            "port": self.port_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "key_file": self.key_input.text()
        } 