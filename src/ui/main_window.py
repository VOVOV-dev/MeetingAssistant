import os
import glob
import markdown
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTextEdit, QSplitter,
                             QListWidget, QListWidgetItem, QMenu, QInputDialog, QMessageBox,
                             QTabWidget, QStyle, QSlider, QTextBrowser)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except Exception:
    QWebEngineView = None
    WEBENGINE_AVAILABLE = False

from src.config import Config
from src.utils.media import extract_audio
from src.services.asr_dashscope import DashScopeASRService
from src.services.llm_openai import LLMService
from src.ui.settings_dialog import SettingsDialog

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str) # title, content
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            from src.config import log
            log(f"WorkerThread started for: {self.file_path}")
            Config.ensure_temp_dir()
            
            # Step 1: Media Processing
            self.progress.emit("检查并提取音频...")
            audio_path = extract_audio(self.file_path, Config.TEMP_DIR)
            
            # Step 2: ASR
            asr_svc = DashScopeASRService(Config.DASHSCOPE_API_KEY)
            self.progress.emit("连接语音识别服务...")
            raw_text = asr_svc.recognize(audio_path, progress_callback=self._emit_progress)
            
            self.progress.emit("语音识别完成。")
            
            # Step 3: LLM
            llm_svc = LLMService(Config.LLM_API_KEY, Config.LLM_BASE_URL, Config.LLM_MODEL_NAME)
            self.progress.emit("正在通过大模型进行理解与总结...")
            summary = llm_svc.generate_meeting_minutes(raw_text, progress_callback=self._emit_progress)
            
            self.progress.emit("处理完毕！")
            
            # Use original file name as default title
            base_name = os.path.basename(self.file_path)
            title = os.path.splitext(base_name)[0] + f"_纪要_{datetime.now().strftime('%m%d%H%M')}"
            
            # Save to Markdown automatically
            save_path = os.path.join(Config.get_save_dir(), title + ".md")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            self.finished.emit(title, summary)
            
        except Exception as e:
            try:
                from src.config import log
                log(f"WorkerThread error: {e}")
            except Exception:
                pass
            self.error.emit(str(e))
            
    def _emit_progress(self, msg: str):
        self.progress.emit(msg)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能会议纪要与总结系统")
        self.resize(1280, 850)
        
        self.selected_file = None
        self.current_md_path = None
        self.media_available = False
        self.media_error = ""
        self.media_player = None
        self.audio_output = None
        self.video_widget = None
        
        self._init_ui()
        try:
            from src.config import log
            log('MainWindow initialized')
        except Exception:
            pass
        self.refresh_minutes_list()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # --- 左侧侧边栏 (历史会议纪要) ---
        sidebar_layout = QVBoxLayout()
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("<b>历史纪要列表</b>"))
        btn_settings = QPushButton("⚙️ 设置")
        btn_settings.clicked.connect(self.open_settings)
        title_layout.addStretch()
        title_layout.addWidget(btn_settings)
        sidebar_layout.addLayout(title_layout)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        sidebar_layout.addWidget(self.list_widget)
        
        # --- 右侧主区域 ---
        right_layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        self.btn_select_file = QPushButton("📂 选择音视频文件")
        self.btn_select_file.setMinimumHeight(40)
        self.btn_select_file.clicked.connect(self.select_file)
        
        self.lbl_file_path = QLabel("未选择文件")
        self.lbl_file_path.setStyleSheet("color: gray;")
        
        self.btn_start = QPushButton("🚀 开始生成纪要")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        
        toolbar_layout.addWidget(self.btn_select_file)
        toolbar_layout.addWidget(self.lbl_file_path, stretch=1)
        toolbar_layout.addWidget(self.btn_start)
        right_layout.addLayout(toolbar_layout)
        
        # 标签页 (会议纪要 / 视频预览)
        self.tabs = QTabWidget()
        
        # Tab 1: 纪要与日志
        tab_summary = QWidget()
        tab_summary_layout = QVBoxLayout(tab_summary)
        summary_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("系统运行日志将展示在这里...")
        summary_splitter.addWidget(self.log_view)
        
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self.web_view.setHtml(self.get_html_template("# 会议纪要\n等待生成或在左侧选择历史纪要..."))
        else:
            self.web_view = QTextBrowser()
            self.web_view.setHtml(self.get_html_template("# 会议纪要\n等待生成或在左侧选择历史纪要..."))
            self.web_view.setOpenExternalLinks(True)
        summary_splitter.addWidget(self.web_view)
        
        summary_splitter.setStretchFactor(0, 1)
        summary_splitter.setStretchFactor(1, 4)
        tab_summary_layout.addWidget(summary_splitter)
        
        self.tabs.addTab(tab_summary, "📝 总结与纪要")
        
        # Tab 2: 音视频预览
        tab_media = QWidget()
        tab_media_layout = QVBoxLayout(tab_media)

        media_controls = QHBoxLayout()
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderMoved.connect(self.set_position)
        
        self.lbl_time = QLabel("00:00 / 00:00")
        
        media_controls.addWidget(self.btn_play)
        media_controls.addWidget(self.slider)
        media_controls.addWidget(self.lbl_time)

        self._init_media_backend(tab_media_layout)
        tab_media_layout.addLayout(media_controls)
        
        self.tabs.addTab(tab_media, "🎬 媒体预览")
        
        right_layout.addWidget(self.tabs)
        
        # 组装整体布局
        main_layout.addLayout(sidebar_layout, stretch=1)
        main_layout.addLayout(right_layout, stretch=4)

    def _init_media_backend(self, tab_media_layout: QVBoxLayout):
        try:
            self.video_widget = QVideoWidget()
            self.audio_output = QAudioOutput()
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)

            if hasattr(self.media_player, "isAvailable") and not self.media_player.isAvailable():
                raise RuntimeError("QtMultimedia backend not available")

            self.media_player.positionChanged.connect(self.position_changed)
            self.media_player.durationChanged.connect(self.duration_changed)
            tab_media_layout.addWidget(self.video_widget, stretch=1)
            self.media_available = True
            self.btn_play.setEnabled(True)
            self.slider.setEnabled(True)
        except Exception as e:
            self.media_available = False
            self.media_error = str(e)
            tip = QLabel(
                "当前环境缺少 QtMultimedia 播放后端，媒体预览已禁用。\n"
                "请在虚拟环境中执行：\n"
                "pip install --upgrade --force-reinstall PyQt6 PyQt6-Qt6 PyQt6-WebEngine PyQt6-WebEngine-Qt6"
            )
            tip.setWordWrap(True)
            tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tab_media_layout.addWidget(tip, stretch=1)
            self.btn_play.setEnabled(False)
            self.slider.setEnabled(False)
            self.lbl_time.setText("后端不可用")
        
    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.refresh_minutes_list()
            self.log_message("存储路径已更新。")

    def refresh_minutes_list(self):
        self.list_widget.clear()
        save_dir = Config.get_save_dir()
        md_files = glob.glob(os.path.join(save_dir, "*.md"))
        md_files.sort(key=os.path.getmtime, reverse=True) # 按修改时间排序
        
        for file in md_files:
            item = QListWidgetItem(os.path.basename(file))
            item.setData(Qt.ItemDataRole.UserRole, file)
            self.list_widget.addItem(item)
            
    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        
        menu = QMenu()
        action_rename = menu.addAction("重命名")
        action_delete = menu.addAction("删除")
        
        action = menu.exec(self.list_widget.mapToGlobal(pos))
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        if action == action_rename:
            new_name, ok = QInputDialog.getText(self, "重命名", "输入新文件名:", text=item.text())
            if ok and new_name:
                if not new_name.endswith('.md'):
                    new_name += '.md'
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                try:
                    os.rename(file_path, new_path)
                    self.refresh_minutes_list()
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"重命名失败: {e}")
                    
        elif action == action_delete:
            reply = QMessageBox.question(self, "确认删除", f"确定要删除 {item.text()} 吗？")
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.remove(file_path)
                    self.refresh_minutes_list()
                    if self.current_md_path == file_path:
                        self.web_view.setHtml(self.get_html_template("# 会议纪要\n已删除。"))
                        self.current_md_path = None
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"删除失败: {e}")

    def on_item_clicked(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if os.path.exists(file_path):
            self.current_md_path = file_path
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.web_view.setHtml(self.get_html_template(content))
            self.tabs.setCurrentIndex(0)

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
            
            if self.media_available and self.media_player is not None:
                # Load into media player
                self.media_player.setSource(QUrl.fromLocalFile(file_path))
                self.media_player.pause()
            else:
                self.log_message("提示: 当前 QtMultimedia 后端不可用，媒体预览已禁用。")
            
    def toggle_play(self):
        if not self.media_available or self.media_player is None:
            return

        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            
    def position_changed(self, position):
        if not self.media_available:
            return
        self.slider.setValue(position)
        self.update_time_label()

    def duration_changed(self, duration):
        if not self.media_available:
            return
        self.slider.setRange(0, duration)
        self.update_time_label()

    def set_position(self, position):
        if not self.media_available or self.media_player is None:
            return
        self.media_player.setPosition(position)

    def update_time_label(self):
        if not self.media_available or self.media_player is None:
            return
        pos = self.media_player.position() // 1000
        dur = self.media_player.duration() // 1000
        self.lbl_time.setText(f"{pos//60:02d}:{pos%60:02d} / {dur//60:02d}:{dur%60:02d}")

    def log_message(self, msg: str):
        self.log_view.append(msg)
        
    def start_processing(self):
        if not self.selected_file:
            return
            
        if not Config.DASHSCOPE_API_KEY:
            self.log_message("⚠️ 错误: 请在 .env 文件中设置 DASHSCOPE_API_KEY。")
            return
            
        self.btn_start.setEnabled(False)
        self.btn_select_file.setEnabled(False)
        self.log_view.clear()
        self.log_message("开始处理...")
        self.tabs.setCurrentIndex(0)
        
        self.worker = WorkerThread(self.selected_file)
        self.worker.progress.connect(self.log_message)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def on_error(self, err_msg: str):
        self.log_message(f"❌ 遇到错误: {err_msg}")
        self.btn_start.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        
    def on_finished(self, title: str, markdown_text: str):
        self.log_message(f"✅ 纪要 '{title}' 生成并保存成功，正在渲染 HTML...")
        html_content = self.get_html_template(markdown_text)
        self.web_view.setHtml(html_content)
        self.btn_start.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        self.refresh_minutes_list()
        
    def get_html_template(self, markdown_text: str) -> str:
        html_body = markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])
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