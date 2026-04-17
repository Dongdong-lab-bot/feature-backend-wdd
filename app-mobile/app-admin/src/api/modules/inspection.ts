import { request } from '../request/client'

export type InspectionModule = 'daily' | 'weekly' | 'joint'

export type InspectionTaskListParams = {
  status?: string
  keyword?: string
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
}

export type InspectionTaskItem = {
  task_id: string
  id?: string | number
  canteen_name?: string
  submitter_name?: string
  template_name?: string
  completion_progress?: string
  total_score?: number
  submission_date?: string
  status?: string
  status_text?: string
}

export type InspectionTaskListData = {
  total: number
  list: InspectionTaskItem[]
}

export type DailyTaskInfo = {
  task_id: number
  canteen_name?: string
  inspector_name?: string
  inspector_id?: string
  actual_start_time?: string
  submission_date?: string
  status?: string
  status_text?: string
}

export type DailyTaskFormItem = {
  item_id: string
  content?: string
  result_id?: number
  is_qualified?: boolean
  description?: string
  photos?: string[]
}

export type DailyTaskDetailData = {
  task_info: DailyTaskInfo
  form_snapshot: DailyTaskFormItem[]
  audit_logs?: Array<Record<string, any>>
}

export type DailyTaskAuditPayload = {
  auditor_id: string
  action: 'PASS' | 'REJECT'
  opinion: string
}

export type DailyTaskAuditData = {
  task_id: number
  status: string
}

export type WeeklyTaskInfo = {
  task_id: number
  canteen_name?: string
  inspector_name?: string
  actual_start_time?: string
  submission_date?: string
  status?: string
  status_text?: string
  total_score?: number
  red_line_issues?: number
  last_audit_opinion?: string
  last_audit_time?: string
}

export type WeeklyTaskMinorItem = {
  item_id: string
  result_id?: number
  content?: string
  issue_type?: string
  total_score?: number
  scoring_options?: number[]
  score_given?: number
  inspection_description?: string
  inspection_photos?: string[]
  rectification_description?: string
  rectification_photos?: string[]
}

export type WeeklyTaskFormSnapshot = {
  form_type?: string
  major_items?: Array<{
    title?: string
    minor_items?: WeeklyTaskMinorItem[]
  }>
}

export type WeeklyTaskDetailData = {
  task_info: WeeklyTaskInfo
  form_snapshot: WeeklyTaskFormSnapshot
  audit_logs?: Array<Record<string, any>>
}

export type WeeklyTaskAuditPayload = {
  auditor_id: string
  action: 'PASS' | 'REJECT'
  opinion: string
}

export type WeeklyTaskAuditData = {
  task_id: number
  status: string
}

const listPathMap: Record<InspectionModule, string> = {
  daily: '/daily-controls/tasks',
  weekly: '/weekly-inspections/tasks',
  joint: '/joint-inspections/tasks'
}

export const getInspectionTasks = async (moduleName: InspectionModule, params: InspectionTaskListParams) => {
  return request<InspectionTaskListData>({
    path: listPathMap[moduleName],
    method: 'GET',
    params
  })
}

export type DailyTaskSubmitItem = {
  item_id: string
  is_qualified: boolean
  description?: string
  photos?: string[]
}

export type DailyTaskSubmitPayload = {
  submitter_id: string
  actual_start_time: string
  results: DailyTaskSubmitItem[]
}

export const getDailyTaskDetail = async (taskId: string | number) => {
  return request<DailyTaskDetailData>({
    path: `/daily-controls/tasks/${taskId}`,
    method: 'GET'
  })
}

export const auditDailyTask = async (taskId: string | number, payload: DailyTaskAuditPayload) => {
  return request<any>({
    path: `/daily-controls/tasks/${taskId}/audit`,
    method: 'POST',
    data: payload
  })
}

export const submitDailyTask = async (taskId: string | number, payload: DailyTaskSubmitPayload) => {
  return request<any>({
    path: `/daily-controls/tasks/${taskId}/submit`,
    method: 'POST',
    data: payload
  })
}

export const getWeeklyTaskDetail = async (taskId: string | number) => {
  return request<WeeklyTaskDetailData>({
    path: `/weekly-inspections/tasks/${taskId}`,
    method: 'GET'
  })
}

export const getJointTaskDetail = async (taskId: string | number) => {
  return request<any>({
    path: `/joint-inspections/tasks/${taskId}`,
    method: 'GET'
  })
}

export const auditWeeklyTask = async (taskId: string | number, payload: WeeklyTaskAuditPayload) => {
  return request<WeeklyTaskAuditData>({
    path: `/weekly-inspections/tasks/${taskId}/audit`,
    method: 'POST',
    data: payload
  })
}

export const auditJointTask = async (taskId: string | number, payload: WeeklyTaskAuditPayload) => {
  return request<WeeklyTaskAuditData>({
    path: `/joint-inspections/tasks/${taskId}/audit`,
    method: 'POST',
    data: payload
  })
}
