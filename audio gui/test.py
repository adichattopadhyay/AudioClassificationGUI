import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("My PyQt5 Application")
        self.setGeometry(100, 100, 400, 300)

        # Add a label
        label = QLabel("Hello, PyQt5!", self)
        label.setGeometry(150, 50, 200, 30)

        # Add a button
        button = QPushButton("Click Me!", self)
        button.setGeometry(150, 100, 100, 30)

        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())
