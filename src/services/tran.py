import os
import sys
import requests
import json
from tqdm import tqdm
import re
import logging

# 设置日志
os.makedirs('log', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/tran.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    config_path = 'config/tran-py.json'
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
            return {}
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"配置文件格式错误: {config_path}")
        raise


class OllamaTranslator:
    def __init__(self):
        config = load_config()

        self.base_url = config.get('ollama_api')
        self.model = config.get('ollama_model')

        if not self.base_url or not self.model:
            logger.error("配置文件缺少必要参数: ollama_api 和 ollama_model")
            raise ValueError("配置文件缺少必要参数")

        # 验证URL格式
        if not self.base_url.startswith(('http://', 'https://')):
            logger.error(f"URL格式错误: {self.base_url}")
            raise ValueError(f"URL格式错误: {self.base_url}")

        # 验证模型名称格式
        if not re.match(r'^[a-zA-Z0-9_-]+:[a-zA-Z0-9._-]+$', self.model):
            logger.error(f"模型名称格式错误: {self.model}")
            raise ValueError(f"模型名称格式错误: {self.model}")

        self.chat_url = f"{self.base_url}/api/chat"
        self.conversation_history = []
        self.max_history = 10

        logger.info(f"初始化翻译器 - API: {self.base_url}, 模型: {self.model}")

        # 开启思考模式的提示词
        self.system_prompt = "你是专业翻译。将外语翻译成自然流畅的中文，保持原意可适当润色修饰。只输出代码块格式：``````，将译文内容放入代码块中，不要有其它提示性内容。"

        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })

    def add_to_history(self, user_message, assistant_response):
        """添加对话到历史记录"""
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})

        if len(self.conversation_history) > self.max_history * 2 + 1:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[
                                                                         -(self.max_history * 2):]

    def translate_text(self, text):
        """调用Ollama API翻译文本"""
        if not text.strip():
            return text

        try:
            payload = {
                "model": self.model,
                "messages": self.conversation_history + [{"role": "user", "content": text}],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "num_ctx": 2048,
                    "reasoning": True,  # 开启思考模式
                    "thinking": True  # 开启思考模式
                }
            }

            logger.info(f"正在翻译: {text[:30]}...")
            response = requests.post(self.chat_url, json=payload, timeout=450)
            response.raise_for_status()

            result = response.json()
            translated = result["message"]["content"]

            # 提取代码块中的翻译结果
            translated = self.extract_translation(translated)

            # 添加到对话历史
            self.add_to_history(text, result["message"]["content"])

            logger.info(f"翻译结果: {translated}")
            return translated

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return text
        except Exception as e:
            logger.error(f"翻译出错: {e}")
            return text

    def extract_translation(self, response):
        """从响应中提取代码块内的翻译结果"""
        # 移除思考标签
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)

        # 查找代码块
        code_block_pattern = r'```(?:text\s*)?\n?([^`]+?)```'
        matches = re.findall(code_block_pattern, response, flags=re.DOTALL)

        if matches:
            translation = matches[0].strip()
            # 移除可能的text标记行
            lines = translation.split('\n')
            filtered_lines = [line for line in lines if line.strip() not in ['text', '']]
            return '\n'.join(filtered_lines).strip()

        # 如果没有代码块，返回清理后的响应
        return response.strip()


def parse_srt_file(srt_path):
    """解析SRT文件"""
    logger.info(f"读取SRT文件: {srt_path}")

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

    logger.info(f"解析到 {len(subtitles)} 条字幕")
    return subtitles


def translate_srt(input_path, output_path=None):
    """翻译SRT字幕文件"""
    if output_path is None:
        output_path = input_path

    logger.info("=" * 50)
    logger.info("SRT字幕翻译程序")
    logger.info("=" * 50)

    # 初始化翻译器
    translator = OllamaTranslator()

    # 解析SRT文件
    subtitles = parse_srt_file(input_path)

    # 翻译每条字幕
    translated_subtitles = []
    logger.info("开始翻译字幕...")

    for i, (index, timestamp, text) in enumerate(tqdm(subtitles, desc="翻译进度")):
        logger.info(f"[{i + 1}/{len(subtitles)}] 处理字幕 #{index}")

        # 跳过空白或过短的文本
        if len(text.strip()) < 2:
            logger.info("跳过空白或过短的文本")
            translated_subtitles.append((index, timestamp, text))
            continue

        # 翻译文本
        translated_text = translator.translate_text(text)
        translated_subtitles.append((index, timestamp, translated_text))

    # 保存翻译结果
    logger.info(f"保存翻译结果到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for index, timestamp, text in translated_subtitles:
            f.write(f"{index}\n{timestamp}\n{text}\n\n")

    logger.info("翻译完成!")
    return True


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        logger.error("用法: python tran.py <输入SRT文件> <输出SRT文件>")
        logger.error("示例: python tran.py input.srt output.srt")
        logger.error("配置文件: config/tran-py.json")
        sys.exit(1)

    input_srt = sys.argv[1]
    output_srt = sys.argv[2]

    # 检查输入文件是否存在
    if not os.path.exists(input_srt):
        logger.error(f"输入文件不存在: {input_srt}")
        sys.exit(1)

    try:
        translate_srt(input_srt, output_srt)
    except Exception as e:
        logger.error(f"翻译失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()