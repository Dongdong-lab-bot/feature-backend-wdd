import request, { get, post, put, del } from '@/utils/request'

export interface Employee {
  id?: number
  username: string      // 用户账号
  nickname: string      // 用户昵称
  gender: '男' | '女'   // 性别
  birthday: string      // 生日
  phone: string         // 手机号码
  status: number        // 1-正常 0-禁用
}

export interface EmployeeQuery {
  page: number
  pageSize: number
  username?: string
  nickname?: string
}

// 获取员工列表
export function getEmployeeList(params: EmployeeQuery) {
  return get<{ list: Employee[], total: number }>('/employee/list', { params })
}

// 获取员工详情
export function getEmployeeDetail(id: number) {
  return get<Employee>(`/employee/${id}`)
}

// 新增员工
export function createEmployee(data: Employee) {
  return post('/employee', data)
}

// 修改员工
export function updateEmployee(data: Employee) {
  return put('/employee', data)
}

// 删除员工
export function deleteEmployee(id: number) {
  return del(`/employee/${id}`)
}

// 更新员工状态
export function updateEmployeeStatus(id: number, status: number) {
  return put(`/employee/${id}/status`, { status })
}

// 上传图片
export function uploadImage(file: File, description?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (description) {
    formData.append('description', description)
  }
  return request<{ image_id: number; filename: string; url: string }>({
    url: '/images/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
