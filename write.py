import sys
import subprocess
import os
import json


def get_video_resolution(video_path):
    """使用 ffprobe 获取视频的分辨率（宽，高）"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 失败: {result.stderr}")

    info = json.loads(result.stdout)
    width = info['streams'][0]['width']
    height = info['streams'][0]['height']
    return width, height


def embed_subtitles(video_path, srt_path, output_path):
    width, height = get_video_resolution(video_path)

    # 根据分辨率自适应字体大小，竖屏小字体
    if height > width:  # 竖屏
        fontsize = 12
    else:  # 横屏
        fontsize = 24

    subtitle_filter = (
        f"subtitles={srt_path}:"
        f"force_style='Fontsize={fontsize},"
        f"PrimaryColour=&Hffffff&,"
        f"OutlineColour=&H000000&,"
        f"BackColour=&H80000000&,"
        f"Outline=2,Shadow=1'"
    )

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        output_path,
        "-y"
    ]

    print(f"嵌入字幕（字体大小: {fontsize}）: {srt_path} -> {output_path}")
    subprocess.run(cmd, check=True)
    print("完成!")


def main():
    if len(sys.argv) != 4:
        print("用法: python write.py <视频文件> <SRT字幕> <输出视频>")
        sys.exit(1)

    video_file = sys.argv[1]
    srt_file = sys.argv[2]
    output_file = sys.argv[3]

    embed_subtitles(video_file, srt_file, output_file)


if __name__ == "__main__":
    main()
