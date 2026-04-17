import request from '@/utils/request'

export interface MenuItem {
  id?: number
  parent_id?: number | null
  name: string
  path: string
  component: string
  sort: number
  hidden: boolean
  children?: MenuItem[]
  created_at?: string
}

export function getMenuList() {
  return request<{ records: MenuItem[]; total: number }>({
    url: '/admin/menus',
    method: 'get'
  })
}

export function createMenu(data: Omit<MenuItem, 'id' | 'children' | 'created_at'>) {
  return request({
    url: '/admin/menus',
    method: 'post',
    data
  })
}

export function updateMenu(id: number, data: Partial<Omit<MenuItem, 'id' | 'children' | 'created_at'>>) {
  return request({
    url: `/admin/menus/${id}`,
    method: 'put',
    data
  })
}

export function deleteMenu(id: number) {
  return request({
    url: `/admin/menus/${id}`,
    method: 'delete'
  })
}
