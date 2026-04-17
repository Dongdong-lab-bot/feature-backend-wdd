"""巡检模块业务异常定义"""
from __future__ import annotations


class InspectionException(Exception):
    """巡检模块基础异常类"""
    code: int = 50000
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidStateTransitionError(InspectionException):
    """
    状态流转异常
    
    当尝试执行非法的状态流转时抛出此异常。
    
    HTTP Status: 400
    业务 Code: 40009
    错误信息: "当前状态不允许执行此操作"
    """
    code = 40009
    
    def __init__(
        self,
        current_state: str,
        target_state: str,
        message: str = "当前状态不允许执行此操作"
    ) -> None:
        self.current_state = current_state
        self.target_state = target_state
        self.message = message
        super().__init__(message)
    
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "msg": self.message,
            "data": {
                "current_state": self.current_state,
                "target_state": self.target_state
            }
        }


__all__ = ["InspectionException", "InvalidStateTransitionError"]
