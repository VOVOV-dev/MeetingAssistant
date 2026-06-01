import sys

try:
    from PyQt6.QtWidgets import QApplication
except ModuleNotFoundError:
    print(
        'PyQt6 is not installed in this Python environment. '
        'Use the packaged release in release/dist, or install the project dependencies first.'
    )
    sys.exit(1)

from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用名称，避免某些系统下的显示问题
    app.setApplicationName("智能会议纪要系统")
    
    window = MainWindow()
    window.show()
    try:
        from src.config import log
        log('Application started')
    except Exception:
        pass
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
