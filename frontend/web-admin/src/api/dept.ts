import request from '@/utils/request'

export interface AdminDept {
  id?: string
  parentId?: string | null
  deptName: string    // maps to name
  orgType?: string    // maps to org_type: AREA, SCHOOL, CANTEEN
  memberCount?: number
  status?: number
}

export interface DeptQuery {
  page: number
  size: number
}

export function getDeptList(params: DeptQuery) {
  return request<{ records: any[]; total: number }>({
    url: '/admin/depts',
    method: 'get',
    params
  })
}

export function createDept(data: AdminDept) {
  return request({
    url: '/admin/depts',
    method: 'post',
    data: { name: data.deptName, parent_id: data.parentId ?? null, org_type: data.orgType || 'AREA' }
  })
}

export function updateDept(id: string, data: Partial<AdminDept>) {
  return request({
    url: `/admin/depts/${id}`,
    method: 'put',
    data: { name: data.deptName, parent_id: data.parentId ?? null, org_type: data.orgType || 'AREA' }
  })
}

export function deleteDept(id: string) {
  return request({
    url: `/admin/depts/${id}`,
    method: 'delete'
  })
}
