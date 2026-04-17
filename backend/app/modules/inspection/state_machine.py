"""巡检任务状态机校验模块"""
from typing import Dict, Optional, Set, Union

from app.core.enums import InspectionTaskStatus
from app.modules.inspection.exceptions import InvalidStateTransitionError


TRANSITIONS: Dict[InspectionTaskStatus, Set[InspectionTaskStatus]] = {
    InspectionTaskStatus.PENDING: {
        InspectionTaskStatus.SUBMITTED,
    },
    InspectionTaskStatus.SUBMITTED: {
        InspectionTaskStatus.COMPLETED,
        InspectionTaskStatus.REJECTED,
    },
    InspectionTaskStatus.REJECTED: {
        InspectionTaskStatus.RECTIFIED,
    },
    InspectionTaskStatus.RECTIFIED: {
        InspectionTaskStatus.COMPLETED,
        InspectionTaskStatus.REJECTED,
    },
    InspectionTaskStatus.COMPLETED: set(),
}


def _normalize_state(
    state: Union[InspectionTaskStatus, str]
) -> Optional[InspectionTaskStatus]:
    if isinstance(state, InspectionTaskStatus):
        return state
    try:
        return InspectionTaskStatus(state)
    except ValueError:
        return None


def validate_state_transition(
    current_state: Union[InspectionTaskStatus, str],
    target_state: Union[InspectionTaskStatus, str]
) -> bool:
    """
    校验状态流转是否合法
    
    Args:
        current_state: 当前状态
        target_state: 目标状态
        
    Returns:
        True 表示流转合法
        
    Raises:
        InvalidStateTransitionError: 当流转非法时抛出
    """
    normalized_current = _normalize_state(current_state)
    normalized_target = _normalize_state(target_state)

    if normalized_current is None or normalized_target is None:
        raise InvalidStateTransitionError(
            current_state=str(current_state),
            target_state=str(target_state),
        )

    allowed_states = TRANSITIONS.get(normalized_current, set())
    
    if normalized_target not in allowed_states:
        raise InvalidStateTransitionError(
            current_state=normalized_current.value,
            target_state=normalized_target.value
        )
    
    return True


def can_transition(
    current_state: Union[InspectionTaskStatus, str],
    target_state: Union[InspectionTaskStatus, str]
) -> bool:
    """
    判断状态流转是否允许（不抛出异常）
    
    Args:
        current_state: 当前状态
        target_state: 目标状态
        
    Returns:
        True 表示允许流转，False 表示不允许
    """
    normalized_current = _normalize_state(current_state)
    normalized_target = _normalize_state(target_state)
    if normalized_current is None or normalized_target is None:
        return False
    allowed_states = TRANSITIONS.get(normalized_current, set())
    return normalized_target in allowed_states


def get_allowed_transitions(
    current_state: Union[InspectionTaskStatus, str]
) -> Set[InspectionTaskStatus]:
    """
    获取当前状态下所有允许的目标状态
    
    Args:
        current_state: 当前状态
        
    Returns:
        允许的目标状态集合
    """
    normalized_current = _normalize_state(current_state)
    if normalized_current is None:
        return set()
    return TRANSITIONS.get(normalized_current, set())


__all__ = [
    "validate_state_transition",
    "can_transition",
    "get_allowed_transitions",
    "TRANSITIONS"
]
