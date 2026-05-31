import os
import markdown
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTextEdit, QSplitter)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl

from src.config import Config
from src.utils.media import extract_audio
from src.services.asr_dashscope import DashScopeASRService
from src.services.llm_openai import LLMService

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            Config.ensure_temp_dir()
            
            # Step 1: Media Processing
            self.progress.emit("检查并提取音频...")
            audio_path = extract_audio(self.file_path, Config.TEMP_DIR)
            
            # Step 2: ASR
            asr_svc = DashScopeASRService(Config.DASHSCOPE_API_KEY)
            self.progress.emit("连接语音识别服务...")
            raw_text = asr_svc.recognize(audio_path, callback=self._emit_progress)
            
            self.progress.emit("语音识别完成。")
            
            # Step 3: LLM
            llm_svc = LLMService(Config.LLM_API_KEY, Config.LLM_BASE_URL, Config.LLM_MODEL_NAME)
            self.progress.emit("正在通过大模型进行理解与总结...")
            summary = llm_svc.generate_meeting_minutes(raw_text, progress_callback=self._emit_progress)
            
            self.progress.emit("处理完毕！")
            self.finished.emit(summary)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def _emit_progress(self, msg: str):
        self.progress.emit(msg)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能会议纪要与总结系统")
        self.resize(1000, 700)
        
        self.selected_file = None
        
        self._init_ui()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        self.btn_select_file = QPushButton("📂 选择音视频文件")
        self.btn_select_file.clicked.connect(self.select_file)
        
        self.lbl_file_path = QLabel("未选择文件")
        self.lbl_file_path.setStyleSheet("color: gray;")
        
        self.btn_start = QPushButton("🚀 开始生成纪要")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        
        toolbar_layout.addWidget(self.btn_select_file)
        toolbar_layout.addWidget(self.lbl_file_path, stretch=1)
        toolbar_layout.addWidget(self.btn_start)
        main_layout.addLayout(toolbar_layout)
        
        # 中间的拆分视图 (左侧日志，右侧结果)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 日志视图
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("系统运行日志将展示在这里...")
        splitter.addWidget(self.log_view)
        
        # Web渲染视图 (渲染 Markdown 与 Mermaid)
        self.web_view = QWebEngineView()
        self.web_view.setHtml(self.get_html_template("# 会议纪要\n等待生成..."))
        splitter.addWidget(self.web_view)
        
        # 调整拆分比例 (1:3)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter, stretch=1)
        
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择音视频文件", 
            "", 
            "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.m4a)"
        )
        if file_path:
            self.selected_file = file_path
            self.lbl_file_path.setText(os.path.basename(file_path))
            self.lbl_file_path.setToolTip(file_path)
            self.btn_start.setEnabled(True)
            self.log_message(f"已选择文件: {file_path}")
            
    def log_message(self, msg: str):
        self.log_view.append(msg)
        
    def start_processing(self):
        if not self.selected_file:
            return
            
        # 检查 API Key
        if not Config.DASHSCOPE_API_KEY:
            self.log_message("⚠️ 错误: 请在 .env 文件中设置 DASHSCOPE_API_KEY。")
            return
            
        self.btn_start.setEnabled(False)
        self.btn_select_file.setEnabled(False)
        self.log_view.clear()
        self.log_message("开始处理...")
        
        self.worker = WorkerThread(self.selected_file)
        self.worker.progress.connect(self.log_message)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def on_error(self, err_msg: str):
        self.log_message(f"❌ 遇到错误: {err_msg}")
        self.btn_start.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        
    def on_finished(self, markdown_text: str):
        self.log_message("✅ 纪要生成成功，正在渲染 HTML...")
        html_content = self.get_html_template(markdown_text)
        self.web_view.setHtml(html_content)
        self.btn_start.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        
    def get_html_template(self, markdown_text: str) -> str:
        """
        将 markdown 转换为 HTML，并嵌入 Mermaid 所需的前端库和样式。
        """
        # 注意: python-markdown 生成 HTML 时需要保留 mermaid 代码块原样
        html_body = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
        
        # 为了让 mermaid 初始化起效，我们将 `<code class="language-mermaid">` 替换为 `<div class="mermaid">`
        html_body = html_body.replace('<pre><code class="language-mermaid">', '<div class="mermaid">')
        html_body = html_body.replace('</code></pre>', '</div>')

        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    color: #333;
                }}
                h1, h2, h3 {{ border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
                th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; }}
                th {{ background-color: #f6f8fa; }}
            </style>
            <!-- 引入 Mermaid -->
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>
                mermaid.initialize({{ startOnLoad: true }});
            </script>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        return template
