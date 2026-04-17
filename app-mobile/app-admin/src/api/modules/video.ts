import { request } from '../request/client'

// --- Types ---

// 1. 获取食堂/区域下摄像头树
export type CameraTreeNode = {
  id: string | number
  name: string
  type: 'AREA' | 'CANTEEN' | 'CAMERA'
  parentId: string | number | null
  cameraId?: string // 仅当 type 为 CAMERA 时存在
  children?: CameraTreeNode[]
}

export type CameraTreeResponse = {
  tree: CameraTreeNode[]
}

// 2. 播放参数接口
export type PlayParamsPayload = {
  cameraId: string | number
  action: 'preview' | 'playback'
  begin?: string
  end?: string
}

// App/SDK (X-App-Client: app) 返回的结构
export type PlayParamsData = {
  oauthToken?: string
  uikitAccessToken?: string
  deviceSerial: string
  channelNo: string
  validCode?: string
  begin?: string
  end?: string
}

// 3. 抓拍监控画面
export type CapturePayload = {
  image_base64: string
  timestamp: string
}

export type CaptureResponse = {
  photo_url: string
}

// 4. 任务详情与表单
export type VideoTaskListItem = {
  task_id: string
  canteen_name?: string
  submitter_name?: string
  template_name?: string
  total_score?: number
  red_line_issues?: number
  submission_date?: string
  status?: string
  status_text?: string
}

export type VideoTaskListResponse = {
  total: number
  list: VideoTaskListItem[]
}

export type VideoTaskMinorItem = {
  item_id: string
  result_id?: string
  content?: string
  issue_type?: string
  total_score?: number
  scoring_options?: number[]
  score_given?: number
  associated_camera_ids?: string[]
  inspection_description?: string
  inspection_photos?: string[]
  rectification_description?: string
  rectification_photos?: string[]
}

export type VideoTaskDetailData = {
  task_info: {
    task_id: string
    canteen_name?: string
    inspector_name?: string
    status?: string
    total_score?: number
  }
  form_snapshot: {
    form_type?: string
    major_items?: Array<{
      title?: string
      minor_items?: VideoTaskMinorItem[]
    }>
  }
  audit_logs?: any[]
}

// 5. 提交检查结果
export type VideoTaskSubmitPayload = {
  inspector_id: string
  actual_start_time: string
  results: Array<{
    item_id: string
    score_given: number
    description: string
    photos: string[]
  }>
}

// 6. 整改与审核
export type VideoTaskRectifyPayload = {
  rectifier_id: string
  feedback_per_item: Array<{
    result_id: string
    description: string
    photos: string[]
  }>
}

export type VideoTaskAuditPayload = {
  auditor_id: string
  action: 'PASS' | 'REJECT'
  opinion?: string
}

// --- APIs ---

/**
 * 1. 获取食堂/区域下摄像头树
 */
export const getVideoCamerasTree = async () => {
  return request<CameraTreeResponse>({
    path: '/video/cameras/tree',
    method: 'GET'
  })
}

/**
 * 2. 播放参数接口（实时/回放监控画面）
 */
export const getVideoPlayParams = async (data: PlayParamsPayload) => {
  return request<PlayParamsData>({
    path: '/api/v1/video/hikvision/play-params',
    method: 'POST',
    data
  })
}

/**
 * 3. 抓拍监控画面
 * @param cameraId 摄像头ID
 */
export const captureVideoFrame = async (cameraId: string, data: CapturePayload) => {
  return request<CaptureResponse>({
    path: `/video-inspections/cameras/${cameraId}/capture`,
    method: 'POST',
    data
  })
}

/**
 * 4. 获取任务列表
 */
export const getVideoTasks = async (params: {
  status?: string
  keyword?: string
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
}) => {
  return request<VideoTaskListResponse>({
    path: '/video-inspections/tasks',
    method: 'GET',
    params
  })
}

/**
 * 5. 获取任务详情
 */
export const getVideoTaskDetail = async (taskId: string | number) => {
  return request<VideoTaskDetailData>({
    path: `/video-inspections/tasks/${taskId}`,
    method: 'GET'
  })
}

/**
 * 6. 监管端提交检查结果
 */
export const submitVideoTask = async (taskId: string | number, data: VideoTaskSubmitPayload) => {
  return request<any>({
    path: `/video-inspections/tasks/${taskId}/submit`,
    method: 'POST',
    data
  })
}

/**
 * 7. 食堂端提交整改
 */
export const rectifyVideoTask = async (taskId: string | number, data: VideoTaskRectifyPayload) => {
  return request<any>({
    path: `/video-inspections/tasks/${taskId}/rectify`,
    method: 'POST',
    data
  })
}

/**
 * 8. 监管端审核整改
 */
export const auditVideoTask = async (taskId: string | number, data: VideoTaskAuditPayload) => {
  return request<any>({
    path: `/video-inspections/tasks/${taskId}/audit`,
    method: 'POST',
    data
  })
}
