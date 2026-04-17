import { get, post } from '@/utils/request'

export type VideoTaskStatus = 'PENDING' | 'SUBMITTED' | 'REJECTED' | 'RECTIFIED' | 'COMPLETED'

export interface VideoCameraTreeNode {
  id: number | string
  name: string
  type: string
  parentId?: number | string | null
  cameraId?: string
  children?: VideoCameraTreeNode[]
}

export interface VideoTaskListParams {
  start_date?: string
  end_date?: string
  status?: VideoTaskStatus
  keyword?: string
  page: number
  page_size: number
}

export interface VideoTaskListItem {
  task_id: number
  canteen_name: string
  submitter_name: string
  template_name?: string | null
  total_score?: number | null
  red_line_issues?: number | null
  submission_date?: string | null
  status: VideoTaskStatus
  status_text: string
}

export interface VideoTaskListResponse {
  total: number
  list: VideoTaskListItem[]
}

export interface VideoTaskInfo {
  task_id: number
  canteen_name: string
  inspector_name: string
  actual_start_time?: string | null
  submission_date?: string | null
  status: VideoTaskStatus
  status_text: string
  total_score?: number | null
  red_line_issues?: number | null
}

export interface VideoMinorItem {
  item_id: string
  result_id?: number
  content: string
  issue_type?: string
  total_score?: number
  scoring_options?: number[]
  score_given?: number | null
  inspection_description?: string | null
  inspection_photos?: string[]
  rectification_description?: string | null
  rectification_photos?: string[]
}

export interface VideoMajorItem {
  title: string
  minor_items: VideoMinorItem[]
}

export interface VideoTaskDetailResponse {
  task_info: VideoTaskInfo
  form_snapshot?: {
    form_type?: string
    major_items?: VideoMajorItem[]
  }
  audit_logs: Array<Record<string, unknown>>
}

export interface RectifyFeedbackItem {
  result_id: number
  description: string
  photos: string[]
}

export interface VideoRectifyPayload {
  rectifier_id: string
  feedback_per_item: RectifyFeedbackItem[]
}

export interface HikvisionPlayParamsRequest {
  cameraId: string | number
  action: 'preview' | 'playback'
  begin?: string
  end?: string
}

export interface HikvisionPlayParamsResponse {
  uikitAccessToken?: string
  oauthToken?: string
  deviceSerial: string
  channelNo: string
  begin?: string
  end?: string
  validCode?: string
}

export interface CameraCaptureRequest {
  image_base64: string
  timestamp: string
}

export interface CameraCaptureResponse {
  evidence_id: string
  url: string
}

function buildIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function getVideoCameraTree() {
  return get<{ tree: VideoCameraTreeNode[] }>('/video/cameras/tree')
}

export function getVideoInspectionTasks(params: VideoTaskListParams) {
  return get<VideoTaskListResponse>('/video-inspections/tasks', { params })
}

export function getVideoInspectionTaskDetail(taskId: number) {
  return get<VideoTaskDetailResponse>(`/video-inspections/tasks/${taskId}`)
}

export function rectifyVideoInspectionTask(taskId: number, payload: VideoRectifyPayload, idempotencyKey?: string) {
  return post(
    `/video-inspections/tasks/${taskId}/rectify`,
    payload,
    {
      headers: {
        'Idempotency-Key': idempotencyKey || buildIdempotencyKey()
      }
    }
  )
}

export function getHikvisionPlayParams(data: HikvisionPlayParamsRequest) {
  return post<HikvisionPlayParamsResponse>('/api/v1/video/hikvision/play-params', data)
}

export function captureCameraFrame(cameraId: string | number, data: CameraCaptureRequest) {
  return post<CameraCaptureResponse>(`/video-inspections/cameras/${cameraId}/capture`, data)
}
