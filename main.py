import sys
import numpy as np

from PySide6.QtCore    import QByteArray, QElapsedTimer, QIODevice
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QGridLayout,
    QLabel, QPushButton, QLineEdit, QApplication
)

from canvas import Canvas
from port   import PortDialog


STOP_MS = 12*1000

SET_PT = 500

CSV_FILE = f"{SET_PT}.csv"

def pid_format(kp, ki, kd, sp):
    return ("0000000"+f"{sp:2.4f}")[-7:]

class MainWindow(QMainWindow):
    serial = None
    set_pt = SET_PT

    buffer = QByteArray(b"")
    data = 0.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1000, 600)
        self.centralwidget = QWidget(self)
        self.gridLayout = QGridLayout(self.centralwidget)

        self.label_kp = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_kp, 0, 0, 1, 1)
        self.label_ki = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_ki, 1, 0, 1, 1)
        self.label_kd = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_kd, 2, 0, 1, 1)
        self.label_sp = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_sp, 3, 0, 1, 1)

        self.lineEdit_kp = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_kp, 0, 1, 1, 1)
        self.lineEdit_ki = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_ki, 1, 1, 1, 1)
        self.lineEdit_kd = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_kd, 2, 1, 1, 1)
        self.lineEdit_sp = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_sp, 3, 1, 1, 1)


        self.canvas = Canvas(parent=self)
        self.gridLayout.addWidget(self.canvas, 0, 3, 5, 9)

        self.button_send = QPushButton(self.centralwidget)
        self.gridLayout.addWidget(self.button_send, 5, 0, 1, 1)
        self.button_port = QPushButton(self.centralwidget)
        self.gridLayout.addWidget(self.button_port, 5, 2, 1, 1)
        self.label_port = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_port, 5, 3, 1, 1)
        self.button_run = QPushButton(self.centralwidget)
        self.gridLayout.addWidget(self.button_run, 5, 11, 1, 1)


        self.setCentralWidget(self.centralwidget)

        self.setUpText()
        # self.button_run.setEnabled(False)
        # can't set pid now
        self.lineEdit_kp.setEnabled(False)
        self.lineEdit_ki.setEnabled(False)
        self.lineEdit_kd.setEnabled(False)
        # won't send now
        # self.button_send.setEnabled(False)

        print("GUI started")

        self.button_send.clicked.connect(self.onSend)
        self.button_port.clicked.connect(self.onConnect)
        self.button_run.clicked.connect(self.onRun)
        self.button_run.setEnabled(False)

        self.timer = QElapsedTimer()
        self.is_running = False

    def setUpText(self):
        self.setWindowTitle("tuning")
        self.label_kp.setText("Kp")
        self.label_ki.setText("Ki")
        self.label_kd.setText("Kd")
        self.label_sp.setText("Set Point")
        self.lineEdit_kp.setText("0")
        self.lineEdit_ki.setText("0")
        self.lineEdit_kd.setText("0")
        self.lineEdit_sp.setText("0")
        self.button_send.setText("Send")
        self.label_port.setText("")
        self.button_port.setText("Connect")
        self.button_run.setText("Start")

    def onRun(self):
        if self.is_running:
            self.stop()
        else:
            self.start()

    def stop(self):
        print('Stopped')
        self.button_run.setText('Start')
        self.is_running = False
        self.serial.readyRead.disconnect(self.onReadyRead)
        self.serial.errorOccurred.disconnect(self.onErrorOccurred)
        self.saveCSV(CSV_FILE)

    def start(self):
        print('Started')
        self.button_run.setText('Stop')
        self.is_running = True
        self.serial.readyRead.connect(self.onReadyRead)
        self.serial.errorOccurred.connect(self.onErrorOccurred)
        self.timer.start()
        self.canvas.reset()

    def onConnect(self):
        serial = PortDialog.getSerial(self)
        if serial is not None:
            name = serial.portName()
            if self.serial is not None:
                self.serial.close()
            if serial.open(QIODevice.OpenModeFlag.ReadWrite):
                self.serial = serial
                self.label_port.setText(name)
                self.button_run.setEnabled(True)
                print(f"Serial connected: {name}")
            else:
                self.serial = None
                self.button_run.setEnabled(False)
                print(f'Failed to open serial port: {name}')

    def onReadyRead(self):
        self.buffer.append(self.serial.readAll())
        idx_l = self.buffer.lastIndexOf(b"[")
        idx_r = self.buffer.lastIndexOf(b"]")
        if idx_l != -1 and idx_r != -1 and idx_l < idx_r:
            msg = self.buffer.mid(1+idx_l, idx_r-idx_l-1)
            msg = msg.data().decode()
            # rslt = parse.parse("{:f}", msg)
            self.data = float(msg)
            # if rslt is not None:
            #     self.data = rslt[0]
            # else:
            #     print("Something wrong")
            self.buffer = QByteArray(b"")

            dur = self.timer.elapsed()
            self.canvas.animate(dur, self.data, self.set_pt)
            print(msg)

            if dur >= STOP_MS:
                self.stop()

        # print(f'Serial read "{msg}"')

    def onErrorOccurred(self):
        print(str(self.serial.error()))
        self.serial.clearError()

    def onSend(self):
        kp = float(self.lineEdit_kp.text())
        ki = float(self.lineEdit_ki.text())
        kd = float(self.lineEdit_kd.text())
        self.set_pt = float(self.lineEdit_sp.text())
        text = pid_format(kp, ki, kd, self.set_pt)

        if self.serial is not None:
            qba = QByteArray(text.encode("utf-8"))
            self.serial.write(qba)

        print(f'Serial sent text "{text}"')

    def saveCSV(self, name: str):
        x = self.canvas.x1
        y = self.canvas.y1
        np.savetxt(
            name, np.array([x, y]).T,
            fmt='%g', delimiter=','
        )

    def closeEvent(self, event):
        if self.serial is not None:
            self.serial.close()
        print("GUI closing")


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
