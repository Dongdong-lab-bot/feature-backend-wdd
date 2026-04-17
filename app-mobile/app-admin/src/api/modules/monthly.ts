import { request } from '../request/client'

export type MonthlyReportRangeSource = {
  start_date: string
  end_date: string
  target_node_ids: string[]
}

export type MonthlyReportPreviewPayload = {
  start_date: string
  end_date: string
  data_sources: number[]
}

export type MonthlyReportPreviewData = Record<string, any>

export const previewMonthlyReport = async (payload: MonthlyReportPreviewPayload) => {
  return request<MonthlyReportPreviewData>({
    path: '/monthly-reports/preview',
    method: 'POST',
    data: payload
  })
}
