#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
from datetime import datetime


def load_database():
    """加载数据库"""
    db_path = "db/main.json"

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件 {db_path} 不存在")

    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"数据库文件格式错误 - {e}")
    except Exception as e:
        raise IOError(f"无法读取数据库文件 - {e}")


def save_database(db_data):
    """保存数据库"""
    db_path = "db/main.json"
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        raise IOError(f"无法保存数据库文件 - {e}")


def check_invitation_code(invite_code):
    """查询邀请码的可用时长（模块化接口）"""
    try:
        db_data = load_database()

        # 查询邀请码
        if invite_code not in db_data:
            return invite_code, 0

        code_info = db_data[invite_code]
        available_minutes = round(code_info.get('available_minutes', 0))
        expire_time_str = code_info.get('expire_time', '')

        # 检查是否过期
        if expire_time_str:
            try:
                expire_time = datetime.fromisoformat(expire_time_str.replace('Z', '+00:00'))
                current_time = datetime.now(expire_time.tzinfo) if expire_time.tzinfo else datetime.now()

                if current_time > expire_time:
                    return invite_code, 0
            except ValueError:
                return invite_code, 0

        return invite_code, available_minutes

    except Exception:
        return invite_code, 0


def deduct_minutes(invite_code, deduct_amount):
    """扣除邀请码的可用时长（模块化接口）"""
    try:
        db_data = load_database()

        if invite_code not in db_data:
            raise ValueError(f"邀请码 {invite_code} 不存在")

        code_info = db_data[invite_code]
        current_minutes = code_info.get('available_minutes', 0)

        # 计算扣除后的时长（四舍五入）
        new_minutes = round(max(0, current_minutes - deduct_amount))
        code_info['available_minutes'] = new_minutes

        # 保存到数据库
        save_database(db_data)
        return invite_code, new_minutes

    except Exception as e:
        raise RuntimeError(f"扣除时长时出错 - {e}")


def validate_invitation(invite_code):
    """验证邀请码是否有效"""
    code, minutes = check_invitation_code(invite_code)
    return {
        "code": code,
        "minutes": minutes,
        "valid": minutes > 0
    }


def main():
    """命令行入口"""
    # 检查参数数量
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("用法:", file=sys.stderr)
        print("  查询: python tq.py <邀请码>", file=sys.stderr)
        print("  扣除: python tq.py <邀请码> --deduct <分钟数>", file=sys.stderr)
        print("示例:", file=sys.stderr)
        print("  python tq.py l234R6L89o", file=sys.stderr)
        print("  python tq.py l234R6L89o --deduct 15.5", file=sys.stderr)
        sys.exit(1)

    invite_code = sys.argv[1].strip()

    # 验证邀请码格式
    if not invite_code or len(invite_code) > 10 or not invite_code.isalnum():
        print("错误: 邀请码格式无效（应为10位以内的数字和字母）", file=sys.stderr)
        sys.exit(1)

    try:
        # 判断是查询还是扣除
        if len(sys.argv) == 2:
            # 查询模式
            code, minutes = check_invitation_code(invite_code)
            print(f"{code} {minutes}")
        elif len(sys.argv) == 4 and sys.argv[2] == '--deduct':
            # 扣除模式
            try:
                deduct_amount = float(sys.argv[3])
                if deduct_amount < 0:
                    print("错误: 扣除时长不能为负数", file=sys.stderr)
                    sys.exit(1)
                code, new_minutes = deduct_minutes(invite_code, deduct_amount)
                print(f"{code} {new_minutes}")
            except ValueError:
                print("错误: 扣除时长必须为数字", file=sys.stderr)
                sys.exit(1)
        else:
            print("错误: 参数格式错误", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()