# 数字化台账 API 接口文档

## 📁 文件结构

```
frontend/
├── common/src/types/
│   ├── ledger.ts          # 共享类型定义
│   └── index.ts           # 类型导出
├── web-admin/src/api/
│   └── ledger.ts          # 监管端台账API
└── web-execution/src/api/
    └── ledger.ts          # 执行端台账API
```

## 🔧 类型定义

共享类型定义位于 `frontend/common/src/types/ledger.ts`，包含：

### 枚举类型
- `LedgerStatus` - 台账状态（草稿、待审核、已通过、已驳回、已完成）
- `FieldType` - 字段类型（文本、数字、日期、选择框、上传等）

### 核心类型
- `Ledger` - 台账记录
- `LedgerTemplate` - 台账模板
- `TemplateField` - 模板字段配置
- `LedgerAttachment` - 台账附件
- `LedgerQuery` - 台账查询参数
- `LedgerStatistics` - 统计数据

## 📋 API 接口规范

### 基础配置

所有API请求都会自动添加以下请求头：
```typescript
{
  'Authorization': `Bearer ${token}`,
  'X-Tenant-ID': tenantId,
  'Content-Type': 'application/json;charset=UTF-8'
}
```

### 响应格式

标准响应格式：
```typescript
{
  "status": "success" | "error",
  "data": any,
  "message": string
}
```

分页响应格式：
```typescript
{
  "list": Array<T>,
  "total": number,
  "page": number,
  "page_size": number
}
```

## 🎯 监管端 API (web-admin)

### 台账记录管理

#### 1. 获取台账列表
```typescript
GET /api/v1/ledger
params: LedgerQuery

getLedgerList(params: LedgerQuery): Promise<LedgerListResponse>
```

#### 2. 获取台账详情
```typescript
GET /api/v1/ledger/{id}

getLedgerDetail(id: string): Promise<Ledger>
```

#### 3. 创建台账
```typescript
POST /api/v1/ledger
body: Partial<Ledger>

createLedger(data: Partial<Ledger>): Promise<Ledger>
```

#### 4. 更新台账
```typescript
PUT /api/v1/ledger/{id}
body: Partial<Ledger>

updateLedger(id: string, data: Partial<Ledger>): Promise<Ledger>
```

#### 5. 删除台账
```typescript
DELETE /api/v1/ledger/{id}

deleteLedger(id: string): Promise<void>
```

#### 6. 批量删除台账
```typescript
POST /api/v1/ledger/batch-delete
body: { ids: string[] }

batchDeleteLedger(ids: string[]): Promise<void>
```

#### 7. 提交台账
```typescript
POST /api/v1/ledger/{id}/submit

submitLedger(id: string): Promise<void>
```

#### 8. 审核台账
```typescript
POST /api/v1/ledger/{id}/review
body: { status: 'approved' | 'rejected', comment?: string }

reviewLedger(id: string, data: ReviewParams): Promise<void>
```

#### 9. 导出台账
```typescript
GET /api/v1/ledger/export
params: LedgerQuery
responseType: 'blob'

exportLedger(params: LedgerQuery): Promise<Blob>
```

#### 10. 获取统计数据
```typescript
GET /api/v1/ledger/statistics
params: { canteen_id?, start_date?, end_date? }

getLedgerStatistics(params?): Promise<LedgerStatistics>
```

### 台账模板管理

#### 1. 获取模板列表
```typescript
GET /api/v1/ledger/template
params: TemplateQuery

getTemplateList(params: TemplateQuery): Promise<TemplateListResponse>
```

#### 2. 获取模板详情
```typescript
GET /api/v1/ledger/template/{id}

getTemplateDetail(id: string): Promise<LedgerTemplate>
```

#### 3. 创建模板
```typescript
POST /api/v1/ledger/template
body: Partial<LedgerTemplate>

createTemplate(data: Partial<LedgerTemplate>): Promise<LedgerTemplate>
```

#### 4. 更新模板
```typescript
PUT /api/v1/ledger/template/{id}
body: Partial<LedgerTemplate>

updateTemplate(id: string, data: Partial<LedgerTemplate>): Promise<LedgerTemplate>
```

#### 5. 删除模板
```typescript
DELETE /api/v1/ledger/template/{id}

deleteTemplate(id: string): Promise<void>
```

#### 6. 启用/禁用模板
```typescript
PUT /api/v1/ledger/template/{id}/status
body: { is_active: boolean }

toggleTemplateStatus(id: string, is_active: boolean): Promise<void>
```

#### 7. 获取所有启用的模板
```typescript
GET /api/v1/ledger/template/active

getActiveTemplates(): Promise<LedgerTemplate[]>
```

#### 8. 复制模板
```typescript
POST /api/v1/ledger/template/{id}/copy
body: { name: string }

copyTemplate(id: string, name: string): Promise<LedgerTemplate>
```

## 🏃 执行端 API (web-execution)

### 台账记录操作

#### 1. 获取我的台账列表
```typescript
GET /api/v1/ledger/my
params: LedgerQuery

getMyLedgerList(params: LedgerQuery): Promise<LedgerListResponse>
```

#### 2. 获取台账列表（所有）
```typescript
GET /api/v1/ledger
params: LedgerQuery

getLedgerList(params: LedgerQuery): Promise<LedgerListResponse>
```

#### 3. 获取台账详情
```typescript
GET /api/v1/ledger/{id}

getLedgerDetail(id: string): Promise<Ledger>
```

