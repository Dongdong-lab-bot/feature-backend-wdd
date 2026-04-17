import request from '@/utils/request'

export interface OrgTreeNode {
  id: number
  name: string
  type: 'AREA' | 'SCHOOL' | 'CANTEEN'
  parentId?: number | null
  children?: OrgTreeNode[]
}

export interface AdminDeptRecord {
  id: number
  name: string
  parent_id?: number | null
  org_type: 'AREA' | 'SCHOOL' | 'CANTEEN'
  tenant_id?: number
  created_at?: string | null
}

export interface LedgerInstanceRecord {
  id: number
  canteen_id?: number | null
  status?: string
  created_at?: string
}

export interface LedgerTemplateRecord {
  id: number
  name: string
  description?: string | null
  is_active: number
  created_at?: string
}

export interface CompilationReportRecord {
  completion_rate: number
  total_tasks: number
  completed_tasks: number
  status_stats: Record<string, number>
}

export interface LedgerTemplateCreatePayload {
  name?: string
  title?: string
  description?: string
  schema: {
    version: string
    fields: Array<{
      field_id: string
      type: string
      label: string
      required?: boolean
      placeholder?: string
      [key: string]: any
    }>
  }
}

export interface DailyTemplateItemPayload {
  sort_order: number
  content: string
  completion_method?: 'CONFIRM_ONLY' | 'PHOTO_REQUIRED' | 'INPUT_REQUIRED'
}

export interface DailyTemplateCreatePayload {
  template_name: string
  executor_role?: string
  approver_role?: string
  target_node_ids: number[]
  start_time?: string
  end_time?: string
  items: DailyTemplateItemPayload[]
}

export interface DailyTemplateRecord {
  id: number
  template_name: string
  executor_role?: string
  approver_role?: string
  start_time?: string
  end_time?: string
  is_active?: boolean
  target_node_ids?: number[]
}

export interface DailyTemplateDetail {
  id: number
  template_name: string
  executor_role?: string
  approver_role?: string
  start_time?: string
  end_time?: string
  target_node_ids: number[]
  items: Array<{
    item_id: number
    sort_order: number
    content: string
    completion_method?: 'CONFIRM_ONLY' | 'PHOTO_REQUIRED' | 'INPUT_REQUIRED'
    is_active?: boolean
  }>
}

export function getOrgTree() {
  return request<{ tree: OrgTreeNode[] }>({
    url: '/org/tree',
    method: 'get'
  })
}

export function getAllDepts() {
  return request<{ records: AdminDeptRecord[]; total: number }>({
    url: '/admin/depts',
    method: 'get',
    params: { page: 1, size: 1000 }
  })
}

export function createCanteenOrg(data: { name: string; parent_id?: number | null }) {
  return request<{ id: number; name: string }>({
    url: '/admin/depts',
    method: 'post',
    data: {
      name: data.name,
      parent_id: data.parent_id ?? null,
      org_type: 'CANTEEN'
    }
  })
}

export function updateCanteenOrg(id: number, data: { name: string; parent_id?: number | null }) {
  return request<{ id: number; name: string }>({
    url: `/admin/depts/${id}`,
    method: 'put',
    data: {
      name: data.name,
      parent_id: data.parent_id ?? null,
      org_type: 'CANTEEN'
    }
  })
}

export function deleteCanteenOrg(id: number) {
  return request<{ id: number }>({
    url: `/admin/depts/${id}`,
    method: 'delete'
  })
}

