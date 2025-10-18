import subprocess
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from services.tran import translate_srt
from utils.write import merge_video_with_subtitles, merge_video_with_multiple_subtitles
from utils.bilingual_subtitle import bilingual_subtitle_generator
from utils.logger import get_cached_logger

logger = get_cached_logger("视频处理")


def get_duration(video_path):
    """获取视频时长（分钟）"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)

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
    """合成视频和字幕（单字幕兼容接口）"""
    try:
        return merge_video_with_subtitles(video_path, srt_path, output_path)
    except Exception:
        return False


def merge_video_with_multilingual_subtitles(video_path: str, raw_srt_path: str, translated_srt_path: str, output_path: str) -> bool:
    """
    合成视频和多语言字幕轨道
    
    Args:
        video_path: 视频文件路径
        raw_srt_path: 原文字幕路径
        translated_srt_path: 翻译字幕路径
        output_path: 输出视频路径
        
    Returns:
        是否成功
    """
    try:
        logger.info(f"开始生成多语言字幕轨道...")
        
        # 确定temp目录和任务ID
        task_id = os.path.splitext(os.path.basename(output_path))[0].replace('_final', '')
        temp_dir = "cache/temp"  # 使用temp目录存放临时字幕文件
        
        # 生成各种类型的字幕文件到temp目录
        subtitle_files = bilingual_subtitle_generator.generate_all_subtitle_types(
            task_id, raw_srt_path, translated_srt_path, temp_dir
        )
        
        if not subtitle_files:
            logger.error("生成字幕文件失败")
            return False
        
        logger.info(f"生成了 {len(subtitle_files)} 种字幕类型: {list(subtitle_files.keys())}")
        
        # 合并视频和多个字幕轨道
        success = merge_video_with_multiple_subtitles(video_path, subtitle_files, output_path)
        
        if success:
            logger.info(f"多语言字幕视频合成成功: {output_path}")
            
            # 清理临时字幕文件（可选，保留用于调试）
            # for subtitle_path in subtitle_files.values():
            #     clean_temp(subtitle_path)
        
        return success
        
    except Exception as e:
        logger.error(f"合成多语言字幕视频失败: {e}")
        return False


def clean_temp(file_path):
    """清理临时文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception:
        return False