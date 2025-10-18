"""
音频预处理模块
提供轻度降噪和人声增强功能，优化Whisper转录效果
"""

import os
import subprocess
import tempfile
from typing import Optional, Dict, Any
from .logger import get_cached_logger

logger = get_cached_logger("音频预处理器")

class AudioPreprocessor:
    """音频预处理器"""
    
    def __init__(self):
        self.temp_files = []  # 追踪临时文件以便清理
    
    def preprocess_audio(self, input_audio_path: str, output_audio_path: str = None, 
                        enable_enhancement: bool = True) -> str:
        """
        对音频进行预处理，包括轻度降噪和人声增强
        
        Args:
            input_audio_path: 输入音频文件路径
            output_audio_path: 输出音频文件路径（可选，默认创建临时文件）
            enable_enhancement: 是否启用人声增强（默认True）
            
        Returns:
            处理后的音频文件路径
        """
        if not os.path.exists(input_audio_path):
            raise FileNotFoundError(f"输入音频文件不存在: {input_audio_path}")
        
        # 如果未指定输出路径，创建临时文件
        if output_audio_path is None:
            with tempfile.NamedTemporaryFile(suffix="_processed.wav", delete=False) as temp_file:
                output_audio_path = temp_file.name
                self.temp_files.append(output_audio_path)
        
        try:
            logger.info(f"开始音频预处理: {input_audio_path}")
            
            if enable_enhancement:
                # 增强模式：轻度降噪 + 人声增强
                filter_chain = self._build_enhancement_filter()
            else:
                # 基础模式：仅轻度降噪
                filter_chain = self._build_basic_filter()
            
            # 构建FFmpeg命令
            cmd = [
                "ffmpeg", "-i", input_audio_path,
                "-acodec", "pcm_s16le",  # 16位PCM编码
                "-ar", "16000",  # 16kHz采样率
                "-ac", "1",  # 单声道
                "-af", filter_chain,  # 音频滤镜链
                "-threads", "2",  # 预处理使用较少线程避免过载
                "-f", "wav",
                output_audio_path, "-y"
            ]
            
            logger.debug(f"FFmpeg预处理命令: {' '.join(cmd)}")
            
            # 执行预处理
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "未知FFmpeg错误"
                logger.error(f"音频预处理失败: {error_msg}")
                raise subprocess.CalledProcessError(result.returncode, cmd, error_msg)
            
            # 验证输出文件
            if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                raise Exception("预处理后的音频文件无效")
            
            logger.info(f"音频预处理完成: {output_audio_path}")
            return output_audio_path
            
        except Exception as e:
            # 清理失败的输出文件
            if output_audio_path and os.path.exists(output_audio_path):
                try:
                    os.remove(output_audio_path)
                except:
                    pass
            raise Exception(f"音频预处理失败: {e}")
    
    def _build_enhancement_filter(self) -> str:
        """构建人声增强滤镜链"""
        # 轻度音频预处理滤镜链，专为人声优化
        filters = [
            "volume=1.2",  # 轻微提升音量
            "highpass=f=80",  # 高通滤波器，去除低频噪音（80Hz以下）
            "lowpass=f=8000",  # 低通滤波器，去除高频噪音（8kHz以上）
            "compand=attacks=0.3:decays=0.8:points=-70/-70|-24/-12|0/-6",  # 动态范围压缩，突出人声
            "equalizer=f=1000:width_type=h:width=2:g=2",  # 轻微增强1kHz人声频段
            "equalizer=f=3000:width_type=h:width=2:g=1.5",  # 轻微增强3kHz清晰度频段
            "dynaudnorm=g=3:f=250:r=0.9:p=0.5:m=100:s=5"  # 动态音频标准化，保持音量一致性
        ]
        return ",".join(filters)
    
    def _build_basic_filter(self) -> str:
        """构建基础降噪滤镜链"""
        # 基础音频处理，仅降噪
        filters = [
            "volume=1.1",  # 轻微提升音量
            "highpass=f=60",  # 去除极低频噪音
            "lowpass=f=10000",  # 去除极高频噪音
            "dynaudnorm=g=2:f=300:r=0.95:p=0.6"  # 轻度动态标准化
        ]
        return ",".join(filters)
    
    def analyze_audio_quality(self, audio_path: str) -> Dict[str, Any]:
        """
        分析音频质量，为预处理提供参数调整建议
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频质量分析结果
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        try:
            # 使用FFprobe分析音频特性
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", "-show_streams", audio_path
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, 
                encoding='utf-8', errors='replace', timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"音频分析失败: {result.stderr}")
                return {"error": "音频分析失败"}
            
            import json
            probe_data = json.loads(result.stdout)
            
            # 提取音频流信息
            audio_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                return {"error": "未找到音频流"}
            
            # 分析音频特性
            analysis = {
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0)),
                "duration": float(audio_stream.get('duration', 0)),
                "bit_rate": int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else None,
                "codec_name": audio_stream.get('codec_name', 'unknown'),
                "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024)
            }
            
            # 提供预处理建议
            suggestions = self._generate_preprocessing_suggestions(analysis)
            analysis["suggestions"] = suggestions
            
            return analysis
            
        except Exception as e:
            logger.error(f"音频质量分析失败: {e}")
            return {"error": f"分析失败: {e}"}
    
    def _generate_preprocessing_suggestions(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """根据音频分析结果生成预处理建议"""
        suggestions = {}
        
        # 采样率建议
        sample_rate = analysis.get('sample_rate', 0)
        if sample_rate < 16000:
            suggestions["sample_rate"] = "音频采样率较低，可能影响识别质量"
        elif sample_rate > 48000:
            suggestions["sample_rate"] = "音频采样率过高，建议降采样以提高处理速度"
        
        # 比特率建议
        bit_rate = analysis.get('bit_rate')
        if bit_rate and bit_rate < 64000:
            suggestions["bit_rate"] = "音频比特率较低，可能影响音质"
        
        # 声道建议
        channels = analysis.get('channels', 0)
        if channels > 2:
            suggestions["channels"] = "多声道音频，建议转换为单声道以优化处理"
        
        # 文件大小建议
        file_size = analysis.get('file_size_mb', 0)
        duration = analysis.get('duration', 1)
        if duration > 0:
            size_per_minute = file_size / (duration / 60)
            if size_per_minute > 10:
                suggestions["file_size"] = "音频文件较大，预处理可能需要更多时间"
        
        return suggestions
    
    def cleanup_temp_files(self):
        """清理创建的临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"已清理临时音频文件: {temp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file}: {e}")
        self.temp_files.clear()
    
    def __del__(self):
        """析构函数，确保清理临时文件"""
        self.cleanup_temp_files()

# 创建全局预处理器实例
audio_preprocessor = AudioPreprocessor()

def preprocess_audio_for_whisper(input_path: str, output_path: str = None, 
                                enable_enhancement: bool = True) -> str:
    """
    为Whisper转录预处理音频的便捷函数
    
    Args:
        input_path: 输入音频路径
        output_path: 输出音频路径（可选）
        enable_enhancement: 是否启用人声增强
        
    Returns:
        预处理后的音频文件路径
    """
    return audio_preprocessor.preprocess_audio(input_path, output_path, enable_enhancement)

def analyze_audio_quality(audio_path: str) -> Dict[str, Any]:
    """
    分析音频质量的便捷函数
    
    Args:
        audio_path: 音频文件路径
        
    Returns:
        音频质量分析结果
    """
    return audio_preprocessor.analyze_audio_quality(audio_path)

__all__ = [
    'AudioPreprocessor',
    'audio_preprocessor', 
    'preprocess_audio_for_whisper',
    'analyze_audio_quality'
]