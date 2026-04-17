import { get, post, put, del } from '@/utils/request'

export type InspectionStatus = 'PENDING' | 'SUBMITTED' | 'REJECTED' | 'RECTIFIED' | 'COMPLETED'
export type InspectionAction = 'SUBMIT' | 'PASS' | 'REJECT' | 'RECTIFY' | 'SIGN' | 'SYSTEM_COMPLETE'
export type EvidenceSource = 'USER_UPLOAD' | 'CAMERA_CAPTURE'

export interface InspectionBaseInfo {
  id: number
  status: InspectionStatus
  type: string
}

export interface CameraConfig {
  camera_id: number
  camera_name: string
  stream_url: string
  allow_capture: boolean
}

export interface CameraBindingItem {
  field_id: string
  camera_id: number
  camera_name: string
  stream_urls: {
    hls?: string
    flv?: string
    [key: string]: string | undefined
  }
  allow_capture: boolean
}

export interface InspectionDetail {
  base_info: InspectionBaseInfo
  camera_configs: Record<string, CameraConfig>
  submission: {
    items: InspectionSubmitItem[]
  }
  rectification_logs: Array<Record<string, unknown>>
  current_round_no: number
}

export interface EvidenceMetaValue {
  source: EvidenceSource
  camera_id?: number
  capture_time?: string
}

export interface InspectionSubmitItem {
  item_id: string
  result: boolean
  issue_desc?: string
  photos: string[]
  evidence_meta?: Record<string, EvidenceMetaValue>
}

export interface RectifyPayload {
  verify_round: number
  rectify_desc: string
  rectify_photos: string[]
  evidence_meta?: Record<string, EvidenceMetaValue>
}

export interface AuditPayload {
  action: 'PASS' | 'REJECT'
  opinion?: string
}

export interface CapturePayload {
  field_id: string
  camera_id: number
}

export interface CaptureResult {
  image_url: string
  capture_time: string
}

export interface ParticipantsProgress {
  is_completed: boolean
  participants: Array<{
    user_name: string
    status: string
  }>
}

export interface CameraLinkPayload {
  template_id: number
  field_id: string
  camera_id: number
  camera_name: string
}

export interface CameraLinkRecord extends CameraLinkPayload {
  id: number
}

export function buildIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function getInspectionDetail(id: number) {
  return get<InspectionDetail>(`/inspection/instances/${id}`)
}

export function getInspectionCameraBindings(id: number) {
  return get<CameraBindingItem[]>(`/inspection/instances/${id}/camera-bindings`)
}

export function captureInspectionPhoto(id: number, payload: CapturePayload) {
  return post<CaptureResult>(`/inspection/instances/${id}/capture`, payload)
}

export function submitInspection(id: number, items: InspectionSubmitItem[], signatureImage: string, idempotencyKey?: string) {
  return post(
    `/inspection/instances/${id}/submit`,
    { items, signature_image: signatureImage },
    {
      headers: {
        'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
      }
    }
  )
}

export function transitInspectionStatus(id: number, payload: { action: InspectionAction; remark?: string }, idempotencyKey?: string) {
  return post(
    `/inspection/instances/${id}/transit`,
    payload,
    {
      headers: {
        'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
      }
    }
  )
}

export function rectifyInspection(id: number, payload: RectifyPayload, idempotencyKey?: string) {
  return post(
    `/inspection/instances/${id}/rectify`,
    payload,
    {
      headers: {
        'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
      }
    }
  )
}

export function auditInspection(id: number, payload: AuditPayload, idempotencyKey?: string) {
  return post(
    `/inspection/instances/${id}/audit`,
    payload,
    {
      headers: {
        'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
      }
    }
  )
}

export function getInspectionParticipants(id: number) {
  return get<ParticipantsProgress>(`/inspection/instances/${id}/participants`)
}

export function signInspection(id: number, signatureImage: string, idempotencyKey?: string) {
  return post(
    `/inspection/instances/${id}/sign`,
    { signature_image: signatureImage },
    {
      headers: {
        'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
      }
    }
  )
}

export function generateInspectionReport(inspectionId: number) {
  return post('/inspection/reports/generate', { inspection_id: inspectionId }, { responseType: 'blob' })
}

export function getInspectionMonthlyReports(month: string) {
  return get('/monthly-reports', { params: { month } })
}

// ==================== 通用查询参数类型 ====================

export interface InspectionTaskQuery {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  status?: string
  keyword?: string
}

