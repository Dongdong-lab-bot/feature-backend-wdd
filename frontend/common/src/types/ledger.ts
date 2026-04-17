/**
 * 数字化台账系统 - 通用类型定义
 * 此文件定义了台账系统中使用的所有共享类型
 */

// ==================== 枚举类型 ====================

/** 台账状态 */
export enum LedgerStatus {
  DRAFT = 'draft',           // 草稿
  PENDING = 'pending',       // 待审核
  APPROVED = 'approved',     // 已通过
  REJECTED = 'rejected',     // 已驳回
  COMPLETED = 'completed'    // 已完成
}

/** 字段类型 */
export enum FieldType {
  TEXT = 'text',             // 单行文本
  TEXTAREA = 'textarea',     // 多行文本
  NUMBER = 'number',         // 数字
  DATE = 'date',             // 日期
  TIME = 'time',             // 时间
  DATETIME = 'datetime',     // 日期时间
  SELECT = 'select',         // 下拉选择
  CHECKBOX = 'checkbox',     // 复选框
  RADIO = 'radio',           // 单选框
  UPLOAD = 'upload',         // 文件上传
  IMAGE = 'image'            // 图片上传
}

// ==================== 核心数据类型 ====================

/** 台账记录 */
export interface Ledger {
  id: string
  template_id?: string       // 模板ID
  template_name?: string     // 模板名称
  title: string              // 台账标题
  type: string               // 台账类型
  status: LedgerStatus       // 状态
  content?: Record<string, any>  // 台账内容（字段值）
  attachments?: LedgerAttachment[]  // 附件列表
  submit_user_id?: string    // 提交人ID
  submit_user_name?: string  // 提交人姓名
  review_user_id?: string    // 审核人ID
  review_user_name?: string  // 审核人姓名
  review_comment?: string    // 审核意见
  canteen_id?: string        // 食堂ID
  canteen_name?: string      // 食堂名称
  tenant_id?: string         // 租户ID
  created_at?: string        // 创建时间
  updated_at?: string        // 更新时间
  submitted_at?: string      // 提交时间
  reviewed_at?: string       // 审核时间
}

/** 台账附件 */
export interface LedgerAttachment {
  id: string
  filename: string           // 文件名
  url: string                // 文件URL
  size?: number              // 文件大小（字节）
  mime_type?: string         // MIME类型
  uploaded_at?: string       // 上传时间
}

/** 台账模板 */
export interface LedgerTemplate {
  id: string
  name: string               // 模板名称
  type: string               // 模板类型（如：食材采购、卫生检查等）
  description?: string       // 模板描述
  fields: TemplateField[]    // 字段配置
  is_active: boolean         // 是否启用
  sort_order?: number        // 排序序号
  category?: string          // 分类
  tags?: string[]            // 标签
  created_by?: string        // 创建人
  created_at?: string        // 创建时间
  updated_at?: string        // 更新时间
}

/** 模板字段配置 */
export interface TemplateField {
  key: string                // 字段键名（唯一标识）
  label: string              // 字段标签（显示名称）
  type: FieldType            // 字段类型
  required?: boolean         // 是否必填
  placeholder?: string       // 占位符文本
  default_value?: any        // 默认值
  options?: FieldOption[]    // 选项列表（用于select、radio、checkbox）
  validation?: FieldValidation  // 验证规则
  help_text?: string         // 帮助文本
  sort_order?: number        // 字段排序
  visible?: boolean          // 是否可见
  disabled?: boolean         // 是否禁用
}

/** 字段选项 */
export interface FieldOption {
  label: string              // 选项显示文本
  value: any                 // 选项值
  disabled?: boolean         // 是否禁用
}

/** 字段验证规则 */
export interface FieldValidation {
  min?: number               // 最小值/最小长度
  max?: number               // 最大值/最大长度
  pattern?: string           // 正则表达式
  message?: string           // 错误提示信息
  custom?: (value: any) => boolean | string  // 自定义验证函数
}

// ==================== 查询参数类型 ====================

/** 台账查询参数 */
export interface LedgerQuery {
  page: number
  page_size: number
  title?: string             // 标题关键字
  type?: string              // 台账类型
  status?: LedgerStatus      // 状态
  canteen_id?: string        // 食堂ID
  submit_user_id?: string    // 提交人ID
  start_date?: string        // 开始日期
  end_date?: string          // 结束日期
  keyword?: string           // 通用关键字搜索
}

/** 模板查询参数 */
export interface TemplateQuery {
  page: number
  page_size: number
  name?: string              // 模板名称关键字
  type?: string              // 模板类型
  is_active?: boolean        // 是否启用
  category?: string          // 分类
}

// ==================== 响应类型 ====================

/** 分页响应基础类型 */
export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

/** 台账列表响应 */
export interface LedgerListResponse extends PaginationResponse<Ledger> {}

/** 模板列表响应 */
export interface TemplateListResponse extends PaginationResponse<LedgerTemplate> {}

/** 统计数据 */
export interface LedgerStatistics {
  total: number              // 总数
  draft: number              // 草稿数
  pending: number            // 待审核数
  approved: number           // 已通过数
  rejected: number           // 已驳回数
  completed: number          // 已完成数
  today_submitted?: number   // 今日提交数
}

/** 审核操作参数 */
export interface ReviewParams {
  status: 'approved' | 'rejected'
  comment?: string           // 审核意见
}

/** 待办任务 */
export interface PendingTask {
  template_id: string
  template_name: string
  type: string
  due_date?: string          // 截止日期
  description?: string       // 任务描述
  priority?: 'high' | 'medium' | 'low'  // 优先级
}

// ==================== API响应包装类型 ====================

/** 标准API响应 */
export interface ApiResponse<T = any> {
  status: 'success' | 'error'
  data?: T
  message?: string
  code?: number
}

/** 带分页的API响应 */
export interface ApiPaginationResponse<T = any> extends ApiResponse {
  data: {
    list: T[]
    total: number
    page: number
    page_size: number
  }
}
