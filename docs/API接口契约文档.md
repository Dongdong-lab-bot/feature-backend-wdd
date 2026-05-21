# API 接口契约文档 V1.1

> 规范来源：`src/api/routes/alert.py`、`src/api/routes/chat.py`、`src/core/event_protocol.py`、`src/core/schemas.py`、`src/core/exceptions.py`
> 适用范围：前端、EdgeAgent、内部服务与基建网关的全部交互接口
> 版本状态：V1.1 正式版（ALERT_RECEIVED 事件 Payload Schema 调整），修改需经架构审批

---

## 1. 总则

### 1.1 接口分层

本项目接口按调用方分为三层：

| 层级 | 调用方 | 协议 | 文件位置 |
|------|--------|------|----------|
| 边缘接入层 | EdgeAgent | HTTP POST + multipart | `src/api/routes/alert.py` |
| 前端交互层 | Web/App | HTTP + WebSocket | `src/api/routes/chat.py` |
| Agent 通信层 | 各业务 Agent | Redis Streams | `src/core/event_protocol.py` |

### 1.2 通用约定

- 所有 HTTP 接口响应遵循 `ResponseBase` 结构：`{trace_id, code, message, success, response_time, data}`
- 所有时间字段为 Aware Datetime（带 `Asia/Shanghai` 时区）
- 所有 ID 字段固定格式：`ALT{13位毫秒时间戳}{8位随机字母数字}`（告警）、`SES{13位毫秒时间戳}{8位随机字母数字}`（会话），详见 `schemas.py::generate_id()`
- 分页查询统一使用 `PageResponseBase`：含 `total`, `page_num`, `page_size`, `total_pages`, `items`
- 默认排序规则：按时间倒序（`timestamp` / `created_at` DESC）

---

## 2. 边缘告警接口（alert.py）

面向 EdgeAgent 与前端/内部服务的告警数据接口。

### 2.1 告警推送

```
POST /api/v1/alerts
Content-Type: multipart/form-data
```

**认证**：`X-API-KEY: <EDGE_AGENT_API_KEY>`

**请求字段**：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `alert_data` | string (JSON) | 是 | `EdgeAlertPayload` 序列化字符串 |
| `file` | file (JPEG/PNG/JPG) | 否 | 带检测框标注截图，≤ 5MB；仅支持 JPEG/PNG/JPG，通过魔数校验；分辨率 ≤ 4096×2160 |

**alert_data 原始 JSON**：

```json
{
  "camera_id": "camera_001",
  "message": "[no_mask] 检测到: no_mask",
  "level": "high",
  "confidence": 0.92,
  "timestamp": "2025-10-29 14:28:50.123456"
}
```

**成功响应**（code=0000）：

```json
{
  "trace_id": "abc123...",
  "code": "0000",
  "message": "告警推送成功",
  "success": true,
  "response_time": "2026-04-27T15:00:00+08:00",
  "data": {
    "alert_id": "ALT1745733600123A7F9X2K1"
  }
}
```

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 处理成功 | 200 |
| 1001 | PARAM_ERROR | alert_data 缺失/格式错误/必填字段缺失 | 400 |
| 1002 | CONFIG_ERROR | 文件存储路径未配置 | 500 |
| 8001 | GATEWAY_REQUEST_INVALID | X-API-KEY 缺失或无效 | 401 |
| 8002 | EDGE_ALERT_PUSH_FAILED | 边缘数据格式校验不通过 | 400 |
| 8003 | STORAGE_FAILED | 截图保存失败 / Stream 写入失败 | 500 |
| 4001 | DB_CONNECT_FAILED | 数据库连接失败 | 503 |

**文件安全校验**（步骤 3 之前执行）：
1. 魔数校验：仅允许 `FF D8 FF` (JPEG)、`89 50 4E 47` (PNG) 开头
2. 格式白名单：禁止上传可执行文件、压缩包、脚本等非图片格式
3. 分辨率限制：宽 × 高 ≤ 4096 × 2160，超限返回 1001

