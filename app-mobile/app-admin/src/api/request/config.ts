const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

const normalizeBaseUrl = (value: string) => {
  let v = (value || '').trim()
  if (!v) return ''
  if (!/^https?:\/\//i.test(v)) {
    v = `http://${v}`
  }
  return v.replace(/\/+$/, '')
}

export const getBaseUrl = () => {
  return normalizeBaseUrl(uni.getStorageSync('baseUrl')) || DEFAULT_BASE_URL
}

export const getAppClient = () => {
  const appClient = uni.getStorageSync('appClient')
  return typeof appClient === 'string' && appClient ? appClient : 'reg_app'
}

export const getToken = () => {
  const token = uni.getStorageSync('token')
  return typeof token === 'string' ? token : ''
}

export const getRefreshToken = () => {
  const token = uni.getStorageSync('refreshToken')
  return typeof token === 'string' ? token : ''
}

export const setAuthTokens = (accessToken: string, refreshToken: string) => {
  uni.setStorageSync('token', accessToken)
  uni.setStorageSync('refreshToken', refreshToken)
}

export const clearAuthStorage = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('refreshToken')
  uni.removeStorageSync('userInfo')
}

export const getTimeout = () => 15000
