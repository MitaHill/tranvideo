"""
显存轮询管理器
管理Whisper和Ollama模型在显存中的加载和卸载
实现显存资源的高效利用
"""

import torch
import gc
import requests
import time
import re
from typing import Optional, Dict, Any
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("显存管理器")


class VRAMManager:
    """显存轮询管理器"""

    def __init__(self):
        self.cuda_available = torch.cuda.is_available()
        self.whisper_manager = None
        self.ollama_base_url = None
        self.ollama_model = None
        self.vram_rotation_enabled = False  # 显存轮询是否启用
        self.translator_type = None

        if self.cuda_available:
            logger.info(f"CUDA可用，设备: {torch.cuda.get_device_name()}")
            self._log_vram_status("初始化")
        else:
            logger.warning("CUDA不可用，显存管理功能将被禁用")

    def _log_vram_status(self, stage: str):
        """记录显存状态"""
        if not self.cuda_available:
            return

        allocated = torch.cuda.memory_allocated() / (1024**3)
        reserved = torch.cuda.memory_reserved() / (1024**3)
        logger.info(f"[{stage}] 显存状态 - 已分配: {allocated:.2f}GB, 已保留: {reserved:.2f}GB")

    def set_whisper_manager(self, manager):
        """设置Whisper管理器引用"""
        self.whisper_manager = manager
        logger.info("已关联Whisper管理器")

    def set_ollama_config(self, base_url: str, model: str, translator_type: str = "ollama"):
        """设置Ollama配置并判断是否启用显存轮询"""
        self.ollama_base_url = base_url
        self.ollama_model = model
        self.translator_type = translator_type

        # 判断是否启用显存轮询
        # 条件: 1. translator_type为ollama  2. 使用127.0.0.1地址(仅127.0.0.1启用，localhost不启用)
        if translator_type == "ollama" and base_url:
            # 检查是否为127.0.0.1地址(严格匹配，localhost不触发轮询)
            # 使用更精确的匹配，避免误判如 192.127.0.1.100 这样的地址
            is_127_local = bool(re.search(r'://127\.0\.0\.1[:/]', base_url))

            if is_127_local:
                self.vram_rotation_enabled = True
                logger.info(f"✅ 已启用显存轮询管理 - Ollama本地模式 (127.0.0.1)")
                logger.info(f"   URL: {base_url}, 模型: {model}")
                logger.info(f"   显存共享: Whisper ⇄ Ollama 自动切换")
            else:
                self.vram_rotation_enabled = False
                logger.info(f"❌ 禁用显存轮询 - Ollama远程/大显存模式 (Whisper常驻显存)")
                logger.info(f"   URL: {base_url}, 模型: {model}")
                logger.info(f"   显存模式: Whisper常驻GPU，Ollama独立运行")
        else:
            self.vram_rotation_enabled = False
            logger.info(f"❌ 禁用显存轮询 - 使用 {translator_type} 翻译器 (Whisper常驻显存)")
            logger.info(f"   配置: {base_url}")

    # ==================== Whisper 显存管理 ====================

    def move_whisper_to_cpu(self) -> bool:
        """将Whisper模型从GPU移动到CPU内存"""
        # 检查是否启用显存轮询
        if not self.vram_rotation_enabled:
            logger.debug("显存轮询未启用，Whisper保持在GPU")
            return True

        if not self.cuda_available or not self.whisper_manager:
            logger.warning("CUDA不可用或Whisper管理器未设置，跳过操作")
            return False

        try:
            with self.whisper_manager.lock:
                if self.whisper_manager.model is None:
                    logger.info("Whisper模型未加载，无需移动")
                    return True

                logger.info("开始将Whisper模型移动到CPU...")
                start_time = time.time()

                # 移动模型到CPU
                self.whisper_manager.model = self.whisper_manager.model.to('cpu')

                # 清理GPU缓存
                torch.cuda.empty_cache()
                gc.collect()

                move_time = time.time() - start_time
                logger.info(f"Whisper模型已移至CPU，用时: {move_time:.2f}秒")
                self._log_vram_status("Whisper移至CPU后")

                return True

        except Exception as e:
            logger.error(f"Whisper模型移至CPU失败: {e}")
            return False

    def move_whisper_to_gpu(self) -> bool:
        """将Whisper模型从CPU移动回GPU显存"""
        # 检查是否启用显存轮询
        if not self.vram_rotation_enabled:
            logger.debug("显存轮询未启用，Whisper已在GPU")
            return True

        if not self.cuda_available or not self.whisper_manager:
            logger.warning("CUDA不可用或Whisper管理器未设置，跳过操作")
            return False

        try:
            with self.whisper_manager.lock:
                if self.whisper_manager.model is None:
                    logger.info("Whisper模型未加载，无需移动")
                    return True

                logger.info("开始将Whisper模型移动到GPU...")
                start_time = time.time()

                # 清理GPU缓存为模型腾出空间
                torch.cuda.empty_cache()
                gc.collect()

                # 移动模型到GPU
                self.whisper_manager.model = self.whisper_manager.model.to('cuda')

                move_time = time.time() - start_time
                logger.info(f"Whisper模型已移至GPU，用时: {move_time:.2f}秒")
                self._log_vram_status("Whisper移至GPU后")

                return True

        except Exception as e:
            logger.error(f"Whisper模型移至GPU失败: {e}")
            return False

    def unload_whisper_completely(self) -> bool:
        """完全卸载Whisper模型(释放CPU和GPU内存)"""
        if not self.whisper_manager:
            logger.warning("Whisper管理器未设置，跳过操作")
            return False

        try:
            logger.info("开始完全卸载Whisper模型...")
            self.whisper_manager.unload_model()
            logger.info("Whisper模型已完全卸载")
            self._log_vram_status("Whisper完全卸载后")
            return True

        except Exception as e:
            logger.error(f"完全卸载Whisper模型失败: {e}")
            return False

    # ==================== Ollama 显存管理 ====================

    def unload_ollama_model(self) -> bool:
        """卸载Ollama模型从显存(通过API)"""
        # 检查是否启用显存轮询
        if not self.vram_rotation_enabled:
            logger.debug("显存轮询未启用，跳过Ollama卸载")
            return True

        if not self.ollama_base_url or not self.ollama_model:
            logger.warning("Ollama配置未设置，跳过操作")
            return False

        try:
            logger.info(f"开始卸载Ollama模型: {self.ollama_model}")

            # 构建API请求
            url = f"{self.ollama_base_url}/api/generate"
            payload = {
                "model": self.ollama_model,
                "keep_alive": 0  # 立即卸载模型
            }

            # 发送请求
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Ollama模型 {self.ollama_model} 已卸载")
                self._log_vram_status("Ollama卸载后")
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

    # ==================== 工作流程管理 ====================

    def prepare_for_transcription(self) -> bool:
        """准备转录阶段: 确保Whisper在GPU，卸载Ollama"""
        logger.info("=" * 50)
        logger.info("准备转录阶段 - 切换到Whisper")
        logger.info("=" * 50)

        success = True

        # 1. 卸载Ollama模型
        if not self.unload_ollama_model():
            logger.warning("Ollama模型卸载失败，继续执行")

        # 2. 确保Whisper在GPU
        if self.whisper_manager:
            if not self.move_whisper_to_gpu():
                logger.error("Whisper模型移至GPU失败")
                success = False

        self._log_vram_status("转录准备完成")
        return success

    def prepare_for_translation(self) -> bool:
        """准备翻译阶段: 将Whisper移至CPU，为Ollama腾出显存"""
        logger.info("=" * 50)
        logger.info("准备翻译阶段 - 切换到Ollama")
        logger.info("=" * 50)

        success = True

        # 将Whisper移至CPU释放显存
        if self.whisper_manager:
            if not self.move_whisper_to_cpu():
                logger.error("Whisper模型移至CPU失败")
                success = False

        self._log_vram_status("翻译准备完成")
        logger.info("显存已为Ollama模型预留")
        return success

    def cleanup_all(self) -> bool:
        """清理所有模型(任务完成后)"""
        logger.info("=" * 50)
        logger.info("清理所有模型")
        logger.info("=" * 50)

        success = True

        # 1. 卸载Ollama
        if not self.unload_ollama_model():
            logger.warning("Ollama模型卸载失败")
            success = False

        # 2. 可选: 将Whisper移至CPU或完全卸载
        # 这里选择移至CPU以加快下次使用
        if self.whisper_manager:
            if not self.move_whisper_to_cpu():
                logger.warning("Whisper模型移至CPU失败")
                success = False

        self._log_vram_status("清理完成")
        return success

    def get_vram_info(self) -> Dict[str, Any]:
        """获取当前显存信息"""
        if not self.cuda_available:
            return {
                "cuda_available": False,
                "message": "CUDA不可用"
            }

        return {
            "cuda_available": True,
            "device_name": torch.cuda.get_device_name(),
            "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
            "reserved_gb": torch.cuda.memory_reserved() / (1024**3),
            "total_gb": torch.cuda.get_device_properties(0).total_memory / (1024**3)
        }


# 全局单例
_vram_manager = None

def get_vram_manager() -> VRAMManager:
    """获取全局显存管理器单例"""
    global _vram_manager
    if _vram_manager is None:
        _vram_manager = VRAMManager()
    return _vram_manager