**网关层处理流程**：
1. 校验 X-API-KEY
2. 解析 multipart，提取 alert_data JSON 和 file
3. 文件安全校验（魔数、格式白名单、分辨率、大小）
4. 校验 alert_data 字段完整性
5. 保存截图到 `/app/alert_images/{uuid}.jpg`，生成 image_url
6. 将 naive 时间字符串转换为带北京时区的 Aware Datetime
7. 将 level 映射为 `AlertLevelEnum`
8. 生成告警 ID
9. **入库 `AlertCoreModel`**（数据库事务内完成）
10. 将 `AlertCoreModel` 写入 Redis Stream，触发 `ALERT_RECEIVED` 事件
11. WebSocket 广播给前端
12. MQTT 推送（若配置）

**时序约束**：必须先完成数据库入库（步骤 9），再写入消息总线（步骤 10）。入库失败直接返回错误，禁止向下游分发事件。

**异常补偿机制**（入库成功但消息总线写入失败）：
- 步骤 9 成功、步骤 10 失败时，告警数据已落库但下游 Agent 未感知，形成**静默告警**
- 补偿方案：基建组启动定时补偿任务（每 5 分钟扫描一次），对满足以下条件的告警重新投递：
  1. `is_verified = false`（未经过 VLM 校验）
  2. `created_at < now - 5min`（已入库超过 5 分钟，避开正常处理窗口）
  3. 不存在对应的 `ALERT_RECEIVED` 事件审计日志（通过 `audit_id` + `event_type` 查询）
- 重新投递前需校验告警是否已被去重/聚合逻辑处理，避免重复触发
- 补偿任务本身需记录审计日志（`event_type = SYSTEM_EVENT`），便于排查循环补偿

---

### 2.2 查询告警详情

```
GET /api/v1/alerts/{alert_id}
Authorization: Bearer <JWT>
```

**路径参数**：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `alert_id` | string | 是 | 告警唯一 ID |

**权限校验**：
- `ENTERPRISE_ADMIN`：可查询全部
- `AREA_SUPERVISOR`：可查询其 region_ids 范围内门店
- `STORE_MANAGER`：仅可查询其 store_ids 范围内
- 所有查询接口必须记录审计日志（event_type=USER_QUERY）

**成功响应**：返回 `AlertDetailResponse`，`alert_detail` 为 `AlertCoreModel`

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 查询成功 | 200 |
| 1001 | PARAM_ERROR | alert_id 格式非法 | 400 |
| 3003 | PERMISSION_DENIED | 越权 | 403 |
| 4003 | DB_RESULT_EMPTY | alert_id 不存在 | 404 |

---

### 2.3 查询告警列表

```
GET /api/v1/alerts?time_range_start=...&time_range_end=...&store_scope=...&page_num=1&page_size=20
Authorization: Bearer <JWT>
```

**查询参数**（全部可选）：

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `time_range_start` | string | null | ISO 8601 起始时间 |
| `time_range_end` | string | null | ISO 8601 结束时间 |
| `store_scope` | string | null | 门店 ID 列表，**逗号分隔**，如 `STORE_001,STORE_002` |
| `violation_type` | string | null | 违规类型编码列表，**逗号分隔**，如 `A01,A02` |
| `risk_level` | string | null | 告警级别列表，**逗号分隔**，如 `high,critical` |
| `rectification_status` | string | null | 整改状态列表，**逗号分隔**，如 `pending` |
| `page_num` | integer | 1 | 页码，≥1 |
| `page_size` | integer | 20 | 每页条数，1~100 |

**权限校验**：
- 基于 role_type 和 store_ids 过滤
- 用户传入的 `store_scope` 必须为其权限范围的**子集**；超出权限范围的门店 ID **直接返回 3003 PERMISSION_DENIED**，禁止自动裁剪或静默忽略
- 不传时后端自动按用户权限填充
- 所有查询接口必须记录审计日志（event_type=USER_QUERY）

