import sys
from PyQt6.QtWidgets import QApplication
from widgets.main_widget import MainWidget

def main():
    app = QApplication(sys.argv)
    window = MainWidget()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()