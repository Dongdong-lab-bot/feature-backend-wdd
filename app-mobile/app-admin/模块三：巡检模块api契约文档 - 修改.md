# 📘 智慧食安 - 巡检业务流程 API 契约 (V1.0.0 核心版)

**适用端**: 监管端 Web/App、执行端 Web/App
**接口风格**: RESTful + 统一响应结构
**依赖说明**: 本模块依赖【台账模块】的基础数据，包含但不限于区域、食堂、人员等数据。

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
| **40401** | 路由匹配失败 | 提示“未知的巡检类型，无法匹配审核流” |

### 0.3 时间与幂等
* **时间**: 统一使用 **UTC ISO8601** (e.g., `2026-03-05T12:00:00Z`)。
* **幂等**: 提交类接口强制要求 Header 携带 `Idempotency-Key: uuid`，防止重复提交。

### 0.4 外部模块依赖
*   **组织与食堂层级树**: 本模块强依赖【用户中心/台账模块】提供的组织与食堂层级树接口。
    *   **响应**: 返回标准的树状结构，每个节点包含 `id`, `name`, `children`。

---

## 1️⃣ 核心枚举与流程图 (Enums & Flow)

### 核心字典字典配置
* **`inspection_type` (巡检类型)**: 
  * `DAILY` (日管控)
  * `WEEKLY` (周排查)
  * `JOINT` (联合巡检)
* **`status` (业务状态)**: 
  * `PENDING` (待上报 / 待签字)
  * `SUBMITTED` (已上报，待审核)
  * `REJECTED` (审核驳回，待整改)
  * `RECTIFIED` (已整改，待复审)
  * `COMPLETED` (已完成)

### 状态流转图 (State Diagram)
> 💡 注：不同 `inspection_type` 会动态路由到不同的审核流节点，但基础状态机保持一致。

```mermaid
stateDiagram-v2
    [*] --> PENDING: 模板下发/定时生成

    state 执行端操作 {
        PENDING --> SUBMITTED: 填报并提交
        REJECTED --> RECTIFIED: 提交整改 (携带当前版本号)
    }

    state 监管端审核 {
        SUBMITTED --> COMPLETED: 审核通过
        SUBMITTED --> REJECTED: 审核驳回
        RECTIFIED --> COMPLETED: 复审通过
        RECTIFIED --> REJECTED: 复审驳回
    }

    state 联合巡检专属 {
        PENDING --> COMPLETED: 参与多方全部签字完成 (系统自动闭环)
    }
```

### 图片来源 (EvidenceSource)

用于在提交时标记照片来源，确保证据链权威性。

*   `USER_UPLOAD`: 用户相册上传
*   `CAMERA_CAPTURE`: 用户实时拍摄

---

## 模块一：日管控 (`/daily-controls`)

> **业务核心**: 由**执行端（食堂）**发起自查自报，**监管端**进行审核与驳回的闭环流程。

### 1.1 模板管理 (监管端 Web)

*   **`GET /daily-controls/templates`**: 获取日管控模板列表。
*   **`POST /daily-controls/templates`**: 创建新的日管控模板。
*   **`GET /daily-controls/templates/{id}`**: 获取单个模板详情。
*   **`PUT /daily-controls/templates/{id}`**: 更新指定模板。
*   **`PATCH /daily-controls/templates/{id}/status`**: 快速启用/禁用模板。
*   **`DELETE /daily-controls/templates/{id}`**: 删除指定模板。

