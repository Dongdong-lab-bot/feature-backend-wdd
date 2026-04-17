export const EXEC_APP_CLIENT = 'exec_web'

export const AUTH_TOKENS_UPDATED_EVENT = 'auth-tokens-updated'
export const AUTH_LOGOUT_EVENT = 'auth-logout'

export interface AuthTokensPayload {
  accessToken: string
  refreshToken: string
}

export function getAccessToken(): string {
  return localStorage.getItem('token') || ''
}

export function getRefreshTokenValue(): string {
  return localStorage.getItem('refresh_token') || ''
}

export function getStoredUserInfo<T = unknown>(): T | null {
  const rawUserInfo = localStorage.getItem('user_info')
  if (!rawUserInfo) {
    return null
  }

  try {
    return JSON.parse(rawUserInfo) as T
  } catch {
    return null
  }
}

export function setStoredUserInfo(userInfo: unknown): void {
  localStorage.setItem('user_info', JSON.stringify(userInfo))
}

export function clearStoredUserInfo(): void {
  localStorage.removeItem('user_info')
}

export function setAuthTokens(payload: AuthTokensPayload): void {
  localStorage.setItem('token', payload.accessToken)
  localStorage.setItem('refresh_token', payload.refreshToken)
  window.dispatchEvent(new CustomEvent<AuthTokensPayload>(AUTH_TOKENS_UPDATED_EVENT, { detail: payload }))
}

export function clearAuthStorage(): void {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_info')
  window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT))
}