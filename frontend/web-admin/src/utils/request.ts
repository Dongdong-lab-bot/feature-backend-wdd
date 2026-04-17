import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { clearRegAuth, getRegTenantId, getRegToken } from '@/utils/auth-storage'

const ORG_DUPLICATE_HINT = '同级部门名称已存在，请修改后重试'
const APP_CLIENT = 'reg_app'

interface CommonResponse<T = any> {
  code: number
  msg: string
  data: T
}

const SUCCESS_CODES = new Set([200, 20000])

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

function resolveBackendErrorMessage(data: any, status?: number): string {
  const rawMessage = data?.msg || data?.message || data?.detail

  if (typeof rawMessage === 'string') {
    const normalized = rawMessage.toLowerCase()
    const isSecurityBlocked = normalized.includes('security block') && normalized.includes("tenant_id")
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

    return rawMessage
  }

  if (typeof data?.code === 'number' && CODE_MESSAGE_MAP[data.code]) {
    return CODE_MESSAGE_MAP[data.code]
  }

  if (typeof status === 'number' && CODE_MESSAGE_MAP[status]) {
    return CODE_MESSAGE_MAP[status]
  }

  switch (status) {
    case 401:
      return '登录已过期，请重新登录'
    case 403:
      return '没有权限访问此资源'
    case 404:
      return '请求的资源不存在'
    case 500:
      return '服务器内部错误'
    case 502:
      return '网关错误'
    case 503:
      return '服务暂时不可用'
    default:
      return '请求失败'
  }
}

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 从localStorage获取token（登录/刷新等公开接口不携带）
    const token = getRegToken()
    const isPublicRoute = config.url === '/auth/login' || config.url === '/auth/refresh'
    if (token && !isPublicRoute) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 从localStorage获取租户ID
    const tenantId = getRegTenantId()
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId
    }

    // 监管端固定使用 reg_app 客户端标识
    config.headers['X-App-Client'] = APP_CLIENT

    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse<CommonResponse>) => {
    const { data, status } = response

    // 如果是文件下载等特殊响应，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }

    // 标准响应结构：{ code, msg, data }
    if (data && typeof data.code === 'number') {
      if (SUCCESS_CODES.has(data.code)) {
        // 保持兼容：仍返回完整包裹结构，避免现有页面改动
        return data
      }

      const message = resolveBackendErrorMessage(data, status)
      ElMessage.error(message)

      const businessError = new Error(message) as Error & { data?: CommonResponse; __shown?: boolean }
      businessError.data = data
      businessError.__shown = true
      return Promise.reject(businessError)
    }

    // 兼容非标准响应
    if (status === 200) {
      return data as any
    }

    // 其他状态码
    const message = resolveBackendErrorMessage(data, status)
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  },
  (error: AxiosError) => {
    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response as AxiosResponse

      if (status === 401 || (data as any)?.code === 401) {
        ElMessage.error(resolveBackendErrorMessage(data, status))
        clearRegAuth()
        router.push('/login')
      } else {
        const message = resolveBackendErrorMessage(data, status)
        ElMessage.error(message)
      }

      ;(error as any).__shown = true
    } else if (error.request) {
      // 请求已发出但没有收到响应
      ElMessage.error('网络连接失败，请检查网络')
      ;(error as any).__shown = true
    } else {
      // 其他错误
      ElMessage.error('请求配置错误')
      ;(error as any).__shown = true
    }

    return Promise.reject(error)
  }
)

// 导出封装的请求方法
export default request

// 导出便捷方法
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.get(url, config)
}

export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.post(url, data, config)
}

export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.put(url, data, config)
}

export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.delete(url, config)
}
