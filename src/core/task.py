import uuid
import os
import time
from src.core.invite import check_code, validate, deduct_time
from src.core.video import get_duration, process_srt, merge_video, merge_video_with_multilingual_subtitles, clean_temp
from src.utils.filer import schedule_del, handle_down, clear_all, save_temp, move_final
from src.core.batch import check_done, create_batch, get_status as get_batch_status
from src.utils.taskq import add_task, get_status as get_queue_status, create_task_data
from src.services.use_whisper import check_whisper_service, call_whisper_service, format_srt
from src.core.coordinate import task_coordinator
from src.api.prog_bar.progress_tracker import progress_tracker
import subprocess
import threading
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("任务处理")


def validate_video_file(file):
    """验证视频文件 - 使用新的安全模块"""
    from src.api.security_modules.file_type_verification import verify_uploaded_file
    return verify_uploaded_file(file)


def call_whisper_service_with_progress(task_id, video_path):
    """带进度监控的Whisper服务调用"""
    try:
        logger.info(f"开始带进度监控的Whisper调用: {task_id[:8]}...")
        
        # 定义进度回调函数，捕获Whisper的真实tqdm输出
        def whisper_progress_callback(progress_line):
            logger.debug(f"Whisper进度输出: {progress_line}")
            # 解析真实的tqdm输出
            progress_tracker._parse_whisper_progress(task_id, progress_line)
        
        # 执行实际的Whisper调用，传入进度回调和task_id
        result = call_whisper_service(video_path, whisper_progress_callback, task_id)
        
        # 设置Whisper进度为100%（确保完成）
        progress_tracker._parse_whisper_progress(task_id, "100%|██████████| 100/100 [02:36<00:00, 462.73frames/s]")
        
        return result
        
    except Exception as e:
        logger.error(f"Whisper进度监控调用失败: {e}")
        return {'success': False, 'error': str(e)}


def process_srt_with_progress(task_id, srt_file_path):
    """带进度监控的SRT翻译处理"""
    try:
        logger.info(f"开始带进度监控的SRT翻译: {task_id[:8]}...")
        
        # 翻译使用tqdm，但是输出到控制台，需要重定向捕获
        # 改为修改翻译函数以支持回调进度更新
        result = process_srt_with_callback(srt_file_path, lambda current, total: 
            progress_tracker._parse_translation_progress(task_id, f"翻译进度: {int(current/total*100)}%|█▏        | {current}/{total} [00:03<13:34, 3.84s/it]")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"翻译进度监控处理失败: {e}")
        return False


def process_srt_with_callback(srt_file_path, progress_callback):
    """带进度回调的SRT翻译处理"""
    try:
        from src.services.tran import translate_srt_with_callback
        translate_srt_with_callback(srt_file_path, progress_callback)
        return True
    except Exception as e:
        logger.error(f"SRT翻译失败: {e}")
        return False


