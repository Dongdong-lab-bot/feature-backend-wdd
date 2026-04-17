import request from '@/utils/request'

export interface Device {
  id: number
  device_name: string
  device_code: string
  status: string
  created_at: string
  org_id: number
  org_name: string
  api_key?: string
  device_type?: string
  vendor?: string
  model?: string
  last_heartbeat?: string
}

export interface DeviceQuery {
  page: number
  page_size: number
  keyword?: string
  status?: string
  org_id?: number
}

export interface DeviceListResult {
  records: Device[]
  total: number
  page: number
  page_size: number
}

// 获取设备列表
export function getDeviceList(params: DeviceQuery) {
  return request<{ code: number; msg: string; data: DeviceListResult }>({
    url: '/devices',
    method: 'get',
    params
  })
}

// 新增设备
export function bindDevice(data: { device_name: string; device_code: string; org_id: number; device_type?: string }) {
  return request<{ code: number; msg: string; data: { id: number } }>({
    url: '/devices',
    method: 'post',
    data
  })
}

// 删除设备
export function unbindDevice(id: number) {
  return request<{ code: number; msg: string; data: { id: number; deleted: boolean } }>({
    url: `/devices/${id}`,
    method: 'delete'
  })
}

// 更新设备信息
export function updateDevice(data: { id: number; device_name?: string; status?: string }) {
  return request<{ code: number; msg: string; data: { id: number } }>({
    url: `/devices/${data.id}`,
    method: 'put',
    data: { device_name: data.device_name, status: data.status }
  })
}
