import { apiRequest } from './request'

export interface JointTaskListParams {
  startDate?: string
  endDate?: string
  status?: string
  keyword?: string
  page?: number
  pageSize?: number
}

export interface JointTaskListItem {
  id: number
  canteen_name: string
  template_name?: string | null
  executor_name?: string | null
  submission_date?: string | null
  status: string
  total_score?: number | null
  red_line_issues?: number | null
  business_date?: string | null
}

export interface JointTaskListResponse {
  total: number
  list: JointTaskListItem[]
}

/**
 * 获取联合巡检单条任务详情：GET /joint-inspections/tasks/{id}
 */
export function fetchJointTaskDetail(id: string) {
  return apiRequest<any>(`/joint-inspections/tasks/${id}`, {
    method: 'GET'
  })
}
export function fetchJointTaskList(params: JointTaskListParams) {
  return apiRequest<JointTaskListResponse>('/joint-inspections/tasks', {
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

export interface JointRectifyItem {
  result_id: string
  description: string
  photos: string[]
}

/**
 * 联合巡检食堂端提交整改：POST /joint-inspections/tasks/{id}/rectify
 */
export function rectifyJointTask(
  id: string,
  payload: { feedbackPerItem: JointRectifyItem[]; rectifierId?: string }
) {
  return apiRequest(`/joint-inspections/tasks/${id}/rectify`, {
    method: 'POST',
    data: {
      rectifier_id: payload.rectifierId,
      feedback_per_item: payload.feedbackPerItem
    }
  })
}

/**
 * 联合巡检协同签字：POST /joint-inspections/tasks/{id}/sign
 */
export function signJointTask(
  id: string,
  payload: { participantId: number; signature: string }
) {
  return apiRequest(`/joint-inspections/tasks/${id}/sign`, {
    method: 'POST',
    data: {
      participant_id: payload.participantId,
      signature: payload.signature
    }
  })
}