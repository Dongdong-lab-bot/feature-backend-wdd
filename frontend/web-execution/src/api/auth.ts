import request from '@/utils/request'
import { EXEC_APP_CLIENT, getRefreshTokenValue } from '@/utils/auth-storage'

export interface LoginParams {
  username: string
  password: string
  app_client: string
}

export interface RefreshTokenParams {
  refreshToken: string
  app_client?: string
}

export interface LoginResult {
  accessToken: string
  refreshToken: string
  userInfo: {
    id: number
    roleType: string
    tenantId: number
    orgId?: number
    username?: string
    nickname?: string
  }
}

// 登录
export function login(data: LoginParams) {
  return request<LoginResult>({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// 刷新Token
export function refreshToken(data: RefreshTokenParams) {
  return request<{ accessToken: string, refreshToken: string }>({
    url: '/auth/refresh',
    method: 'post',
    data: {
      refreshToken: data.refreshToken,
      refresh_token: data.refreshToken,
      app_client: data.app_client || EXEC_APP_CLIENT
    }
  })
}

// 获取权限列表
export function getPermissions() {
  return request<string[]>({
    url: '/auth/me/permissions',
    method: 'get'
  })
}

// 退出登录
export function logout() {
  const refreshToken = getRefreshTokenValue()
  return request({
    url: '/auth/logout',
    method: 'post',
    data: { refreshToken }
  })
}

// 获取当前用户信息
export function getMe() {
  return request<{ id: number; username: string; realName: string; roleType: string; tenantId: number; orgId?: number }>({
    url: '/auth/me',
    method: 'get'
  })
}
