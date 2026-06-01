# 智能会议纪要系统 (Meeting Assistant)

## 项目简介
这是一个基于 PyQt6 和人工智能技术的桌面级应用程序。该应用旨在解决会议记录整理的痛点，用户只需上传一段会议音频或视频，系统即可自动化执行“音视频提取音频 -> 语音识别为文字 -> 大模型润色与提炼总结”的全工作流，最终生成高度结构化的 markdown 会议报告，并在内嵌浏览器中直观地展示报告内容与 Mermaid 流程图。

## 核心特性
- **支持多格式媒体上传**: 本地自动抽离视频中的音频（支持 `.mp4`, `.mov`, `.mkv` 等提取，直接支持 `.mp3`, `.wav` 等格式）。
- **带有说话人分离(Diarization)的语音识别**: 深度结合阿里云 DashScope (Paraformer API)，精准区分出“谁”在“什么时间”说了什么。
- **智能排版与逻辑梳理 (LLM)**: 大脑部分通过标准 OpenAI 接口方式调用 Qwen，能敏锐抓取各个角色的核心观点、提炼议程，并支持提炼业务流程成结构化 Mermaid 逻辑图。
- **现代化可视化界面**: 使用 PyQt6 开发的主流桌面应用响应式分离布局，左侧提供处理过程流水日志，右侧支持原生 Markdown 与 Mermaid 代码块的富文本直接渲染，清晰可读。

## 技术结构
整个架构围绕高内聚低耦合的理念分为以下核心层级：
```text
MeetingAssistant/
├── main.py                  # 系统入口文件，负责拉起事件循环和主窗体
├── requirements.txt         # 所需第三方依赖包记录
├── .env                     # [必须项] 配置 API 密钥与大模型基础信息 
├── docs/                    # 存放所有的开发、设计与进度说明文档
└── src/
    ├── config.py            # 全局配置管理：读取并管理所有的系统与接口环境变量
    ├── utils/
    │   └── media.py         # 工具库：集成 moviepy 完成对音视频处理进行本地分离操作
    ├── services/
    │   ├── asr_dashscope.py # 核心服务：封装了阿里云录音文件转写服务，处理轮询和解析字幕时间戳格式
    │   └── llm_openai.py    # 核心服务：封装了兼容 OpenAI 的 SDK，注入 Prompt 用于生成结构化纪要
    └── ui/
        └── main_window.py   # PyQt6 用户界面、线程分离调度控制与 Markdown WebView 渲染引擎层
```

## 环境准备
1. 确保电脑已安装 Python 3.8+ 版本环境。
2. 安装项目所有的第三方依赖包 (建议在虚拟环境中):
   ```bash
   pip install -r requirements.txt
   ```

## 配置项
为了保证服务能正常运行，请在项目的根目录下参考 `.env.example` 文件创建自己的环境变量文件 `.env`。
其中必须要配置的核心环境变量有：
```ini
# (阿里云 Dashcope) 提供语音识别与千问大模型的鉴权密钥，必须填写
DASHSCOPE_API_KEY=sk-xxxxxx

# 默认会复用上述密钥调用阿里大模型服务。如果您希望能切换其他的大语言模型供文案生成，可独立配置下面信息：
LLM_API_KEY=您的_OPENAI_格式_密钥
LLM_BASE_URL=大模型提供商_BASEURL (默认指向阿里云DashScope)
LLM_MODEL_NAME=模型名称 (默认为使用千问的 qwen-plus)
```

## 使用方法
1. 在配置好 `.venv` 文件且安装好全部依赖的 Python 环境中，通过终端或命令行运行程序启动脚本：
   ```bash
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   (此处执行./.venv\Scripts\Activate.ps1)
   python main.py
   ```
2. 在弹出的图形界面中点击 **📂 选择音视频文件** 按钮选取您准备好的会议记录文件。
3. 点击 **🚀 开始生成纪要**。
4. 程序将静默运行提取任务，并将各阶段的状态进度输出在界面**左侧的运行日志区**。
5. （请耐心等待语音转写（最耗时）与大模型生成结束），完毕后，右侧的预览区将**自动呈现出一份包含流程图的详细 Markdown 会议纪要**报告。

## 常见问题

### 1) 视频预览报错：No QtMultimedia backends found
如果你看到如下日志：
- `No QtMultimedia backends found...`
- `Failed to create QVideoSink "Not available"`
- `Failed to initialize QMediaPlayer "Not available"`

这代表当前 Python 环境里的 Qt 多媒体后端不完整。请在项目虚拟环境中执行：

```bash
pip install --upgrade --force-reinstall PyQt6 PyQt6-Qt6 PyQt6-WebEngine PyQt6-WebEngine-Qt6
```

安装后重启程序。若仍失败，可先继续使用纪要生成功能（媒体预览会自动降级禁用，不影响转写与总结）。

## 打包发布

如果你希望把程序打包成在没有 Python 环境的 Windows 电脑上直接运行的版本，推荐使用 PyInstaller。

### 1. 准备打包环境
先在当前虚拟环境里安装打包工具：

```bash
pip install pyinstaller
```

### 2. 执行打包脚本
项目根目录已经提供了 `build.ps1`：

```powershell
.\build.ps1
```

如果你更想要单个 exe 文件，也可以：

```powershell
.\build.ps1 -OneFile
```

打包完成后，结果会在 `dist/MeetingAssistant/` 或 `dist/MeetingAssistant.exe` 中。

### 3. 分发注意事项
你需要把下面这些内容一起带给使用者：
- 打包出来的程序文件
- 同目录下的 `.env` 文件（里面放 `DASHSCOPE_API_KEY`、`LLM_API_KEY` 等）

程序已经改成从 exe 同目录读取 `.env`，所以用户不需要安装 Python，只要把 exe 和 `.env` 放在一起即可。
