export const REG_TOKEN_KEY = 'reg_token'
export const REG_REFRESH_TOKEN_KEY = 'reg_refresh_token'
export const REG_USER_INFO_KEY = 'reg_user_info'
export const REG_TENANT_ID_KEY = 'reg_tenant_id'

export function getRegToken(): string {
  return localStorage.getItem(REG_TOKEN_KEY) || ''
}

export function getRegTenantId(): string {
  return localStorage.getItem(REG_TENANT_ID_KEY) || ''
}

export function setRegAuth(token: string, userInfo: unknown, tenantId?: string, refreshToken?: string): void {
  localStorage.setItem(REG_TOKEN_KEY, token)
  localStorage.setItem(REG_USER_INFO_KEY, JSON.stringify(userInfo))
  if (tenantId) {
    localStorage.setItem(REG_TENANT_ID_KEY, tenantId)
  }
  if (refreshToken) {
    localStorage.setItem(REG_REFRESH_TOKEN_KEY, refreshToken)
  }
}

export function clearRegAuth(): void {
  localStorage.removeItem(REG_TOKEN_KEY)
  localStorage.removeItem(REG_REFRESH_TOKEN_KEY)
  localStorage.removeItem(REG_USER_INFO_KEY)
  localStorage.removeItem(REG_TENANT_ID_KEY)
}
