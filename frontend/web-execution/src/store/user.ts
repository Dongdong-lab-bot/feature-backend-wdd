import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getPermissions as getPermissionsApi, logout as logoutApi, getMe as getMeApi, LoginParams } from '@/api/auth'
import {
  AUTH_LOGOUT_EVENT,
  AUTH_TOKENS_UPDATED_EVENT,
  getAccessToken,
  getRefreshTokenValue,
  getStoredUserInfo,
  setAuthTokens,
  setStoredUserInfo,
  clearAuthStorage
} from '@/utils/auth-storage'

// 类型定义
interface UserInfo {
  id: number
  roleType: string
  tenantId: number
  orgId?: number
  username?: string
  nickname?: string
  permissions: string[]
}

/**
 * 用户状态管理 Store
 * 功能：用户信息、Token 管理
 */
export const useUserStore = defineStore('user', () => {
  // ==================== 状态 ====================
  const token = ref<string>('')
  const refreshToken = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)

  // ==================== 计算属性 ====================
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const nickname = computed(() => userInfo.value?.nickname || '')
  const permissions = computed(() => userInfo.value?.permissions || [])
  const roleType = computed(() => userInfo.value?.roleType || '')
  let authEventsBound = false

  const syncTokensFromStorage = () => {
    token.value = getAccessToken()
    refreshToken.value = getRefreshTokenValue()
  }

  const bindAuthEvents = () => {
    if (authEventsBound || typeof window === 'undefined') {
      return
    }

    window.addEventListener(AUTH_TOKENS_UPDATED_EVENT, () => {
      syncTokensFromStorage()
    })

    window.addEventListener(AUTH_LOGOUT_EVENT, () => {
      token.value = ''
      refreshToken.value = ''
      userInfo.value = null
    })

    authEventsBound = true
  }

  // ==================== 方法 ====================
  
  /**
   * 初始化用户信息（从本地存储恢复）
   */
  function initUserInfo() {
    bindAuthEvents()
    syncTokensFromStorage()

    const savedUserInfo = getStoredUserInfo<UserInfo>()

    if (savedUserInfo) {
      userInfo.value = savedUserInfo
      // 若旧数据缺少 username/nickname，异步从 /auth/me 补全
      if (!savedUserInfo.username && token.value) {
        getMeApi().then((me: any) => {
          if (me && userInfo.value) {
            userInfo.value = {
              ...userInfo.value,
              username: me.username || '',
              nickname: me.realName || me.username || '',
            }
            setStoredUserInfo(userInfo.value)
          }
        }).catch(() => {/* 静默失败，不影响主流程 */})
      }
    } else if (localStorage.getItem('user_info')) {
      console.error('解析用户信息失败')
      logout()
    }
  }

  /**
   * 登录
   */
  async function login(params: LoginParams) {
    const payload = await loginApi(params)
    const { accessToken, refreshToken: newRefreshToken, userInfo: apiUserInfo } = payload

    setAuthTokens({ accessToken, refreshToken: newRefreshToken })
    syncTokensFromStorage()

    // 尝试获取权限列表，失败不中断登录流程
    let perms: string[] = []
    try {
      perms = await getPermissionsApi()
    } catch (e) {
      console.warn('权限列表获取失败，使用空权限继续', e)
    }

    userInfo.value = {
      ...apiUserInfo,
      username: apiUserInfo.username || '',
      nickname: apiUserInfo.nickname || '',
      permissions: perms
    }

    setStoredUserInfo(userInfo.value)

    return payload
  }

  /**
   * 退出登录
   * @param callApi 是否调用后端登出接口（主动退出时为 true，清理状态时为 false）
   */
  async function logout(callApi = false) {
    if (callApi) {
      try {
        await logoutApi()
      } catch (e) {
        console.warn('调用登出接口失败', e)
      }
    }
    clearAuthStorage()
    console.log('已退出登录')
  }

  function setUserInfo(value: UserInfo | null) {
    userInfo.value = value
    if (value) {
      setStoredUserInfo(value)
      return
    }
    localStorage.removeItem('user_info')
  }

  /**
   * 检查是否有指定权限
   */
  function hasPermission(permission: string): boolean {
    if (!permission) return true
    if (!userInfo.value || !userInfo.value.permissions) return false
    
    return permissions.value.includes('*:*:*') || permissions.value.includes(permission)
  }

  /**
   * 检查是否有任意一个权限
   */
  function hasAnyPermission(perms: string[]): boolean {
    if (!perms || perms.length === 0) return true
    if (!userInfo.value || !userInfo.value.permissions) return false
    
    if (permissions.value.includes('*:*:*')) return true
    return perms.some(p => permissions.value.includes(p))
  }

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    username,
    nickname,
    permissions,
    roleType,
    initUserInfo,
    login,
    logout,
    setUserInfo,
    hasPermission,
    hasAnyPermission
  }
})
