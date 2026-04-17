import { get, post, put, del } from '@/utils/request'

// ==================== 类型定义 ====================

/** 台账状态枚举 */
export enum LedgerStatus {
  DRAFT = 'draft',           // 草稿
  PENDING = 'pending',       // 待审核
  APPROVED = 'approved',     // 已通过
  REJECTED = 'rejected',     // 已驳回
  COMPLETED = 'completed'    // 已完成
}

/** 台账类型 */
export interface Ledger {
  id: string
  template_id?: string       // 模板ID
  title: string             // 台账标题
  type: string              // 台账类型
  status: LedgerStatus      // 状态
  content?: any             // 台账内容（JSON格式）
  submit_user_id?: string   // 提交人ID
  submit_user_name?: string // 提交人姓名
  review_user_id?: string   // 审核人ID
  review_user_name?: string // 审核人姓名
  review_comment?: string   // 审核意见
  canteen_id?: string       // 食堂ID
  canteen_name?: string     // 食堂名称
  created_at?: string       // 创建时间
  updated_at?: string       // 更新时间
  submitted_at?: string     // 提交时间
  reviewed_at?: string      // 审核时间
}

/** 台账查询参数 */
export interface LedgerQuery {
  page: number
  page_size: number
  title?: string            // 标题模糊查询
  type?: string             // 台账类型
  status?: LedgerStatus     // 状态
  start_date?: string       // 开始日期
  end_date?: string         // 结束日期
}

/** 台账列表响应 */
export interface LedgerListResponse {
  list: Ledger[]
  total: number
  page: number
  page_size: number
}

/** 台账模板类型 */
export interface LedgerTemplate {
  id: string
  name: string              // 模板名称
  type: string              // 模板类型
  description?: string      // 模板描述
  fields: TemplateField[]   // 字段配置
  is_active: boolean        // 是否启用
  sort_order?: number       // 排序
  created_at?: string
  updated_at?: string
}

/** 模板字段配置 */
export interface TemplateField {
  key: string               // 字段键名
  label: string             // 字段标签
  type: 'text' | 'number' | 'date' | 'time' | 'datetime' | 'select' | 'textarea' | 'upload' | 'checkbox'
  required?: boolean        // 是否必填
  placeholder?: string      // 占位符
  options?: Array<{ label: string; value: any }>  // 选项（用于select等）
  validation?: any          // 验证规则
  default_value?: any       // 默认值
}

/** 我的台账统计 */
export interface MyLedgerStatistics {
  total: number             // 总数
  draft: number             // 草稿数
  pending: number           // 待审核数
  approved: number          // 已通过数
  rejected: number          // 已驳回数
  today_submitted: number   // 今日提交数
}

export interface LedgerInstanceRecord {
  id: number
  canteen_id?: number
  status: string
  template_title?: string
  created_at?: string
  create_date?: string
  title?: string
  schema_snapshot?: any
  content?: any
}

export interface LedgerInstanceListData {
  total: number
  page: number
  size: number
  records: LedgerInstanceRecord[]
}

// ==================== 台账记录接口 ====================

/**
 * 获取我的台账列表
 */
export function getMyLedgerList(params: LedgerQuery) {
  return get<LedgerListResponse>('/api/v1/ledger/my', { params })
}

/**
 * 获取台账列表（所有）
 */
export function getLedgerList(params: LedgerQuery) {
  return get<LedgerListResponse>('/api/v1/ledger', { params })
}

/**
 * 获取台账详情
 */
export function getLedgerDetail(id: string) {
  return get<Ledger>(`/api/v1/ledger/${id}`)
}

/**
 * 创建台账（基于模板）
 */
export function createLedger(data: Partial<Ledger>) {
  return post<Ledger>('/api/v1/ledger', data)
}

/**
 * 保存台账草稿
 */
export function saveLedgerDraft(id: string, data: Partial<Ledger>) {
  return put<Ledger>(`/api/v1/ledger/${id}`, data)
}

/**
 * 更新台账
 */
export function updateLedger(id: string, data: Partial<Ledger>) {
  return put<Ledger>(`/api/v1/ledger/${id}`, data)
}

/**
 * 删除台账
 */
export function deleteLedger(id: string) {
  return del(`/api/v1/ledger/${id}`)
}

/**
 * 提交台账（提交审核）
 */
export function submitLedger(id: string) {
  return post(`/api/v1/ledger/${id}/submit`)
}

/**
 * 撤回台账
 */
export function withdrawLedger(id: string) {
  return post(`/api/v1/ledger/${id}/withdraw`)
}

/**
 * 获取我的台账统计数据
 */
export function getMyLedgerStatistics() {
  return get<MyLedgerStatistics>('/api/v1/ledger/my/statistics')
}

/**
 * 获取待填写的台账任务
 */
export function getPendingTasks() {
  return get<Array<{
    template_id: string
    template_name: string
    type: string
    due_date?: string
    description?: string
  }>>('/api/v1/ledger/tasks/pending')
}

/**
 * 获取台账实例任务列表（按后端已注册路由）
 */
export function getLedgerInstances(params: { page: number; size: number; date?: string; status?: string }) {
  return get<LedgerInstanceListData>('/ledger/instances', { params })
}

/**
 * 暂存台账实例（按后端已注册路由）
 */
export function saveLedgerInstanceDraft(id: number, content: Record<string, unknown> = {}) {
  return put(`/ledger/instances/${id}/draft`, { content })
}

/**
 * 提交台账实例（按后端已注册路由）
 */
export function submitLedgerInstance(id: number, content: Record<string, unknown> = {}) {
  return post(`/ledger/instances/${id}/submit`, { content })
}

/**
 * 验签台账实例（按后端已注册路由）
 */
export function verifyLedgerInstance(id: number) {
  return get<{ ledger_id: number; is_valid: boolean }>(`/ledger/instances/${id}/verify`)
}

// ==================== 台账模板接口 ====================

/**
 * 获取启用的台账模板列表
 */
export function getActiveTemplates(params?: { type?: string }) {
  return get<LedgerTemplate[]>('/api/v1/ledger/template/active', { params })
}

/**
 * 获取台账模板详情（用于填写）
 */
export function getTemplateDetail(id: string) {
  return get<LedgerTemplate>(`/api/v1/ledger/template/${id}`)
}

/**
 * 根据模板创建新台账
 */
export function createLedgerFromTemplate(templateId: string, data?: { title?: string }) {
  return post<Ledger>(`/api/v1/ledger/template/${templateId}/create`, data)
}

// ==================== 文件上传接口 ====================

/**
 * 上传台账附件
 */
export function uploadLedgerFile(file: File, ledgerId?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (ledgerId) {
    formData.append('ledger_id', ledgerId)
  }
  return post<{ url: string; filename: string }>('/api/v1/ledger/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除台账附件
 */
export function deleteLedgerFile(fileId: string) {
  return del(`/api/v1/ledger/file/${fileId}`)
}

// ==================== 快捷操作 ====================

/**
 * 快速提交今日台账
 */
export function quickSubmitTodayLedger(data: {
  template_id: string
  content: any
}) {
  return post<Ledger>('/api/v1/ledger/quick-submit', data)
}

/**
 * 复制昨日台账内容
 */
export function copyYesterdayLedger(templateId: string) {
  return get<Ledger>(`/api/v1/ledger/copy-yesterday/${templateId}`)
}
