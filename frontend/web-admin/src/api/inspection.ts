import request from '@/utils/request'

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

export interface InspectionSubmitItem {
  item_id: string
  result: boolean
  issue_desc?: string
  photos: string[]
  evidence_meta?: Record<string, {
    source: EvidenceSource
    camera_id?: number
    capture_time?: string
  }>
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

export interface RectifyPayload {
  verify_round: number
  rectify_desc: string
  rectify_photos: string[]
  evidence_meta?: Record<string, {
    source: EvidenceSource
    camera_id?: number
    capture_time?: string
  }>
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
  return request<InspectionDetail>({
    url: `/inspection/instances/${id}`,
    method: 'get'
  })
}

export function getInspectionCameraBindings(id: number) {
  return request<CameraBindingItem[]>({
    url: `/inspection/instances/${id}/camera-bindings`,
    method: 'get'
  })
}

export function captureInspectionPhoto(id: number, payload: { field_id: string; camera_id: number }) {
  return request<{ image_url: string; capture_time: string }>({
    url: `/inspection/instances/${id}/capture`,
    method: 'post',
    data: payload
  })
}

export function submitInspection(id: number, items: InspectionSubmitItem[], signatureImage: string, idempotencyKey?: string) {
  return request({
    url: `/inspection/instances/${id}/submit`,
    method: 'post',
    data: {
      items,
      signature_image: signatureImage
    },
    headers: {
      'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
    }
  })
}

export function transitInspectionStatus(id: number, payload: { action: InspectionAction; remark?: string }, idempotencyKey?: string) {
  return request({
    url: `/inspection/instances/${id}/transit`,
    method: 'post',
    data: payload,
    headers: {
      'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
    }
  })
}

export function rectifyInspection(id: number, payload: RectifyPayload, idempotencyKey?: string) {
  return request({
    url: `/inspection/instances/${id}/rectify`,
    method: 'post',
    data: payload,
    headers: {
      'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
    }
  })
}

export function auditInspection(id: number, payload: { action: 'PASS' | 'REJECT'; opinion?: string }, idempotencyKey?: string) {
  return request({
    url: `/inspection/instances/${id}/audit`,
    method: 'post',
    data: payload,
    headers: {
      'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
    }
  })
}

export function getInspectionParticipants(id: number) {
  return request<ParticipantsProgress>({
    url: `/inspection/instances/${id}/participants`,
    method: 'get'
  })
}

export function signInspection(id: number, signatureImage: string, idempotencyKey?: string) {
  return request({
    url: `/inspection/instances/${id}/sign`,
    method: 'post',
    data: { signature_image: signatureImage },
    headers: {
      'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
    }
  })
}

export function generateInspectionReport(inspectionId: number) {
  return request({
    url: '/inspection/reports/generate',
    method: 'post',
    data: { inspection_id: inspectionId },
    responseType: 'blob'
  })
}

export function getInspectionMonthlyReports(month: string) {
  return request({
    url: '/inspection/monthly-reports',
    method: 'get',
    params: { month }
  })
}

export function createCameraLink(payload: CameraLinkPayload) {
  return request<CameraLinkRecord>({
    url: '/inspection/camera-links',
    method: 'post',
    data: payload
  })
}

export function getCameraLinks(templateId: number) {
  return request<CameraLinkRecord[]>({
    url: '/inspection/camera-links',
    method: 'get',
    params: { template_id: templateId }
  })
}

export function updateCameraLink(linkId: number, payload: Partial<CameraLinkPayload>) {
  return request<CameraLinkRecord>({
    url: `/inspection/camera-links/${linkId}`,
    method: 'put',
    data: payload
  })
}

export function deleteCameraLink(linkId: number) {
  return request({
    url: `/inspection/camera-links/${linkId}`,
    method: 'delete'
  })
}

export function auditWeeklyTask(
  taskId: number,
  payload: {
    auditor_id: string
    action: 'PASS' | 'REJECT'
    opinion?: string
    item_scores?: { result_id: number; score: number }[]
  },
  idempotencyKey?: string
) {
  return request({
    url: `/weekly-inspections/tasks/${taskId}/audit`,
    method: 'post',
    data: payload,
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

export function auditDailyTask(
  taskId: number,
  payload: { auditor_id: string; action: 'PASS' | 'REJECT'; opinion?: string },
  idempotencyKey?: string
) {
  return request({
    url: `/daily-controls/tasks/${taskId}/audit`,
    method: 'post',
    data: payload,
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}

export function auditJointTask(
  taskId: number,
  payload: { auditor_id: string; action: 'PASS' | 'REJECT'; opinion?: string },
  idempotencyKey?: string
) {
  return request({
    url: `/joint-inspections/tasks/${taskId}/audit`,
    method: 'post',
    data: payload,
    headers: { 'Idempotency-Key': idempotencyKey || buildIdempotencyKey() }
  })
}
