from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor, QKeyEvent
import threading
import paramiko

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
        
        self.terminal = QTextEdit()
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 5px;
            }
        """)
        self.terminal.setReadOnly(True)  # Делаем терминал только для чтения
        self.layout.addWidget(self.terminal)
        
        self.ssh_client = None
        self.channel = None
        self.reader = None
        self.terminal_lock = threading.Lock()

    def connect_to_server(self, ssh_client):
        self.ssh_client = ssh_client
        if self.ssh_client:
            try:
                # Создаем интерактивный shell с псевдотерминалом
                self.channel = self.ssh_client.get_transport().open_session()
                self.channel.get_pty(term='xterm', width=80, height=24)
                self.channel.invoke_shell()
                
                # Запускаем поток чтения
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

    def keyPressEvent(self, event: QKeyEvent):
        if not self.channel or self.channel.closed:
            return

        try:
            # Обрабатываем специальные клавиши
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.channel.send("\r")
            elif event.key() == Qt.Key.Key_Backspace:
                self.channel.send("\x7f")
            elif event.key() == Qt.Key.Key_Up:
                self.channel.send("\x1b[A")
            elif event.key() == Qt.Key.Key_Down:
                self.channel.send("\x1b[B")
            elif event.key() == Qt.Key.Key_Right:
                self.channel.send("\x1b[C")
            elif event.key() == Qt.Key.Key_Left:
                self.channel.send("\x1b[D")
            elif event.key() == Qt.Key.Key_Home:
                self.channel.send("\x1b[H")
            elif event.key() == Qt.Key.Key_End:
                self.channel.send("\x1b[F")
            # Обработка Ctrl+C
            elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.channel.send("\x03")
            # Обработка Ctrl+D
            elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.channel.send("\x04")
            # Обычный ввод текста
            elif len(event.text()) > 0:
                self.channel.send(event.text())

        except Exception as e:
            self.append_text(f"\nError sending command: {str(e)}\n")

    def closeEvent(self, event):
        if self.reader:
            self.reader.stop()
        if self.channel:
            self.channel.close()
        super().closeEvent(event)

    def resizeEvent(self, event):
        if self.channel and not self.channel.closed:
            try:
                # Получаем новый размер терминала в символах
                # Предполагаем, что один символ примерно 10x20 пикселей
                width = self.terminal.width() // 10
                height = self.terminal.height() // 20
                self.channel.resize_pty(width=width, height=height)
            except:
                pass
        super().resizeEvent(event) 