**成功响应**：返回 `AlertListQueryResponse`，含 `items: List[AlertCoreModel]`

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 查询成功 | 200 |
| 1001 | PARAM_ERROR | page_num/page_size 非法 | 400 |
| 3003 | PERMISSION_DENIED | store_scope 越权 | 403 |
| 4001 | DB_CONNECT_FAILED | 数据库连接失败 | 503 |

---

### 2.4 查询违规事件详情

```
GET /api/v1/events/{event_id}
Authorization: Bearer <JWT>
```

**路径参数**：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `event_id` | string | 是 | 事件唯一 ID |

**权限校验**：同 2.2，按 store_id 过滤

**成功响应**：返回 `EventDetailResponse`，`event_detail` 为 `ViolationEventModel`

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 查询成功 | 200 |
| 1001 | PARAM_ERROR | event_id 格式非法 | 400 |
| 3003 | PERMISSION_DENIED | 越权 | 403 |
| 4003 | DB_RESULT_EMPTY | event_id 不存在 | 404 |

---

### 2.5 查询违规事件列表

```
GET /api/v1/events?time_range_start=...&page_num=1&page_size=20
Authorization: Bearer <JWT>
```

**查询参数**：同 2.3

**成功响应**：返回 `EventListQueryResponse`，含 `items: List[ViolationEventModel]`

**错误码**：同 2.3

---

## 3. 前端聊天接口（chat.py）

面向前端用户的路由 Agent 交互接口，支持 HTTP 轮询与 WebSocket 实时双模式。

### 3.1 创建会话

```
POST /api/v1/chat/sessions
Authorization: Bearer <JWT>
```

**请求体**：空（或可选初始上下文）

**成功响应**（code=0000）：

```json
{
  "trace_id": "abc123...",
  "code": "0000",
  "message": "会话创建成功",
  "success": true,
  "response_time": "2026-04-27T15:00:00+08:00",
  "data": {
    "session_id": "SES1745733600123A7F9X2K1",
    "user_id": "user_001",
    "created_at": "2026-04-27T15:00:00+08:00",
    "expire_time": "2026-04-27T15:30:00+08:00"
  }
}
```

**会话约束**：
- session_id 格式：`SES{13位毫秒时间戳}{8位随机字母数字}`
- 默认过期：30 分钟
- 每个用户同时活跃会话数上限：5 个（超出返回 1001）
- **活跃会话判定**：最后一次消息交互时间距当前 ≤ 30 分钟
- **超限处理策略**：创建新会话时，先自动清理最早的非活跃会话；若全部 5 个均为活跃会话，返回 1001 PARAM_ERROR，提示用户关闭历史会话
- chat_history 最大保留 10 轮

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 创建成功 | 201 |
| 1001 | PARAM_ERROR | 活跃会话数超限 | 400 |
| 3003 | PERMISSION_DENIED | JWT 无效或已过期 | 401 |
| 5001 | AGENT_INIT_FAILED | 路由 Agent 初始化失败 | 503 |

---

### 3.2 HTTP 发送消息

```
POST /api/v1/chat/messages
Authorization: Bearer <JWT>
```

**请求体**（`ChatMessageRequest`）：

```json
{
  "trace_id": "auto-generated",
  "user_id": "user_001",
  "request_time": "2026-04-27T15:00:00+08:00",
  "session_id": "SES1745733600123A7F9X2K1",
  "message_text": "查询今天南山店的告警",
  "input_type": "text",
  "attachments": null,
  "confirmation_id": null
}
```

**处理流程**：
1. 校验 JWT 与 session_id 归属
2. 更新会话上下文（延长 30 分钟过期时间）
3. 路由 Agent 意图识别
4. 置信度不足 → 返回 clarification
5. 需要二次确认 → 生成 ConfirmationModel
6. 路由到目标 Agent（data_agent / triage_agent）
7. 聚合结果返回 ChatMessageResponse
8. 更新 session.chat_history

**响应类型**（`response_type` 字段区分）：

