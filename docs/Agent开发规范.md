# Agent 开发规范 V1.0

> 规范来源：`src/agents/base_agent.py`、`src/core/schemas.py`、`src/core/event_protocol.py`
> 适用范围：监管 Agent（A组）、数据 Agent（B组）、路由 Agent（C组）及后续新增业务 Agent
> 版本状态：V1.0 草案，待 Day4 评审后冻结，修改需经架构审批

---

## 1. 总则

### 1.1 设计目标

本规范定义 Safefood Agent Cluster 中所有业务 Agent 的开发标准，确保：
- 生命周期管理统一（启动 → 运行 → 停止）
- 熔断降级能力开箱即用
- 审计日志全链路自动埋点
- 异常处理标准化，禁止裸抛原生 Exception
- 新增 Agent 即插即用，通过元类自动注册

### 1.2 必须遵守的红线

1. **Schema 统一红线**：Agent 间通信必须使用 `AgentEventModel`，禁止私自扩展字段
2. **稳定性红线**：所有大模型调用必须配置超时重试、熔断降级，连续 3 次失败必须切硬编码兜底
3. **可追溯红线**：所有关键决策必须写入审计日志，handle_event 已内置自动埋点
4. **异常纪律红线**：禁止在 Agent 业务代码中 `raise Exception()`，必须抛 `ProjectBaseException` 子类

---

## 2. 快速开始：编写一个业务 Agent

### 2.1 最小可运行示例

```python
from src.agents.base_agent import BaseAgent
from src.core.schemas import AgentEventModel
from src.core.logger import log


class DemoAgent(BaseAgent):
    """示例业务 Agent"""

    # 自定义熔断参数（可选，以下为默认值）
    # FUSE_FAILURE_THRESHOLD = 5    # 次，触发熔断的连续失败次数
    # FUSE_RECOVERY_TIMEOUT = 60.0  # 秒，熔断后进入半开状态的等待时间
    # FUSE_HALF_OPEN_MAX_CALLS = 3  # 次，半开状态允许的试探请求数

    async def run(self) -> None:
        """启动逻辑：订阅消息、初始化资源"""
        self.status = self.status.RUNNING
        log.info(f"{self.agent_name} started")

    async def _on_event(self, event: AgentEventModel) -> dict:
        """处理具体业务事件

        Args:
            event: 标准化事件模型，含 event_type / payload / trace_id 等

        Returns:
            业务结果字典，handle_event 会自动包装为统一响应格式
        """
        # 强制使用枚举判断，禁止硬编码字符串（Schema统一红线）
        if event.event_type == AgentEventTypeEnum.ALERT_RECEIVED:
            alert_id = event.payload.get("alert_id")
            # ... 业务逻辑 ...
            return {"processed_alert_id": alert_id, "result": "ok"}

        return {"result": "ignored", "reason": "unknown_event_type"}
```

### 2.2 实例化与运行

```python
import asyncio

async def main():
    agent = DemoAgent(agent_id="demo_001", agent_name="demo_agent")
    await agent.run()

    # 模拟接收事件
    from src.core.schemas import AgentEventModel, AgentEventTypeEnum
    event = AgentEventModel(
        event_id="evt_001",
        event_type=AgentEventTypeEnum.ALERT_RECEIVED,
        source_agent="infra",
        payload={"alert_id": "ALT001"},
    )
    result = await agent.handle_event(event)
    print(result)

    await agent.stop()

asyncio.run(main())
```

### 2.3 自动注册验证

```python
from src.agents.base_agent import AgentRegistry

# 无需手动注册，继承 BaseAgent 即自动注册
cls = AgentRegistry.get("DemoAgent")
assert cls is not None
print(AgentRegistry.list_agents())  # {'DemoAgent': <class 'DemoAgent'>}
```

---

## 3. 生命周期规范

### 3.1 标准生命周期流程

