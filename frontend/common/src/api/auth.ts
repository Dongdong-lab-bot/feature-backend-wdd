import { RequestService } from '../utils/request'

export interface LoginParams {
  username: string
  password: string
  app_client: string
}

export interface LoginResult {
  accessToken: string
  refreshToken: string
  userInfo: {
    id: number
    roleType: string
    tenantId: number
    username?: string
    nickname?: string
  }
}

export interface RefreshTokenResult {
  accessToken: string
  refreshToken: string
}

export function createAuthApi(request: RequestService) {
  return {
    login(data: LoginParams) {
      return request<LoginResult>({
        url: '/auth/login',
        method: 'post',
        data
      })
    },

    refreshToken(refreshToken: string) {
      return request<RefreshTokenResult>({
        url: '/auth/refresh',
        method: 'post',
        data: { refreshToken }
      })
    },

    getPermissions() {
      return request<string[]>({
        url: '/auth/me/permissions',
        method: 'get'
      })
    }
  }
}

export type AuthApi = ReturnType<typeof createAuthApi>