| 类型 | 含义 | 关键字段 |
|------|------|----------|
| `answer` | 直接回答 | `answer_payload` |
| `clarification` | 需要澄清 | `clarification_content` |
| `confirmation_preview` | 高危操作预览 | `pending_confirmation` |
| `refusal` | 拒绝处理 | 越权/安全拦截 |
| `error` | 系统错误 | 错误信息 |
| `guidance` | 引导操作 | `suggested_actions` |

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 处理成功 | 200 |
| 1001 | PARAM_ERROR | session_id 不存在 / message_text 为空 | 400 |
| 3003 | PERMISSION_DENIED | JWT 无效 / 非会话所有者 | 401/403 |
| 5002 | AGENT_HANDLE_FAILED | 路由 Agent 处理异常 | 500 |
| 6001 | INTENT_RECOGNITION_FAILED | 意图识别置信度不足 | 422 |
| 6002 | ROUTE_DISPATCH_FAILED | 目标 Agent 不可用 | 503 |
| 6003 | CONFIRMATION_EXPIRED | 二次确认单已过期 | 410 |
| 2001 | LLM_CALL_FAILED | 大模型调用失败（3次重试后） | 503 |
| 2003 | LLM_FUSE_TRIGGERED | 大模型熔断已触发 | 503 |

**超时**：整体接口 30 秒，超时返回 5002

---

### 3.3 获取会话信息

```
GET /api/v1/chat/sessions/{session_id}
Authorization: Bearer <JWT>
```

**权限**：仅会话所有者；ENTERPRISE_ADMIN 可查看全部

**响应**：`SessionContext` 脱敏版本

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 查询成功 | 200 |
| 1001 | PARAM_ERROR | session_id 格式非法 | 400 |
| 3003 | PERMISSION_DENIED | 非所有者 | 403 |
| 4003 | DB_RESULT_EMPTY | session_id 不存在 | 404 |

---

### 3.4 获取对话历史

```
GET /api/v1/chat/sessions/{session_id}/history?page_num=1&page_size=20
Authorization: Bearer <JWT>
```

**响应**：

```json
{
  "trace_id": "...",
  "code": "0000",
  "message": "查询成功",
  "success": true,
  "response_time": "...",
  "data": {
    "total": 15,
    "page_num": 1,
    "page_size": 20,
    "total_pages": 1,
    "items": [
      {"role": "user", "content": "查询今天告警", "timestamp": "...", "intent_type": "query_summary"},
      {"role": "assistant", "content": "今天共有 5 条告警...", "timestamp": "...", "intent_type": null}
    ]
  }
}
```

---

### 3.5 WebSocket 实时对话

```
WS /ws/v1/chat/{session_id}
```

**认证**：连接建立后，Client 必须在第一条消息发送认证包完成 JWT 校验。禁止在 URL、Header 中传递 JWT。

**Client → Server 认证消息（连接后第一条）**：

```json
{"auth": "eyJhbGciOiJIUzI1NiIs..."}
```

服务端校验通过后回复 `{"type": "auth_ok"}`，此后进入正常消息交互。

**消息格式**：JSON 字符串

**Client → Server 业务消息**：

```json
{
  "message_text": "查询今天南山店的告警",
  "input_type": "text",
  "attachments": null,
  "confirmation_id": null
}
```

**Server → Client**：

```json
{
  "session_id": "SES1745733600123A7F9X2K1",
  "response_type": "answer",
  "answer_payload": "今天南山店共有 3 条告警...",
  "structured_summary": {"total": 3, "items": [...]},
  "guidance_type": "none",
  "suggested_actions": [{"label": "查看详情", "action": "query_detail"}],
  "pending_confirmation": null
}
```

**连接管理**：
- 心跳：Server 每 30 秒 ping，Client 10 秒内回复 pong
- 连续 3 次心跳未回复 pong → Server 断开连接（避免网络抖动导致频繁断连）
- 同一 session 支持多端同时连接
- 会话过期（30 分钟无操作）→ Server 发送过期通知后断开

**错误消息**（Server → Client）：

