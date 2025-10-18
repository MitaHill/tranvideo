#!/usr/bin/env python3
import os
import sys
import glob

def get_file_size_mb(filepath):
    """获取文件大小（MB）"""
    return os.path.getsize(filepath) / (1024 * 1024)

def trim_log_file(filepath, max_size_mb=2):
    """修剪日志文件到指定大小"""
    if not os.path.exists(filepath):
        return
    
    current_size = get_file_size_mb(filepath)
    if current_size <= max_size_mb:
        return
    
    print(f"修剪日志文件: {filepath} ({current_size:.2f}MB -> {max_size_mb}MB)")
    
    # 读取文件内容
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # 逐行删除直到文件大小符合要求
    while lines:
        # 计算当前内容大小
        content = ''.join(lines)
        current_bytes = len(content.encode('utf-8'))
        current_mb = current_bytes / (1024 * 1024)
        
        if current_mb <= max_size_mb:
            break
            
        # 删除第一行
        lines.pop(0)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    new_size = get_file_size_mb(filepath)
    print(f"修剪完成: {filepath} 现在大小 {new_size:.2f}MB")

def manage_log_directory(log_dir='log', max_size_mb=2):
    """管理日志目录下所有文件"""
    if not os.path.exists(log_dir):
        print(f"日志目录不存在: {log_dir}")
        return
    
    # 获取所有日志文件
    log_files = glob.glob(os.path.join(log_dir, '*.log')) + \
                glob.glob(os.path.join(log_dir, '*.txt'))
    
    if not log_files:
        print("未找到日志文件")
        return
    
    print(f"检查 {len(log_files)} 个日志文件...")
    
    total_size_before = 0
    total_size_after = 0
    trimmed_count = 0
    
    for log_file in log_files:
        size_before = get_file_size_mb(log_file)
        total_size_before += size_before
        
        if size_before > max_size_mb:
            trim_log_file(log_file, max_size_mb)
            trimmed_count += 1
        
        size_after = get_file_size_mb(log_file)
        total_size_after += size_after
    
    print(f"处理完成: 修剪了 {trimmed_count} 个文件")
    print(f"总大小: {total_size_before:.2f}MB -> {total_size_after:.2f}MB")

def main():
    if len(sys.argv) < 2:
        print("用法: python log-ctl.py <命令> [参数]")
        print("命令:")
        print("  cleanup [目录] [最大大小MB] - 清理日志文件")
        print("示例: python log-ctl.py cleanup log 2")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "cleanup":
        log_dir = sys.argv[2] if len(sys.argv) > 2 else 'log'
        max_size = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
        
        manage_log_directory(log_dir, max_size)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()