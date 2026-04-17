import request from '@/utils/request'

export interface AdminUser {
  id?: number
  username?: string
  real_name?: string
  mobile?: string
  gender?: string
  canteen_scope?: string
  org_id?: number
  org_name?: string
  role_id?: number
  role_name?: string
  role_type?: string
  status?: string
  password?: string
}

export interface UserQuery {
  page: number
  size: number
  keyword?: string
}

export function getUserList(params: UserQuery) {
  return request<{ records: AdminUser[]; total: number }>({
    url: '/admin/users',
    method: 'get',
    params
  })
}

export function createUser(data: AdminUser) {
  return request({
    url: '/admin/users',
    method: 'post',
    data: {
      username: data.username,
      real_name: data.real_name,
      mobile: data.mobile,
      gender: data.gender,
      canteen_scope: data.canteen_scope,
      org_id: data.org_id,
      role_id: data.role_id,
      password: data.password || 'Changeme123!',
      role_type: data.role_type || 'REGULATOR'
    }
  })
}

export function updateUser(id: number, data: Partial<AdminUser>) {
  return request({
    url: `/admin/users/${id}`,
    method: 'put',
    data: {
      real_name: data.real_name,
      mobile: data.mobile,
      gender: data.gender,
      canteen_scope: data.canteen_scope,
      org_id: data.org_id,
      role_ids: data.role_id != null ? [data.role_id] : undefined,
      status: data.status
    }
  })
}

export function deleteUser(id: number) {
  return request({
    url: `/admin/users/${id}`,
    method: 'delete'
  })
}

export function resetUserPassword(id: number, newPassword: string) {
  return request({
    url: `/admin/users/${id}/reset-password`,
    method: 'post',
    data: { new_password: newPassword }
  })
}
