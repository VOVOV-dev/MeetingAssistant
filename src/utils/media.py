import os
from moviepy.editor import VideoFileClip
import uuid

def extract_audio(file_path: str, temp_dir: str) -> str:
    """
    检查文件扩展名，如果是视频格式，则提取音频保存到 temp_dir，否则返回原路径。
    支持的视频格式：.mp4, .avi, .mov, .mkv
    支持的音频格式：.mp3, .wav, .m4a
    """
    ext = os.path.splitext(file_path)[1].lower()
    video_exts = ['.mp4', '.avi', '.mov', '.mkv']
    
    if ext in video_exts:
        print(f"检测到视频文件，正在提取音频: {file_path}")
        audio_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.mp3")
        try:
            video = VideoFileClip(file_path)
            # 提取音频并保存，减少码率加速上传
            video.audio.write_audiofile(audio_path, logger=None, bitrate="128k")
            video.close()
            return audio_path
        except Exception as e:
            raise RuntimeError(f"提取音频失败: {str(e)}")
    else:
        return file_path
