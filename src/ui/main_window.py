from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QTreeWidget, 
                           QTreeWidgetItem, QLabel, QSplitter,
                           QTabWidget, QMenuBar, QMenu, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
from .connection_dialog import ConnectionDialog
from .terminal_widget import TerminalWidget
from .file_manager import SFTPFileManager
from connections.ssh_manager import SSHConnection
import json
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DTerminal")
        self.setMinimumSize(1200, 800)
        
        # Устанавливаем иконку приложения
        self.setWindowIcon(QIcon("src/ui/icons/terminal.png"))
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Левая панель с подключениями
        connections_panel = QWidget()
        connections_panel.setMaximumWidth(250)
        connections_layout = QVBoxLayout(connections_panel)
        connections_layout.setContentsMargins(5, 5, 5, 5)
        
        # Дерево подключений
        self.connections_tree = QTreeWidget()
        self.connections_tree.setHeaderLabel("Подключения")
        self.connections_tree.setIconSize(QSize(16, 16))
        self.connections_tree.itemDoubleClicked.connect(self.connect_to_server)
        
        # Кнопки управления подключениями
        buttons_layout = QHBoxLayout()
        new_button = QPushButton(QIcon("src/ui/icons/add.png"), "Новое")
        new_button.setMaximumWidth(80)
        delete_button = QPushButton(QIcon("src/ui/icons/delete.png"), "Удалить")
        delete_button.setMaximumWidth(80)
        
        buttons_layout.addWidget(new_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        
        connections_layout.addWidget(self.connections_tree)
        connections_layout.addLayout(buttons_layout)
        
        # Правая панель с вкладками
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Добавляем панели в основной layout
        layout.addWidget(connections_panel)
        layout.addWidget(self.tab_widget)
        
        # Создаем строку состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Создаем меню
        self.create_menu()
        
        # Подключаем сигналы
        new_button.clicked.connect(self.new_connection)
        delete_button.clicked.connect(self.delete_connection)
        
        self.ssh_connections = {}  # Словарь для хранения активных подключений
        
        self.config_file = os.path.expanduser('~/.dterminal/connections.json')
        
        # Загружаем сохраненные подключения
        self.load_saved_connections()
        
    def create_menu(self):
        menubar = self.menuBar()
        
        # Меню Файл с иконками
        file_menu = menubar.addMenu('Файл')
        
        new_conn_action = QAction(QIcon("src/ui/icons/add.png"), 'Новое подключение', self)
        new_conn_action.setShortcut('Ctrl+N')
        new_conn_action.triggered.connect(self.new_connection)
        file_menu.addAction(new_conn_action)
        
        exit_action = QAction(QIcon("src/ui/icons/exit.png"), 'Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Вид
        view_menu = menubar.addMenu('Вид')
        
    def load_saved_connections(self):
        """Загружает сохраненные подключения в дерево"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    connections = json.load(f)
                    for conn_data in connections:
                        item = QTreeWidgetItem(self.connections_tree)
                        item.setText(0, conn_data["name"])
                        item.setData(0, Qt.ItemDataRole.UserRole, conn_data)
                        self.connections_tree.addTopLevelItem(item)
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка загрузки подключений: {str(e)}", 3000)

    def save_connections(self):
        """Сохраняет все подключения в файл"""
        connections = []
        root = self.connections_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            conn_data = item.data(0, Qt.ItemDataRole.UserRole)
            if conn_data:
                # Сохраняем все данные включая пароль
                connections.append(conn_data)
                
        try:
            with open(self.config_file, 'w') as f:
                json.dump(connections, f, indent=4)
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка сохранения подключений: {str(e)}", 3000)

    def new_connection(self):
        dialog = ConnectionDialog(self)
        if dialog.exec():
            connection_data = dialog.get_connection_data()
            item = QTreeWidgetItem(self.connections_tree)
            item.setText(0, connection_data["name"])
            item.setData(0, Qt.ItemDataRole.UserRole, connection_data)
            self.connections_tree.addTopLevelItem(item)
            # Сохраняем подключения после добавления нового
            self.save_connections()

    def delete_connection(self):
        current_item = self.connections_tree.currentItem()
        if current_item:
            self.connections_tree.takeTopLevelItem(
                self.connections_tree.indexOfTopLevelItem(current_item)
            )
            # Сохраняем подключения после удаления
            self.save_connections()

    def connect_to_server(self, item):
        connection_data = item.data(0, Qt.ItemDataRole.UserRole)
        if connection_data:
            try:
                # Создаем новое подключение
                ssh_connection = SSHConnection()
                
                # Проверяем наличие необходимых данных
                if not connection_data.get("host"):
                    raise ValueError("Не указан хост")
                if not connection_data.get("username"):
                    raise ValueError("Не указан пользователь")
                if not connection_data.get("password") and not connection_data.get("key_file"):
                    raise ValueError("Необходимо указать пароль или SSH ключ")
                
                success = ssh_connection.connect(
                    hostname=connection_data["host"],
                    username=connection_data["username"],
                    password=connection_data.get("password"),
                    key_filename=connection_data.get("key_file")
                )
                
                if success:
                    # Создаем новую вкладку с разделителем
                    tab = QSplitter(Qt.Orientation.Vertical)
                    
                    # Создаем терминал и файловый менеджер для этого подключения
                    terminal = TerminalWidget()
                    file_manager = SFTPFileManager()
                    
                    terminal.connect_to_server(ssh_connection.client)
                    file_manager.connect_to_server(ssh_connection.client)
                    
                    tab.addWidget(terminal)
                    tab.addWidget(file_manager)
                    
                    # Добавляем вкладку
                    tab_name = f"{connection_data['name']} ({connection_data['host']})"
                    self.tab_widget.addTab(tab, tab_name)
                    self.tab_widget.setCurrentWidget(tab)
                    
                    # Сохраняем подключение
                    self.ssh_connections[tab_name] = ssh_connection
                    
                    self.status_bar.showMessage(f"Подключено к {connection_data['host']}", 3000)
                else:
                    error_msg = "Ошибка подключения к серверу. Проверьте логи для деталей."
                    QMessageBox.warning(self, "Ошибка", error_msg)
                    self.status_bar.showMessage("Ошибка подключения", 3000)
                    
            except Exception as e:
                error_msg = f"Ошибка: {str(e)}"
                QMessageBox.warning(self, "Ошибка", error_msg)
                self.status_bar.showMessage("Ошибка подключения", 3000)

    def close_tab(self, index):
        tab_name = self.tab_widget.tabText(index)
        if tab_name in self.ssh_connections:
            # Закрываем SSH подключение
            self.ssh_connections[tab_name].disconnect()
            del self.ssh_connections[tab_name]
        
        # Удаляем вкладку
        self.tab_widget.removeTab(index)

    def closeEvent(self, event):
        # Сохраняем подключения при закрытии приложения
        self.save_connections()
        super().closeEvent(event) 