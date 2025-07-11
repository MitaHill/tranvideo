import subprocess
import os
from src.services.tran import translate_srt
from src.utils.write import merge_video_with_subtitles


def get_duration(video_path):
    """获取视频时长（分钟）"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            duration_seconds = float(result.stdout.strip())
            return duration_seconds / 60
        return 0
    except Exception:
        return 0


def process_srt(srt_path):
    """翻译字幕文件"""
    try:
        translate_srt(srt_path)
        return True
    except Exception:
        return False


def merge_video(video_path, srt_path, output_path):
    """合成视频和字幕"""
    try:
        return merge_video_with_subtitles(video_path, srt_path, output_path)
    except Exception:
        return False


def clean_temp(file_path):
    """清理临时文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception:
        return False