def process_video_background(task_id, video_path, mode, app_state):
    """后台处理视频"""
    try:
        # 导入显存管理器
        from src.utils.vram_manager import get_vram_manager
        from src.services.whisper_direct import get_whisper_manager
        from src.services.tran import load_config

        # 初始化显存管理器
        vram_manager = get_vram_manager()

        # 设置Whisper管理器引用
        whisper_manager = get_whisper_manager()
        vram_manager.set_whisper_manager(whisper_manager)

        # 设置Ollama配置
        try:
            config = load_config()
            translator_type = config.get('translator_type', 'ollama')
            ollama_url = config.get('ollama_api', '')
            ollama_model = config.get('ollama_model', '')

            if translator_type == 'ollama' and ollama_url and ollama_model:
                vram_manager.set_ollama_config(ollama_url, ollama_model, translator_type)
            elif translator_type == 'openai':
                openai_url = config.get('openai_base_url', '')
                vram_manager.set_ollama_config(openai_url, '', translator_type)
        except Exception as e:
            logger.warning(f"无法加载翻译器配置: {e}")

        # 获取当前任务状态，不要立即覆盖，让后续逻辑根据状态正确处理
        current_task = task_coordinator.get_task(task_id)
        current_status = current_task.get('status') if current_task else '队列中'

        print(f"[INFO] 🎯 开始处理任务 {task_id[:8]}...，数据库状态: {current_status}")
        
        # 启动进度跟踪
        progress_tracker.start_whisper_tracking(task_id)
        
        # 只有状态为"队列中"的新任务才设置为processing
        if current_status == "队列中":
            print(f"[INFO] ⚙️  初始化新任务 {task_id[:8]}...")
            task_coordinator.update_task_status(task_id, "processing", "初始化...", "processing")
        else:
            print(f"[INFO] 🔄 恢复中断任务 {task_id[:8]}...，从状态 '{current_status}' 继续处理")

        if not os.path.exists(video_path):
            raise Exception(f"文件不存在: {video_path}")

        if not check_whisper_service():
            raise Exception("Whisper 服务不可用")

        # 步骤1: 提取原文字幕
        cache_dirs = app_state.cache_dirs
        # raw.srt文件放在temp/{task_id}目录中
        task_temp_dir = f"{cache_dirs['temp']}/{task_id}"
        os.makedirs(task_temp_dir, exist_ok=True)
        raw_srt = f"{task_temp_dir}/{task_id}_raw.srt"
        translated_srt = f"{cache_dirs['outputs']}/{task_id}_translated.srt"
        
        # 重新获取最新状态（可能已从队列中更新为processing）
        current_task = task_coordinator.get_task(task_id)
        current_status = current_task.get('status') if current_task else '队列中'
        
        # 完全基于数据库状态决定是否需要提取原文字幕
        need_extract = False
        
        if current_status in ['队列中', 'processing']:
            # 新任务或从头开始的任务
            need_extract = True
            print(f"[INFO] 📝 步骤1: 任务 {task_id[:8]}... 状态为 {current_status}，需要提取原文字幕")
        elif current_status == '提取原文字幕':
            # 在提取阶段中断的任务，删除不完整文件重新开始
            print(f"[INFO] 🔄 步骤1: 任务 {task_id[:8]}... 状态为'提取原文字幕'，继续提取工作")
            need_extract = True
        elif current_status in ['翻译原文字幕', '已完成']:
            # 已完成提取阶段的任务
            print(f"[INFO] ⏩ 步骤1: 任务 {task_id[:8]}... 状态为 {current_status}，跳过提取步骤（提取工作已完成）")
            need_extract = False
        
        if need_extract:
            # 删除可能存在的不完整raw文件
            if os.path.exists(raw_srt):
                print(f"[INFO] 删除不完整的原文字幕文件: {raw_srt}")
                os.remove(raw_srt)

            # 准备转录阶段: 确保Whisper在GPU，卸载Ollama
            print(f"[INFO] 📊 准备转录阶段 - 优化显存分配")
            vram_manager.prepare_for_transcription()

            # 先更新状态，再执行提取
            task_coordinator.update_task_status(task_id, "提取原文字幕", "提取原文字幕中...", "extracting")

            # 调用Whisper服务时，启动控制台输出监控，传入task_id
            whisper_result = call_whisper_service_with_progress(task_id, video_path)
            if not whisper_result.get('success'):
                raise Exception(f"转录失败: {whisper_result.get('error', '未知错误')}")

            # 保存原文字幕文件到temp/{task_id}/目录
            with open(raw_srt, 'w', encoding='utf-8') as f:
                f.write(format_srt(whisper_result['segments']))
            print(f"[INFO] 任务 {task_id} 原文字幕已保存到: {raw_srt}")

            # Whisper转录完成，将模型移至CPU释放显存
            print(f"[INFO] 📊 转录完成 - 将Whisper移至CPU释放显存")
            vram_manager.move_whisper_to_cpu()

        else:
            print(f"[INFO] ⏩ 步骤1: 任务 {task_id[:8]}... 跳过提取步骤（提取工作已完成），直接进入翻译阶段")

        # 步骤2: 翻译字幕
        # 重新获取最新任务状态并智能地处理翻译阶段
        current_task = task_coordinator.get_task(task_id)
        current_status = current_task.get('status') if current_task else '队列中'
        
        # 完全基于数据库状态决定是否需要翻译
        need_translate = False
        
        if current_status == '提取原文字幕':
            # 刚完成提取，需要翻译
            print(f"[INFO] 🈶 步骤2: 任务 {task_id[:8]}... 状态为'提取原文字幕'，开始翻译工作")
            need_translate = True
        elif current_status == '翻译原文字幕':
            # 在翻译阶段中断的任务，删除不完整文件重新开始
            print(f"[INFO] 🔄 步骤2: 任务 {task_id[:8]}... 状态为'翻译原文字幕'，继续翻译工作")
            need_translate = True
        elif current_status == '已完成':
            # 已完成翻译阶段的任务
            print(f"[INFO] ⏩ 步骤2: 任务 {task_id[:8]}... 状态为'已完成'，跳过翻译步骤（翻译工作已完成）")
            need_translate = False
        
        if need_translate:
            # 检查raw文件是否存在
            if not os.path.exists(raw_srt) or os.path.getsize(raw_srt) == 0:
                raise Exception(f"原文字幕文件不存在或为空: {raw_srt}")
            
            # 删除可能存在的不完整翻译文件
            if os.path.exists(translated_srt):
                print(f"[INFO] 删除不完整的翻译字幕文件: {translated_srt}")
                os.remove(translated_srt)

            # 准备翻译阶段: Whisper应该已经在CPU，这里为Ollama预留显存
            print(f"[INFO] 📊 准备翻译阶段 - 为Ollama模型预留显存")
            vram_manager.prepare_for_translation()

            # 先更新状态，再执行翻译
            task_coordinator.update_task_status(task_id, "翻译原文字幕", "翻译字幕中...", "translating")

            # 启动翻译进度跟踪
            progress_tracker.start_translation_tracking(task_id)

            # 复制原文字幕文件作为翻译基础
            import shutil
            shutil.copy2(raw_srt, translated_srt)

            # 调用翻译服务时，启动控制台输出监控
            if not process_srt_with_progress(task_id, translated_srt):
                raise Exception("字幕翻译失败")

            print(f"[INFO] 任务 {task_id} 翻译字幕已保存到: {translated_srt}")

            # 翻译完成，卸载Ollama模型并将Whisper重新移至CPU(确保)
            print(f"[INFO] 📊 翻译完成 - 卸载Ollama模型")
            vram_manager.unload_ollama_model()
            vram_manager.move_whisper_to_cpu()  # 确保Whisper在CPU

            # 翻译完成后，立即生成三轨道字幕到 cache/temp/{task_id}/ 目录
            from src.utils.bilingual_subtitle import bilingual_subtitle_generator
            subtitle_files = bilingual_subtitle_generator.generate_all_subtitle_types(
                task_id, raw_srt, translated_srt, cache_dirs['temp']
            )
            
            if not subtitle_files:
                print(f"[WARNING] 任务 {task_id} 生成三轨道字幕文件失败")
            else:
                print(f"[INFO] 任务 {task_id} 已生成三轨道字幕到: cache/temp/{task_id}/")
        else:
            print(f"[INFO] ⏩ 步骤2: 任务 {task_id[:8]}... 跳过翻译步骤（翻译工作已完成），直接进入最终阶段")
            
            # 即使跳过翻译，也要确保三轨道字幕文件存在
            bilingual_files = ['chinese.srt', 'original.srt', 'bilingual.srt']
            all_exist = all(os.path.exists(f"{task_temp_dir}/{f}") for f in bilingual_files)
            
            if not all_exist:
                print(f"[INFO] 三轨道字幕文件不完整，重新生成...")
                from src.utils.bilingual_subtitle import bilingual_subtitle_generator
                subtitle_files = bilingual_subtitle_generator.generate_all_subtitle_types(
                    task_id, raw_srt, translated_srt, cache_dirs['temp']
                )
                
                if subtitle_files:
                    print(f"[INFO] 任务 {task_id} 已重新生成三轨道字幕到: cache/temp/{task_id}/")

        # 步骤3: 生成最终文件
        # 重新获取最新任务状态和任务信息
        current_task = task_coordinator.get_task(task_id)
        current_status = current_task.get('status') if current_task else '队列中'
        batch_id = current_task.get('batch_id') if current_task else None
        
        if mode == "video":
            # 视频模式：生成带字幕的视频
            if current_status == "翻译原文字幕":
                # 检查翻译字幕文件是否存在
                if not os.path.exists(translated_srt) or os.path.getsize(translated_srt) == 0:
                    raise Exception(f"翻译字幕文件不存在或为空: {translated_srt}")
                
                # 先更新状态，再执行视频合成
                task_coordinator.update_task_status(task_id, "生成视频", "合成视频中...", "generating")
                
                # 视频模式：输出文件名为 {video_name}_{task_id}_video.mp4
                # 获取原文件名（不含扩展名）
                db_task = task_coordinator.get_task(task_id)
                video_name = db_task.get('video_name', 'video.mp4') if db_task else 'video.mp4'
                video_name_without_ext = os.path.splitext(video_name)[0]
                
                output_video = f"{cache_dirs['outputs']}/{video_name_without_ext}_{task_id}_video.mp4"
                
                # 执行多语言字幕视频合成
                if not merge_video_with_multilingual_subtitles(video_path, raw_srt, translated_srt, output_video):
                    raise Exception("多语言字幕视频合成失败")
                
                print(f"[INFO] 任务 {task_id} 视频已生成到: {output_video}")
            else:
                print(f"[INFO] 任务 {task_id} 状态为 {current_status}，无需视频生成")
            
            result_file = f"{video_name_without_ext}_{task_id}_video.mp4"
        else:
            # SRT模式：生成三种字幕的压缩包
            if current_status == "翻译原文字幕":
                # 检查翻译字幕文件是否存在
                if not os.path.exists(translated_srt) or os.path.getsize(translated_srt) == 0:
                    raise Exception(f"翻译字幕文件不存在或为空: {translated_srt}")
                
                # 更新状态
                task_coordinator.update_task_status(task_id, "生成字幕文件", "打包字幕文件中...", "generating")
                
                # 从 temp/{task_id}/目录获取三种字幕文件
                if not os.path.exists(task_temp_dir):
                    raise Exception(f"任务临时目录不存在: {task_temp_dir}")
                
                # 创建单文件任务的SRT压缩包
                # 获取原文件名（不含扩展名）
                db_task = task_coordinator.get_task(task_id)
                video_name = db_task.get('video_name', 'video.mp4') if db_task else 'video.mp4'
                video_name_without_ext = os.path.splitext(video_name)[0]
                
                zip_path = f"{cache_dirs['outputs']}/{video_name_without_ext}_{task_id}_srt.zip"
                _create_single_srt_zip(task_temp_dir, zip_path)
                
                print(f"[INFO] 任务 {task_id} 字幕压缩包已生成到: {zip_path}")
            else:
                print(f"[INFO] 任务 {task_id} 状态为 {current_status}，无需生成字幕文件")
            
            result_file = f"{video_name_without_ext}_{task_id}_srt.zip"

        clean_temp(video_path)

        # 更新任务状态为完成
        task_coordinator.update_task_status(task_id, "已完成", "处理完成", "completed")
        
        # 停止进度跟踪
        progress_tracker.stop_tracking(task_id)

        # 扣除时长（从数据库获取任务信息）
        db_task = task_coordinator.get_task(task_id)
        if db_task and db_task.get("invite_code") and db_task.get("video_duration"):
            duration_minutes = db_task["video_duration"] / 60  # 转换为分钟
            deduct_time(db_task["invite_code"], duration_minutes)

    except Exception as e:
        # 停止进度跟踪
        progress_tracker.stop_tracking(task_id)
        
        # 仅更新数据库失败状态（不再依赖内存）
        task_coordinator.update_task_status(task_id, "failed", f"处理失败: {str(e)}", "failed", error=str(e))
        
        if video_path and os.path.exists(video_path):
            clean_temp(video_path)


