import request from '@/utils/request'

export interface Org {
  id: number
  name: string
  type: 'AREA' | 'SCHOOL' | 'CANTEEN'
  parentId?: number
  managerId?: number
  address?: string
  licenseUrl?: string
  children?: Org[]
}

// 获取组织树
export function getOrgTree(params?: { type?: string, parentId?: number }) {
  return request<Org[]>({
    url: '/org/tree',
    method: 'get',
    params
  })
}

// 获取组织详情
export function getOrgDetail(id: number) {
  return request<Org>({
    url: `/org/${id}`,
    method: 'get'
  })
}

// 更新组织信息
export function updateOrg(data: Partial<Org>) {
  return request({
    url: '/org',
    method: 'put',
    data
  })
}