```
初始化                          运行期（事件驱动）                         停止
  │                              │                                      │
  ▼                              ▼                                      ▼
__init__()  ──►  run()  ──►  IDLE / RUNNING  ──► [handle_event() …]  ──►  stop()
  │           │           │    ▲    │    ▲          │   │              │
  │           │           │    │    │    │          ▼   │              │
  │  • 状态    │  • 订阅   │    │    │    └────── BUSY ─┘              │
  │    =INIT   │    消息   │    │    │         (处理中)                 │
  │  • 初始化  │  • 状态   │    │    │                                │
  │    熔断器   │    =IDLE  │    │    │                                │
  │            │           │    │    │                                │
  │            │           │    │    └────────────────────────────────┤
  │            │           │    │                                     │
  │            │           │    └─────────────────────────────────────┤
  │            │           │         (事件处理完成，回到 RUNNING)        │
  │            │           │                                          │
  │            └───────────┴──────────────────────────────────────────►│
  │                        (stop() 可从任意可运行状态触发)               │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────►
                                (异常导致 ERROR，需重启)
```

### 3.2 状态流转图

```
                         事件处理完成
INITIALIZING ──► IDLE ───────────────► RUNNING
                    │                    │
                    │ 收到事件            │ 收到事件
                    ▼                    ▼
                  BUSY ◄────────────────┘
                    │
                    │ 处理完成
                    └────────────────────►

  STOPPING ◄─── 任意可运行状态触发 stop()
       │
       ▼
    STOPPED

  ERROR ◄─── 严重异常（后台任务崩溃等）
```

| 状态 | 含义 | 可处理事件 | 进入条件 |
|------|------|-----------|----------|
| `INITIALIZING` | `__init__()` 执行期间，未完成初始化 | 否 | 实例化时自动进入 |
| `IDLE` | `run()` 完成后，等待事件 | 是 | `run()` 完成且无事件处理 |
| `RUNNING` | 事件处理完成后的活跃状态 | 是 | 事件处理完成，或 `run()` 后直接设为 RUNNING |
| `BUSY` | `handle_event()` 执行期间 | 是（并发由调度层控制） | `handle_event()` 开始 |
| `STOPPING` | `stop()` 执行期间 | 否 | `stop()` 被调用 |
| `STOPPED` | 已停止，资源已释放 | 否 | `stop()` 完成 |
| `ERROR` | 发生不可恢复错误（后台任务崩溃等） | 否 | 未捕获异常导致 |

**状态切换规则（由 `handle_event` 自动管理，子类禁止手动修改）**：
1. `handle_event()` 开始时：当前状态必须是 `RUNNING` / `IDLE` / `BUSY` → 切换为 `BUSY`
2. `handle_event()` 成功完成：`BUSY` → `RUNNING`
3. `handle_event()` 异常完成：`BUSY` → `RUNNING`（异常已捕获包装，不进入 ERROR）
4. 只有后台任务发生**未捕获异常**时，才会进入 `ERROR` 状态

### 3.3 子类必须实现的方法

| 方法 | 说明 | 调用方 |
|------|------|--------|
| `run()` | 启动逻辑，完成初始化后将状态置为 RUNNING/IDLE | 外部调度器 |
| `_on_event(event)` | 业务事件处理，返回任意结果 | `handle_event()` 内部调用 |

### 3.4 子类可选覆盖的方法

| 方法 | 默认行为 | 覆盖场景 |
|------|----------|---------|
| `stop()` | 取消后台任务，置状态 STOPPED | 需要额外资源释放时，**必须调用 `super().stop()`** |
| `_health_check()` | 检查状态是否为 RUNNING/IDLE/BUSY | 自定义健康探活逻辑 |

---

## 4. 熔断器规范

### 4.1 状态机

```
         失败 < threshold              成功
    ┌────────────────────┐        ┌──────────┐
    │                    ▼        ▼          │
  CLOSED ──► 失败 ≥ threshold ──► OPEN ──► 超时恢复 ──► HALF_OPEN
    ▲                                                    │
    │              成功（半开期内）                        │ 失败
    └────────────────────────────────────────────────────┘
```

### 4.2 配置参数

子类通过类属性覆盖默认值。所有时间参数单位为**秒**，计数参数单位为**次**：

