# 巡检状态机与 Outbox 对接说明

**日期**：2026-03-05

## 1. 状态机定义
**负责人**：张子昊

### 1.1 状态枚举 `InspectionStatus`
*   PENDING
*   SUBMITTED
*   REJECTED
*   RECTIFIED
*   COMPLETED

### 1.2 动作枚举 `InspectionAction`
*   SUBMIT
*   PASS
*   REJECT
*   RECTIFY
*   SIGN
*   SYSTEM_COMPLETE

### 1.3 表驱动流转矩阵
```python
ALLOWED_TRANSITIONS = {
    PENDING: {SUBMIT: SUBMITTED},
    SUBMITTED: {PASS: COMPLETED, REJECT: REJECTED, SYSTEM_COMPLETE: COMPLETED},
    REJECTED: {RECTIFY: RECTIFIED},
    RECTIFIED: {PASS: COMPLETED, REJECT: REJECTED},
}
```
*禁止 if-else 硬编码；新增动作需更新枚举 + 矩阵。*

## 2. Outbox 事件规范
**负责人**：张子昊 / 李文钊

### 2.1 表字段（核心）
*   `aggregate_type`: 固定 `INSPECTION`
*   `aggregate_id`: `inspection id`
*   `event_type`: `STATUS_CHANGED` / `SNAPSHOT_TAKEN` / `AUDIT_REJECT` 等
*   `payload`: JSON
*   `status`: `PENDING` / `PROCESSING` / `DONE` / `FAILED`
*   `retry_count` / `next_retry_at`

### 2.2 Payload 示例
```json
{
    "id": 1001,
    "old": "SUBMITTED",
    "new": "COMPLETED",
    "action": "SYSTEM_COMPLETE",
    "extra": {
        "reason": "all_participants_signed"
    }
}
```

## 3. 关键接口

### 3.1 状态流转
*   **POST** `/inspection/{inspection_id}/transit`
*   body: `{ "action": "SUBMIT", "remark": "..." }`

### 3.2 联合巡检签字
*   **POST** `/inspection/{inspection_id}/sign`
*   说明：签字后若所有参与人均完成，系统触发 `SYSTEM_COMPLETE`。

### 3.3 摄像头绑定（管理员）
*   **POST/GET/PUT/DELETE** `/inspection/camera-links`

### 3.4 巡检实例摄像头注入
*   **GET** `/inspection/instances/{instance_id}/camera-bindings`
*   返回：`field_id` + `camera_id` + `stream_urls`

### 3.5 抓拍证据
*   **POST** `/inspection/instances/{instance_id}/capture`
*   body: `{ "field_id": "...", "camera_id": "...", "snapshot_reason": "..." }`

## 4. 联合巡检汇聚规则
*   `SIGN` 动作触发时，系统锁定主表与参与人表。
*   若全部参与人 `SIGNED`，自动触发 `SYSTEM_COMPLETE`，并写入 Outbox。

## 5. 对接注意事项
*   需按 Outbox 状态机消费，并实现幂等。（负责人：李文钊）
*   若未配置摄像头绑定，接口返回 `bindings: []`。（负责人：张子昊/麦锦涛）

## 6. 与张子昊对接清单（补充）
1.  **Action 枚举边界**：参与人更新、整改、审核均需通过 `WorkflowService.transit` 驱动。
2.  **Payload 约定**：审核驳回的 payload 需包含整改建议与证据快照引用。
3.  **整改触发**：提交整改应触发 `RECTIFY` 动作。
4.  **摄像头**：直播流地址与抓拍目前为“占位对接”，仅做 URL 拼接。