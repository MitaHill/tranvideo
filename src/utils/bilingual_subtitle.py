"""
双语字幕生成器
负责从原文和译文字幕生成多种格式的字幕文件
"""

import re
import os
from typing import List, Dict, Any, Tuple
from .logger import get_cached_logger

logger = get_cached_logger("双语字幕生成器")


class BilingualSubtitleGenerator:
    """双语字幕生成器"""
    
    def __init__(self):
        pass
    
    def parse_srt_file(self, srt_path: str) -> List[Dict[str, Any]]:
        """
        解析SRT文件
        
        Args:
            srt_path: SRT文件路径
            
        Returns:
            字幕条目列表
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割字幕块
            blocks = re.split(r'\n\s*\n', content.strip())
            subtitles = []
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                # 解析序号
                try:
                    index = int(lines[0])
                except ValueError:
                    continue
                
                # 解析时间码
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if not time_match:
                    continue
                
                start_time = time_match.group(1)
                end_time = time_match.group(2)
                
                # 解析文本（可能多行）
                text = '\n'.join(lines[2:]).strip()
                
                subtitles.append({
                    'index': index,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text
                })
            
            return subtitles
            
        except Exception as e:
            logger.error(f"解析SRT文件失败 {srt_path}: {e}")
            return []
    
    def generate_chinese_only_subtitle(self, translated_srt_path: str, output_path: str) -> bool:
        """
        生成纯中文字幕
        
        Args:
            translated_srt_path: 翻译后的SRT文件路径
            output_path: 输出文件路径
            
        Returns:
            生成是否成功
        """
        try:
            subtitles = self.parse_srt_file(translated_srt_path)
            if not subtitles:
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for subtitle in subtitles:
                    f.write(f"{subtitle['index']}\n")
                    f.write(f"{subtitle['start_time']} --> {subtitle['end_time']}\n")
                    f.write(f"{subtitle['text']}\n\n")
            
            logger.info(f"纯中文字幕生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成纯中文字幕失败: {e}")
            return False
    
    def generate_original_only_subtitle(self, raw_srt_path: str, output_path: str) -> bool:
        """
        生成纯原文字幕
        
        Args:
            raw_srt_path: 原文SRT文件路径
            output_path: 输出文件路径
            
        Returns:
            生成是否成功
        """
        try:
            subtitles = self.parse_srt_file(raw_srt_path)
            if not subtitles:
                return False
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for subtitle in subtitles:
                    f.write(f"{subtitle['index']}\n")
                    f.write(f"{subtitle['start_time']} --> {subtitle['end_time']}\n")
                    f.write(f"{subtitle['text']}\n\n")
            
            logger.info(f"纯原文字幕生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成纯原文字幕失败: {e}")
            return False
    
    def generate_bilingual_subtitle(self, raw_srt_path: str, translated_srt_path: str, output_path: str) -> bool:
        """
        生成双语字幕（上中文，下原文）
        
        Args:
            raw_srt_path: 原文SRT文件路径
            translated_srt_path: 翻译后的SRT文件路径
            output_path: 输出文件路径
            
        Returns:
            生成是否成功
        """
        try:
            raw_subtitles = self.parse_srt_file(raw_srt_path)
            translated_subtitles = self.parse_srt_file(translated_srt_path)
            
            if not raw_subtitles or not translated_subtitles:
                logger.error("原文或译文字幕为空")
                return False
            
            if len(raw_subtitles) != len(translated_subtitles):
                logger.warning(f"原文和译文字幕数量不匹配: {len(raw_subtitles)} vs {len(translated_subtitles)}")
            
            # 以较短的为准
            min_length = min(len(raw_subtitles), len(translated_subtitles))
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i in range(min_length):
                    raw_sub = raw_subtitles[i]
                    translated_sub = translated_subtitles[i]
                    
                    # 使用翻译字幕的时间码（通常更准确）
                    f.write(f"{translated_sub['index']}\n")
                    f.write(f"{translated_sub['start_time']} --> {translated_sub['end_time']}\n")
                    
                    # 双语文本：上中文，下原文
                    bilingual_text = f"{translated_sub['text']}\n{raw_sub['text']}"
                    f.write(f"{bilingual_text}\n\n")
            
            logger.info(f"双语字幕生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成双语字幕失败: {e}")
            return False
    
    def generate_all_subtitle_types(self, task_id: str, raw_srt_path: str, translated_srt_path: str, 
                                   cache_temp_dir: str) -> Dict[str, str]:
        """
        生成所有类型的字幕文件（存放在以任务ID命名的temp子目录）
        
        Args:
            task_id: 任务ID
            raw_srt_path: 原文SRT文件路径
            translated_srt_path: 翻译后的SRT文件路径
            cache_temp_dir: temp根目录路径
            
        Returns:
            生成的字幕文件路径字典
        """
        subtitle_files = {}
        
        try:
            # 创建以任务ID命名的子目录
            task_temp_dir = os.path.join(cache_temp_dir, task_id)
            os.makedirs(task_temp_dir, exist_ok=True)
            
            # 1. 纯中文字幕
            chinese_path = os.path.join(task_temp_dir, "chinese.srt")
            if self.generate_chinese_only_subtitle(translated_srt_path, chinese_path):
                subtitle_files['chinese'] = chinese_path
            
            # 2. 纯原文字幕  
            original_path = os.path.join(task_temp_dir, "original.srt")
            if self.generate_original_only_subtitle(raw_srt_path, original_path):
                subtitle_files['original'] = original_path
            
            # 3. 双语字幕
            bilingual_path = os.path.join(task_temp_dir, "bilingual.srt")
            if self.generate_bilingual_subtitle(raw_srt_path, translated_srt_path, bilingual_path):
                subtitle_files['bilingual'] = bilingual_path
            
            logger.info(f"为任务 {task_id} 生成了 {len(subtitle_files)} 种字幕类型到temp子目录: {task_temp_dir}")
            return subtitle_files
            
        except Exception as e:
            logger.error(f"生成字幕文件失败: {e}")
            return subtitle_files


# 全局实例
bilingual_subtitle_generator = BilingualSubtitleGenerator()