| 参数名 | 默认值 | 单位 | 取值范围 | 说明 |
|--------|--------|------|----------|------|
| `FUSE_FAILURE_THRESHOLD` | 5 | 次 | ≥1 | 触发熔断的连续失败次数 |
| `FUSE_RECOVERY_TIMEOUT` | 60.0 | 秒 | ≥10 | 熔断后进入半开状态的等待时间 |
| `FUSE_HALF_OPEN_MAX_CALLS` | 3 | 次 | ≥1 | 半开状态允许的试探请求数 |

```python
class MyAgent(BaseAgent):
    FUSE_FAILURE_THRESHOLD = 3      # 次
    FUSE_RECOVERY_TIMEOUT = 30.0    # 秒
    FUSE_HALF_OPEN_MAX_CALLS = 5    # 次
```

### 4.3 熔断触发后的行为

当熔断器处于 `OPEN` 状态时，`handle_event()` 不会调用 `_on_event()`，直接返回：

```python
{
    "success": False,
    "code": "2003",
    "message": "熔断器已触发: open",
    "data": None,
    "latency_ms": 0,
}
```

业务组无需额外处理熔断逻辑，但应在 Agent 设计文档中注明熔断降级的业务影响。

### 4.4 熔断与稳定性红线

- 大模型调用失败 → `_on_failure()` 自动计数
- 连续失败达到阈值 → 熔断器自动 OPEN
- 熔断期间所有请求快速失败，不消耗大模型资源
- 恢复后进入 HALF_OPEN，允许少量试探请求
- **严禁在熔断触发期间继续重试大模型调用**

---

## 5. 事件处理规范

### 5.1 handle_event 内部流程

```python
async def handle_event(self, event) -> dict:
    # 1. 状态检查 ──► 非 RUNNING/IDLE/BUSY 直接返回错误
    # 2. 熔断检查 ──► OPEN 状态直接返回熔断响应
    # 3. trace_id 透传 ──► 注入 TraceContext
    # 4. 执行 _on_event() ──► 子类业务逻辑
    # 5. 异常捕获
    #    ├── ProjectBaseException ──► 直接透传
    #    └── Exception ──► 包装为 AgentHandleFailedError
    # 6. 熔断计数更新 ──► 成功/失败各走各的分支
    # 7. 审计日志 ──► 自动记录 start / success / error
    # 8. 统一响应包装
```

### 5.2 子类 _on_event 编写约束

**必须遵守：**
- 返回值为 `dict` 或任意可被 JSON 序列化的对象
- 禁止裸抛 `Exception`，必须抛 `ProjectBaseException` 子类
- 禁止在 `_on_event` 中直接修改 `self._status`，由 `handle_event` 自动管理
- `handle_event()` 已自动埋点事件处理的生命周期（start/success/error）
- **业务关键决策**（VLM 判定、SQL 生成、意图识别结果、权限判定）**必须在 `_on_event` 内显式调用 `log.audit()`**，确保审计链路完整
- 禁止为每一条普通日志都调用 `log.audit()`（避免审计日志膨胀），仅限"重大决策"场景
- 如需非审计类额外信息，使用 `log.info()` / `log.debug()`

**推荐做法：**
- 复杂业务逻辑拆分为私有方法，保持 `_on_event` 简洁
- 使用 `try/except` 捕获预期异常并转换为对应 `ProjectBaseException`
- 返回结果包含明确的业务标识字段，便于下游消费

### 5.3 事件类型与业务映射

当前项目定义的 `AgentEventTypeEnum` 中，各 Agent 应关注的事件类型：

| Agent | 应处理的事件类型 |
|-------|----------------|
| 监管 Agent (triage) | `ALERT_RECEIVED`, `ALERT_DISPATCHED`, `VERIFY_FAILED` |
| 数据 Agent (data) | `ROUTE_DISPATCHED` (intent_type=query_*) |
| 路由 Agent (router) | `USER_QUERY_RECEIVED`, `USER_CONFIRMED`, `USER_REJECTED`, `ALERT_VERIFIED` |

---

## 6. 后台任务管理

### 6.1 注册后台任务

```python
async def run(self) -> None:
    # 启动消费循环等后台任务
    task = asyncio.create_task(self._consume_loop())
    self.add_background_task(task)
    self.status = self.status.RUNNING
```

**异常兜底**：`add_background_task()` 已自动为任务注册 `add_done_callback`，后台任务抛未捕获异常时会记录日志并更新失败计数，**禁止异常向上抛到事件循环导致 Agent 进程崩溃**。

