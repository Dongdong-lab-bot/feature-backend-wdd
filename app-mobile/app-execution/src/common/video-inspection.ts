import { apiRequest } from './request'

export interface VideoTaskListParams {
  startDate?: string
  endDate?: string
  status?: string
  keyword?: string
  page?: number
  pageSize?: number
}

export interface VideoTaskListItem {
  task_id: string
  canteen_name: string
  submitter_name: string
  template_name: string
  total_score: number
  red_line_issues: number
  submission_date: string
  status: string
  status_text: string
}

export interface VideoTaskListResponse {
  total: number
  list: VideoTaskListItem[]
}

/**
 * 获取视频巡检任务列表：GET /video-inspections/tasks
 */
export function fetchVideoTaskList(params: VideoTaskListParams) {
  return apiRequest<VideoTaskListResponse>('/video-inspections/tasks', {
    method: 'GET',
    data: {
      start_date: params.startDate,
      end_date: params.endDate,
      status: params.status,
      keyword: params.keyword,
      page: params.page,
      page_size: params.pageSize
    }
  })
}

/**
 * 获取视频巡检任务详情：GET /video-inspections/tasks/{id}
 */
export function fetchVideoTaskDetail(id: string) {
  return apiRequest<any>(`/video-inspections/tasks/${id}`, {
    method: 'GET'
  })
}

export interface VideoRectifyItem {
  result_id: string
  description: string
  photos: string[]
}

/**
 * 食堂端提交视频巡检整改：POST /video-inspections/tasks/{id}/rectify
 */
export function rectifyVideoTask(
  id: string,
  payload: { feedbackPerItem: VideoRectifyItem[]; rectifierId?: string }
) {
  return apiRequest(`/video-inspections/tasks/${id}/rectify`, {
    method: 'POST',
    data: {
      rectifier_id: payload.rectifierId,
      feedback_per_item: payload.feedbackPerItem
    }
  })
}