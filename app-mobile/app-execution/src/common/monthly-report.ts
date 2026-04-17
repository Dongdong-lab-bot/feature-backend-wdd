import { apiRequest } from './request'

export interface MonthlyReportPreviewParams {
  startDate: string
  endDate: string
  dataSources: number[]  // 食堂ID列表（canteen_ids）
}

/**
 * 生成月调度报告预览：POST /monthly-reports/preview
 * 注意：后端当前的 MonthlyReportPreviewRequest 是 { start_date, end_date, data_sources }
 */
export function previewMonthlyReport(params: MonthlyReportPreviewParams) {
  return apiRequest<any>('/monthly-reports/preview', {
    method: 'POST',
    data: {
      start_date: params.startDate,
      end_date: params.endDate,
      data_sources: params.dataSources
    }
  })
}

export interface MonthlyReportExportParams extends MonthlyReportPreviewParams {
  exportFormat?: 'pdf' | 'docx'
}

/**
 * 导出月调度报告文件：POST /monthly-reports/export
 * 返回文件流（arraybuffer），前端当前只做“接口打通 + 提示”，实际保存可后续扩展
 */
export function exportMonthlyReport(params: MonthlyReportExportParams) {
  const baseUrl = uni.getStorageSync('baseUrl')
  const token = uni.getStorageSync('token')
  const appClient = uni.getStorageSync('appClient') || 'exec_app'

  return new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
    uni.request({
      url: `${baseUrl}/monthly-reports/export`,
      method: 'POST',
      header: {
        Authorization: token ? `Bearer ${token}` : '',
        'X-App-Client': appClient,
        'Content-Type': 'application/json'
      },
      responseType: 'arraybuffer',
      data: {
        start_date: params.startDate,
        end_date: params.endDate,
        data_sources: params.dataSources,
        export_format: params.exportFormat || 'pdf'
      },
      success: (res) => {
        resolve(res)
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}