### 6.2 stop() 自动清理

`stop()` 会自动取消所有通过 `add_background_task()` 注册的任务，无需子类手动处理。

---

## 7. 健康检查

### 7.1 默认健康检查

```python
agent._health_check()
# 返回:
# {
#     "healthy": True,         # 全部检查项通过
#     "status": "running",
#     "fuse_state": "closed",
#     "status_ok": True,       # Agent 状态正常
#     "fuse_ok": True,         # 熔断器未 OPEN
#     "tasks_ok": True,        # 后台任务无崩溃
#     "background_tasks_count": 2,
# }
```

默认检查项：
1. **Agent 状态**：必须为 RUNNING/IDLE/BUSY
2. **熔断器状态**：不能处于 OPEN 状态
3. **后台任务存活**：无已崩溃（抛未捕获异常）的后台任务

任意一项不通过，`healthy` 返回 `False`，容器编排系统应据此自动重启服务。

### 7.2 覆盖健康检查

```python
class MyAgent(BaseAgent):
    def _health_check(self) -> dict:
        base = super()._health_check()  # 必须保留默认检查项
        base["db_connected"] = self._db is not None
        base["queue_depth"] = self._queue.qsize()
        return base
```

---

## 8. 运行时统计

### 8.1 获取统计信息

```python
stats = agent.get_stats()
# {
#     "agent_id": "demo_001",
#     "agent_name": "demo_agent",
#     "status": "running",
#     "fuse_state": "closed",
#     "fuse_failure_count": 0,
#     "total_requests": 42,
#     "success_requests": 40,
#     "failed_requests": 2,
# }
```

---

## 9. 与消息总线集成

### 9.1 标准集成模式

```python
from src.core.message_bus import MessageBusFactory
from src.core.schemas import AgentEventModel

class MyAgent(BaseAgent):
    async def run(self) -> None:
        self._bus = MessageBusFactory.create("redis")
        await self._bus.start()

        import os, uuid

        # 消费者 ID 必须包含实例唯一标识，避免 K8s 多 Pod 冲突
        hostname = os.environ.get("HOSTNAME", uuid.uuid4().hex[:6])
        consumer_id = f"{self.agent_name}_{self.agent_id}_{hostname}"

        await self._bus.subscribe_topic(
            topic="agent_message_bus",
            callback=self._on_bus_message,
            group="my_consumer_group",
            consumer=consumer_id,
        )
        self.status = self.status.RUNNING

    async def _on_bus_message(self, data: dict) -> None:
        """消息总线回调 → 转换为 AgentEventModel → 交给 handle_event

        必须捕获异常：消息格式错误时不应导致 Agent 进程崩溃。
        """
        try:
            event = AgentEventModel(**data)
            await self.handle_event(event)
        except Exception as exc:
            log.error(
                f"Message parsing/handling failed | agent={self.agent_name} "
                f"exc={type(exc).__name__}: {exc}",
                extra={"raw_data": data},
            )
            # 不 ACK 消息（由消息总线层控制），消息将留在 PEL 等待重投或转入死信队列
            # 禁止 re-raise，避免 asyncio 事件循环崩溃

    async def stop(self) -> None:
        await self._bus.stop()
        await super().stop()
```

### 9.2 事件 Payload 规范（强约束）

`AgentEventModel.payload` 的类型为 `Dict[str, Any]`，但这不代表可以随便构造字典。**所有跨 Agent 通信的 payload 必须基于 `schemas.py` 中的具体模型序列化**，禁止直接手写裸字典。

**推荐（类型安全、可校验）**：
```python
from src.core.schemas import AlertPushRequest

payload = AlertPushRequest(
    camera_id="cam_001",
    message="[no_mask] 检测到: no_mask",
    level=AlertLevelEnum.HIGH,
    confidence=0.92,
    timestamp=beijing_now(),
).model_dump()

event = AgentEventModel(
    event_id="evt_001",
    event_type=AgentEventTypeEnum.ALERT_RECEIVED,
    source_agent=self.agent_name,
    payload=payload,
)
```