def create_single_task(invite_code, file, mode, app_state, cache_dirs):
    """创建单个任务"""
    validation = validate(invite_code)
    if not validation["valid"]:
        return {"error": "邀请码无效或时长不足", "code": 403}

    is_valid, message = validate_video_file(file)
    if not is_valid:
        return {"error": message, "code": 400}

    try:
        temp_path = save_temp(file, cache_dirs)
        duration = get_duration(temp_path)

        if duration > validation["minutes"]:
            clean_temp(temp_path)
            return {
                "error": f"视频时长 {duration:.1f} 分钟超过可用时长 {validation['minutes']} 分钟",
                "code": 413
            }

        task_id = str(uuid.uuid4())
        video_path = move_final(temp_path, cache_dirs, task_id, file.filename)
        task_data = create_task_data(mode, video_path, invite_code, duration, original_name=file.filename)
        final_task_id = add_task(task_data, app_state)

        # 计算队列位置
        all_tasks = task_coordinator.get_all_tasks()
        queued_tasks = [t for t in all_tasks['single_tasks'].values() if t['status'] == "队列中"]
        queue_position = f"队列: {len(queued_tasks)}"
        
        return {
            "task_id": final_task_id,
            "status": "queued",
            "queue_position": queue_position,
            "duration": duration
        }

    except Exception as e:
        return {"error": f"处理文件时出错: {str(e)}", "code": 500}


