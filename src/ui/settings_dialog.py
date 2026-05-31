import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from src.config import Config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.resize(500, 150)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 保存路径设置
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("纪要保存路径:"))
        
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setText(Config.get_save_dir())
        path_layout.addWidget(self.path_input)
        
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.btn_browse)
        
        layout.addLayout(path_layout)
        
        layout.addStretch()
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存纪要的文件夹", self.path_input.text())
        if folder:
            self.path_input.setText(os.path.normpath(folder))

    def save_settings(self):
        new_path = self.path_input.text()
        if not os.path.exists(new_path):
            try:
                os.makedirs(new_path, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法创建文件夹:\n{e}")
                return
        
        Config.set_save_dir(new_path)
        QMessageBox.information(self, "成功", "设置已保存！")
        self.accept()
