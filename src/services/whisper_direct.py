"""
Whisper直接调用模块
替代HTTP服务方式，直接在程序内部调用Whisper模型
关闭上下文记忆功能，每句话独立处理
"""

import whisper
import torch
import gc
import threading
import time
import os
import tempfile
import subprocess
import sys
import io
from contextlib import redirect_stderr, redirect_stdout
from typing import Optional, Dict, Any, List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.audio_preprocessor import preprocess_audio_for_whisper, analyze_audio_quality
from utils.logger import get_cached_logger

logger = get_cached_logger("Whisper语音识别")

class WhisperDirectManager:
    """Whisper直接调用管理器"""
    
    def __init__(self, preload=False):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "large-v3-turbo"  # 使用turbo版本，文件更小且速度更快
        self.lock = threading.Lock()
        self.is_loading = False
        self.is_warmed_up = False
        
        # 设置本地模型目录
        self.whisper_cache_dir = os.path.abspath("whisper")
        os.makedirs(self.whisper_cache_dir, exist_ok=True)
        
        # 优化设置
        if self.device == "cuda":
            torch.cuda.set_per_process_memory_fraction(0.90)  # 使用90%显存(turbo模型需求较小，留10%缓冲)
            torch.backends.cudnn.benchmark = False  # 禁用benchmark避免超时
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'  # 增大分割大小以提升性能
            os.environ['CUDA_LAUNCH_BLOCKING'] = '1'  # 启用同步执行
        
        # 防止并行冲突
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        
        logger.info(f"初始化Whisper直接调用管理器，设备: {self.device}")
        logger.info(f"Whisper缓存目录: {self.whisper_cache_dir}")
        
        # 清理系统缓存中可能损坏的文件
        self._cleanup_system_cache()
        
        # 如果启用预加载，立即加载模型并预热
        if preload:
            logger.info("启用预加载模式，立即加载并预热Whisper模型...")
            self.preload_and_warmup()
    
    def _cleanup_system_cache(self):
        """清理系统缓存中可能损坏的Whisper模型"""
        try:
            import os
            
            # 系统缓存路径
            system_cache = os.path.expanduser("~/.cache/whisper")
            if os.path.exists(system_cache):
                large_v3_turbo_path = os.path.join(system_cache, "large-v3-turbo.pt")
                if os.path.exists(large_v3_turbo_path):
                    try:
                        os.remove(large_v3_turbo_path)
                        logger.info("已清理系统缓存中可能损坏的large-v3-turbo.pt")
                    except Exception as e:
                        logger.warning(f"清理系统缓存失败: {e}")
        except Exception as e:
            logger.warning(f"清理系统缓存过程出错: {e}")
    
    def _check_local_model(self) -> str:
        """检查本地模型文件"""
        local_model_path = os.path.join(self.whisper_cache_dir, f"{self.model_name}.pt")
        if os.path.exists(local_model_path):
            file_size = os.path.getsize(local_model_path) / (1024**3)  # GB
            logger.info(f"发现本地模型文件: {local_model_path} ({file_size:.2f}GB)")
            return local_model_path
        return None
    
    def _load_model(self) -> bool:
        """加载Whisper模型"""
        if self.is_loading:
            return False

        try:
            self.is_loading = True
            logger.info(f"开始加载Whisper {self.model_name}模型到{self.device}")

            # 步骤1: 如果是本地Ollama且使用CUDA，先卸载Ollama模型释放显存
            if self.device == "cuda":
                try:
                    # 动态导入避免循环依赖
                    import json
                    import requests

                    config_path = 'config/tran-py.json'
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)

                        translator_type = config.get('translator_type', 'ollama')
                        ollama_url = config.get('ollama_api', '')
                        ollama_model = config.get('ollama_model', '')

                        # 检查是否为本地Ollama
                        if translator_type == 'ollama' and ollama_url and ollama_model:
                            is_local = any(host in ollama_url.lower() for host in ['127.0.0.1', 'localhost', '::1'])

                            if is_local:
                                logger.info(f"检测到本地Ollama，加载前先卸载模型释放显存...")
                                try:
                                    unload_url = f"{ollama_url}/api/generate"
                                    payload = {"model": ollama_model, "keep_alive": 0}
                                    response = requests.post(unload_url, json=payload, timeout=10)

                                    if response.status_code == 200:
                                        logger.info(f"✅ Ollama模型已卸载")
                                    else:
                                        logger.debug(f"Ollama卸载返回: {response.status_code}")
                                except Exception as e:
                                    logger.debug(f"卸载Ollama失败(继续): {e}")
                except Exception as e:
                    logger.debug(f"检查Ollama配置失败(继续): {e}")

            # 步骤2: 清理之前的模型
            if self.model is not None:
                del self.model
                self.model = None

            if self.device == "cuda":
                torch.cuda.empty_cache()
            gc.collect()
            
            # 检查本地模型
            local_model_path = self._check_local_model()
            
            start_time = time.time()
            
            if local_model_path:
                # 尝试加载本地模型
                logger.info("尝试加载本地模型...")
                try:
                    self.model = whisper.load_model(local_model_path, device=self.device)
                    logger.info("本地模型加载成功")
                except Exception as e:
                    logger.warning(f"本地模型加载失败，将重新下载: {e}")
                    # 删除损坏的文件
                    try:
                        os.remove(local_model_path)
                    except:
                        pass
                    self.model = None
            
            if self.model is None:
                # 下载并加载模型到项目目录
                logger.info(f"正在下载{self.model_name}模型到项目目录...")
                self.model = whisper.load_model(
                    self.model_name, 
                    device=self.device,
                    download_root=self.whisper_cache_dir
                )
                logger.info("模型下载并加载成功")
            
            # 设置为评估模式，不需要梯度
            self.model.eval()
            for param in self.model.parameters():
                param.requires_grad = False
            
            load_time = time.time() - start_time
            
            if self.device == "cuda":
                memory_used = torch.cuda.memory_allocated() / (1024**3)
                torch.cuda.empty_cache()
                logger.info(f"模型加载完成，用时: {load_time:.2f}秒，显存使用: {memory_used:.2f}GB")
            else:
                logger.info(f"模型加载完成，用时: {load_time:.2f}秒")
            
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
        finally:
            self.is_loading = False
    
    def preload_and_warmup(self):
        """预加载模型并进行预热"""
        try:
            # 加载模型
            if not self._load_model():
                raise RuntimeError("预加载Whisper模型失败")
            
            logger.info("开始预热Whisper模型...")
            start_time = time.time()
            
            # 创建一个短的测试音频用于预热
            import numpy as np
            
            # 创建5秒的无声音频用于预热 (16kHz采样率)
            sample_rate = 16000
            duration = 5
            dummy_audio = np.zeros(sample_rate * duration, dtype=np.float32)
            
            # 进行一次空转录来预热模型
            with torch.no_grad():
                result = self.model.transcribe(
                    dummy_audio,
                    language=None,
                    task="transcribe",
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    condition_on_previous_text=False,
                    verbose=False,
                    fp16=True if self.device == "cuda" else False
                )
            
            warmup_time = time.time() - start_time
            self.is_warmed_up = True
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                memory_used = torch.cuda.memory_allocated() / (1024**3)
                logger.info(f"模型预热完成，用时: {warmup_time:.2f}秒，显存使用: {memory_used:.2f}GB")
            else:
                logger.info(f"模型预热完成，用时: {warmup_time:.2f}秒")
            
            return True
            
        except Exception as e:
            logger.error(f"模型预热失败: {e}")
            self.is_warmed_up = False
            return False
    
    def get_model(self):
        """获取模型实例，如果未加载则自动加载"""
        with self.lock:
            if self.model is None:
                if not self._load_model():
                    raise RuntimeError("Whisper模型加载失败")
            return self.model
    
    def extract_audio_from_video(self, video_path: str, task_id: str = None) -> str:
        """从视频中提取音频到指定任务目录"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 如果提供了task_id，将音频保存到task目录中
        if task_id:
            task_temp_dir = os.path.join("cache", "temp", task_id)
            os.makedirs(task_temp_dir, exist_ok=True)
            audio_path = os.path.join(task_temp_dir, f"{task_id}_audio.wav")
        else:
            # 创建临时音频文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                audio_path = temp_audio.name
        
        # FFmpeg命令提取音频，增加轻度预处理
        cmd = [
            "ffmpeg", "-i", video_path, 
            "-vn",  # 不要视频流
            "-acodec", "pcm_s16le",  # 16位PCM编码
            "-ar", "16000",  # 16kHz采样率
            "-ac", "1",  # 单声道
            "-af", "volume=1.2,highpass=f=80,lowpass=f=8000,dynaudnorm=g=3:f=250:r=0.9:p=0.5",  # 音频预处理滤镜
            "-threads", "4",  # 多线程
            "-f", "wav",  # WAV格式
            audio_path, "-y"  # 覆盖输出文件
        ]
        
        try:
            logger.info(f"开始提取并预处理音频: {video_path}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                encoding='utf-8',  # 明确指定UTF-8编码
                errors='replace',  # 遇到编码错误时替换为?
                timeout=900  # 15分钟超时（预处理需要更多时间）
            )
            
            if result.returncode != 0:
                # 如果stderr包含编码错误，尝试用bytes处理
                try:
                    error_msg = result.stderr
                except:
                    error_msg = "FFmpeg处理错误（包含非UTF-8字符）"
                logger.error(f"FFmpeg音频预处理错误: {error_msg}")
                raise subprocess.CalledProcessError(result.returncode, cmd, error_msg)
            
            # 验证预处理结果
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                raise Exception("音频预处理生成的文件无效")
            
            # 可选：分析预处理后的音频质量
            try:
                quality_info = analyze_audio_quality(audio_path)
                if quality_info.get('sample_rate') == 16000:
                    logger.info(f"音频预处理完成，质量检查通过: {audio_path}")
                else:
                    logger.warning(f"预处理音频采样率异常: {quality_info.get('sample_rate', 'unknown')}")
            except Exception as e:
                logger.debug(f"音频质量分析失败（不影响使用）: {e}")
            
            logger.info(f"音频提取和预处理完成: {audio_path}")
            return audio_path
            
        except Exception as e:
            # 清理临时文件
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            raise Exception(f"音频提取失败: {e}")
    
    def transcribe_audio(self, audio_path: str, progress_callback=None) -> Dict[str, Any]:
        """转录音频文件"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        model = self.get_model()
        
        # Whisper转录选项 - 关闭上下文记忆，提升质量
        transcribe_options = {
            "language": None,  # 自动检测语言
            "task": "transcribe",  # 转录任务
            "beam_size": 5,  # 增大束搜索以提升准确度（1->5）
            "best_of": 5,  # 增大候选数量以获得更好结果（1->5）
            "temperature": 0.0,  # 温度设置为0，确保结果稳定
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
            "condition_on_previous_text": False,  # 关闭上下文记忆！每句话独立处理
            "initial_prompt": None,  # 不使用初始提示
            "verbose": False,  # 不显示详细信息
            "fp16": True if self.device == "cuda" else False  # GPU使用半精度
        }
        
        try:
            logger.info(f"开始转录音频: {audio_path}")
            start_time = time.time()
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            # 执行转录，关闭梯度计算，同时捕获控制台输出
            if progress_callback:
                # 捕获stderr以获取tqdm输出
                captured_output = io.StringIO()
                with torch.no_grad(), redirect_stderr(captured_output):
                    # 在后台线程中监控输出
                    def monitor_progress():
                        last_pos = 0
                        while True:
                            time.sleep(0.1)
                            captured_output.seek(last_pos)
                            new_content = captured_output.read()
                            if new_content:
                                lines = new_content.strip().split('\n')
                                for line in lines:
                                    if line.strip() and ('frames/s' in line or '%|' in line):
                                        progress_callback(line.strip())
                                last_pos = captured_output.tell()
                            else:
                                # 检查是否完成
                                if not hasattr(monitor_progress, 'running') or not monitor_progress.running:
                                    break
                    
                    monitor_progress.running = True
                    monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
                    monitor_thread.start()
                    
                    try:
                        result = model.transcribe(audio_path, **transcribe_options)
                    finally:
                        monitor_progress.running = False
                        if monitor_thread.is_alive():
                            monitor_thread.join(timeout=1)
            else:
                with torch.no_grad():
                    result = model.transcribe(audio_path, **transcribe_options)
            
            transcribe_time = time.time() - start_time
            
            # 处理结果
            segments = result.get('segments', [])
            text = result.get('text', '').strip()
            language = result.get('language', 'unknown')
            
            # 确保每个片段都是独立的（移除可能的上下文依赖）
            processed_segments = []
            for segment in segments:
                processed_segment = {
                    'id': segment.get('id', 0),
                    'start': segment.get('start', 0.0),
                    'end': segment.get('end', 0.0),
                    'text': segment.get('text', '').strip(),
                    'avg_logprob': segment.get('avg_logprob', 0.0),
                    'compression_ratio': segment.get('compression_ratio', 0.0),
                    'no_speech_prob': segment.get('no_speech_prob', 0.0)
                }
                processed_segments.append(processed_segment)
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
                memory_used = torch.cuda.memory_allocated() / (1024**3)
                logger.info(f"转录完成，用时: {transcribe_time:.2f}秒，显存: {memory_used:.2f}GB")
            else:
                logger.info(f"转录完成，用时: {transcribe_time:.2f}秒")
            
            return {
                'success': True,
                'text': text,
                'language': language,
                'segments': processed_segments,
                'processing_time': transcribe_time,
                'context_disabled': True,  # 标记已关闭上下文记忆
                'segment_count': len(processed_segments)
            }
            
        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            if self.device == "cuda":
                torch.cuda.empty_cache()
            raise Exception(f"转录失败: {e}")
    
    def transcribe_video(self, video_path: str, task_id: str = None, progress_callback=None) -> Dict[str, Any]:
        """转录视频文件（提取音频后转录）"""
        audio_path = None
        try:
            # 提取音频到任务目录
            audio_path = self.extract_audio_from_video(video_path, task_id)
            
            # 转录音频
            result = self.transcribe_audio(audio_path, progress_callback)
            
            # 添加视频信息
            result['video_path'] = video_path
            result['audio_path'] = audio_path
            
            return result
            
        finally:
            # 只在没有task_id时清理临时音频文件（有task_id时保留在任务目录）
            if not task_id and audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.debug(f"已清理临时音频文件: {audio_path}")
                except Exception as e:
                    logger.warning(f"清理临时音频文件失败: {e}")
    
    def unload_model(self):
        """卸载模型，释放内存"""
        with self.lock:
            if self.model is not None:
                logger.info("开始卸载Whisper模型")
                del self.model
                self.model = None
                
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                gc.collect()
                
                logger.info("模型已卸载")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        with self.lock:
            # 检测模型当前所在设备
            current_device = None
            if self.model is not None:
                # 获取模型第一个参数的设备
                try:
                    first_param = next(self.model.parameters())
                    current_device = str(first_param.device)
                except StopIteration:
                    current_device = "unknown"

            status = {
                'model_loaded': self.model is not None,
                'device': self.device,
                'current_model_device': current_device,  # 模型当前所在设备
                'model_name': self.model_name,
                'is_loading': self.is_loading,
                'is_warmed_up': self.is_warmed_up,
                'context_memory_disabled': True
            }

            if torch.cuda.is_available():
                status['cuda_available'] = True
                status['cuda_memory'] = {
                    'allocated_gb': torch.cuda.memory_allocated() / (1024**3),
                    'reserved_gb': torch.cuda.memory_reserved() / (1024**3),
                    'device_name': torch.cuda.get_device_name()
                }
            else:
                status['cuda_available'] = False

            return status

    def move_to_cpu(self) -> bool:
        """将模型移动到CPU内存"""
        with self.lock:
            if self.model is None:
                logger.warning("模型未加载，无法移动到CPU")
                return False

            try:
                logger.info("将Whisper模型移动到CPU...")
                start_time = time.time()

                self.model = self.model.to('cpu')

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

                move_time = time.time() - start_time
                logger.info(f"模型已移至CPU，用时: {move_time:.2f}秒")
                return True

            except Exception as e:
                logger.error(f"模型移至CPU失败: {e}")
                return False

    def move_to_gpu(self) -> bool:
        """将模型移动到GPU显存"""
        with self.lock:
            if self.model is None:
                logger.warning("模型未加载，无法移动到GPU")
                return False

            if not torch.cuda.is_available():
                logger.error("CUDA不可用，无法移动到GPU")
                return False

            try:
                logger.info("将Whisper模型移动到GPU...")
                start_time = time.time()

                # 先清理显存
                torch.cuda.empty_cache()
                gc.collect()

                self.model = self.model.to('cuda')

                move_time = time.time() - start_time
                memory_used = torch.cuda.memory_allocated() / (1024**3)
                logger.info(f"模型已移至GPU，用时: {move_time:.2f}秒，显存: {memory_used:.2f}GB")
                return True

            except Exception as e:
                logger.error(f"模型移至GPU失败: {e}")
                return False

# 全局单例
_whisper_manager = None

def get_whisper_manager(preload=False) -> WhisperDirectManager:
    """获取全局Whisper管理器单例"""
    global _whisper_manager
    if _whisper_manager is None:
        _whisper_manager = WhisperDirectManager(preload=preload)
    return _whisper_manager

def transcribe_video_direct(video_path: str, task_id: str = None, progress_callback=None) -> Dict[str, Any]:
    """直接转录视频的便捷函数"""
    manager = get_whisper_manager()
    return manager.transcribe_video(video_path, task_id, progress_callback)

def transcribe_audio_direct(audio_path: str, progress_callback=None) -> Dict[str, Any]:
    """直接转录音频的便捷函数"""
    manager = get_whisper_manager()
    return manager.transcribe_audio(audio_path, progress_callback)

def get_whisper_status() -> Dict[str, Any]:
    """获取Whisper状态的便捷函数"""
    manager = get_whisper_manager()
    return manager.get_status()

def unload_whisper_model():
    """卸载Whisper模型的便捷函数"""
    manager = get_whisper_manager()
    manager.unload_model()