export function uploadLicenseImage(file: File, description?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (description) {
    formData.append('description', description)
  }

  return request<{
    success: boolean
    message: string
    data?: { filename: string; url: string }
  }>({
    url: '/images/license/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function getLedgerInstanceList(params?: { page?: number; size?: number; status?: string; date?: string }) {
  return request<{ total: number; page: number; size: number; records: LedgerInstanceRecord[] }>({
    url: '/ledger/instances',
    method: 'get',
    params: {
      page: params?.page ?? 1,
      size: params?.size ?? 50,
      status: params?.status,
      date: params?.date
    }
  })
}

export function verifyLedgerInstance(id: number) {
  return request<{ ledger_id: number; is_valid: boolean }>({
    url: `/ledger/instances/${id}/verify`,
    method: 'get'
  })
}

export function getLedgerTemplateList(params?: { page?: number; size?: number }) {
  return request<{ total: number; page: number; size: number; records: LedgerTemplateRecord[] }>({
    url: '/ledger/templates',
    method: 'get',
    params: {
      page: params?.page ?? 1,
      size: params?.size ?? 100
    }
  })
}

export function createLedgerTemplate(data: LedgerTemplateCreatePayload) {
  return request<{ id: number; name: string }>({
    url: '/ledger/templates',
    method: 'post',
    data: {
      title: data.title ?? data.name,
      description: data.description,
      schema: data.schema
    }
  })
}

export function updateLedgerTemplate(id: number, data: Partial<LedgerTemplateCreatePayload>) {
  return request<{ id: number }>({
    url: `/ledger/templates/${id}`,
    method: 'put',
    data: {
      title: data.title ?? data.name,
      description: data.description,
      schema: data.schema
    }
  })
}

export function deleteLedgerTemplate(id: number) {
  return request<null>({
    url: `/ledger/templates/${id}`,
    method: 'delete'
  })
}

export function getDailyTemplateList(params?: { page?: number; page_size?: number }) {
  return request<{ total: number; list: DailyTemplateRecord[] }>({
    url: '/daily-controls/templates',
    method: 'get',
    params: {
      page: params?.page ?? 1,
      page_size: params?.page_size ?? 100
    }
  })
}

export function createDailyTemplate(data: DailyTemplateCreatePayload) {
  return request<{ id: number }>({
    url: '/daily-controls/templates',
    method: 'post',
    data
  })
}

export function getDailyTemplateDetail(templateId: number) {
  return request<DailyTemplateDetail>({
    url: `/daily-controls/templates/${templateId}`,
    method: 'get'
  })
}

export function updateDailyTemplate(templateId: number, data: DailyTemplateCreatePayload) {
  return request<{ id: number }>({
    url: `/daily-controls/templates/${templateId}`,
    method: 'put',
    data
  })
}

export function toggleDailyTemplateStatus(templateId: number, isActive: boolean) {
  return request<{ id: number; is_active: boolean }>({
    url: `/daily-controls/templates/${templateId}/status`,
    method: 'patch',
    data: { is_active: isActive }
  })
}

export function deleteDailyTemplate(templateId: number) {
  return request<null>({
    url: `/daily-controls/templates/${templateId}`,
    method: 'delete'
  })
}

// ============ 周排查模板 & 任务 ============

export interface WeeklyTemplateMinorItemPayload {
  sort_order?: number
  content: string
  issue_type?: string
  total_score?: number
  scoring_options?: number[]
}

export interface WeeklyTemplateMajorItemPayload {
  sort_order?: number
  title: string
  minor_items: WeeklyTemplateMinorItemPayload[]
}

export interface WeeklyTemplateCreatePayload {
  template_name: string
  executor_role?: string
  approver_role?: string
  target_node_ids: number[]
  start_time?: string
  end_time?: string
  form_type?: string
  major_items: WeeklyTemplateMajorItemPayload[]
}

export function getWeeklyTemplateList(params?: { page?: number; page_size?: number }) {
  return request<{ total: number; list: DailyTemplateRecord[] }>({
    url: '/weekly-inspections/templates',
    method: 'get',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 100 }
  })
}

export function createWeeklyTemplate(data: WeeklyTemplateCreatePayload) {
  return request<{ id: number }>({
    url: '/weekly-inspections/templates',
    method: 'post',
    data
  })
}

export function getWeeklyTemplateDetail(templateId: number) {
  return request({
    url: `/weekly-inspections/templates/${templateId}`,
    method: 'get'
  })
}

export function updateWeeklyTemplate(templateId: number, data: WeeklyTemplateCreatePayload) {
  return request<{ id: number }>({
    url: `/weekly-inspections/templates/${templateId}`,
    method: 'put',
    data
  })
}

export function deleteWeeklyTemplate(templateId: number) {
  return request({
    url: `/weekly-inspections/templates/${templateId}`,
    method: 'delete'
  })
}

export function dispatchWeeklyTemplate(data: {
  template_id: number
  business_date: string
  canteen_ids: number[]
  form_snapshot?: object
}) {
  return request<{ created: number[]; skipped: number[] }>({
    url: '/weekly-inspections/tasks/dispatch',
    method: 'post',
    data
  })
}

export function getWeeklyTaskList(params?: {
  page?: number
  page_size?: number
  status?: string
  start_date?: string
  end_date?: string
  keyword?: string
}) {
  return request<{ total: number; list: unknown[] }>({
    url: '/weekly-inspections/tasks',
    method: 'get',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 100, ...params }
  })
}

export function deleteWeeklyTask(taskId: number) {
  return request({
    url: `/weekly-inspections/tasks/${taskId}`,
    method: 'delete'
  })
}

// ============ 联合巡检模板 & 任务 ============

