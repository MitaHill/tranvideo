from src.utils.tq import check_invitation_code as tq_check, deduct_minutes as tq_deduct, validate_invitation
import subprocess
import sys

def check_code(invite_code):
    """检查邀请码，返回(invite_code, available_minutes)"""
    return tq_check(invite_code)

def deduct_time(invite_code, duration):
    """扣除邀请码时长"""
    try:
        tq_deduct(invite_code, duration)
        return True
    except Exception as e:
        print(f"警告: 扣除时长失败 - {e}")
        return False

def validate(invite_code):
    """验证邀请码是否有效"""
    return validate_invitation(invite_code)