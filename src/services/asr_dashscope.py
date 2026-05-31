import dashscope
import time


def _extract_uploaded_file_id(upload_response) -> str:
    """从 DashScope 文件上传响应中提取 file_id。"""
    uploaded_files = getattr(upload_response, "output", None)
    if not uploaded_files or not isinstance(uploaded_files, dict):
        raise Exception(f"文件上传失败: {upload_response}")

    files = uploaded_files.get("uploaded_files", [])
    if not files:
        raise Exception(f"文件上传失败，未返回 uploaded_files: {upload_response}")

    file_id = files[0].get("file_id")
    if not file_id:
        raise Exception(f"文件上传成功但未找到 file_id: {upload_response}")

    return file_id


def _resolve_file_url(file_id: str, api_key: str) -> str:
    """通过 file_id 获取 DashScope 可访问的临时文件 URL。"""
    from dashscope import Files

    file_info = Files.get(file_id=file_id, api_key=api_key)
    if file_info.status_code != 200:
        raise Exception(f"获取文件信息失败: {file_info}")

    file_output = file_info.output or {}
    file_url = file_output.get("url")
    if not file_url:
        raise Exception(f"文件信息中未找到 url: {file_info}")

    return file_url

class DashScopeASRService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        dashscope.api_key = self.api_key

    def recognize(self, audio_file_path: str, progress_callback=None) -> str:
        """
        调用 DashScope 异步录音文件识别 API
        返回包含时间戳和角色信息的逐句识别文本
        """
        from dashscope.audio.asr import Transcription
        from dashscope import Files
        if progress_callback:
            progress_callback("开始上传并提交语音识别任务...")
            
        try:
            model_name = Transcription.Models.paraformer_mtl_v1

            upload_response = Files.upload(file_path=audio_file_path, purpose="inference", api_key=self.api_key)
            if upload_response.status_code != 200:
                raise Exception(f"文件上传失败: {upload_response}")

            file_id = _extract_uploaded_file_id(upload_response)
            file_url = _resolve_file_url(file_id, self.api_key)

            # 提交任务
            # 使用支持说话人分离的模型，避免模型名不兼容导致提交失败
            task_response = Transcription.async_call(
                model=model_name,
                file_urls=[file_url],
                diarization_enabled=True # 开启说话人角色分离
            )
            
            if task_response.status_code != 200:
                raise Exception(f"语音识别任务提交失败: {task_response}")

            task_id = task_response.get("output", {}).get("task_id")
            if not task_id:
                raise Exception(f"语音识别任务未返回 task_id: {task_response}")
            
            if progress_callback:
                progress_callback(f"任务已提交，Task ID: {task_id}，正在识别中 (这可能需要几分钟)...")

            # 轮询获取结果
            while True:
                status_response = Transcription.wait(task=task_id)
                if status_response.status_code != 200:
                    raise Exception(f"语音识别查询失败: {status_response}")

                status = status_response.get("output", {}).get("task_status")
                if status == 'SUCCEEDED':
                    if progress_callback:
                        progress_callback("识别成功，正在解析结果...")
                    break
                elif status == 'FAILED':
                    error_msg = status_response.get('output', {}).get('task_metrics', {}).get('FAILED', 'Unknown Error')
                    raise Exception(f"语音识别失败: {error_msg}")
                else:
                    # RUNNING or PENDING
                    time.sleep(2)

            # 解析结果
            results = status_response.get('output', {}).get('results', [])
            if not results:
                return "未能识别到任何语音。"
                
            # DashScope 录音文件识别结果 URL 中包含了详细文本
            # 不过 wait 会自动在 results 中返回部分数据。通过 transcription_url 可以获取详细 JSON。
            transcription_url = results[0].get('transcription_url')
            if transcription_url:
                import requests
                resp = requests.get(transcription_url)
                resp.raise_for_status()
                data = resp.json()
                
                # 提取带时间和角色的字幕文本
                transcript_text = self._parse_transcription_data(data)
                return transcript_text
            else:
                return "无法获取识别结果的下载链接。"

        except Exception as e:
            raise Exception(f"ASR 处理失败: {str(e)}")

    def _parse_transcription_data(self, data: dict) -> str:
        """
        格式化返回的 JSON 为带有说话人和时间戳的文本:
        [00:00:10 - 00:00:15] Speaker 1: 大家好。
        """
        lines = []
        transcripts = data.get('transcripts', [])
        if not transcripts:
            return ""
            
        sentences = transcripts[0].get('sentences', [])
        for sentence in sentences:
            bg = sentence.get('begin_time', 0)
            ed = sentence.get('end_time', 0)
            spk = sentence.get('speaker_id', 'Unknown')
            text = sentence.get('text', '')
            
            # 格式化时间戳 (毫秒换算为 MM:SS)
            def fmt_time(ms):
                s = ms // 1000
                m = s // 60
                s = s % 60
                return f"{m:02d}:{s:02d}"
                
            line = f"[{fmt_time(bg)} - {fmt_time(ed)}] 发言人 {spk}: {text}"
            lines.append(line)
            
        return "\n".join(lines)