export function getJointTemplateList(params?: { page?: number; page_size?: number }) {
  return request<{ total: number; list: DailyTemplateRecord[] }>({
    url: '/joint-inspections/templates',
    method: 'get',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 100 }
  })
}

export function createJointTemplate(data: WeeklyTemplateCreatePayload) {
  return request<{ id: number }>({
    url: '/joint-inspections/templates',
    method: 'post',
    data
  })
}

export function getJointTemplateDetail(templateId: number) {
  return request({
    url: `/joint-inspections/templates/${templateId}`,
    method: 'get'
  })
}

export function updateJointTemplate(templateId: number, data: WeeklyTemplateCreatePayload) {
  return request<{ id: number }>({
    url: `/joint-inspections/templates/${templateId}`,
    method: 'put',
    data
  })
}

export function deleteJointTemplate(templateId: number) {
  return request({
    url: `/joint-inspections/templates/${templateId}`,
    method: 'delete'
  })
}

export function getJointTaskList(params?: {
  page?: number
  page_size?: number
  status?: string
  start_date?: string
  end_date?: string
  keyword?: string
}) {
  return request<{ total: number; list: unknown[] }>({
    url: '/joint-inspections/tasks',
    method: 'get',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 100, ...params }
  })
}

export function getJointTaskDetail(taskId: number) {
  return request<{
    task_info: {
      task_id: number
      canteen_name: string
      inspector_name: string
      submission_date: string | null
      status: string
      status_text: string
      total_score: number | null
      red_line_issues: number
    }
    form_snapshot: Record<string, unknown> | null
    audit_logs: unknown[]
  }>({
    url: `/joint-inspections/tasks/${taskId}`,
    method: 'get'
  })
}

export function getCompilationReport(params: {
  start_date: string
  end_date: string
  canteen_id?: number
  task_type?: string
}) {
  return request<CompilationReportRecord>({
    url: '/report/compilation',
    method: 'get',
    params
  })
}

export function listMonthlyReports(params?: {
  start_date?: string
  end_date?: string
  canteen_id?: number
  page?: number
  page_size?: number
}) {
  return request<{ total: number; records: any[] }>({
    url: '/monthly-reports',
    method: 'get',
    params: { page: 1, page_size: 20, ...params }
  })
}

export function previewMonthlyReport(data: {
  start_date: string
  end_date: string
  data_sources: number[]
}) {
  return request<any>({
    url: '/monthly-reports/preview',
    method: 'post',
    data
  })
}

export function exportMonthlyReport(data: {
  start_date: string
  end_date: string
  data_sources: number[]
  export_format?: string
}) {
  return request({
    url: '/monthly-reports/export',
    method: 'post',
    data: { export_format: 'docx', ...data },
    responseType: 'blob'
  })
}

export function uploadOfflineMonthlyReport(data: {
  title: string
  canteen_id: number
  remark?: string
}) {
  return request<{ id: number }>({
    url: '/monthly-reports/offline-upload',
    method: 'post',
    data
  })
}

export function deleteMonthlyReport(reportId: number) {
  return request({
    url: `/monthly-reports/${reportId}`,
    method: 'delete'
  })
}

export function getDailyTaskList(params?: {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  status?: string
  keyword?: string
}) {
  return request<{ total: number; list: unknown[] }>({
    url: '/daily-controls/tasks',
    method: 'get',
    params: { page: params?.page ?? 1, page_size: params?.page_size ?? 100, ...params }
  })
}

export function getDailyTaskDetail(taskId: number) {
  return request<{
    task_info: {
      task_id: number
      canteen_name: string
      inspector_name: string
      submission_date: string | null
      status: string
      status_text: string
    }
    form_snapshot: unknown[] | null
    audit_logs: unknown[]
  }>({
    url: `/daily-controls/tasks/${taskId}`,
    method: 'get'
  })
}

export function getWeeklyTaskDetail(taskId: number) {
  return request<{
    task_info: {
      task_id: number
      canteen_name: string
      inspector_name: string
      submission_date: string | null
      status: string
      status_text: string
      total_score: number | null
      red_line_issues: number
    }
    form_snapshot: Record<string, unknown> | null
    audit_logs: unknown[]
  }>({
    url: `/weekly-inspections/tasks/${taskId}`,
    method: 'get'
  })
}

export function updateWeeklyTaskSnapshot(taskId: number, formSnapshot: object) {
  return request({
    url: `/weekly-inspections/tasks/${taskId}/snapshot`,
    method: 'patch',
    data: { form_snapshot: formSnapshot }
  })
}
