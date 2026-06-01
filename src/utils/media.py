import os
import uuid
import subprocess
from typing import Optional


def _get_video_file_clip():
    try:
        # lazy import to avoid import-time failures in frozen executables
        try:
            from moviepy.editor import VideoFileClip
        except Exception:
            # older moviepy may expose VideoFileClip at top level
            from moviepy import VideoFileClip
        return VideoFileClip
    except Exception:
        return None


def _ffmpeg_extract(input_path: str, output_path: str) -> None:
    # Try to use ffmpeg available on PATH
    candidates = ["ffmpeg"]

    # Check common bundled locations relative to executable or script
    try:
        import sys
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        candidates += [
            os.path.join(base, '_internal', 'imageio_ffmpeg', 'binaries', 'ffmpeg-win-x86_64-v7.1.exe'),
            os.path.join(base, 'imageio_ffmpeg', 'binaries', 'ffmpeg-win-x86_64-v7.1.exe'),
            os.path.join(base, 'ffmpeg.exe'),
        ]
    except Exception:
        pass

    last_err: Optional[Exception] = None
    for exe in candidates:
        cmd = [exe, "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", "-ab", "128k", output_path]
        try:
            proc = subprocess.run(cmd, capture_output=True)
            if proc.returncode == 0:
                return
            last_err = RuntimeError(proc.stderr.decode(errors='ignore'))
        except FileNotFoundError as e:
            last_err = e
            continue

    raise RuntimeError(f"ffmpeg extraction failed. Last error: {last_err}")


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
        os.makedirs(temp_dir, exist_ok=True)
        audio_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.mp3")

        VideoFileClip = _get_video_file_clip()
        if VideoFileClip is not None:
            try:
                video = VideoFileClip(file_path)
                # 提取音频并保存，减少码率加速上传
                video.audio.write_audiofile(audio_path, logger=None, bitrate="128k")
                video.close()
                return audio_path
            except Exception as e:
                # Fall through to ffmpeg fallback
                print(f"moviepy 提取失败，尝试 ffmpeg: {e}")

        # Fallback: use ffmpeg CLI
        try:
            _ffmpeg_extract(file_path, audio_path)
            return audio_path
        except Exception as e:
            raise RuntimeError(f"提取音频失败: {str(e)}")
    else:
        return file_path
