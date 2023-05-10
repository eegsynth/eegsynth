import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.layout = QVBoxLayout()
        self.label = QLabel("My text")

        self.layout.addWidget(self.label)
        self.setWindowTitle("My Own Title")
        self.setLayout(self.layout)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
