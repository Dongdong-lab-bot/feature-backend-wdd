# Week3 完成情况报告

## 1. 结论

- 结论：Week3（跨 Agent 路由分发闭环）中 C 组代码区可完成项已完成。
- 完成范围：路由策略优先级、目标 Agent/Tool 决策、结构化聚合摘要、分发状态表达。
- 待联调范围：真实跨组 Agent 调用、消息总线投递、外部 HTTP/WS 入口接入。

## 2. 已完成项

1. 路由策略优先级
- `router_service.py` 已按写操作、导出、整改查询、趋势、排名、统计、明细、合规、问候、领域外进行优先判断。
- 高风险动作优先进入确认预览，不走静默写操作。

2. Function Calling 字段兼容
- 兼容旧版 `intent/confidence/function_call`。
- 兼容新版 `intent_type/intent_confidence/target_tool/tool_args`。
- 解析失败时降级到关键词路由。

3. 分发目标收敛
- 查询类路由到 `data_agent` + `query_food_safety_data`。
- 写操作预览类路由到 `triage_agent` + `preview_dispatch_action`。
- 澄清/拒答类留在 `router_agent`。

4. 聚合摘要
- `chat_router.py` 的 `structured_summary` 已补充 `target_agent`、`target_tool`、`tool_args`、`slots`、`missing_slots`、`dispatch_status`、`entity_boundary`。
5. 联调留痕补档
- 已补齐 `docs/router_agent/week3_联调测试脚本与报告.md` 作为当前联调留痕基线。

## 3. 未完成项

- 未直接调用 `data_agent` 或 `triage_agent` 的真实业务方法。
- 未发布 `ROUTE_DISPATCHED/ROUTE_COMPLETED` 消息总线事件。
- 未完成真实跨组联调执行与执行型联调记录沉淀。
- 原因：这些属于跨组联调或核心消息总线链路，不应在 C 组代码区内私自改动。

## 4. 验收口径

- C 组内部验收：用户消息可得到稳定路由结果与聚合摘要。
- 跨组验收：需等待外部接口层和目标 Agent 契约接入后执行。
