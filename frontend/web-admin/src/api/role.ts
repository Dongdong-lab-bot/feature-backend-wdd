import request from '@/utils/request'

export interface AdminRole {
  id?: string
  positionName: string  // maps to name
  level: string         // maps to role_type
  jobLevel?: string     // maps to level (职级)
  permissionsDesc?: string  // maps to permissions_desc
}

export interface RoleQuery {
  page: number
  size: number
}

export function getRoleList(params: RoleQuery) {
  return request<{ records: any[]; total: number }>({
    url: '/admin/roles',
    method: 'get',
    params
  })
}

export function createRole(data: AdminRole) {
  return request({
    url: '/admin/roles',
    method: 'post',
    data: { name: data.positionName, role_type: data.level, level: data.jobLevel, permissions_desc: data.permissionsDesc }
  })
}

export function updateRole(id: string, data: Partial<AdminRole>) {
  return request({
    url: `/admin/roles/${id}`,
    method: 'put',
    data: { name: data.positionName, role_type: data.level, level: data.jobLevel, permissions_desc: data.permissionsDesc }
  })
}

export function deleteRole(id: string) {
  return request({
    url: `/admin/roles/${id}`,
    method: 'delete'
  })
}
