# 📘 智慧食安 - 巡检业务流程 API 契约

**适用端**: 监管端 Web/App、执行端 Web/App
**接口风格**: RESTful + 统一响应结构

---

## 0️⃣ 全局规范 (Global Specs)

### 0.1 统一响应结构

```json
{
  "code": 20000,
  "message": "success",
  "data": {},
  "request_id": "trace-abc123"
}
```

### 0.2 核心业务状态码

| code | 说明 | 处理建议 |
| :--- | :--- | :--- |
| **20000** | 成功 | - |
| **40009** | 状态非法 | 提示“当前状态不允许执行此操作”，刷新列表 |
| **40901** | 并发冲突 | 提示“整改版本已更新”，强制刷新页面 |
| **50002** | 抓拍失败 | 提示“摄像头连接超时或离线” |

### 0.3 时间与幂等

*   **时间**: 统一使用 **UTC ISO8601** (e.g., `2026-03-05T12:00:00Z`)。
*   **幂等**: 提交类接口支持 Header `Idempotency-Key: uuid`。

---

## 1️⃣ 核心枚举与流程图 (Enums & Flow)

### 1.1 状态流转图 (State Diagram)

前端请依据此图理解 `status` 变化逻辑。

```mermaid
stateDiagram-v2
    [*] --> PENDING: 每日自动生成

    state 执行端操作 {
        PENDING --> SUBMITTED: 提交/填报
        REJECTED --> RECTIFIED: 提交整改 (版本追加)
    }

    state 监管端审核 {
        SUBMITTED --> COMPLETED: 审核通过
        SUBMITTED --> REJECTED: 审核驳回
        RECTIFIED --> COMPLETED: 复审通过
        RECTIFIED --> REJECTED: 复审驳回
    }

    state 联合巡检 {
        PENDING --> COMPLETED: 所有参与人签字汇聚 (系统自动流转)
    }
```

### 1.2 证据来源 (EvidenceSource)

用于在提交时标记照片来源，确保证据链权威性。

*   `USER_UPLOAD`: 用户相册上传
*   `CAMERA_CAPTURE`: 系统视频抓拍

---

## 2️⃣ 巡检任务执行 (Execution)

### 2.1 获取巡检详情 (含摄像头配置)

**GET** `/inspection/instances/{id}`

**场景**: 巡检员打开表单，系统自动加载对应的摄像头画面。

**响应数据**:

```json
{
  "code": 20000,
  "data": {
    "base_info": { "id": 1001, "status": "PENDING", "type": "DAILY" },
    // 1. 题目与摄像头关联配置 (V3.7 新增)
    // 前端需根据此配置，在对应题目旁渲染播放器
    "camera_configs": {
      "item_kitchen_01": {
        "camera_id": 105,
        "camera_name": "后厨1号",
        "stream_url": "http://media-server.../hls/t_1001_c_105.m3u8",
        "allow_capture": true
      }
    },
    "submission": { "items": [] }, // 已填内容
    "rectification_logs": [], // 整改历史
    "current_round_no": 0 // 乐观锁版本
  }
}
```

### 2.2 视频抓拍 (Capture) [V3.7 新增]

**POST** `/inspection/instances/{id}/capture`

**场景**: 巡检员点击播放器上的“抓拍”按钮。

**Request Body**:

```json
{
  "field_id": "item_kitchen_01", // 针对哪道题抓拍
  "camera_id": 105
}
```

**Response**:

```json
{
  "code": 20000,
  "data": {
    "image_url": "https://oss.../capture_20260305_1200.jpg",
    "capture_time": "2026-03-05T12:00:00Z"
  }
}
```

### 2.3 提交/填报 (Submit)

**POST** `/inspection/instances/{id}/submit`

**场景**: 提交巡检结果，需携带证据元数据。

**Request Body**:

```json
{
  "items": [
    {
      "item_id": "item_kitchen_01",
      "result": false,
      "issue_desc": "地面有积水",
      "photos": [
        "https://oss.../capture_20260305_1200.jpg", // 抓拍图
        "https://oss.../manual_upload.jpg" // 手机拍图
      ],
      // [V3.7 新增] 证据元数据，用于审计
      "evidence_meta": {
        "https://oss.../capture_20260305_1200.jpg": {
          "source": "CAMERA_CAPTURE",
          "camera_id": 105,
          "capture_time": "..."
        }
      }
    }
  ],
  "signature_image": "https://oss..."
}
```