**禁止（字段漂移、无法校验）**：
```python
payload = {
    "camera_id": "cam_001",
    "levle": "high",  # 拼写错误，静默失败
    "confidence": 1.5,  # 超出范围，无校验
}
```

**消费者侧反序列化**：
```python
async def _on_bus_message(self, data: dict) -> None:
    event = AgentEventModel(**data)
    # 根据 event_type 选择对应的 payload 模型反序列化
    if event.event_type == AgentEventTypeEnum.ALERT_RECEIVED:
        alert = AlertPushRequest(**event.payload)
        await self.handle_event(event)
```

### 9.3 发送事件

```python
response_event = AgentEventModel(
    event_id="evt_002",
    event_type=AgentEventTypeEnum.ALERT_VERIFIED,
    source_agent=self.agent_name,
    payload={"alert_id": "ALT001", "result": "true_violation"},
)
await self._bus.send_message("agent_message_bus", response_event)
```

---

## 10. 异常处理最佳实践

### 10.1 异常选择速查表

| 场景 | 应抛异常 | 错误码 |
|------|----------|--------|
| 参数校验失败 | `ParamError` | 1001 |
| 配置缺失/错误 | `ConfigError` | 1002 |
| 大模型调用失败 | `LLMCallFailedError` | 2001 |
| 大模型响应格式错误 | `LLMResponseInvalidError` | 2002 |
| 大模型熔断触发 | `LLMFuseTriggeredError` | 2003 |
| SQL 安全拦截 | `SQLSecurityBlockedError` | 3001 |
| SQL 性能拦截 | `SQLPerformanceBlockedError` | 3002 |
| 权限不足 | `PermissionDeniedError` | 3003 |
| 数据库连接失败 | `DBConnectFailedError` | 4001 |
| 数据库执行失败 | `DBExecuteFailedError` | 4002 |
| 查询结果为空 | `DBResultEmptyError` | 4003 |
| Agent 初始化失败 | `AgentInitFailedError` | 5001 |
| Agent 处理失败 | `AgentHandleFailedError` | 5002 |
| 路由失败 | `RouteFailedError` | 5003 |
| 意图识别失败 | `IntentRecognitionFailedError` | 6001 |
| 路由分发失败 | `RouteDispatchFailedError` | 6002 |
| 确认单过期 | `ConfirmationExpiredError` | 6003 |
| VLM 校验失败 | `VLMVerifyFailedError` | 7003 |
| 网关请求无效 | `GatewayRequestInvalidError` | 8001 |
| 边缘告警推送失败 | `EdgeAlertPushFailedError` | 8002 |
| 存储写入失败 | `StorageFailedError` | 8003 |

### 10.2 异常处理示例

```python
async def _on_event(self, event: AgentEventModel) -> dict:
    alert_id = event.payload.get("alert_id")
    if not alert_id:
        raise ParamError("alert_id 不能为空", detail={"payload": event.payload})

    try:
        result = await self._call_vlm(alert_id)
    except TimeoutError:
        raise LLMCallFailedError(
            "VLM 调用超时",
            detail={"alert_id": alert_id, "timeout": 30}
        )

    return {"verified": True, "result": result}
```

---

## 11. 开发 Checklist

新建业务 Agent 时，逐项确认：

- [ ] 继承 `BaseAgent`，实现 `run()` 和 `_on_event()`
- [ ] 通过 `AgentRegistry.get("MyAgent")` 验证自动注册成功
- [ ] 配置合适的熔断参数（`FUSE_FAILURE_THRESHOLD` 等）
- [ ] `run()` 中将状态置为 RUNNING/IDLE
- [ ] `stop()` 中调用 `super().stop()`
- [ ] `_on_event()` 中不裸抛 `Exception`
- [ ] `_on_event()` 中不修改 `self._status`
- [ ] 大模型调用有超时和重试逻辑
- [ ] 与消息总线集成时使用 `AgentEventModel`
- [ ] 编写单元测试覆盖正常/异常/熔断场景

---

## 12. 变更记录

| 版本 | 日期 | 变更内容 | 审批人 |
|------|------|----------|--------|
| V1.0 | 2026-04-27 | 初始版本，基于 BaseAgent 实现冻结发布 | 架构组 |