```json
{
  "response_type": "error",
  "answer_payload": "会话已过期，请重新创建会话",
  "code": "6003"
}
```

---

### 3.6 确认高危操作

```
POST /api/v1/chat/confirmations/{confirmation_id}/confirm
Authorization: Bearer <JWT>
```

**处理流程**：
1. 校验确认单存在且未过期
2. 校验用户为确认单所有者
3. 执行 action_type（export_report / send_notice / create_task）
4. 更新确认单状态为 confirmed
5. 返回执行结果

**响应**：`ChatMessageResponse`（response_type="answer" 或 "error"）

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 确认成功 | 200 |
| 1001 | PARAM_ERROR | confirmation_id 格式非法 | 400 |
| 3003 | PERMISSION_DENIED | 非所有者 | 403 |
| 6003 | CONFIRMATION_EXPIRED | 确认单已过期 | 410 |
| 4003 | DB_RESULT_EMPTY | confirmation_id 不存在 | 404 |
| 5002 | AGENT_HANDLE_FAILED | 操作执行失败 | 500 |

---

### 3.7 拒绝高危操作

```
POST /api/v1/chat/confirmations/{confirmation_id}/reject
Authorization: Bearer <JWT>
```

**处理流程**：校验 → 更新状态为 rejected → 返回拒绝确认

**响应**：`ChatMessageResponse`（response_type="answer"）

**错误码**：同 3.6

---

### 3.8 删除会话

```
DELETE /api/v1/chat/sessions/{session_id}
Authorization: Bearer <JWT>
```

**删除方式**：**逻辑删除（软删除）**，更新 `is_deleted=true` 标记，禁止物理删除数据库记录，确保审计链路完整可追溯。

**权限**：仅会话所有者或 ENTERPRISE_ADMIN

**响应**：

```json
{
  "trace_id": "...",
  "code": "0000",
  "message": "会话已删除",
  "success": true,
  "response_time": "...",
  "data": null
}
```

**错误码**：

| 错误码 | 错误名称 | 触发场景 | HTTP Status |
|--------|----------|----------|-------------|
| 0000 | SUCCESS | 删除成功 | 200 |
| 3003 | PERMISSION_DENIED | 无权删除 | 403 |
| 4003 | DB_RESULT_EMPTY | session_id 不存在 | 404 |

---

## 4. Agent 间通信协议（event_protocol.py）

Agent 间异步通信的唯一标准，禁止业务 Agent 直接使用底层 Redis API。

### 4.1 通信拓扑

```
EdgeAgent ──HTTP──► 基建网关 ──[ALERT_RECEIVED]──► 消息总线
                                          ▲
                                          │ RECTIFICATION_UPDATED
                                          ▼
                                    ┌─────────────┐
                                    │  监管 Agent  │ ──[ALERT_VERIFIED]──►
                                    │  (triage)    │ ◄──[ALERT_DISPATCHED]──
                                    └─────────────┘
                                          │
                                          ▼
                                    ┌─────────────┐
                                    │  数据 Agent  │ ──[SQL_GENERATED/EXECUTED/BLOCKED]──►
                                    │  (data)      │ ◄──[ROUTE_DISPATCHED]──
                                    └─────────────┘
                                          │
                                          ▼
                                    ┌─────────────┐
                                    │  路由 Agent  │ ──[INTENT_RECOGNIZED/ROUTE_DISPATCHED/COMPLETED]──►
                                    │  (router)    │ ◄──[USER_QUERY_RECEIVED/CONFIRMED/REJECTED]──
                                    └─────────────┘
                                          │
                                          ▼
                                       前端 (WebSocket)
```

### 4.2 事件类型总表