def create_batch_tasks(invite_code, files, mode, app_state, cache_dirs):
    """创建批量任务"""
    validation = validate(invite_code)
    if not validation["valid"]:
        return {"error": "邀请码无效或时长不足", "code": 403}

    if not files:
        return {"error": "未选择文件", "code": 400}

    # 验证文件
    for file in files:
        if file.filename:
            is_valid, message = validate_video_file(file)
            if not is_valid:
                return {"error": message, "code": 400}

    temp_files = []
    total_duration = 0

    try:
        # 保存文件并计算时长
        for file in files:
            if file.filename:
                temp_path = save_temp(file, cache_dirs)
                temp_files.append((temp_path, file))
                total_duration += get_duration(temp_path)

        if total_duration > validation["minutes"]:
            for temp_path, _ in temp_files:
                clean_temp(temp_path)
            return {
                "error": f"视频总时长 {total_duration:.1f} 分钟超过可用时长 {validation['minutes']} 分钟",
                "code": 413
            }

        # 创建批量任务
        batch_id = str(uuid.uuid4())
        task_ids = []

        for temp_path, file in temp_files:
            task_id = str(uuid.uuid4())
            video_path = move_final(temp_path, cache_dirs, task_id, file.filename)
            task_data = create_task_data(mode, video_path, invite_code, 0,
                                         batch_id=batch_id, original_name=file.filename)
            task_ids.append(add_task(task_data, app_state))

        create_batch(batch_id, task_ids, mode, invite_code, app_state)

        return {
            "batch_id": batch_id,
            "file_count": len(task_ids),
            "status": "processing",
            "total_duration": total_duration
        }

    except Exception as e:
        for temp_path, _ in temp_files:
            clean_temp(temp_path)
        return {"error": f"处理文件时出错: {str(e)}", "code": 500}


