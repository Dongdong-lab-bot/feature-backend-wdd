import { apiRequest } from './request'

export interface WeeklyTaskListParams {
  startDate?: string
  endDate?: string
  status?: string
  keyword?: string
  page?: number
  pageSize?: number
}

export interface WeeklyTaskListItem {
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

export interface WeeklyTaskListResponse {
  total: number
  list: WeeklyTaskListItem[]
}

/**
 * 获取周排查任务列表：GET /weekly-inspections/tasks
 */
export function fetchWeeklyTaskList(params: WeeklyTaskListParams) {
  return apiRequest<WeeklyTaskListResponse>('/weekly-inspections/tasks', {
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
 * 获取单条周排查任务详情：GET /weekly-inspections/tasks/{id}
 */
export function fetchWeeklyTaskDetail(id: string) {
  return apiRequest<any>(`/weekly-inspections/tasks/${id}`, {
    method: 'GET'
  })
}

export interface WeeklyRectifyItem {
  result_id: number
  description?: string
  photos?: string[]
}

/**
 * 食堂端提交整改：POST /weekly-inspections/tasks/{id}/rectify
 */
export function submitWeeklyTask(id: string, params: any) {
  return apiRequest<any>(`/weekly-inspections/tasks/${id}/submit`, {
    method: 'POST',
    data: params
  })
}

export function rectifyWeeklyTask(id: string, params: {
  rectifier_id?: string
  feedback_per_item: WeeklyRectifyItem[]
}) {
  return apiRequest<any>(`/weekly-inspections/tasks/${id}/rectify`, {
    method: 'POST',
    data: params
  })
}