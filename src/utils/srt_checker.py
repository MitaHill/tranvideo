"""
SRT字幕文件内容检查和清理模块

功能：
- 清理翻译后的SRT字幕文件中的有害字符
- 移除AI模型输出的格式标记（反引号、思考标签等）
- 保持SRT文件原有格式和时间轴不变

作者：Claude Code
"""

import re
from .logger import get_cached_logger

logger = get_cached_logger("SRT_Checker")


def clean_srt_content(text):
    """
    清理SRT字幕内容中的有害字符
    
    Args:
        text (str): 需要清理的字幕文本内容
        
    Returns:
        str: 清理后的字幕文本
        
    清理内容：
    - 移除所有反引号字符（`）
    - 移除AI思考标签（<think></think>）
    - 保持原有空行、空格和格式不变
    """
    if not text or not isinstance(text, str):
        return text
    
    original_text = text
    
    # 移除AI思考标签（支持多行）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除所有反引号字符
    text = text.replace('`', '')
    
    # 记录清理操作
    if text != original_text:
        logger.info(f"SRT内容已清理: 原文长度{len(original_text)} -> 清理后长度{len(text)}")
    
    return text


def clean_srt_file(input_path, output_path=None):
    """
    清理整个SRT文件的内容
    
    Args:
        input_path (str): 输入SRT文件路径
        output_path (str, optional): 输出SRT文件路径，默认覆盖原文件
        
    Returns:
        bool: 清理是否成功
    """
    if output_path is None:
        output_path = input_path
    
    try:
        logger.info(f"开始清理SRT文件: {input_path}")
        # 读取SRT文件
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清理内容
        cleaned_content = clean_srt_content(content)
        
        # 写回文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        logger.info(f"SRT文件清理完成: {input_path}")
        return True
        
    except Exception as e:
        logger.error(f"清理SRT文件失败 {input_path}: {e}")
        return False


def validate_srt_content(text):
    """
    验证SRT内容是否包含有害字符
    
    Args:
        text (str): 要验证的文本内容
        
    Returns:
        dict: 验证结果
            - is_clean: bool, 是否干净
            - issues: list, 发现的问题列表
    """
    issues = []
    
    # 检查反引号
    if '`' in text:
        backtick_count = text.count('`')
        issues.append(f"发现{backtick_count}个反引号字符")
    
    # 检查思考标签
    think_tags = re.findall(r'<think>.*?</think>', text, flags=re.DOTALL | re.IGNORECASE)
    if think_tags:
        issues.append(f"发现{len(think_tags)}个思考标签")
    
    result = {
        'is_clean': len(issues) == 0,
        'issues': issues
    }
    
    if issues:
        logger.info(f"发现内容问题: {', '.join(issues)}")
    else:
        logger.info(f"内容验证通过，无问题发现")
    
    return result


def batch_clean_srt_files(file_paths):
    """
    批量清理多个SRT文件
    
    Args:
        file_paths (list): SRT文件路径列表
        
    Returns:
        dict: 清理结果统计
    """
    results = {
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'details': []
    }
    
    logger.info(f"开始批量清理 {len(file_paths)} 个SRT文件")
    
    for file_path in file_paths:
        try:
            if clean_srt_file(file_path):
                results['success'] += 1
                results['details'].append({'file': file_path, 'status': 'success'})
            else:
                results['failed'] += 1
                results['details'].append({'file': file_path, 'status': 'failed'})
        except Exception as e:
            results['failed'] += 1
            results['details'].append({'file': file_path, 'status': 'error', 'error': str(e)})
            logger.error(f"处理文件异常 {file_path}: {e}")
    
    logger.info(f"批量清理完成: 成功{results['success']}, 失败{results['failed']}")
    return results


# 向后兼容的函数别名
check_and_clean_srt = clean_srt_content
clean_subtitle_content = clean_srt_content

__all__ = [
    'clean_srt_content',
    'clean_srt_file', 
    'validate_srt_content',
    'batch_clean_srt_files',
    'check_and_clean_srt',
    'clean_subtitle_content'
]