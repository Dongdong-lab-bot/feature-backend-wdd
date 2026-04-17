import { request } from '../request/client'
import { getAppClient, getRefreshToken, setAuthTokens } from '../request/config'

export type LoginPayload = {
  username: string
  password: string
}

export type LoginData = {
  accessToken: string
  refreshToken: string
  userInfo: {
    id: number
    roleType: string
    tenantId: number
  }
}

export const login = async (payload: LoginPayload) => {
  const appClient = getAppClient()
  const data = await request<LoginData>({
    path: '/auth/login',
    method: 'POST',
    skipAuth: true,
    data: {
      username: payload.username,
      password: payload.password,
      app_client: appClient
    }
  })

  setAuthTokens(data.accessToken, data.refreshToken)
  uni.setStorageSync('userInfo', data.userInfo)

  return data
}

export type SmsLoginPayload = {
  mobile: string
  code: string
  bizNo: string
}

export const loginBySms = async (payload: SmsLoginPayload) => {
  const appClient = getAppClient()
  const data = await request<LoginData>({
    path: '/auth/login/sms',
    method: 'POST',
    skipAuth: true,
    data: {
      mobile: payload.mobile,
      code: payload.code,
      bizNo: payload.bizNo,
      app_client: appClient
    }
  })
  setAuthTokens(data.accessToken, data.refreshToken)
  uni.setStorageSync('userInfo', data.userInfo)
  return data
}

export type RefreshData = {
  accessToken: string
  refreshToken: string
}

export const refresh = async (refreshToken: string) => {
  const data = await request<RefreshData>({
    path: '/auth/refresh',
    method: 'POST',
    skipAuth: true,
    disableRefreshRetry: true,
    data: { refreshToken }
  })
  setAuthTokens(data.accessToken, data.refreshToken)
  return data
}

export type SmsScene = 'LOGIN' | 'REGISTER' | 'RESET_PASSWORD'

export type SendSmsPayload = {
  mobile: string
  scene: SmsScene
}

export type SendSmsData = {
  bizNo: string
  expireSeconds: number
  retryAfterSeconds: number
}

export const sendSms = async (payload: SendSmsPayload) => {
  const appClient = getAppClient()
  return request<SendSmsData>({
    path: '/auth/sms/send',
    method: 'POST',
    skipAuth: true,
    data: {
      mobile: payload.mobile,
      scene: payload.scene,
      app_client: appClient
    }
  })
}

export type RegisterPayload = {
  mobile: string
  code: string
  bizNo: string
  password: string
  inviteCode: string
}

export type RegisterData = {
  userId: number
}

export const register = async (payload: RegisterPayload) => {
  const appClient = getAppClient()
  return request<RegisterData>({
    path: '/auth/register',
    method: 'POST',
    skipAuth: true,
    data: {
      mobile: payload.mobile,
      code: payload.code,
      bizNo: payload.bizNo,
      password: payload.password,
      inviteCode: payload.inviteCode,
      app_client: appClient
    }
  })
}

export type VerifyResetCodePayload = {
  mobile: string
  code: string
  bizNo: string
}

export type VerifyResetCodeData = {
  resetToken: string
  expireSeconds: number
}

export const verifyResetCode = async (payload: VerifyResetCodePayload) => {
  const appClient = getAppClient()
  return request<VerifyResetCodeData>({
    path: '/auth/password/verify-code',
    method: 'POST',
    skipAuth: true,
    data: {
      mobile: payload.mobile,
      code: payload.code,
      bizNo: payload.bizNo,
      app_client: appClient
    }
  })
}

export type ResetPasswordPayload = {
  mobile: string
  newPassword: string
  resetToken: string
}

export type ResetPasswordData = {
  updated: boolean
}

export const resetPassword = async (payload: ResetPasswordPayload) => {
  const appClient = getAppClient()
  return request<ResetPasswordData>({
    path: '/auth/password/reset',
    method: 'POST',
    skipAuth: true,
    data: {
      mobile: payload.mobile,
      newPassword: payload.newPassword,
      resetToken: payload.resetToken,
      app_client: appClient
    }
  })
}

export type CurrentUser = {
  id: number
  username: string
  realName: string | null
  mobile: string | null
  gender?: string | null
  birthday?: string | null
  email?: string | null
  canteenScope?: string | null
  orgId?: number | null
  orgName?: string | null
  roleId?: number | null
  roleName?: string | null
  roleType: string
  tenantId: number
  status: string
}

export const getCurrentUser = async () => {
  return request<CurrentUser>({
    path: '/auth/me',
    method: 'GET'
  })
}

export const getPermissions = async () => {
  return request<string[]>({
    path: '/auth/me/permissions',
    method: 'GET'
  })
}

export type LogoutData = {
  ok: boolean
}

export const logout = async () => {
  const refreshToken = getRefreshToken()
  return request<LogoutData>({
    path: '/auth/logout',
    method: 'POST',
    data: { refreshToken }
  })
}

export type ChangePasswordPayload = {
  oldPassword: string
  newPassword: string
}

export type ChangePasswordData = {
  updated: boolean
}

export const changePassword = async (payload: ChangePasswordPayload) => {
  return request<ChangePasswordData>({
    path: '/auth/password',
    method: 'PUT',
    data: {
      oldPassword: payload.oldPassword,
      newPassword: payload.newPassword
    }
  })
}
