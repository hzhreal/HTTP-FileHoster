from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading
import zipfile
import datetime
import time
import json

DIRECTORYPATH = "Storage"  # where you will put the files you want to host

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
        folderpath = DIRECTORYPATH
        fileSuccess = []
        files = self.check_dir(folderpath, fileSuccess)
        print(f"Found {len(files)} files in {folderpath}")

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
                        zipf.writestr(file, fileContent)

            except ConnectionAbortedError or ConnectionResetError:
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
        if len(self.txtHost.text()) > 0 and self.txtPort.text().isdigit():
            host = self.txtHost.text()
            port = int(self.txtPort.text())

            self.server_thread = threading.Thread(target=self.start_server, args=(host, port))
            self.server_thread.start()
        else:
            self.errorMsg("Invalid host or port!")
    
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

    @staticmethod
    def errorMsg(errorCode: str) -> None:
        # Messagebox for errors
        msgBox = QMessageBox()
        msgBox.setText(errorCode)
        msgBox.setWindowTitle("Error")
        msgBox.setStandardButtons(QMessageBox.Ok)

        msgBox.exec()

if __name__ == "__main__":
    if not os.path.exists(DIRECTORYPATH):
        try:
            os.makedirs(DIRECTORYPATH)
        except:
            print(f"Could not create directory {DIRECTORYPATH}. Make sure it exists before running the program.")
            exit()

    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
