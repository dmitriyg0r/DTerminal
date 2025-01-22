from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QHeaderView, QMenu,
                           QPushButton, QHBoxLayout, QLineEdit,
                           QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
import paramiko
import os
import stat
import time

class SFTPFileManager(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Панель навигации
        nav_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.returnPressed.connect(self.navigate_to_path)
        
        self.up_button = QPushButton("↑")
        self.up_button.clicked.connect(self.go_up)
        self.up_button.setMaximumWidth(30)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.clicked.connect(self.refresh)
        self.refresh_button.setMaximumWidth(30)
        
        nav_layout.addWidget(self.up_button)
        nav_layout.addWidget(self.path_input)
        nav_layout.addWidget(self.refresh_button)
        
        self.layout.addLayout(nav_layout)
        
        # Дерево файлов
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Имя", "Размер", "Тип", "Изменен"])
        self.file_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_tree.itemDoubleClicked.connect(self.item_double_clicked)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        self.layout.addWidget(self.file_tree)
        
        self.sftp = None
        self.current_path = "/"

    def connect_to_server(self, ssh_client):
        if ssh_client:
            self.sftp = ssh_client.open_sftp()
            self.refresh()

    def refresh(self):
        try:
            self.file_tree.clear()
            self.path_input.setText(self.current_path)
            
            # Получаем список файлов
            files = self.sftp.listdir_attr(self.current_path)
            
            for file_attr in files:
                item = QTreeWidgetItem()
                
                # Имя файла
                item.setText(0, file_attr.filename)
                
                # Размер
                size = file_attr.st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                item.setText(1, size_str)
                
                # Тип
                if file_attr.filename.startswith('.'):
                    item.setText(2, "Скрытый")
                elif file_attr.longname.startswith('d'):
                    item.setText(2, "Папка")
                else:
                    item.setText(2, "Файл")
                
                # Дата изменения
                from datetime import datetime
                mtime = datetime.fromtimestamp(file_attr.st_mtime)
                item.setText(3, mtime.strftime("%Y-%m-%d %H:%M"))
                
                self.file_tree.addTopLevelItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить содержимое папки: {str(e)}")

    def item_double_clicked(self, item: QTreeWidgetItem, column: int):
        file_name = item.text(0)
        file_type = item.text(2)
        
        if file_type == "Папка":
            # Переходим в папку
            new_path = f"{self.current_path.rstrip('/')}/{file_name}"
            self.navigate_to_path(new_path)

    def navigate_to_path(self, path=None):
        if isinstance(path, bool):  # Вызвано через returnPressed
            path = self.path_input.text()
            
        try:
            # Проверяем, существует ли путь
            self.sftp.stat(path)
            self.current_path = path
            self.refresh()
        except:
            QMessageBox.warning(self, "Ошибка", "Указанный путь не существует")
            self.path_input.setText(self.current_path)

    def go_up(self):
        parent_path = "/".join(self.current_path.rstrip("/").split("/")[:-1])
        if not parent_path:
            parent_path = "/"
        self.navigate_to_path(parent_path)

    def show_context_menu(self, position):
        menu = QMenu()
        
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)
        
        # Добавьте дополнительные действия здесь (создание папки, удаление и т.д.)
        
        menu.exec(self.file_tree.viewport().mapToGlobal(position)) 