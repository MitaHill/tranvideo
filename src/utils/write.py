import sys
import subprocess
import os
from typing import Dict, List
from .logger import get_cached_logger

logger = get_cached_logger("视频字幕合成")


def embed_soft_subtitles(video_path, srt_path, output_path):
    """嵌入软字幕到视频"""
    # 检查输出目录是否存在，如果不存在则创建
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", srt_path,
        "-c", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=chi",
        output_path,
        "-y"
    ]

    try:
        print(f"合并视频和软字幕: {srt_path} -> {output_path}")
        # 使用 subprocess.run 来执行命令
        # check=True 会在 ffmpeg 返回非零退出码时抛出异常
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        print("完成!")
        print(f"输出文件已保存到: {output_path}")
        return True

    except subprocess.CalledProcessError as e:
        print("ffmpeg 执行失败!")
        print(f"返回码: {e.returncode}")
        print("FFmpeg 标准输出:")
        print(e.stdout)
        print("FFmpeg 错误输出:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("错误: 'ffmpeg' 命令未找到。")
        print("请确保 FFmpeg 已安装并配置在系统的 PATH 环境变量中。")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False


def validate_subtitle_files(subtitle_files: Dict[str, str]) -> bool:
    """验证字幕文件是否有效"""
    for subtitle_type, subtitle_path in subtitle_files.items():
        if not os.path.exists(subtitle_path):
            logger.error(f"字幕文件不存在: {subtitle_path}")
            return False
        
        # 检查文件大小
        if os.path.getsize(subtitle_path) == 0:
            logger.error(f"字幕文件为空: {subtitle_path}")
            return False
        
        # 简单验证SRT格式
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read(200)  # 读取前200字符
                if not content.strip():
                    logger.error(f"字幕文件内容为空: {subtitle_path}")
                    return False
                logger.info(f"字幕文件验证通过: {subtitle_type} -> {subtitle_path} ({os.path.getsize(subtitle_path)} bytes)")
        except Exception as e:
            logger.error(f"读取字幕文件失败 {subtitle_path}: {e}")
            return False
    
    return True


def embed_multiple_subtitles(video_path: str, subtitle_files: Dict[str, str], output_path: str) -> bool:
    """
    嵌入多个字幕轨道到视频
    
    Args:
        video_path: 视频文件路径
        subtitle_files: 字幕文件字典 {'chinese': 'path1', 'original': 'path2', 'bilingual': 'path3'}
        output_path: 输出视频路径
        
    Returns:
        是否成功
    """
    try:
        # 验证字幕文件
        if not validate_subtitle_files(subtitle_files):
            return False
        # 检查输出目录是否存在，如果不存在则创建
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"创建输出目录: {output_dir}")
        
        # 构建ffmpeg命令
        cmd = ["ffmpeg", "-i", video_path]
        
        # 按固定顺序添加字幕文件输入（确保一致的映射）
        subtitle_order = ['chinese', 'original', 'bilingual']
        valid_subtitles = []
        
        for subtitle_type in subtitle_order:
            if subtitle_type in subtitle_files and os.path.exists(subtitle_files[subtitle_type]):
                cmd.extend(["-i", subtitle_files[subtitle_type]])
                valid_subtitles.append(subtitle_type)
        
        if not valid_subtitles:
            logger.error("没有有效的字幕文件")
            return False
        
        # 映射视频和音频流
        cmd.extend(["-map", "0:v", "-map", "0:a"])
        
        # 映射每个字幕流
        for i, subtitle_type in enumerate(valid_subtitles):
            cmd.extend(["-map", f"{i+1}:0"])  # i+1因为视频是输入0
        
        # 复制视频和音频编码
        cmd.extend(["-c:v", "copy", "-c:a", "copy"])
        
        # 设置字幕编码和元数据（使用mov_text，这是MP4的标准字幕格式）
        for i, subtitle_type in enumerate(valid_subtitles):
            cmd.extend([f"-c:s:{i}", "mov_text"])
            
            if subtitle_type == 'chinese':
                cmd.extend([f"-metadata:s:s:{i}", "language=chi"])
                cmd.extend([f"-metadata:s:s:{i}", "title=中文"])
            elif subtitle_type == 'original':
                cmd.extend([f"-metadata:s:s:{i}", "language=eng"]) 
                cmd.extend([f"-metadata:s:s:{i}", "title=原文"])
            elif subtitle_type == 'bilingual':
                cmd.extend([f"-metadata:s:s:{i}", "language=und"])
                cmd.extend([f"-metadata:s:s:{i}", "title=双语"])
        
        # 确保字幕流被正确处理
        cmd.extend(["-movflags", "faststart"])
        
        cmd.extend(["-y", output_path])
        
        logger.info(f"合并视频和多字幕轨道: {len(subtitle_files)} 个字幕 -> {output_path}")
        logger.debug(f"FFmpeg命令: {' '.join(cmd)}")
        
        # 执行ffmpeg命令
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8', 
            errors='replace'
        )
        
        logger.info("多字幕轨道合成完成!")
        logger.info(f"输出文件已保存到: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error("ffmpeg 执行失败!")
        logger.error(f"返回码: {e.returncode}")
        logger.error(f"FFmpeg 标准输出: {e.stdout}")
        logger.error(f"FFmpeg 错误输出: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("错误: 'ffmpeg' 命令未找到")
        return False
    except Exception as e:
        logger.error(f"合成多字幕轨道时发生错误: {e}")
        return False


def merge_video_with_subtitles(video_file, srt_file, output_file):
    """合并视频和字幕（模块化接口，兼容旧版本）"""
    # 确保输入文件存在
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"视频文件未找到: {video_file}")
    if not os.path.exists(srt_file):
        raise FileNotFoundError(f"字幕文件未找到: {srt_file}")

    return embed_soft_subtitles(video_file, srt_file, output_file)


def merge_video_with_multiple_subtitles(video_file: str, subtitle_files: Dict[str, str], output_file: str) -> bool:
    """
    合并视频和多个字幕轨道（新接口）
    
    Args:
        video_file: 视频文件路径
        subtitle_files: 字幕文件字典
        output_file: 输出文件路径
        
    Returns:
        是否成功
    """
    # 确保视频文件存在
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"视频文件未找到: {video_file}")
    
    # 过滤存在的字幕文件
    valid_subtitle_files = {}
    for subtitle_type, subtitle_path in subtitle_files.items():
        if os.path.exists(subtitle_path):
            valid_subtitle_files[subtitle_type] = subtitle_path
        else:
            logger.warning(f"字幕文件不存在，跳过: {subtitle_path}")
    
    if not valid_subtitle_files:
        raise FileNotFoundError("没有有效的字幕文件")
    
    return embed_multiple_subtitles(video_file, valid_subtitle_files, output_file)


def main():
    """命令行入口"""
    if len(sys.argv) != 4:
        print("用法: python write.py <视频文件> <字幕文件.srt> <输出视频>")
        sys.exit(1)

    video_file = sys.argv[1]
    srt_file = sys.argv[2]
    output_file = sys.argv[3]

    try:
        success = merge_video_with_subtitles(video_file, srt_file, output_file)
        if not success:
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()