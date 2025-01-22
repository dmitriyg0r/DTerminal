from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor, QKeyEvent
import threading
import paramiko
import json
import os

class TerminalReader(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.running = True

    def run(self):
        while self.running and not self.channel.closed:
            if self.channel.recv_ready():
                data = self.channel.recv(1024).decode('utf-8', errors='ignore')
                if data:
                    self.data_received.emit(data)
            elif self.channel.recv_stderr_ready():
                data = self.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
                if data:
                    self.data_received.emit(data)
            self.msleep(10)

    def stop(self):
        self.running = False
        self.wait()

class TerminalWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.terminal = QTextEdit()
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 10px;
                selection-background-color: #264f78;
                border: none;
            }
        """)
        self.terminal.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.terminal.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.terminal.setUndoRedoEnabled(False)
        self.terminal.setReadOnly(False)
        self.terminal.keyPressEvent = self.handle_key_press
        self.layout.addWidget(self.terminal)
        
        self.ssh_client = None
        self.channel = None
        self.reader = None
        self.terminal_lock = threading.Lock()
        self.command_history = []
        self.history_index = -1
        self.current_command = ""
        self.prompt_length = 0
        
        # Добавляем путь к файлу конфигурации
        self.config_file = os.path.expanduser('~/.dterminal/connections.json')

    def connect_to_server(self, ssh_client):
        self.ssh_client = ssh_client
        if self.ssh_client:
            try:
                self.channel = self.ssh_client.get_transport().open_session()
                term_width = self.terminal.width() // 10
                term_height = self.terminal.height() // 20
                
                self.channel.get_pty(
                    term='xterm-256color',
                    width=term_width,
                    height=term_height
                )
                self.channel.invoke_shell()
                
                self.reader = TerminalReader(self.channel)
                self.reader.data_received.connect(self.append_text)
                self.reader.start()
                
            except Exception as e:
                self.append_text(f"Error: {str(e)}\n")

    def append_text(self, text):
        with self.terminal_lock:
            cursor = self.terminal.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(text)
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()
            # Сохраняем позицию промпта
            if text.endswith('$ ') or text.endswith('# '):
                self.prompt_length = len(self.terminal.toPlainText())

    def handle_key_press(self, event: QKeyEvent):
        if not self.channel or self.channel.closed:
            event.ignore()
            return

        try:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                command = self.get_current_command()
                if command:
                    self.command_history.append(command)
                    self.history_index = len(self.command_history)
                self.channel.send('\n')
                self.current_command = ""
            
            elif event.key() == Qt.Key.Key_Backspace:
                if len(self.get_current_command()) > 0:
                    # Используем стандартный DEL для Linux
                    self.channel.send('\x7f')
                    self.current_command = self.current_command[:-1]
            
            elif event.key() == Qt.Key.Key_Up:
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.clear_current_line()
                    command = self.command_history[self.history_index]
                    self.channel.send(command)
                    self.current_command = command
            
            elif event.key() == Qt.Key.Key_Down:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.clear_current_line()
                    command = self.command_history[self.history_index]
                    self.channel.send(command)
                    self.current_command = command
                elif self.history_index == len(self.command_history) - 1:
                    self.history_index = len(self.command_history)
                    self.clear_current_line()
                    self.current_command = ""
            
            elif event.key() == Qt.Key.Key_Left:
                cursor_pos = self.terminal.textCursor().position()
                if cursor_pos > self.prompt_length:
                    self.channel.send('\x1b[D')
            
            elif event.key() == Qt.Key.Key_Right:
                self.channel.send('\x1b[C')
            
            elif event.key() == Qt.Key.Key_Home:
                self.channel.send('\x1b[H')
            
            elif event.key() == Qt.Key.Key_End:
                self.channel.send('\x1b[F')
            
            elif event.key() == Qt.Key.Key_Tab:
                self.channel.send('\t')
            
            elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.channel.send('\x03')
            
            elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.channel.send('\x04')
            
            elif event.text() and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.channel.send(event.text())
                self.current_command += event.text()

            event.accept()
            
        except Exception as e:
            self.append_text(f"\nError sending command: {str(e)}\n")
            event.ignore()

    def get_current_command(self):
        text = self.terminal.toPlainText()
        if len(text) > self.prompt_length:
            return text[self.prompt_length:].strip()
        return ""

    def clear_current_line(self):
        text = self.terminal.toPlainText()
        if len(text) > self.prompt_length:
            self.channel.send('\x1b[2K\r')  # Очищаем текущую строку
            self.channel.send(text[:self.prompt_length])  # Восстанавливаем промпт

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.terminal.setFocus()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.terminal.setFocus()

    def closeEvent(self, event):
        if self.reader:
            self.reader.stop()
        if self.channel:
            self.channel.close()
        super().closeEvent(event)

    def resizeEvent(self, event):
        if self.channel and not self.channel.closed:
            try:
                width = self.terminal.width() // 10
                height = self.terminal.height() // 20
                self.channel.resize_pty(width=width, height=height)
            except:
                pass
        super().resizeEvent(event)

    def save_connections(self, connections_data):
        """Сохраняет список подключений в файл"""
        try:
            # Убираем пароли перед сохранением для безопасности
            safe_connections = []
            for conn in connections_data:
                safe_conn = conn.copy()
                if 'password' in safe_conn:
                    safe_conn['password'] = ''  # Очищаем пароль
                safe_connections.append(safe_conn)
                
            with open(self.config_file, 'w') as f:
                json.dump(safe_connections, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить подключения: {str(e)}")

    def load_connections(self):
        """Загружает список подключений из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить подключения: {str(e)}")
        return [] 