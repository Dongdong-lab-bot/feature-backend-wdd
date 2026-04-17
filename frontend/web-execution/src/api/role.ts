import { get, post, put, del } from '@/utils/request'

export interface RoleRecord {
  id: number
  name: string
  role_type: string
  level: string
  permissions: string[]
  permissions_desc?: string
  created_at?: string
}

export interface RoleQuery {
  page: number
  size: number
}

export interface RoleCreatePayload {
  name: string
  level: string
  permissions_desc?: string
}

export interface RoleUpdatePayload {
  name?: string
  level?: string
  permissions_desc?: string
}

const toRoleItem = (record: RoleRecord) => ({
  id: record.id,
  name: record.name,
  level: record.level || '',
  permission: record.permissions_desc || ''
})

export function getRoleList(params: RoleQuery) {
  return get<{ records: RoleRecord[], total: number }>('/admin/roles', { params }).then((data: any) => {
    const records = Array.isArray(data?.records) ? data.records.map(toRoleItem) : []
    return {
      records,
      total: Number(data?.total || 0)
    }
  })
}

export function createRole(data: RoleCreatePayload) {
  return post('/admin/roles', {
    name: data.name,
    role_type: 'EXECUTOR',
    level: data.level,
    permissions_desc: data.permissions_desc
  })
}

export function updateRole(id: number, data: RoleUpdatePayload) {
  return put(`/admin/roles/${id}`, {
    name: data.name,
    level: data.level,
    permissions_desc: data.permissions_desc
  })
}

export function deleteRole(id: number) {
  return del(`/admin/roles/${id}`)
}
