import os
import sys
import requests
import json
from tqdm import tqdm
import re
import logging

# 导入标准化日志器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_cached_logger

logger = get_cached_logger("翻译服务")


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


def load_prompt():
    """加载模型提示词"""
    prompt_path = 'config/prompt.txt'
    default_prompt = "你是专业翻译。将外语翻译成自然流畅的中文，保持原意可适当润色修饰。只输出代码块格式：``````，将译文内容放入代码块中，不要有其它提示性内容。"
    
    try:
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
                if prompt:
                    return prompt
        return default_prompt
    except Exception as e:
        logger.warning(f"加载提示词文件失败，使用默认提示词: {e}")
        return default_prompt


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
        self.generate_url = f"{self.base_url}/api/generate"
        self.conversation_history = []
        self.max_history = 10

        logger.info(f"初始化翻译器 - API: {self.base_url}, 模型: {self.model}")

        # 从配置文件加载提示词
        self.system_prompt = load_prompt()

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

    def unload_model(self) -> bool:
        """卸载Ollama模型从显存"""
        try:
            logger.info(f"请求卸载Ollama模型: {self.model}")

            payload = {
                "model": self.model,
                "keep_alive": 0  # 立即卸载
            }

            response = requests.post(self.generate_url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Ollama模型 {self.model} 已卸载")
                return True
            else:
                logger.warning(f"Ollama卸载请求返回状态码: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama模型卸载请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"卸载Ollama模型失败: {e}")
            return False


class OpenAITranslator:
    def __init__(self):
        config = load_config()

        self.base_url = config.get('openai_base_url')
        self.api_key = config.get('openai_api_key')
        self.model = config.get('openai_model')

        if not self.base_url or not self.api_key or not self.model:
            logger.error("配置文件缺少必要参数: openai_base_url, openai_api_key 和 openai_model")
            raise ValueError("配置文件缺少必要参数")

        # 验证URL格式
        if not self.base_url.startswith(('http://', 'https://')):
            logger.error(f"URL格式错误: {self.base_url}")
            raise ValueError(f"URL格式错误: {self.base_url}")

        self.chat_url = f"{self.base_url.rstrip('/')}/chat/completions"
        self.conversation_history = []
        self.max_history = 10

        logger.info(f"初始化OpenAI翻译器 - API: {self.base_url}, 模型: {self.model}")

        # 从配置文件加载提示词
        self.system_prompt = load_prompt()

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
        """调用OpenAI兼容API翻译文本"""
        if not text.strip():
            return text

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": self.conversation_history + [{"role": "user", "content": text}],
                "stream": False,
                "temperature": 0.3,
                "top_p": 0.8,
                "max_tokens": 2048
            }

            logger.info(f"正在翻译: {text[:30]}...")
            response = requests.post(self.chat_url, headers=headers, json=payload, timeout=450)
            response.raise_for_status()

            result = response.json()
            translated = result["choices"][0]["message"]["content"]

            # 提取代码块中的翻译结果
            translated = self.extract_translation(translated)

            # 添加到对话历史
            self.add_to_history(text, result["choices"][0]["message"]["content"])

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


def create_translator():
    """根据配置创建翻译器"""
    config = load_config()
    translator_type = config.get('translator_type', 'ollama').lower()
    
    if translator_type == 'openai':
        logger.info("使用 OpenAI 兼容接口翻译器")
        return OpenAITranslator()
    elif translator_type == 'ollama':
        logger.info("使用 Ollama 接口翻译器")
        return OllamaTranslator()
    else:
        logger.error(f"不支持的翻译器类型: {translator_type}")
        raise ValueError(f"不支持的翻译器类型: {translator_type}")


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
    return translate_srt_with_callback(input_path, None, output_path)


def translate_srt_with_callback(input_path, progress_callback=None, output_path=None):
    """带进度回调的SRT字幕翻译函数"""
    if output_path is None:
        output_path = input_path

    logger.info("=" * 50)
    logger.info("SRT字幕翻译程序")
    logger.info("=" * 50)

    # 初始化翻译器（根据配置自动选择）
    translator = create_translator()

    # 解析SRT文件
    subtitles = parse_srt_file(input_path)

    # 翻译每条字幕
    translated_subtitles = []
    logger.info("开始翻译字幕...")
    
    total_count = len(subtitles)

    for i, (index, timestamp, text) in enumerate(tqdm(subtitles, desc="翻译进度")):
        logger.info(f"[{i + 1}/{total_count}] 处理字幕 #{index}")
        
        # 调用进度回调
        if progress_callback:
            progress_callback(i + 1, total_count)

        # 跳过空白或过短的文本
        if len(text.strip()) < 2:
            logger.info("跳过空白或过短的文本")
            translated_subtitles.append((index, timestamp, text))
            continue

        # 翻译文本
        translated_text = translator.translate_text(text)
        translated_subtitles.append((index, timestamp, translated_text))
    
    # 最后一次调用进度回调，表示完成
    if progress_callback:
        progress_callback(total_count, total_count)

    # 保存翻译结果
    logger.info(f"保存翻译结果到: {output_path}")
    from src.utils.srt_checker import clean_srt_content
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for index, timestamp, text in translated_subtitles:
            # 在保存时执行SRT内容清理
            cleaned_text = clean_srt_content(text)
            f.write(f"{index}\n{timestamp}\n{cleaned_text}\n\n")

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