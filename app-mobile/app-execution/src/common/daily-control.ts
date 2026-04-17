import { apiRequest } from './request'

export interface DailyTaskListParams {
  startDate?: string
  endDate?: string
  status?: string
  keyword?: string
  page?: number
  pageSize?: number
}

export interface DailyTaskListItem {
  task_id: string
  canteen_name: string
  submitter_name: string
  template_name: string
  completion_progress: string
  submission_date: string
  status: string
  status_text: string
}

export interface DailyTaskListResponse {
  total: number
  list: DailyTaskListItem[]
}

export interface DailyTaskSubmitItem {
  item_id: string
  is_qualified: boolean
  description?: string | null
  photos?: string[]
}

export interface DailyTaskRectifyItem {
  result_id: string
  description: string
  photos: string[]
}

/**
 * 获取日管控任务列表：GET /daily-controls/tasks
 */
export function fetchDailyTaskList(params: DailyTaskListParams) {
  return apiRequest<DailyTaskListResponse>('/daily-controls/tasks', {
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
 * 食堂端提交自查：POST /daily-controls/tasks/{id}/submit
 */
export function submitDailyTask(
  id: string,
  payload: { actualStartTime: string; results: DailyTaskSubmitItem[]; submitterId?: string }
) {
  // Add Idempotency-Key header explicitly for the backend requirement
  const idempotencyKey = `daily-submit-${id}-${Date.now()}`
  return apiRequest(`/daily-controls/tasks/${id}/submit`, {
    method: 'POST',
    header: {
      'Idempotency-Key': idempotencyKey
    },
    data: {
      submitter_id: payload.submitterId,
      actual_start_time: payload.actualStartTime,
      results: payload.results
    }
  })
}

/**
 * 食堂端提交整改：POST /daily-controls/tasks/{id}/rectify
 */
export function rectifyDailyTask(
  id: string,
  payload: { feedbackPerItem: DailyTaskRectifyItem[]; rectifierId?: string }
) {
  const idempotencyKey = `daily-rectify-${id}-${Date.now()}`
  return apiRequest(`/daily-controls/tasks/${id}/rectify`, {
    method: 'POST',
    header: {
      'Idempotency-Key': idempotencyKey
    },
    data: {
      rectifier_id: payload.rectifierId,
      feedback_per_item: payload.feedbackPerItem
    }
  })
}

/**
 * 获取单条日管控任务详情：GET /daily-controls/tasks/{id}
 */
export function fetchDailyTaskDetail(id: string) {
  return apiRequest<any>(`/daily-controls/tasks/${id}`, {
    method: 'GET'
  })
}