| 事件类型 | 描述 | 生产者 | 消费者 | 优先级 | Payload Schema |
|----------|------|--------|--------|--------|----------------|
| `ALERT_RECEIVED` | 网关收到边缘告警，已解析并入库 | infra | triage_agent | 1 | `AlertCoreModel` |
| `ALERT_DEDUPED` | 时空去重判定完成 | triage_agent | triage_agent | 2 | `{alert_id, dedup_result, ...}` |
| `ALERT_DISPATCHED` | 告警下发至监管 Agent | triage_agent | triage_agent | 1 | `AlertCoreModel` |
| `ALERT_VERIFIED` | VLM 校验完成 | triage_agent | infra, data_agent, router_agent | 1 | `ViolationEventModel` |
| `VERIFY_COMPLETED` | 二次校验完成 | triage_agent | triage_agent | 2 | `{alert_id, event_id, verify_result, latency_ms}` |
| `VERIFY_FAILED` | 二次校验失败/异常 | triage_agent | triage_agent, infra | 1 | `{alert_id, error_code, error_message, retry_count}` |
| `SQL_GENERATED` | Text-to-SQL 生成完成 | data_agent | data_agent | 2 | `SQLGenerateResult` |
| `SQL_EXECUTED` | SQL 执行完成 | data_agent | data_agent, router_agent | 2 | `DBExecuteResult` |
| `SQL_BLOCKED` | AST 拦截触发 | data_agent | data_agent, router_agent, infra | 1 | `ASTSecurityCheckResult / ASTPerformanceCheckResult` |
| `INTENT_RECOGNIZED` | 意图识别完成 | router_agent | router_agent | 2 | `IntentRecognitionResult` |
| `ROUTE_DISPATCHED` | 路由分发已下发 | router_agent | data_agent, triage_agent | 1 | `{session_id, plan_id, target_agent, intent_type, tool_args}` |
| `ROUTE_COMPLETED` | 路由计划执行完成 | router_agent | infra | 2 | `{session_id, plan_id, execution_status, result_summary}` |
| `ROUTE_FAILED` | 路由计划执行失败 | router_agent | infra | 1 | `{session_id, plan_id, error_code, error_message}` |
| `USER_QUERY_RECEIVED` | 用户查询请求已接收 | infra | router_agent | 1 | `ChatMessageRequest` |
| `USER_CONFIRMED` | 用户确认高危操作 | infra | router_agent | 1 | `{confirmation_id, session_id, user_id, action_type}` |
| `USER_REJECTED` | 用户拒绝高危操作 | infra | router_agent | 1 | `{confirmation_id, session_id, user_id, action_type}` |
| `RECTIFICATION_CREATED` | 整改工单已创建 | triage_agent | data_agent, infra | 2 | `{task_id, event_id, assignee, deadline}` |
| `RECTIFICATION_UPDATED` | 整改状态已更新 | triage_agent | infra | 2 | `{task_id, event_id, old_status, new_status, operator}` |
| `AGENT_HEARTBEAT` | Agent 心跳 | router/data/triage | infra | 5 | `{agent_name, agent_id, status, stats}` |
| `AGENT_ERROR` | Agent 异常报告 | router/data/triage | infra | 1 | `{agent_name, agent_id, error_code, error_message, trace_id}` |
| `SYSTEM_EVENT` | 系统级事件 | infra | router/data/triage | 3 | `{event_name, payload}` |

### 4.3 消费者组配置

```python
MESSAGE_BUS_CONFIG = {
    "stream_topic": "agent_message_bus",
    "consumer_groups": {
        "triage_agent": {
            "group_name": "triage_consumer_group",
            "consumers": ["triage_001", "triage_002"],
        },
        "data_agent": {
            "group_name": "data_consumer_group",
            "consumers": ["data_001", "data_002"],
        },
        "router_agent": {
            "group_name": "router_consumer_group",
            "consumers": ["router_001"],
        },
        "infra": {
            "group_name": "infra_consumer_group",
            "consumers": ["infra_001"],
        },
    },
}
```

### 4.4 错误处理策略

1. **消息处理失败**（回调抛异常）：不发送 ACK，消息留在 PEL 中；其他消费者可通过 XCLAIM 认领（空闲超过 30s 后）
2. **同一消息最多处理 3 次**，超出后转入死信队列 `agent_message_bus_dlq`
3. **消息处理超时**（30 秒）视为失败，不 ACK
4. **死信队列附加字段**：`__fail_count`, `__last_error`, `__failed_agent`

