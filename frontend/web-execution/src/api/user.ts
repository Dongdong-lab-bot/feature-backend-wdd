import request from '@/utils/request'

export interface UserRecord {
  id: number
  username: string
  real_name?: string
  mobile?: string
  gender?: string
  birthday?: string
  role_id?: number
  role_name?: string
  status: string
  faceImage?: string
  healthImage?: string
}

export interface UserItem {
  id: number
  username: string
  realName: string
  mobile: string
  gender: string
  birthday: string
  roleId?: number
  roleName: string
  status: 1 | 0
  faceImage?: string
  healthImage?: string
}

export interface UserCreatePayload {
  username: string
  password: string
  realName: string
  mobile: string
  gender: string
  face_image_url?: string
  health_image_url?: string
}

export interface UserUpdatePayload {
  realName: string
  mobile: string
  gender: string
  face_image_url?: string
  health_image_url?: string
}

export interface RoleOption {
  id: number
  name: string
}

export interface UserQuery {
  page: number
  size: number
  keyword?: string
}

const toUserItem = (item: any): UserItem => {
  // [Fix] 后端 /users 接口返回驼峰字段（realName），兼容驼峰和下划线两种格式
  const realName = item.realName || item.real_name || '-'
  const mobile = item.mobile || '-'
  const gender = item.gender || '-'
  const birthday = item.birthday || '-'
  // roles 数组：取第一个角色名
  const roles: Array<{ role_id: number; role_name?: string }> = Array.isArray(item.roles) ? item.roles : []
  const roleId = item.roleId ?? item.role_id ?? roles[0]?.role_id
  const roleName = item.roleName || item.role_name || roles[0]?.role_name || '-'
  // status：后端返回 1/0 数字 或 'ACTIVE'/'DISABLED' 字符串
  const statusVal: 1 | 0 = typeof item.status === 'number'
    ? (item.status as 1 | 0)
    : (item.status === 'ACTIVE' ? 1 : 0)
  return {
    id: item.id,
    username: item.username,
    realName,
    mobile,
    gender,
    birthday,
    roleId,
    roleName,
    status: statusVal,
    faceImage: item.faceImage || item.face_image_url || '',
    healthImage: item.healthImage || item.health_image_url || ''
  }
}

// 获取用户列表
export function getUserList(params: UserQuery) {
  return request<{ records: UserItem[], total: number }>({
    url: '/users',
    method: 'get',
    params
  }).then((data: any) => {
    const records = Array.isArray(data?.records) ? data.records.map(toUserItem) : []
    return {
      records,
      total: Number(data?.total || 0)
    }
  })
}

// 新增用户
export function createUser(data: UserCreatePayload) {
  return request({
    url: '/user',
    method: 'post',
    data: {
      username: data.username,
      password: data.password,
      role_type: 'EXECUTOR',
      real_name: data.realName,
      mobile: data.mobile,
      gender: data.gender,
      face_image_url: data.face_image_url,
      health_image_url: data.health_image_url
    }
  })
}

// 修改当前登录用户
export function updateUser(data: UserUpdatePayload) {
  return request({
    url: '/user',
    method: 'put',
    data: {
      real_name: data.realName,
      mobile: data.mobile,
      gender: data.gender,
      face_image_url: data.face_image_url,
      health_image_url: data.health_image_url
    }
  })
}

// 更新用户状态（ACTIVE / DISABLED）
export function updateUserStatus(id: number, status: 1 | 0) {
  const nextStatus = status === 1 ? 'ACTIVE' : 'DISABLED'
  return request({
    url: `/user/${id}/status`,
    method: 'put',
    data: { status: nextStatus }
  })
}

// 删除用户
export function deleteUser(id: number) {
  return request({
    url: `/user/${id}`,
    method: 'delete'
  })
}

// 执行端后端暂未提供角色列表接口，前端走固定职务选项
export function getRoleList() {
  return Promise.resolve({ records: [] as RoleOption[] })
}
