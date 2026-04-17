from typing import List, Optional
from .constants.permissions import PERMISSIONS_BY_MODULE
import logging

logger = logging.getLogger(__name__)

def validate_permission(permission: str) -> bool:
    """验证权限标识符是否有效"""
    # 遍历所有模块的权限
    for module_permissions in PERMISSIONS_BY_MODULE.values():
        if permission in module_permissions:
            return True
    return False

def get_permissions_by_module(module: str) -> List[str]:
    """根据模块获取权限列表"""
    return PERMISSIONS_BY_MODULE.get(module, [])

def get_all_permissions() -> List[str]:
    """获取所有权限标识符"""
    all_permissions = []
    for module_permissions in PERMISSIONS_BY_MODULE.values():
        all_permissions.extend(module_permissions)
    return list(set(all_permissions))

def check_permission_in_list(permission: str, permission_list: List[str]) -> bool:
    """检查权限是否在权限列表中"""
    return permission in permission_list

def get_permission_module(permission: str) -> Optional[str]:
    """获取权限所属的模块"""
    for module, permissions in PERMISSIONS_BY_MODULE.items():
        if permission in permissions:
            return module
    return None

def get_permission_info(permission: str) -> dict:
    """获取权限信息"""
    module = get_permission_module(permission)
    return {
        "permission": permission,
        "module": module,
        "valid": validate_permission(permission)
    }

def filter_valid_permissions(permissions: List[str]) -> List[str]:
    """过滤有效的权限标识符"""
    return [perm for perm in permissions if validate_permission(perm)]
