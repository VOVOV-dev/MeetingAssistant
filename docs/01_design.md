# 智能会议纪要应用 - 架构与设计文档

## 1. 项目简介
本项目是一个基于本地 GUI 架构的 AI 桌面应用。主要功能为接收用户上传的会议录音或视频文件，通过语音识别大模型（集成阿里云 DashScope）将其转换为带有发言人和时间戳的文本，接着通过通用大语言模型（集成 Qwen / OpenAI 兼容接口）生成结构化、具有润色效果并支持 Mermaid 流程图的会议纪要报表，最后将纪要展示在 GUI 界面上。

## 2. 技术栈
- **GUI 框架**: PyQt6, PyQt6-WebEngine (用于渲染 Markdown 和 Mermaid 图表)
- **多媒体处理**: moviepy (用于从视频中提取音频，减小识别接口传输体积)
- **语音识别 (ASR)**: 阿里云 DashScope (通过 dashscope SDK 调用 Paraformer 模型，支持角色分离 Speaker Diarization)
- **大语言模型 (LLM)**: Qwen (通义千问，采用标准 `openai` 库封装，便于未来无缝切换其他厂商 API)
- **数据流转**: 本地生成 Markdown 资产文本并渲染到 WebEngine。

## 3. 核心模块规划
- `src/ui/`: 界面组件，包括主窗口、上传控件、预览控件、Markdown渲染器。
- `src/services/`: 核心服务
  - `asr_dashscope.py`: 封装 DashScope 的录音文件识别 API。
  - `llm_openai.py`: 封装 OpenAI 标准库，提示词工程 (Prompt Engineering) 处理会议记录生成与 Mermaid 生成。
- `src/utils/`: 辅助工具
  - `media.py`: 音频与视频的提取及预处理。
- `src/config.py`: 全局配置读取和环境变量获取。

## 4. 交互流程图
1. 用户在客户端点击上传按钮，选择 `.mp4`, `.mp3`, `.wav` 等文件。
2. 客户端调用 `utils.media` 检查文件是否为视频，若是视频，提取音频保存为临时文件。
3. `services.asr_dashscope` 上传临时音频文件，发起异步识别任务。
4. 获取带发言人标记、时间戳的识别结果字符串。
5. `services.llm_openai` 根据识别字符串与特定 System Prompt 生成 Markdown 纪要（含 Mermaid 图表）。
6. UI 获取最终结果，并在 QWebEngine 渲染前端渲染，完成全流程交互。
