# 初版Intent
"""
Intent Recognition Service
"""

from src.core.schemas import (
    IntentRecognitionResult,
    UserIntentEnum,
)


class IntentRecognitionService:
    def extract_slots(
        self,
        user_query: str,
    ) -> dict:

        slots = {}

        # 时间范围
        if "最近7天" in user_query:
            slots["time_range"] = "last_7_days"

        elif "今天" in user_query:
            slots["time_range"] = "today"

        # 风险等级
        if "高风险" in user_query:
            slots["risk_level"] = "high"

        # 区域
        if "深圳" in user_query:
            slots["region"] = "深圳"

        return slots

    def recognize(
        self,
        user_query: str,
    ) -> IntentRecognitionResult:

        query = user_query.lower()
        slots = self.extract_slots(user_query)

        # 排行
        if "最多" in query or "排名" in query:

            return IntentRecognitionResult(
                user_query=user_query,
                intent_type=UserIntentEnum.QUERY_RANKING,
                intent_confidence=0.9,
                target_agent="data_agent",
            )

        # 趋势
        elif "趋势" in query:

            return IntentRecognitionResult(
                user_query=user_query,
                intent_type=UserIntentEnum.QUERY_TREND,
                intent_confidence=0.9,
                target_agent="data_agent",
                slots=slots,
            )

        # 整改
        elif "整改" in query:

            return IntentRecognitionResult(
                user_query=user_query,
                intent_type=UserIntentEnum.QUERY_RECTIFICATION,
                intent_confidence=0.9,
                target_agent="data_agent",
            )

        # 默认
        return IntentRecognitionResult(
            user_query=user_query,
            intent_type=UserIntentEnum.OUT_OF_DOMAIN,
            intent_confidence=0.3,
            target_agent="router_agent",
            is_out_of_domain=True,
        )
