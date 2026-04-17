import { apiRequest } from './request'

/**
 * 登录接口：POST /auth/login
 * 请求体：{ username, password, app_client: 'exec_app' }
 * 返回：后端文档中的 { accessToken, refreshToken, userInfo, ... }
 */
export async function login(username: string, password: string) {
  const data = await apiRequest('/auth/login', {
    method: 'POST',
    data: {
      username,
      password,
      app_client: 'exec_app'
    }
  })

  const accessToken = (data as any)?.accessToken
  const refreshToken = (data as any)?.refreshToken

  if (accessToken) {
    uni.setStorageSync('token', accessToken)
    if (refreshToken) {
      uni.setStorageSync('refreshToken', refreshToken)
    }
    uni.setStorageSync('appClient', 'exec_app')
  }

  return data
}

/**
 * 退出登录：请求后端接口后，清空本地登录态并回到登录页
 */
export async function logout() {
  try {
    // 尝试调用后端退出接口
    const refreshToken = uni.getStorageSync('refreshToken')
    await apiRequest('/auth/logout', {
      method: 'POST',
      data: {
        refreshToken,
        app_client: 'exec_app'
      }
    })
  } catch (error) {
    console.error('Logout API failed:', error)
  } finally {
    // 无论后端是否成功（后端可能返回404因为暂未实现），都清除本地缓存
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('appClient')
    uni.reLaunch({
      url: '/pages/login/login'
    })
  }
}

/**
 * 短信验证码发送：POST /auth/sms/send
 * 请求体：{ mobile, scene, app_client: 'exec_app' }
 * scene: LOGIN | REGISTER | RESET_PASSWORD
 */
export async function sendSmsCode(mobile: string, scene: 'LOGIN' | 'REGISTER' | 'RESET_PASSWORD' = 'LOGIN') {
  return apiRequest('/auth/sms/send', {
    method: 'POST',
    data: {
      mobile,
      scene,
      app_client: 'exec_app'
    }
  })
}

/**
 * 短信验证码登录：POST /auth/login/sms
 * 请求体：{ mobile, code, bizNo, app_client: 'exec_app' }
 * 返回：同 /auth/login，成功后写入 token
 */
export async function loginBySms(mobile: string, code: string, bizNo: string) {
  const data = await apiRequest('/auth/login/sms', {
    method: 'POST',
    data: {
      mobile,
      code,
      bizNo,
      app_client: 'exec_app'
    }
  })

  const accessToken = (data as any)?.accessToken
  const refreshToken = (data as any)?.refreshToken

  if (accessToken) {
    uni.setStorageSync('token', accessToken)
    if (refreshToken) {
      uni.setStorageSync('refreshToken', refreshToken)
    }
    uni.setStorageSync('appClient', 'exec_app')
  }

  return data
}

/**
 * 用户注册：POST /auth/register
 */
export async function registerByMobile(
  mobile: string,
  code: string,
  bizNo: string,
  password: string,
  inviteCode?: string
) {
  return apiRequest('/auth/register', {
    method: 'POST',
    data: {
      mobile,
      code,
      bizNo,
      password,
      inviteCode,
      app_client: 'exec_app'
    }
  })
}

/**
 * 忘记密码 - 验证码校验：POST /auth/password/verify-code
 */
export async function verifyResetCode(mobile: string, code: string, bizNo: string) {
  return apiRequest('/auth/password/verify-code', {
    method: 'POST',
    data: {
      mobile,
      code,
      bizNo,
      app_client: 'exec_app'
    }
  })
}

/**
 * 忘记密码 - 重置密码：POST /auth/password/reset
 */
export async function resetPassword(mobile: string, newPassword: string, resetToken: string) {
  return apiRequest('/auth/password/reset', {
    method: 'POST',
    data: {
      mobile,
      newPassword,
      resetToken,
      app_client: 'exec_app'
    }
  })
}

/**
 * 已登录用户修改密码：PUT /auth/password
 */
export async function changePassword(oldPassword: string, newPassword: string) {
  return apiRequest('/auth/password', {
    method: 'PUT',
    data: {
      oldPassword,
      newPassword
    }
  })
}

/**
 * 获取当前用户信息：GET /auth/me
 */
export async function getUserInfo() {
  return apiRequest('/auth/me', {
    method: 'GET'
  })
}

/**
 * 修改手机号：PUT /auth/phone
 */
export async function changePhoneBySms(newPhone: string, code: string, bizNo: string) {
  return apiRequest('/auth/phone', {
    method: 'PUT',
    data: {
      newPhone,
      code,
      bizNo
    }
  })
}
