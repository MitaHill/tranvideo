import whisper
import argparse
import subprocess
import os


def extract_audio(video_path):
    audio_path = "temp_audio.wav"
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path, "-y"
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path


def transcribe_audio(audio_path, model_name):
    model_path = f"whisper/{model_name}.pt"
    model = whisper.load_model(model_path)
    result = model.transcribe(audio_path)
    return result


def format_srt(segments):
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()
        srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
    return srt_content


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def main():
    parser = argparse.ArgumentParser(description='语音识别模块')
    parser.add_argument('--source-video', required=True, help='源视频路径')
    parser.add_argument('--dist-srt-path', required=True, help='SRT字幕文件存放路径')
    parser.add_argument('--model', default='large-v3', choices=['base', 'large-v3', 'small'], help='模型选择')

    args = parser.parse_args()

    audio_path = extract_audio(args.source_video)
    result = transcribe_audio(audio_path, args.model)
    srt_content = format_srt(result['segments'])

    with open(args.dist_srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)

    os.remove(audio_path)
    print(f"Generated: {args.dist_srt_path}")


if __name__ == "__main__":
    main()