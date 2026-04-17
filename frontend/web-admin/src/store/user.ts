import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { REG_USER_INFO_KEY, clearRegAuth, getRegToken, setRegAuth } from '@/utils/auth-storage'

// 类型定义（Day 2 任务 - A同学）
interface UserInfo {
  id: string
  username: string
  nickname: string
  permissions: string[]
  tenantId: string
}

/**
 * 用户状态管理 Store
 * Day 2 任务：配置 Pinia 用户状态管理（A 同学）
 * 功能：用户信息、Token 管理
 */
export const useUserStore = defineStore('user', () => {
  // ==================== 状态 ====================
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)

  // ==================== 计算属性 ====================
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const nickname = computed(() => userInfo.value?.nickname || '')
  const permissions = computed(() => userInfo.value?.permissions || [])
  const tenantId = computed(() => userInfo.value?.tenantId || '')

  // ==================== 方法 ====================
  
  /**
   * 初始化用户信息（从本地存储恢复）
   */
  function initUserInfo() {
    const savedToken = getRegToken()
    const savedUserInfo = localStorage.getItem(REG_USER_INFO_KEY)

    if (savedToken) {
      token.value = savedToken
    }

    if (savedUserInfo) {
      try {
        userInfo.value = JSON.parse(savedUserInfo)
        // 兼容旧缓存数据，如果没有权限字段，默认赋予管理员权限
        if (!userInfo.value?.permissions || userInfo.value.permissions.length === 0) {
          if (userInfo.value) {
            userInfo.value.permissions = ['*:*:*']
            localStorage.setItem(REG_USER_INFO_KEY, JSON.stringify(userInfo.value))
          }
        }
      } catch (error) {
        console.error('解析用户信息失败:', error)
        logout()
      }
    }
  }

  /**
   * 登录（保存Token和用户信息）
   * 注：实际的登录表单和API调用将由E同学在Day2完成
   */
  function login(loginToken: string, user: UserInfo) {
    // 保存token和用户信息到状态
    token.value = loginToken
    userInfo.value = user

    // 持久化到localStorage
    setRegAuth(loginToken, user, user.tenantId)
  }

  /**
   * 退出登录
   */
  function logout() {
    // 清空状态
    token.value = ''
    userInfo.value = null

    // 清空本地存储
    clearRegAuth()

    console.log('已退出登录')
  }

  /**
   * 检查是否有指定权限
   */
  function hasPermission(permission: string): boolean {
    // 超级管理员权限
    if (permissions.value.includes('*:*:*')) {
      return true
    }
    return permissions.value.includes(permission)
  }

  /**
   * 检查是否有任意一个权限
   */
  function hasAnyPermission(permissionList: string[]): boolean {
    if (!permissionList || permissionList.length === 0) {
      return true
    }
    // 超级管理员权限
    if (permissions.value.includes('*:*:*')) {
      return true
    }
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  /**
   * 检查是否有所有权限
   */
  function hasAllPermissions(permissionList: string[]): boolean {
    if (!permissionList || permissionList.length === 0) {
      return true
    }
    // 超级管理员权限
    if (permissions.value.includes('*:*:*')) {
      return true
    }
    return permissionList.every(permission => permissions.value.includes(permission))
  }

  // 初始化（从本地存储恢复数据）
  initUserInfo()

  // ==================== 返回 ====================
  return {
    // 状态
    token,
    userInfo,
    
    // 计算属性
    isLoggedIn,
    username,
    nickname,
    permissions,
    tenantId,
    
    // 方法
    initUserInfo,
    login,
    logout,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions
  }
})
