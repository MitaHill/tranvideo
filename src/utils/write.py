import sys
import subprocess
import os


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
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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


def merge_video_with_subtitles(video_file, srt_file, output_file):
    """合并视频和字幕（模块化接口）"""
    # 确保输入文件存在
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"视频文件未找到: {video_file}")
    if not os.path.exists(srt_file):
        raise FileNotFoundError(f"字幕文件未找到: {srt_file}")

    return embed_soft_subtitles(video_file, srt_file, output_file)


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