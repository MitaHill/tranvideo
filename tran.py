import os
import sys
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from tqdm import tqdm

# 启用详细输出
os.environ["TRANSFORMERS_VERBOSITY"] = "info"


def load_model():
    print("正在加载NLLB-200翻译模型...")
    model_name = "./tran-m/models--facebook--nllb-200-3.3B/snapshots/1a07f7d195896b2114afcb79b7b57ab512e7b43e"
    print("下载/加载tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print("✓ Tokenizer加载完成")
    print("下载/加载模型...")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print("✓ 模型加载完成")
    return tokenizer, model


def translate_text(text, tokenizer, model, target_lang="zho_Hans"):
    print(f"翻译文本: {text[:50]}...")

    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)

    print("正在生成翻译...")
    outputs = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang),
        max_length=512,
        num_beams=4
    )

    translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"翻译结果: {translated}")
    return translated


def parse_srt_file(srt_path):
    print(f"读取SRT文件: {srt_path}")

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split('\n\n')
    subtitles = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            index = lines[0]
            timestamp = lines[1]
            text = '\n'.join(lines[2:])
            subtitles.append((index, timestamp, text))

    print(f"解析到 {len(subtitles)} 条字幕")
    return subtitles


def translate_srt(input_path, output_path, target_lang="zho_Hans"):
    print("=" * 50)
    print("SRT字幕翻译程序")
    print("=" * 50)

    # 加载模型
    tokenizer, model = load_model()

    # 解析SRT文件
    subtitles = parse_srt_file(input_path)

    # 翻译每条字幕
    translated_subtitles = []
    print("\n开始翻译字幕...")

    for i, (index, timestamp, text) in enumerate(tqdm(subtitles, desc="翻译进度")):
        print(f"\n[{i + 1}/{len(subtitles)}] 处理字幕 #{index}")
        translated_text = translate_text(text, tokenizer, model, target_lang)
        translated_subtitles.append((index, timestamp, translated_text))

    # 保存翻译结果
    print(f"\n保存翻译结果到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for index, timestamp, text in translated_subtitles:
            f.write(f"{index}\n{timestamp}\n{text}\n\n")

    print("✓ 翻译完成!")


def main():
    if len(sys.argv) != 3:
        print("用法: python translator.py <输入SRT文件> <输出SRT文件>")
        sys.exit(1)

    input_srt = sys.argv[1]
    output_srt = sys.argv[2]

    translate_srt(input_srt, output_srt)


if __name__ == "__main__":
    main()