#### 4. 创建台账
```typescript
POST /api/v1/ledger
body: Partial<Ledger>

createLedger(data: Partial<Ledger>): Promise<Ledger>
```

#### 5. 保存草稿
```typescript
PUT /api/v1/ledger/{id}
body: Partial<Ledger>

saveLedgerDraft(id: string, data: Partial<Ledger>): Promise<Ledger>
```

#### 6. 提交台账
```typescript
POST /api/v1/ledger/{id}/submit

submitLedger(id: string): Promise<void>
```

#### 7. 撤回台账
```typescript
POST /api/v1/ledger/{id}/withdraw

withdrawLedger(id: string): Promise<void>
```

#### 8. 删除台账
```typescript
DELETE /api/v1/ledger/{id}

deleteLedger(id: string): Promise<void>
```

#### 9. 获取我的统计数据
```typescript
GET /api/v1/ledger/my/statistics

getMyLedgerStatistics(): Promise<MyLedgerStatistics>
```

#### 10. 获取待填写任务
```typescript
GET /api/v1/ledger/tasks/pending

getPendingTasks(): Promise<PendingTask[]>
```

### 模板操作

#### 1. 获取启用的模板列表
```typescript
GET /api/v1/ledger/template/active
params: { type?: string }

getActiveTemplates(params?): Promise<LedgerTemplate[]>
```

#### 2. 获取模板详情
```typescript
GET /api/v1/ledger/template/{id}

getTemplateDetail(id: string): Promise<LedgerTemplate>
```

#### 3. 根据模板创建台账
```typescript
POST /api/v1/ledger/template/{templateId}/create
body: { title?: string }

createLedgerFromTemplate(templateId: string, data?): Promise<Ledger>
```

### 文件操作

#### 1. 上传附件
```typescript
POST /api/v1/ledger/upload
Content-Type: multipart/form-data
body: FormData { file: File, ledger_id?: string }

uploadLedgerFile(file: File, ledgerId?: string): Promise<{ url: string, filename: string }>
```

#### 2. 删除附件
```typescript
DELETE /api/v1/ledger/file/{fileId}

deleteLedgerFile(fileId: string): Promise<void>
```

### 快捷操作

#### 1. 快速提交今日台账
```typescript
POST /api/v1/ledger/quick-submit
body: { template_id: string, content: any }

quickSubmitTodayLedger(data): Promise<Ledger>
```

#### 2. 复制昨日台账
```typescript
GET /api/v1/ledger/copy-yesterday/{templateId}

copyYesterdayLedger(templateId: string): Promise<Ledger>
```

## 💡 使用示例

### 执行端：提交台账

```typescript
import { createLedger, submitLedger } from '@/api/ledger'
import { LedgerStatus } from '@common/types'

// 1. 创建台账草稿
const ledger = await createLedger({
  template_id: 'template_123',
  title: '今日食材采购台账',
  content: {
    supplier: '供应商A',
    items: ['蔬菜', '肉类'],
    total_amount: 1500
  }
})

// 2. 提交审核
await submitLedger(ledger.id)
```

### 监管端：审核台账

```typescript
import { getLedgerList, reviewLedger } from '@/api/ledger'
import { LedgerStatus } from '@common/types'

// 1. 获取待审核台账
const result = await getLedgerList({
  page: 1,
  page_size: 10,
  status: LedgerStatus.PENDING
})

// 2. 审核通过
await reviewLedger(result.list[0].id, {
  status: 'approved',
  comment: '符合要求，审核通过'
})
```

### 监管端：创建模板

```typescript
import { createTemplate } from '@/api/ledger'
import { FieldType } from '@common/types'

const template = await createTemplate({
  name: '食材采购台账',
  type: 'procurement',
  fields: [
    {
      key: 'date',
      label: '采购日期',
      type: FieldType.DATE,
      required: true
    },
    {
      key: 'supplier',
      label: '供应商',
      type: FieldType.TEXT,
      required: true
    },
    {
      key: 'amount',
      label: '总金额',
      type: FieldType.NUMBER,
      required: true,
      validation: {
        min: 0,
        message: '金额不能为负数'
      }
    }
  ],
  is_active: true
})
```

## ⚠️ 注意事项

1. **权限控制**：所有API调用都需要有效的JWT Token
2. **租户隔离**：通过 X-Tenant-ID 请求头实现多租户数据隔离
3. **错误处理**：API调用失败时会自动显示错误提示，无需手动处理
4. **文件上传**：上传文件时需要使用 FormData 格式
5. **日期格式**：所有日期使用 ISO 8601 格式（YYYY-MM-DDTHH:mm:ss）
6. **分页参数**：page 从 1 开始，page_size 建议范围 10-100

## 🔄 后端对接要求

后端需要实现以上所有API接口，并遵循以下规范：

1. **路径规范**：使用 `/api/v1/ledger` 作为基础路径
2. **HTTP方法**：GET(查询)、POST(创建)、PUT(更新)、DELETE(删除)
3. **状态码**：成功返回200，创建成功返回201，错误返回4xx/5xx
4. **响应格式**：统一使用标准响应格式
5. **权限控制**：根据用户角色控制不同操作权限
6. **数据验证**：服务端必须进行完整的数据验证

## 📝 更新日志

- 2026-03-01: 创建初始版本，实现完整的台账API接口定义
