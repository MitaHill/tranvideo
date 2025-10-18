"""
文件类型验证模块
仅允许MP4文件格式，提供严格的文件类型验证
"""

import os
import mimetypes
from typing import Tuple


class FileTypeVerifier:
    """文件类型验证器"""
    
    # 允许的文件扩展名（仅MP4）
    ALLOWED_EXTENSIONS = {'.mp4'}
    
    # 允许的MIME类型
    ALLOWED_MIME_TYPES = {
        'video/mp4',
        'application/octet-stream'  # 某些情况下MP4会被识别为此类型
    }
    
    # MP4文件头魔数（前8字节的可能组合）
    MP4_SIGNATURES = [
        b'ftyp',  # 从第4字节开始的MP4标识
    ]
    
    def __init__(self, max_file_size_mb: int = 102400):
        """
        初始化文件验证器
        
        Args:
            max_file_size_mb: 最大文件大小（MB），默认102400MB
        """
        self.max_file_size = max_file_size_mb * 1024 * 1024  # 转换为字节
    
    def validate_file(self, file) -> Tuple[bool, str]:
        """
        验证上传的文件
        
        Args:
            file: Flask文件对象
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 错误信息)
        """
        try:
            # 1. 检查文件是否存在
            if not file or not file.filename:
                return False, "未选择文件或文件名为空"
            
            filename = file.filename.lower()
            
            # 2. 检查文件扩展名
            ext = os.path.splitext(filename)[1]
            if ext not in self.ALLOWED_EXTENSIONS:
                return False, f"不允许的文件格式: {ext}，仅支持MP4格式"
            
            # 3. 检查文件大小
            file.seek(0, 2)  # 移动到文件末尾
            file_size = file.tell()
            file.seek(0)     # 重置到文件开头
            
            if file_size > self.max_file_size:
                return False, f"文件过大: {file_size/1024/1024:.1f}MB，最大允许{self.max_file_size/1024/1024:.0f}MB"
            
            if file_size == 0:
                return False, "文件为空"
            
            # 4. 检查MIME类型
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
                return False, f"不允许的MIME类型: {mime_type}"
            
            # 5. 检查文件头魔数
            if not self._verify_file_signature(file):
                return False, "文件格式验证失败，不是有效的MP4文件"
            
            return True, "文件验证通过"
            
        except Exception as e:
            return False, f"文件验证时出错: {str(e)}"
    
    def _verify_file_signature(self, file) -> bool:
        """
        验证文件头魔数
        
        Args:
            file: Flask文件对象
            
        Returns:
            bool: 是否为有效的MP4文件
        """
        try:
            # 读取文件前20字节用于魔数检测
            file.seek(0)
            header = file.read(20)
            file.seek(0)  # 重置文件指针
            
            if len(header) < 8:
                return False
            
            # 检查MP4文件头特征
            # MP4文件通常在第4-7字节包含'ftyp'标识
            if len(header) >= 8:
                ftyp_signature = header[4:8]
                if ftyp_signature == b'ftyp':
                    return True
            
            # 检查其他可能的MP4标识
            header_str = header.decode('latin1', errors='ignore')
            return any(sig.decode('latin1') in header_str for sig in self.MP4_SIGNATURES)
            
        except Exception:
            return False
    
    def get_file_info(self, file) -> dict:
        """
        获取文件信息
        
        Args:
            file: Flask文件对象
            
        Returns:
            dict: 文件信息字典
        """
        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            mime_type, _ = mimetypes.guess_type(filename)
            
            return {
                'filename': filename,
                'size_bytes': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2),
                'extension': ext,
                'mime_type': mime_type or 'unknown'
            }
        except Exception as e:
            return {
                'error': f'获取文件信息失败: {str(e)}'
            }


# 全局验证器实例
file_verifier = FileTypeVerifier(max_file_size_mb=102400)


def verify_uploaded_file(file) -> Tuple[bool, str]:
    """
    验证上传的文件（便捷函数）
    
    Args:
        file: Flask文件对象
        
    Returns:
        Tuple[bool, str]: (是否通过验证, 错误信息)
    """
    return file_verifier.validate_file(file)


def get_uploaded_file_info(file) -> dict:
    """
    获取上传文件信息（便捷函数）
    
    Args:
        file: Flask文件对象
        
    Returns:
        dict: 文件信息字典
    """
    return file_verifier.get_file_info(file)