### 2.4 状态流转 (Transit)

**POST** `/inspection/instances/{id}/transit`

**场景**: 统一的状态机入口，所有状态变更必须走该接口。

**Request Body**:

```json
{
  "action": "SUBMIT", // SUBMIT/PASS/REJECT/RECTIFY/SIGN/SYSTEM_COMPLETE
  "remark": "..."
}
```

---

## 3️⃣ 整改与闭环 (Rectification)

### 3.1 提交整改 (带乐观锁)

**POST** `/inspection/instances/{id}/rectify`

**Request Body**:

```json
{
  "verify_round": 1, // 必须等于 current_round_no
  "rectify_desc": "已清理完毕",
  "rectify_photos": ["..."],
  // 整改也可以包含抓拍证据
  "evidence_meta": { ... }
}
```

### 3.2 审核 (Audit)

**POST** `/inspection/instances/{id}/audit`

**Request Body**:

```json
{
  "action": "PASS", // 或 REJECT
  "opinion": "同意归档"
}
```

---

## 4️⃣ 联合巡检 (Joint Inspection)

### 4.1 获取进度

**GET** `/inspection/instances/{id}/participants`

**响应**:

```json
{
  "code": 20000,
  "data": {
    "is_completed": false, // 主状态是否完成
    "participants": [
      { "user_name": "市监局-张三", "status": "SIGNED" },
      { "user_name": "教育局-李四", "status": "PENDING" }
    ]
  }
}
```

### 4.2 签字

**POST** `/inspection/instances/{id}/sign`

*(参数同提交接口，只需传签名图)*

---

## 5️⃣ 报表与导出 (Report)

### 5.1 生成 PDF 报告

**POST** `/inspection/reports/generate`

**Request**: `{ "inspection_id": 1001 }`
**Response**: PDF 文件流。

### 5.2 获取月报快照

**GET** `/inspection/monthly-reports?month=2026-03`

---

## 6️⃣ 摄像头配置 (Camera Binding)

### 6.1 管理端摄像头绑定 CRUD

**POST** `/inspection/camera-links`

**Request Body**:

```json
{
  "template_id": 10,
  "field_id": "item_kitchen_01",
  "camera_id": 105,
  "camera_name": "后厨1号"
}
```

*   **GET** `/inspection/camera-links?template_id=10`
*   **PUT** `/inspection/camera-links/{link_id}`
*   **DELETE** `/inspection/camera-links/{link_id}`

### 6.2 巡检实例摄像头注入

**GET** `/inspection/instances/{id}/camera-bindings`

**Response**:

```json
{
  "code": 20000,
  "data": [
    {
      "field_id": "item_kitchen_01",
      "camera_id": 105,
      "camera_name": "后厨1号",
      "stream_urls": {
        "hls": "http://media.../hls/xxx.m3u8",
        "flv": "http://media.../flv/xxx.flv"
      },
      "allow_capture": true
    }
  ]
}
```

### 6.3 视频能力占位说明

*   当前视频流与抓拍仅为“占位对接”，返回 URL 为拼接结果。
*   `stream_urls` 与抓拍能力待海康云眸/第三方 SDK 接入后替换为真实能力。

---

## 💡 给前端开发的关键提示

1.  **视频播放器渲染逻辑**：
    *   在遍历渲染表单项（items）时，检查 `data.camera_configs` 中是否存在当前 `item_id` 的配置。
    *   如果存在，**必须**在题目下方渲染 `<VideoPlayer>` 组件，并传入 `stream_url`。
    *   如果 `allow_capture` 为 true，播放器右下角需显示 **[📷 抓拍]** 按钮。

2.  **整改冲突处理**：
    *   在调用 `/rectify` 接口时，务必捕获 `40901` 状态码。
    *   交互建议：弹窗提示“当前整改记录已被更新，请点击确定刷新页面”，点击后重新调用详情接口。

3.  **列表状态颜色**：
    *   PENDING : 🔵 蓝色 (待办)
    *   REJECTED : 🔴 红色 (急需处理)
    *   SUBMITTED : 🟠 橙色 (等待中)
    *   COMPLETED : 🟢 绿色 (已完成)