**[POST/PUT] Request Body 示例**:
```json
{
  "template_name": "幼儿园晨检日管控表",
  "executor_role": "FOOD_SAFETY_DIRECTOR",
  "approver_role": "SUPERVISOR",
  "target_node_ids": ["region_1", "canteen_102"],
  // 【UI对应】检查表覆盖范围。可以同时包含父节点ID和子节点ID。
  // 后端逻辑:
  // 1. 接收到 ID 列表。
  // 2. 遍历 ID，如果 ID 是一个区域 (e.g., "region_1")，
  //    则递归查询该区域下的所有末端食堂。
  // 3. 将所有食堂ID去重后，存入数据库关联关系中。
  "start_time": "06:00",
  "end_time": "20:00",
  "items": [
    {
      "sort_order": 1,                // 排序号 (对应UI的 1, 2, 3...)
      "content": "检查员工健康证是否在有效期内",
      "completion_method": "PHOTO_REQUIRED" // 【UI对应】完成方式枚举
      // 枚举值定义:
      // CONFIRM_ONLY: 仅确认 (打勾/单选是与否)
      // PHOTO_REQUIRED: 必须拍照 (强制要求上传图片)
      // INPUT_REQUIRED: 必须填报 (强制要求输入文本说明)
    }
  ]
}
```

### 1.2 任务工作流

#### `GET /daily-controls/tasks` - 获取日管控任务列表
**场景**: 用于渲染“日管控记录”列表页面。

**Query Params**:
*   `start_date` (可选): `2026-01-12`
*   `end_date` (可选): `2026-02-23`
*   `status` (可选): `PENDING_AUDIT` (待审核), `PENDING_RECTIFICATION` (待整改), `COMPLETED` (已完成) 等
*   `keyword` (可选): 用于按食堂或提交人搜索
*   `page`, `page_size`

**Response**:
```json
{
  "total": 30,
  "list": [
    {
      "task_id": "daily-123",
      "canteen_name": "武尚一中一食堂", // 【UI对应】提交食堂
      "submitter_name": "张三",          // 【UI对应】提交人
      "template_name": "高中日管控检查表",// 【UI对应】提交表格
      "completion_progress": "25/25", // 【UI对应】日管控完成项
      "submission_date": "2020-05-24",// 【UI对应】提交日期
      "status": "PENDING_AUDIT",      // 【UI对应】状态
      "status_text": "待审核"          // 状态文本
    }
  ]
}
```

#### `GET /daily-controls/tasks/{id}` - 获取单条日管控任务详情
**场景**:
*   在“日管控记录”列表页点击“查看”按钮。
*   监管端审核此任务时加载数据。

**Response**:
```json
{
  "task_info": {
    "task_id": "daily-123",
    "canteen_name": "武尚一中一食堂",
    "inspector_name": "食品安全员", // 提交人
    "actual_start_time": "2026-01-20T09:30:00Z", // 实际开始时间
    "submission_date": "2026-01-20T11:00:00Z",
    "status": "PENDING_AUDIT"
  },
  "form_snapshot": [ // 表单的结构和用户提交的结果
    {
      "item_id": "uuid-item-daily-1",
      "content": "每日完成晨检，人员人数及身体要求达标",
      // --- 用户提交的数据 ---
      "is_qualified": false,
      "description": "晨检发现张三体温异常，已安排其离岗休息。",
      "photos": ["https://.../photo.jpg"]
    },
    {
      "item_id": "uuid-item-daily-2",
      "content": "每日完成留样，早中晚已完成留样并达标",
      // --- 用户提交的数据 ---
      "is_qualified": true,
      "description": "早餐留样20类，中餐留样40类...",
      "photos": ["https://.../photo2.jpg"]
    }
  ],
  "audit_logs": [ /* 完整的审核与整改历史 */ ]
}
```

#### `POST /daily-controls/tasks/{id}/submit` - 食堂端提交自查
**Request Body**:
```json
{
  "submitter_id": "user-canteen-liuneng",
  "actual_start_time": "2026-01-20T09:30:00Z",
  "results": [
    {
      "item_id": "uuid-item-daily-1", 
      "is_qualified": false,        // 【UI对应】true: 完成且合格, false: 未完成
      "description": "早餐留样仅18类，未达到20类标准", // 【UI对应】请输入的文本框
      "photos": ["https://.../photo.jpg"]        // 【UI对应】“+”号上传的照片
    },
    {
      "item_id": "uuid-item-daily-2",
      "is_qualified": true,
      "description": null,
      "photos": ["https://.../photo.jpg"]
    }
  ]
}
```

