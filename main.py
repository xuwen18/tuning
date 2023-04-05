import sys

from PySide6.QtCore    import QByteArray, QTimer, QIODevice
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QGridLayout,
    QLabel, QPushButton, QLineEdit, QApplication
)

from canvas import Canvas
from port   import PortDialog

INTERVAL = 500

def pid_format(kp, ki, kd):
    return f",{kp},{ki},{kd}"

class MainWindow(QMainWindow):
    serial = None
    set_pt = 0
    data = 0.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(640, 480)
        self.centralwidget = QWidget(self)
        self.gridLayout = QGridLayout(self.centralwidget)

        self.label_kp = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_kp, 0, 0, 1, 1)

        self.label_ki = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_ki, 1, 0, 1, 1)

        self.label_kd = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_kd, 2, 0, 1, 1)

        self.lineEdit_kp = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_kp, 0, 1, 1, 1)

        self.lineEdit_ki = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_ki, 1, 1, 1, 1)

        self.lineEdit_kd = QLineEdit(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit_kd, 2, 1, 1, 1)


        self.canvas = Canvas(parent=self)
        self.gridLayout.addWidget(self.canvas, 0, 2, 5, 5)


        self.button_send = QPushButton(self.centralwidget)
        self.gridLayout.addWidget(self.button_send, 5, 0, 1, 1)

        self.label_port = QLabel(self.centralwidget)
        self.gridLayout.addWidget(self.label_port, 5, 1, 1, 1)

        self.button_port = QPushButton(self.centralwidget)
        self.gridLayout.addWidget(self.button_port, 5, 2, 1, 1)

        self.button_run = QPushButton(self.centralwidget)
        self.gridLayout.addWidget(self.button_run, 5, 6, 1, 1)


        self.setCentralWidget(self.centralwidget)

        self.setUpText()
        self.button_run.setEnabled(False)
        print("GUI started")

        self.button_send.clicked.connect(self.onSend)
        self.button_port.clicked.connect(self.onConnect)
        self.button_run.clicked.connect(self.onRun)

        self.interval = INTERVAL
        self.timer = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.onTimeout)
        self.i = 0

    def setUpText(self):
        self.setWindowTitle("tuning")
        self.label_kp.setText("Kp")
        self.label_ki.setText("Ki")
        self.label_kd.setText("Kd")
        self.button_send.setText("Send")
        self.label_port.setText("")
        self.button_port.setText("Connect")
        self.button_run.setText("Start")

    def onRun(self):
        if self.timer.isActive():
            self.stop()
        else:
            self.start()

    def stop(self):
        self.timer.stop()
        print('Stopped')
        self.button_run.setText('Start')
        self.i = 0

    def start(self):
        self.timer.start()
        print('Started')
        self.button_run.setText('Stop')
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
                print(f"Serial connected: {name}")

                self.button_run.setEnabled(True)
            else:
                self.serial = None
                print(f'Failed to open serial port: {name}')

                self.button_run.setEnabled(False)

    def onTimeout(self):
        self.i += 1
        dur = self.interval*self.i

        str = self.serial.readAll().data().decode()
        print(f'Serial read "{str}"')
        if len(str) > 0:
            self.data = float(str)

        self.canvas.animate(dur, self.data, self.set_pt)

    def onSend(self):
        kp = float(self.lineEdit_kp.text())
        ki = float(self.lineEdit_ki.text())
        kd = float(self.lineEdit_kd.text())
        text = pid_format(kp, ki, kd)
        print(f'Serial sent text "{text}"')
        if self.serial is not None:
            qba = QByteArray(text.encode("utf-8"))
            self.serial.write(qba)

    def closeEvent(self, event):
        if self.serial is not None:
            self.serial.close()
        print("GUI closing")


app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
