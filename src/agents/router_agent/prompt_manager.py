"""
Prompt 管理模块
根据用户角色动态返回对应 Prompt
"""

from src.core.schemas import UserRoleEnum

from src.agents.router_agent.prompts.store_manager_prompt import (
    STORE_MANAGER_SYSTEM_PROMPT,
)

from src.agents.router_agent.prompts.area_supervisor_prompt import (
    AREA_SUPERVISOR_SYSTEM_PROMPT,
)

from src.agents.router_agent.prompts.enterprise_admin_prompt import (
    ENTERPRISE_ADMIN_SYSTEM_PROMPT,
)


def get_system_prompt(role: UserRoleEnum) -> str:
    """
    根据用户角色返回对应系统 Prompt
    """

    if role == UserRoleEnum.STORE_MANAGER:
        return STORE_MANAGER_SYSTEM_PROMPT

    elif role == UserRoleEnum.AREA_SUPERVISOR:
        return AREA_SUPERVISOR_SYSTEM_PROMPT

    elif role == UserRoleEnum.ENTERPRISE_ADMIN:
        return ENTERPRISE_ADMIN_SYSTEM_PROMPT

    else:
        raise ValueError(f"未知用户角色: {role}")


if __name__ == "__main__":

    prompt = get_system_prompt(
        UserRoleEnum.STORE_MANAGER
    )

    print(prompt)
