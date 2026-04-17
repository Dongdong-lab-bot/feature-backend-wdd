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
  canteen_id?: string       // 食堂ID
  start_date?: string       // 开始日期
  end_date?: string         // 结束日期
  submit_user_id?: string   // 提交人ID
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

/** 台账模板查询参数 */
export interface TemplateQuery {
  page: number
  page_size: number
  name?: string
  type?: string
  is_active?: boolean
}

/** 台账统计数据 */
export interface LedgerStatistics {
  total: number             // 总数
  draft: number             // 草稿数
  pending: number           // 待审核数
  approved: number          // 已通过数
  rejected: number          // 已驳回数
  completed: number         // 已完成数
}

// ==================== 台账记录接口 ====================

/**
 * 获取台账列表
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
 * 创建台账
 */
export function createLedger(data: Partial<Ledger>) {
  return post<Ledger>('/api/v1/ledger', data)
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
 * 批量删除台账
 */
export function batchDeleteLedger(ids: string[]) {
  return post('/api/v1/ledger/batch-delete', { ids })
}

/**
 * 提交台账（提交审核）
 */
export function submitLedger(id: string) {
  return post(`/api/v1/ledger/${id}/submit`)
}

/**
 * 审核台账
 */
export function reviewLedger(id: string, data: { status: 'approved' | 'rejected'; comment?: string }) {
  return post(`/api/v1/ledger/${id}/review`, data)
}

/**
 * 导出台账
 */
export function exportLedger(params: LedgerQuery) {
  return get('/api/v1/ledger/export', { 
    params,
    responseType: 'blob'
  })
}

/**
 * 获取台账统计数据
 */
export function getLedgerStatistics(params?: { canteen_id?: string; start_date?: string; end_date?: string }) {
  return get<LedgerStatistics>('/api/v1/ledger/statistics', { params })
}

// ==================== 台账模板接口 ====================

/**
 * 获取台账模板列表
 */
export function getTemplateList(params: TemplateQuery) {
  return get<{ list: LedgerTemplate[]; total: number }>('/api/v1/ledger/template', { params })
}

/**
 * 获取台账模板详情
 */
export function getTemplateDetail(id: string) {
  return get<LedgerTemplate>(`/api/v1/ledger/template/${id}`)
}

/**
 * 创建台账模板
 */
export function createTemplate(data: Partial<LedgerTemplate>) {
  return post<LedgerTemplate>('/api/v1/ledger/template', data)
}

/**
 * 更新台账模板
 */
export function updateTemplate(id: string, data: Partial<LedgerTemplate>) {
  return put<LedgerTemplate>(`/api/v1/ledger/template/${id}`, data)
}

/**
 * 删除台账模板
 */
export function deleteTemplate(id: string) {
  return del(`/api/v1/ledger/template/${id}`)
}

/**
 * 启用/禁用模板
 */
export function toggleTemplateStatus(id: string, is_active: boolean) {
  return put(`/api/v1/ledger/template/${id}/status`, { is_active })
}

/**
 * 获取所有启用的模板（下拉选择用）
 */
export function getActiveTemplates() {
  return get<LedgerTemplate[]>('/api/v1/ledger/template/active')
}

/**
 * 复制模板
 */
export function copyTemplate(id: string, name: string) {
  return post<LedgerTemplate>(`/api/v1/ledger/template/${id}/copy`, { name })
}
