"""Tool wrapper for DataAgent unified entry."""

from typing import Any

from src.agents.data_agent.agent import DataAgent


_DATA_AGENT = DataAgent()


async def query_food_safety_data(
    user_query: str,
    scene: str = "alarm_query",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Query food safety data via DataAgent.

    Tool description:
    - Function: convert natural language queries into safe data-query workflow.
    - Permission boundary: relies on context.user_role for role-level access checks.
    - Output contract: always returns standard_response structure.
    """
    return await _DATA_AGENT.query_food_safety_data(
        user_query=user_query,
        scene=scene,
        context=context,
    )