#### `POST /daily-controls/tasks/{id}/audit` - 监管端审核
**Request Body**:
```json
{
  "auditor_id": "user-regulator-zhaosi",
  "action": "REJECT", // PASS (通过) | REJECT (驳回)
  "opinion": "补办健康证需要提供回执照片作为凭证，请补充。"
}
```

#### `POST /daily-controls/tasks/{id}/rectify` - 食堂端提交整改
**Request Body**:
```json
{
  "rectifier_id": "user-canteen-liuneng",
  "feedback_per_item": [ // 允许针对每个问题项进行反馈
    {
      "result_id": "uuid-result-1", // 关联到具体的问题结果
      "description": "已上传张三办理新健康证的回执照片。",
      "photos": ["https://.../receipt.jpg"]
    }
  ]
}
```

---

## 模块二：周排查 (`/weekly-inspections`)

> **业务核心**: 由**监管端**发起线下检查并打分，指派给**执行端（食堂）**进行整改，**监管端**对整改结果进行审核的闭环流程。

### 2.1 模板管理 (监管端 Web)

*   `GET /weekly-inspections/templates`
*   `POST /weekly-inspections/templates`
*   `GET /weekly-inspections/templates/{id}`
*   `PUT /weekly-inspections/templates/{id}`
*   `PATCH /weekly-inspections/templates/{id}/status`
*   `DELETE /weekly-inspections/templates/{id}`

**[POST/PUT] Request Body 示例 (复杂层级模型)**:
```json
{
  "template_name": "学校食堂春季食品安全周排查表",
  "executor_role": "FOOD_SAFETY_DIRECTOR",
  "approver_role": "SUPERVISOR",
  "target_node_ids": ["region_1", "canteen_102"],
  "start_time": "06:00",
  "end_time": "20:00",
  "form_type": "SCORE_BASED", // 表格类型: 选分表
  "major_items": [
    {
      "title": "食材问题排查",
      "minor_items": [
        {
          "content": "食堂无三无、腐烂、过期食材",
          "issue_type": "RED_LINE",     // 问题类型：红黄蓝线
          "total_score": 6,             // 总分
          "scoring_options": [6, 3, 0]  // 打分项
        }
      ]
    }
  ]
}
```

### 2.2 任务工作流

#### `GET /weekly-inspections/tasks` - 获取周排查任务列表
**场景**: 用于渲染“周排查记录”列表页面。

**Query Params**:
*   `start_date`, `end_date`, `status`, `keyword`, `page`, `page_size`

**Response**:
```json
{
  "total": 25,
  "list": [
    {
      "task_id": "weekly-456",
      "canteen_name": "武尚实验中学一食堂",// 【UI对应】提交食堂
      "submitter_name": "李四",          // 【UI对应】提交人 (这里指监管员)
      "template_name": "初中周排查检查表",// 【UI对应】提交表格
      "total_score": 89,              // 【UI对应】检查分数
      "red_line_issues": 0,           // 【UI对应】红线问题
      "submission_date": "2020-05-24",// 【UI对应】提交日期
      "status": "PENDING_AUDIT",      // 【UI对应】状态
      "status_text": "已改待审"
    }
  ]
}
```

#### `GET /weekly-inspections/tasks/{id}` - 获取单条周排查任务详情
**场景**:
*   在“周排查记录”列表页点击“查看”或“编辑”按钮。
*   食堂端查看需要整改的项。
*   监管端审核整改结果。