// ==================== 日管控 ====================

export interface DailyTaskItem {
  task_id: number
  template_id: number | null
  canteen_name: string
  submitter_name: string
  template_name: string | null
  completion_progress: string | null
  submission_date: string | null
  status: string
  status_text: string
}

export function getDailyControlTasks(params: InspectionTaskQuery = {}) {
  return get<{ total: number; list: DailyTaskItem[] }>('/daily-controls/tasks', { params })
}

export function getDailyControlTaskDetail(taskId: number) {
  return get(`/daily-controls/tasks/${taskId}`)
}

export function submitDailyControlTask(taskId: number, payload: Record<string, unknown>, idempotencyKey?: string) {
  return post(`/daily-controls/tasks/${taskId}/submit`, payload, {
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

export function rectifyDailyControlTask(taskId: number, payload: Record<string, unknown>, idempotencyKey?: string) {
  return post(`/daily-controls/tasks/${taskId}/rectify`, payload, {
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

export interface DailyTemplateItem {
  id: number
  template_name: string
  is_active: boolean
  start_time: string | null
  end_time: string | null
}

export function getDailyControlTemplates(params?: { page?: number; page_size?: number }) {
  return get<{ total: number; list: DailyTemplateItem[] }>('/daily-controls/templates', { params: { page: 1, page_size: 100, ...params } })
}

export function getDailyControlTemplateDetail(templateId: number) {
  return get(`/daily-controls/templates/${templateId}`)
}

export function startDailyControlTask(templateId: number) {
  return post<{ task_id: number; status: string }>('/daily-controls/tasks/start', { template_id: templateId })
}

// ==================== 周排查 ====================

export interface WeeklyTaskItem {
  task_id: number
  canteen_name: string
  executor_name: string
  template_name: string | null
  total_score: number | null
  red_line_issues: number | null
  red_line_count: number | null
  yellow_line_count: number | null
  submission_date: string | null
  business_date: string | null
  status: string
  status_text: string
}

export function getWeeklyInspectionTasks(params: InspectionTaskQuery = {}) {
  return get<{ total: number; list: WeeklyTaskItem[] }>('/weekly-inspections/tasks', { params })
}

export function getWeeklyInspectionTaskDetail(taskId: number) {
  return get(`/weekly-inspections/tasks/${taskId}`)
}

export function submitWeeklyReport(
  taskId: number,
  payload: { inspector_id: string; actual_start_time: string; results: Array<{ item_id: number; score_given: number; description?: string; photos?: string[] }> },
  idempotencyKey?: string
) {
  return post(`/weekly-inspections/tasks/${taskId}/submit`, payload, {
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

export function submitWeeklyInspectionTask(taskId: number, payload: Record<string, unknown>, idempotencyKey?: string) {
  return post(`/weekly-inspections/tasks/${taskId}/rectify`, payload, {
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

// ==================== 月调度报告 ====================

export interface MonthlyReportItem {
  id: number
  title: string
  canteen_name: string
  reporter_name: string
  report_time: string | null
  source_type: string
}

export function getMonthlyReports(params: { page?: number; page_size?: number; start_date?: string; end_date?: string; canteen_id?: number } = {}) {
  return get<{ total: number; list: MonthlyReportItem[] }>('/monthly-reports', { params })
}

// ==================== 联合巡检 ====================

export interface JointTaskQuery {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  status?: string
  keyword?: string
}

export function getJointInspectionTasks(params: JointTaskQuery = {}) {
  return get('/joint-inspections/tasks', { params })
}

export function getJointInspectionTaskDetail(taskId: number) {
  return get(`/joint-inspections/tasks/${taskId}`)
}

export function rectifyJointInspectionTask(taskId: number, payload: Record<string, unknown>, idempotencyKey?: string) {
  return post(`/joint-inspections/tasks/${taskId}/rectify`, payload, {
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

export function createCameraLink(payload: CameraLinkPayload) {
  return post<CameraLinkRecord>('/inspection/camera-links', payload)
}

export function getCameraLinks(templateId: number) {
  return get<CameraLinkRecord[]>('/inspection/camera-links', { params: { template_id: templateId } })
}

export function updateCameraLink(linkId: number, payload: Partial<CameraLinkPayload>) {
  return put<CameraLinkRecord>(`/inspection/camera-links/${linkId}`, payload)
}

export function deleteCameraLink(linkId: number) {
  return del(`/inspection/camera-links/${linkId}`)
}
