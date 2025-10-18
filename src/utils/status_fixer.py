#!/usr/bin/env python3
"""
任务状态修正工具
根据outputs目录中的文件情况修正tasks.json中的任务状态
"""

import os
import sys
import glob
from typing import List, Tuple

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.coordinate import task_coordinator


def find_output_files() -> List[Tuple[str, str, str]]:
    """
    扫描outputs目录，找到所有输出文件
    返回: [(task_id, file_type, file_path), ...]
    """
    output_files = []
    outputs_dir = "cache/outputs"
    
    if not os.path.exists(outputs_dir):
        return output_files
    
    # 查找所有输出文件
    srt_files = glob.glob(f"{outputs_dir}/*_translated.srt")
    mp4_files = glob.glob(f"{outputs_dir}/*_final.mp4")
    
    # 提取任务ID
    for srt_file in srt_files:
        basename = os.path.basename(srt_file)
        task_id = basename.replace("_translated.srt", "")
        output_files.append((task_id, "srt", srt_file))
    
    for mp4_file in mp4_files:
        basename = os.path.basename(mp4_file)
        task_id = basename.replace("_final.mp4", "")
        output_files.append((task_id, "video", mp4_file))
    
    return output_files


def fix_task_statuses(dry_run: bool = True) -> List[str]:
    """
    修正任务状态
    
    Args:
        dry_run: 如果为True，只检查不修改
    
    Returns:
        修正的任务ID列表
    """
    fixed_tasks = []
    output_files = find_output_files()
    
    print(f"扫描到 {len(output_files)} 个输出文件")
    
    # 按任务ID分组
    task_outputs = {}
    for task_id, file_type, file_path in output_files:
        if task_id not in task_outputs:
            task_outputs[task_id] = {"srt": None, "video": None}
        task_outputs[task_id][file_type] = file_path
    
    print(f"涉及 {len(task_outputs)} 个任务")
    
    for task_id, outputs in task_outputs.items():
        # 获取任务信息
        task = task_coordinator.get_task(task_id)
        if not task:
            print(f"⚠️  任务 {task_id[:8]}... 在数据库中不存在，但有输出文件")
            continue
        
        current_status = task["status"]
        task_mode = task.get("mode", "srt")
        
        # 检查输出文件是否匹配任务模式
        expected_output = outputs.get(task_mode)
        has_valid_output = expected_output and os.path.exists(expected_output)
        
        # 判断是否需要修正
        should_fix = False
        new_status = None
        new_progress = None
        
        if has_valid_output and current_status == "failed":
            # 有有效输出但状态为失败 -> 修正为已完成
            should_fix = True
            new_status = "已完成"
            new_progress = "处理完成"
            reason = f"输出文件存在但状态为失败 ({task_mode}文件: {os.path.basename(expected_output)})"
            
        elif has_valid_output and current_status in ["队列中", "processing", "提取原文字幕", "翻译原文字幕"]:
            # 有有效输出但状态为处理中 -> 修正为已完成
            should_fix = True
            new_status = "已完成"
            new_progress = "处理完成"
            reason = f"输出文件存在但状态未更新 ({task_mode}文件: {os.path.basename(expected_output)})"
        
        if should_fix:
            print(f"🔧 任务 {task_id[:8]}... 需要修正: {reason}")
            
            if not dry_run:
                success = task_coordinator.update_task_status(
                    task_id,
                    new_status,
                    new_progress,
                    "completed"
                )
                if success:
                    print(f"   ✅ 修正成功: {current_status} -> {new_status}")
                    fixed_tasks.append(task_id)
                else:
                    print(f"   ❌ 修正失败")
            else:
                print(f"   🔍 (试运行) 将修正: {current_status} -> {new_status}")
                fixed_tasks.append(task_id)
        else:
            if current_status in ["已完成", "被下载过进入清理倒计时", "过期文件已经被清理"]:
                print(f"✅ 任务 {task_id[:8]}... 状态正常: {current_status}")
            else:
                print(f"ℹ️  任务 {task_id[:8]}... 状态: {current_status} (无输出文件，可能确实未完成)")
    
    return fixed_tasks


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="任务状态修正工具")
    parser.add_argument("--fix", action="store_true", help="执行修正（默认为试运行）")
    parser.add_argument("--task-id", help="只修正指定的任务ID")
    
    args = parser.parse_args()
    
    print("=== 任务状态修正工具 ===")
    print(f"模式: {'修正模式' if args.fix else '试运行模式'}")
    print()
    
    if args.task_id:
        # 修正单个任务
        task = task_coordinator.get_task(args.task_id)
        if not task:
            print(f"❌ 任务 {args.task_id} 不存在")
            return
        
        output_files = find_output_files()
        task_outputs = {task_id: {"srt": None, "video": None} for task_id, _, _ in output_files}
        for task_id, file_type, file_path in output_files:
            if task_id == args.task_id:
                task_outputs[task_id][file_type] = file_path
        
        if args.task_id in task_outputs:
            fixed = fix_task_statuses(dry_run=not args.fix)
            if fixed:
                print(f"\n修正了 {len(fixed)} 个任务")
            else:
                print("\n没有需要修正的任务")
        else:
            print(f"❌ 任务 {args.task_id} 没有输出文件")
    else:
        # 修正所有任务
        fixed = fix_task_statuses(dry_run=not args.fix)
        
        print(f"\n{'修正' if args.fix else '检查'}完成！")
        if fixed:
            print(f"{'修正了' if args.fix else '发现'} {len(fixed)} 个任务需要修正")
            for task_id in fixed:
                print(f"  - {task_id}")
        else:
            print("没有需要修正的任务")


if __name__ == "__main__":
    main()