# 开发进度报告

## 1. 当前环境配置
- 项目目录骨架已建立。
- `requirements.txt` 已导出，主要依赖包括 `PyQt6`, `dashscope`, `openai` 和 `moviepy`。

## 2. 已完成功能开发
1. **统一配置 (`src/config.py`)**: 从 `.env` 加载 `DASHSCOPE_API_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`。支持全局读取密钥与配置参数。
2. **多媒体处理 (`src/utils/media.py`)**: 已经实现了使用 `moviepy` 从上传的视频文件（若是视频则自动提取音频降采样到 128k）中剥离提取纯音频，以便进行语音识别。
3. **语音识别 (`src/services/asr_dashscope.py`)**: 接入阿里云 DashScope Python SDK (Paraformer模型)，使用带有 Dzarization 说话人分离的能力，异步提交并轮询等待结果，并将 JSON 处理拼装带时间戳（如 `[00:10 - 00:15] 发言人1: 你们好`）的逐句字符串供后续使用。
4. **生成纪要大模型 (`src/services/llm_openai.py`)**: 根据 OpenAI 兼容格式封住了接口请求并加入 System Prompt，强制要求润色纠错错字，要求按照 **会议概述**, **发言人要点**, **详细内容/议程**, **决策与待办**, 和 **会议流程图(Mermaid)** 格式输出。
5. **本地 UI (`src/ui/main_window.py`)**: 
   - 使用 PyQt6。包含左侧的操作日志与运行进度框，右侧用于显示生成的 HTML。
   - 使用 `QWebEngineView` 与开源的 `Mermaid.js` 前端脚本实现了动态渲染 Markdown 内容。如果模型输出了 `mermaid` 代码块，则会自动捕获并渲染为图形。
   - 已构建非阻塞 GUI 的 QThread `WorkerThread` 执行长时间的音视频处理与大模型请求任务。

## 3. 下一步指示
- 您需要在根目录下的 `.env.example` 中复制重命名为 `.env`，填入您的通义千问 `DASHSCOPE_API_KEY`（和 LLM API 即可重用）。
- 使用终端安装依赖：`pip install -r requirements.txt`。
- 然后运行 `python main.py` 启动程序。