def clear_all_cache(app_state, cache_dirs):
    """清理所有缓存文件"""
    with app_state.processing_lock:
        if app_state.task_queue or app_state.current_processing:
            return {"error": "系统忙碌，请在队列为空时重试", "code": 400}

    return {"message": "所有缓存文件已成功删除"} if clear_all(
        app_state.file_deletion_timers, app_state.file_download_info, cache_dirs
    ) else {"error": "删除缓存文件失败", "code": 500}


def _create_single_srt_zip(task_temp_dir, zip_path):
    """创建单文件任务的SRT压缩包"""
    import zipfile
    
    subtitle_files = [
        ("chinese.srt", "中文字幕"),
        ("original.srt", "原文字幕"),
        ("bilingual.srt", "双语字幕")
    ]
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for filename, description in subtitle_files:
            file_path = os.path.join(task_temp_dir, filename)
            if os.path.exists(file_path):
                zf.write(file_path, filename)
                print(f"[INFO] 添加{description}到压缩包: {filename}")
            else:
                print(f"[WARNING] 字幕文件不存在: {file_path}")


class TaskManager:
    """任务管理器"""

    def __init__(self, app_state, cache_dirs):
        self.app_state = app_state
        self.cache_dirs = cache_dirs

    def create_task(self, invite_code, file, mode):
        return create_single_task(invite_code, file, mode, self.app_state, self.cache_dirs)

    def create_batch(self, invite_code, files, mode):
        return create_batch_tasks(invite_code, files, mode, self.app_state, self.cache_dirs)

    def get_task_status(self, task_id):
        # 完全基于数据库查询，移除内存依赖
        db_task = task_coordinator.get_task(task_id)
        if db_task:
            # 映射数据库状态到前端期望的状态
            frontend_status = self._map_db_status_to_frontend(db_task["status"])
            
            # 计算队列位置
            queue_position = self._calculate_queue_position(task_id, db_task["status"])
            
            # 转换为前端期望格式
            return {
                "status": frontend_status,
                "progress": db_task["progress"],
                "queue_position": queue_position,
                "mode": db_task.get("mode", "srt"),
                "video_path": db_task.get("video_path", ""),
                "invite_code": db_task.get("invite_code", ""),
                "duration": db_task.get("video_duration", 0) / 60,  # 转换回分钟
                "filename": self._get_result_filename(task_id, db_task) if db_task["status"] in ["已完成", "被下载过进入清理倒计时"] else "",
                "error": db_task.get("error")
            }
        # 任务不存在
        return None
    
    def _calculate_queue_position(self, task_id, status):
        """基于数据库计算队列位置"""
        if status == "已完成":
            return "已完成"
        elif status == "failed":
            return "处理失败"
        elif status in ["提取原文字幕", "翻译原文字幕", "processing"]:
            if status == "提取原文字幕":
                return "提取字幕中"
            elif status == "翻译原文字幕":
                return "翻译字幕中"
            else:
                return "处理中"
        elif status == "队列中":
            # 计算在队列中的位置
            all_tasks = task_coordinator.get_all_tasks()
            queued_tasks = []
            
            for tid, task in all_tasks['single_tasks'].items():
                if task['status'] == "队列中":
                    queued_tasks.append((tid, task['created_at']))
            
            # 按创建时间排序
            queued_tasks.sort(key=lambda x: x[1])
            
            # 找到当前任务的位置
            for i, (tid, _) in enumerate(queued_tasks):
                if tid == task_id:
                    return f"排队位置: {i + 1}"
            
            return "排队位置: 1"
        else:
            return "未知状态"
    
    def _map_db_status_to_frontend(self, db_status):
        """映射数据库状态到前端状态，返回中文状态"""
        status_map = {
            "队列中": "排队中",
            "提取原文字幕": "提取字幕",
            "翻译原文字幕": "翻译字幕", 
            "已完成": "已完成",
            "过期文件已经被清理": "已过期",
            "被下载过进入清理倒计时": "清理倒计时",
            "failed": "处理失败",
            "processing": "处理中"
        }
        return status_map.get(db_status, db_status)
    
    def _get_result_filename(self, task_id, db_task):
        """根据任务模式生成结果文件名"""
        mode = db_task.get("mode", "srt")
        batch_id = db_task.get('batch_id')
        
        if batch_id:
            # 批量任务：返回批量压缩包文件名
            if mode == "video":
                return f"{batch_id}_video.zip"
            else:
                return f"{batch_id}_batch_srt.zip"
        else:
            # 单文件任务 - 使用新的命名规范
            video_name = db_task.get('video_name', 'video.mp4')
            video_name_without_ext = os.path.splitext(video_name)[0]
            
            if mode == "video":
                return f"{video_name_without_ext}_{task_id}_video.mp4"
            else:
                return f"{video_name_without_ext}_{task_id}_srt.zip"

    def get_batch_status(self, batch_id):
        return get_batch_status(batch_id, self.app_state)

    def get_system_status(self):
        """基于数据库获取系统状态"""
        try:
            # 获取任务统计
            status_count = task_coordinator.get_task_count_by_status()
            all_tasks = task_coordinator.get_all_tasks()
            
            # 计算各种状态
            queued_count = status_count.get("队列中", 0)
            processing_count = (
                status_count.get("提取原文字幕", 0) + 
                status_count.get("翻译原文字幕", 0) + 
                status_count.get("processing", 0)
            )
            completed_count = status_count.get("已完成", 0)
            failed_count = status_count.get("failed", 0)
            
            # 确定当前处理的任务
            current_task = None
            for task_id, task in all_tasks['single_tasks'].items():
                if task['status'] in ["提取原文字幕", "翻译原文字幕", "processing"]:
                    current_task = task_id
                    break
            
            return {
                "busy": processing_count > 0,
                "queue_length": queued_count,
                "current_task": current_task,
                "total_tasks": len(all_tasks['single_tasks']),
                "processing_count": processing_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "task_statistics": status_count
            }
        except Exception as e:
            return {
                "busy": False,
                "queue_length": 0,
                "current_task": None,
                "error": str(e)
            }

    def clear_cache(self):
        return clear_all_cache(self.app_state, self.cache_dirs)


# 兼容性别名
check_invitation_code = check_code
get_video_duration = get_duration
schedule_file_deletion = schedule_del
handle_file_download = handle_down
check_batch_completion = check_done

__all__ = [
    'check_invitation_code', 'get_video_duration', 'schedule_file_deletion',
    'handle_file_download', 'check_batch_completion', 'process_video_background',
    'create_single_task', 'create_batch_tasks', 'clear_all_cache', 'TaskManager'
]