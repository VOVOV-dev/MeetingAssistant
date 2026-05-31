import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用名称，避免某些系统下的显示问题
    app.setApplicationName("智能会议纪要系统")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