**Response**:
```json
{
  "task_info": {
    "task_id": "weekly-456",
    "canteen_name": "武尚实验中学一食堂",
    "inspector_name": "李四",
    "actual_start_time": "2026-01-20T09:30:00Z",
    "submission_date": "2026-01-20T11:00:00Z",
    "status": "PENDING_AUDIT",
    "total_score": 89,
    "red_line_issues": 0
  },
  "form_snapshot": {
    "form_type": "SCORE_BASED",
    "major_items": [
      {
        "title": "食材问题排查",
        "minor_items": [
          {
            "item_id": "uuid-item-weekly-1",
            "result_id": "uuid-result-weekly-1", // 本条检查结果ID，供整改接口使用
            "content": "食堂无三无、腐烂、过期食材",
            "issue_type": "RED_LINE",
            "total_score": 6,
            "scoring_options": [6, 3, 0],
            "score_given": 3,
            "inspection_description": "发现生鲜食材上有发芽情况",
            "inspection_photos": ["https://.../photo1.jpg"],
            "rectification_description": "已将发芽土豆全部销毁并重新采购",
            "rectification_photos": ["https://.../rectify1.jpg"]
          }
        ]
      }
    ]
  },
  "audit_logs": []
}
```

#### `POST /weekly-inspections/tasks/{id}/submit` - 监管端提交检查结果
**Request Body**:
```json
{
  "inspector_id": "user-regulator-zhangsan",
  "actual_start_time": "2026-01-20T09:30:00Z",
  "results": [
    {
      "item_id": "uuid-item-weekly-1",
      "score_given": 3, // 实际得分
      "description": "发现生鲜食材上有发芽情况",
      "photos": ["https://.../photo1.jpg"]
    }
  ]
}
```

#### `POST /weekly-inspections/tasks/{id}/rectify` - 食堂端提交整改
**Request Body**:
```json
{
  "rectifier_id": "user-canteen-wangwu",
  "feedback_per_item": [
    {
      "result_id": "uuid-result-weekly-1",
      "description": "已将发芽土豆全部销毁并重新采购",
      "photos": ["https://.../rectify1.jpg"]
    }
  ]
}
```

#### `POST /weekly-inspections/tasks/{id}/audit` - 监管端审核整改
**Request Body**:
```json
{
  "auditor_id": "user-regulator-zhangsan",
  "action": "PASS", // PASS (通过) | REJECT (驳回)
  "opinion": "整改到位，同意归档"
}
```

---

## 模块三：联合巡检 (`/joint-inspections`)

> **业务核心**: 流程与**周排查**高度相似，但强调**多部门协同**。建议后端复用周排查的状态机和大部分逻辑，仅在参与人管理上做特殊处理。

*   **模板管理**: `POST /joint-inspections/templates` 等 (结构复用周排查模板)
*   **任务提交流程**: `POST /joint-inspections/tasks/{id}/submit` 等 (复用周排查流程)
*   **专属接口**: `POST /joint-inspections/tasks/{id}/sign` - **协同签字**
  **Request Body**:
    {
      "signature_image": "data:image/png;base64,iVBORw0KG...", // 建议使用Base64或上传后返回URL
    }

---

## 模块四：月调度报告 (`/monthly-reports`)

> **业务核心**: 独立的报告生成工具，数据源于已完成的日管控和周排查记录。

### `POST /monthly-reports/preview` - 生成报告预览
**Request Body**:
```json
{
  "title": "2026年1月武尚一中月调度报告",
  "reporter_id": "user-director-wang",      // 【UI对应】报告人 (新增)
  "report_date": "2026-01-31",
  "attendees": ["张三", "李四"],             // 【UI对应】月调度参会人员
  "data_sources": {
    "daily": {
      "start_date": "2026-01-01", "end_date": "2026-01-31",
      "target_node_ids": ["canteen_101"]
    },
    "weekly": {
      "start_date": "2026-01-01", "end_date": "2026-01-31",
      "target_node_ids": ["canteen_101"]
    }
  }
}
```
**Response**: 返回用于前端渲染的 Markdown 或结构化 JSON。

### `POST /monthly-reports/export` - 导出报告文件
*接收与 `/preview` 接口**完全相同**的请求体，但直接返回 PDF 或 Word 文件流。*

---
