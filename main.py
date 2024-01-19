from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit, QFileDialog
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading
import zipfile
import datetime
import time
import json

DIRECTORY_PATH = ""

class FileHoster(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server) -> None:
        super().__init__(request, client_address, server)

    @staticmethod
    def check_dir(folderpath: str, fileSuccess: list) -> list:
        fileList = os.listdir(folderpath)

        for content in fileList:
            contentPath = os.path.join(folderpath, content)

            if os.path.isdir(contentPath):
                FileHoster.check_dir(contentPath, fileSuccess)

            elif os.path.isfile(contentPath):
                print(contentPath)
                fileSuccess.append(contentPath)

        return fileSuccess

    def do_GET(self) -> None:
        global DIRECTORY_PATH

        fileSuccess = []
        files = self.check_dir(DIRECTORY_PATH, fileSuccess)
        print(f"Found {len(files)} files in {DIRECTORY_PATH}")

        if len(files) == 0:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"No Files Uploaded.")
        
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/zip")
            self.send_header("Content-disposition", f"attachment; filename=files_{datetime.datetime.now().strftime('%B %d')}.zip")
            self.end_headers()
            
            try:

                with zipfile.ZipFile(self.wfile, "w") as zipf:
                    for file in files:
                        with open(file, "rb") as f:
                            fileContent = f.read()
                        filtered_path = os.path.relpath(file)
                        zipf.writestr(filtered_path, fileContent)

            except (ConnectionAbortedError, ConnectionResetError):
                pass

    def do_POST(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        response_data = {"time": date}
        response_json = json.dumps(response_data)

        self.wfile.write(bytes(response_json, "utf-8"))


class Window(QMainWindow):
    def __init__(self) -> None:
        super(Window, self).__init__()
        self.server = None

        self.setGeometry(650, 250, 300, 200)
        self.setWindowTitle("File Hoster")
        self.initUI()

    def initUI(self) -> None:
        # Label imitating a terminal
        self.terminal = QtWidgets.QLabel(self)
        self.terminal.setText("")
        self.terminal.move(50, 150)

        # Start server button
        self.bS = QtWidgets.QPushButton(self)
        self.bS.setText("Start")
        self.bS.clicked.connect(self.on_start)

        # Stop server button
        self.bE = QtWidgets.QPushButton(self)
        self.bE.setText("Stop")
        self.bE.clicked.connect(self.on_stop)
        self.bE.move(200, 0)

        # Select folder button
        self.fSelect = QtWidgets.QPushButton(self)
        self.fSelect.setText("Select folder")
        self.fSelect.clicked.connect(self.selectFolder)
        self.fSelect.move(0, 150)

        # Folder path textbox
        self.foldertxt = QLineEdit(self)
        self.foldertxt.move(120, 145)
        self.foldertxt.resize(100, 35)
        self.foldertxt.setPlaceholderText("Folder to upload")

        # Host textbox
        self.txtHost = QLineEdit(self)
        self.txtHost.move(0, 50)
        self.txtHost.resize(200, 35)
        self.txtHost.setPlaceholderText("localhost")

        # Port textbox
        self.txtPort = QLineEdit(self)
        self.txtPort.move(0, 100)
        self.txtPort.resize(200, 35)
        self.txtPort.setPlaceholderText("80")

    def on_start(self) -> None:
        global DIRECTORY_PATH
        if len(self.txtHost.text()) > 0 and self.txtPort.text().isdigit() and os.path.exists(self.foldertxt.text()):
            DIRECTORY_PATH = self.foldertxt.text()
            host = self.txtHost.text()
            port = int(self.txtPort.text())

            self.server_thread = threading.Thread(target=self.start_server, args=(host, port))
            self.server_thread.start()
        else:
            self.errorMsg("Invalid host, port or folderpath!")
    
    def on_stop(self) -> None:
        if self.server:
           self.updateTerminal("Stopping server...")
           
           self.server.shutdown()
           self.server_thread.join()

           self.updateTerminal("Server stopped.")
           self.server = None

           os.system("cls" if os.name == "nt" else "clear")
        else:
           self.errorMsg("Server is not running!")

    def start_server(self, host: str, port: int) -> None:
        try:
            self.server = HTTPServer((host, port), FileHoster)
            self.updateTerminal("Server now running...")
            self.server.serve_forever()

        except Exception as e:
            print(f"Error starting server:\n{e}")

    def updateTerminal(self, new_text: str) -> None:
        self.terminal.setText(new_text)

    def selectFolder(self) -> None:
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select the folder you want to host.")
        self.foldertxt.setText(folderpath)

    @staticmethod
    def errorMsg(errorCode: str) -> None:
        # Messagebox for errors
        msgBox = QMessageBox()
        msgBox.setText(errorCode)
        msgBox.setWindowTitle("Error")
        msgBox.setStandardButtons(QMessageBox.Ok)

        msgBox.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
