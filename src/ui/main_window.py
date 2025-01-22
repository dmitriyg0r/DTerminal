from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QTreeWidget, 
                           QTreeWidgetItem, QLabel, QSplitter,
                           QTabWidget, QMenuBar, QMenu, QStatusBar)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
from .connection_dialog import ConnectionDialog
from .terminal_widget import TerminalWidget
from .file_manager import SFTPFileManager
from connections.ssh_manager import SSHConnection

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DTerminal")
        self.setMinimumSize(1200, 800)
        
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
        new_button = QPushButton("Новое")
        new_button.setMaximumWidth(80)
        delete_button = QPushButton("Удалить")
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
        
    def create_menu(self):
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu('Файл')
        
        new_conn_action = QAction('Новое подключение', self)
        new_conn_action.triggered.connect(self.new_connection)
        file_menu.addAction(new_conn_action)
        
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Вид
        view_menu = menubar.addMenu('Вид')
        
    def new_connection(self):
        dialog = ConnectionDialog(self)
        if dialog.exec():
            connection_data = dialog.get_connection_data()
            item = QTreeWidgetItem(self.connections_tree)
            item.setText(0, connection_data["name"])
            item.setData(0, Qt.ItemDataRole.UserRole, connection_data)
            self.connections_tree.addTopLevelItem(item)

    def delete_connection(self):
        current_item = self.connections_tree.currentItem()
        if current_item:
            self.connections_tree.takeTopLevelItem(
                self.connections_tree.indexOfTopLevelItem(current_item)
            )

    def connect_to_server(self, item):
        connection_data = item.data(0, Qt.ItemDataRole.UserRole)
        if connection_data:
            # Создаем новое подключение
            ssh_connection = SSHConnection()
            success = ssh_connection.connect(
                hostname=connection_data["host"],
                username=connection_data["username"],
                password=connection_data["password"],
                key_filename=connection_data["key_file"] if connection_data["key_file"] else None
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
                self.status_bar.showMessage("Ошибка подключения", 3000)

    def close_tab(self, index):
        tab_name = self.tab_widget.tabText(index)
        if tab_name in self.ssh_connections:
            # Закрываем SSH подключение
            self.ssh_connections[tab_name].disconnect()
            del self.ssh_connections[tab_name]
        
        # Удаляем вкладку
        self.tab_widget.removeTab(index) 