### 4.5 安全要求

1. Redis 认证：生产环境必须配置 `REDIS_PASSWORD`
2. 当前阶段消息不加密（依赖内网隔离）
3. Agent 间通信不校验细粒度权限（信任内网环境）
4. 所有事件发布/消费必须记录 audit log
5. 禁止在消息总线上传递明文密码、API Key
6. 禁止传递前端不应见的敏感数据

---

## 5. 全局错误码总表

| 错误码 | 错误名称 | 所属域 | 典型触发场景 |
|--------|----------|--------|-------------|
| 0000 | SUCCESS | 全局 | 操作成功 |
| 1001 | PARAM_ERROR | 通用参数 | 字段缺失、格式非法、范围越界 |
| 1002 | CONFIG_ERROR | 通用配置 | 配置项缺失、环境变量未设置 |
| 2001 | LLM_CALL_FAILED | 大模型 | 调用超时、网络错误、3次重试后仍失败 |
| 2002 | LLM_RESPONSE_INVALID | 大模型 | 响应格式无法解析、缺少必填字段 |
| 2003 | LLM_FUSE_TRIGGERED | 大模型 | 连续失败达到阈值，熔断器 OPEN |
| 3001 | SQL_SECURITY_BLOCKED | 安全 | AST 拦截到 INSERT/UPDATE/DELETE/DROP |
| 3002 | SQL_PERFORMANCE_BLOCKED | 安全 | AST 拦截到无 WHERE 全表扫描、笛卡尔积 |
| 3003 | PERMISSION_DENIED | 安全权限 | JWT 无效、越权访问、非资源所有者 |
| 4001 | DB_CONNECT_FAILED | 数据库 | 连接超时、认证失败、实例不可用 |
| 4002 | DB_EXECUTE_FAILED | 数据库 | SQL 执行报错、锁超时 |
| 4003 | DB_RESULT_EMPTY | 数据库 | 查询结果为空、ID 不存在 |
| 5001 | AGENT_INIT_FAILED | Agent | Agent 启动失败、依赖初始化失败 |
| 5002 | AGENT_HANDLE_FAILED | Agent | 事件处理异常、内部逻辑错误 |
| 5003 | ROUTE_FAILED | Agent | 路由计划执行失败 |
| 6001 | INTENT_RECOGNITION_FAILED | 路由 | 意图识别置信度不足、无法分类 |
| 6002 | ROUTE_DISPATCH_FAILED | 路由 | 目标 Agent 不可用、消息总线写入失败 |
| 6003 | CONFIRMATION_EXPIRED | 路由 | 二次确认单已过期 |
| 7001 | ALERT_PUSH_FAILED | 监管 | **已废弃**，改用 8002 |
| 7002 | ALERT_DUPLICATE | 监管 | 告警重复推送 |
| 7003 | VLM_VERIFY_FAILED | 监管 | VLM 调用失败、返回格式错误 |
| 8001 | GATEWAY_REQUEST_INVALID | 基建 | X-API-KEY 缺失/无效、multipart 解析失败 |
| 8002 | EDGE_ALERT_PUSH_FAILED | 基建 | 边缘数据格式校验不通过 |
| 8003 | STORAGE_FAILED | 基建 | 截图保存失败、Stream 写入失败 |

---

## 6. 变更记录

| 版本 | 日期 | 变更内容 | 审批人 |
|------|------|----------|--------|
| V1.1 | 2026-05-07 | `ALERT_RECEIVED` 事件 Payload Schema 由 `AlertPushRequest` 调整为 `AlertCoreModel`；网关层直接投递完整告警数据，triage_agent 消费方无需二次查询存储层 | 架构组 |
| V1.0 | 2026-04-27 | 初始版本，合并 alert/chat/event 三类接口契约冻结发布 | 架构组 |
