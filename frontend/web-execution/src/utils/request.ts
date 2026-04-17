import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { clearAuthStorage, EXEC_APP_CLIENT, getAccessToken, getRefreshTokenValue, setAuthTokens } from '@/utils/auth-storage'

interface BackendResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

interface RequestQueueItem {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

interface RetryRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

const ORG_DUPLICATE_HINT = '同级部门名称已存在，请修改后重试'
const CODE_MESSAGE_MAP: Record<number, string> = {
  400: '请求参数或业务校验失败',
  401: '未认证或登录已过期，请重新登录',
  403: '无权限访问',
  404: '资源不存在',
  500: '服务器内部错误',
  40002: '数据冲突，请检查是否存在重复或关联数据',
  40301: '跨租户访问被拒绝',
  40302: '请求被安全策略拦截'
}

const SUCCESS_CODES = new Set([200, 20000])
const requests: RequestQueueItem[] = []
let isRefreshing = false

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
})

const refreshClient = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8',
    'X-App-Client': EXEC_APP_CLIENT
  }
})

function isPublicAuthRoute(url?: string): boolean {
  return url === '/auth/login' || url === '/auth/refresh'
}

function getMessageByCode(code: number, msg?: string): string {
  if (msg) {
    const normalized = msg.toLowerCase()
    const isSecurityBlocked = normalized.includes('security block') && normalized.includes('tenant_id')
    const isOrgUniqueError =
      normalized.includes('unique constraint failed: orgs.tenant_id, orgs.parent_id, orgs.name') ||
      normalized.includes('uq_org_name_parent') ||
      normalized.includes('duplicate key')

    if (isSecurityBlocked) {
      return '操作被租户安全策略拦截，请刷新后重试；若持续失败请联系后端修复租户过滤条件'
    }

    if (isOrgUniqueError) {
      return ORG_DUPLICATE_HINT
    }

    return msg
  }

  if (CODE_MESSAGE_MAP[code]) {
    return CODE_MESSAGE_MAP[code]
  }

  switch (code) {
    case 40001:
      return '请勿重复操作'
    case 40002:
      return '请求参数不合法'
    case 40003:
      return '导出数据超出限制'
    case 40004:
      return '当前操作缺少必要参数'
    case 401:
      return '登录已过期，请重新登录'
    case 403:
    case 40301:
      return '没有权限访问此资源'
    case 404:
    case 40401:
      return '请求的资源不存在'
    case 500:
    case 50000:
      return '服务器内部错误'
    default:
      return '请求失败'
  }
}

function flushRequests(error: unknown, newToken?: string): void {
  requests.splice(0).forEach((requestItem) => {
    if (error || !newToken) {
      requestItem.reject(error)
      return
    }
    requestItem.resolve(newToken)
  })
}

function redirectToLogin(message = '登录已过期，请重新登录'): void {
  clearAuthStorage()
  ElMessage.error(message)
  if (router.currentRoute.value.path !== '/login') {
    router.push('/login')
  }
}

async function refreshAccessToken(): Promise<string> {
  const currentRefreshToken = getRefreshTokenValue()
  if (!currentRefreshToken) {
    throw new Error('missing refresh token')
  }

  const response = await refreshClient.post<BackendResponse<{ accessToken: string; refreshToken: string }>>('/auth/refresh', {
    refreshToken: currentRefreshToken,
    refresh_token: currentRefreshToken,
    app_client: EXEC_APP_CLIENT
  })

  const payload = response.data
  if (!SUCCESS_CODES.has(payload.code) || !payload.data?.accessToken || !payload.data?.refreshToken) {
    throw new Error(getMessageByCode(payload.code, payload.msg))
  }

  setAuthTokens(payload.data)
  return payload.data.accessToken
}

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从localStorage获取token（登录/刷新等公开接口不携带）
    const token = getAccessToken()
    const isPublicRoute = isPublicAuthRoute(config.url)
    if (token && !isPublicRoute) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 执行端固定使用 exec_web 客户端标识
    config.headers['X-App-Client'] = EXEC_APP_CLIENT

    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<BackendResponse>) => {
    const { data } = response

    // 如果是文件下载等特殊响应，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }

    if (typeof data?.code === 'number') {
      if (SUCCESS_CODES.has(data.code)) {
        return data.data
      }

      const message = getMessageByCode(data.code, data.msg)
      if (data.code === 40001) {
        ElMessage.warning(message)
      } else {
        ElMessage.error(message)
      }

      return Promise.reject(new Error(message))
    }

    return data
  },
  (error: AxiosError) => {
    const originalRequest = error.config as RetryRequestConfig | undefined

    // 处理HTTP错误
    if (error.response && originalRequest) {
      const { status, data } = error.response as AxiosResponse<BackendResponse>

      if (status === 401 && !originalRequest._retry && !isPublicAuthRoute(originalRequest.url)) {
        if (!getRefreshTokenValue()) {
          redirectToLogin()
          return Promise.reject(error)
        }

        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            requests.push({
              resolve: (newToken: string) => {
                originalRequest.headers.Authorization = `Bearer ${newToken}`
                resolve(request(originalRequest))
              },
              reject
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        return refreshAccessToken()
          .then((newToken) => {
            flushRequests(null, newToken)
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return request(originalRequest)
          })
          .catch((refreshError: unknown) => {
            flushRequests(refreshError)
            redirectToLogin(refreshError instanceof Error ? refreshError.message : '登录已过期，请重新登录')
            return Promise.reject(refreshError)
          })
          .finally(() => {
            isRefreshing = false
          })
      }

      switch (status) {
        case 403:
          ElMessage.error(getMessageByCode((data as BackendResponse | undefined)?.code || 403, (data as BackendResponse | undefined)?.msg))
          break
        case 404:
          ElMessage.error(getMessageByCode((data as BackendResponse | undefined)?.code || 404, (data as BackendResponse | undefined)?.msg))
          break
        case 500:
          ElMessage.error(getMessageByCode((data as BackendResponse | undefined)?.code || 500, (data as BackendResponse | undefined)?.msg))
          break
        case 502:
          ElMessage.error('网关错误')
          break
        case 503:
          ElMessage.error('服务暂时不可用')
          break
        default:
          ElMessage.error(getMessageByCode((data as BackendResponse | undefined)?.code || status, (data as BackendResponse | undefined)?.msg))
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      // 其他错误
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

// 导出封装的请求方法
const service = async <T = any>(config: AxiosRequestConfig): Promise<T> => {
  return request(config) as unknown as Promise<T>
}

export default service

// 导出便捷方法
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.get(url, config) as unknown as Promise<T>
}

export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.post(url, data, config) as unknown as Promise<T>
}

export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.put(url, data, config) as unknown as Promise<T>
}

export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.delete(url, config) as unknown as Promise<T>
}
