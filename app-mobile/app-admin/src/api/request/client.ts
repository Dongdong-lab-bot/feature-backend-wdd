import { clearAuthStorage, getAppClient, getBaseUrl, getRefreshToken, getTimeout, getToken, setAuthTokens } from './config'
import { ApiError, type ApiResponse, type HttpMethod, type RequestOptions } from './types'

const SUCCESS_CODES = new Set([200, 20000])

const buildUrl = (path: string, params?: Record<string, any>) => {
  const base = getBaseUrl()
  const p = path.startsWith('/') ? path : `/${path}`
  const url = `${base}${p}`
  if (!params) return url
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  if (!entries.length) return url
  const query = entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
  return `${url}${url.includes('?') ? '&' : '?'}${query}`
}

let refreshingPromise: Promise<boolean> | null = null

const clearRefreshPromise = () => {
  refreshingPromise = null
}

const createIdempotencyKey = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const getResponseMessage = (body: any) => {
  return body?.msg || body?.message || '请求失败'
}

const callRawRequest = (options: RequestOptions, url: string, method: HttpMethod, header: Record<string, string>) => {
  return new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
    uni.request({
      url,
      method: method as any,
      data: options.data,
      timeout: options.timeout ?? getTimeout(),
      header,
      success: resolve,
      fail: reject
    })
  })
}

const runRefresh = async () => {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false
  const url = buildUrl('/auth/refresh')
  const method: HttpMethod = 'POST'
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-App-Client': getAppClient()
  }
  try {
    const res = await callRawRequest(
      {
        path: '/auth/refresh',
        method,
        skipAuth: true,
        silent: true,
        disableRefreshRetry: true,
        data: { refreshToken }
      },
      url,
      method,
      header
    )
    const body = (res.data || {}) as ApiResponse<{ accessToken: string; refreshToken: string }>
    if (
      Number(res.statusCode || 0) >= 200 &&
      Number(res.statusCode || 0) < 300 &&
      SUCCESS_CODES.has(body.code) &&
      body.data?.accessToken &&
      body.data?.refreshToken
    ) {
      setAuthTokens(body.data.accessToken, body.data.refreshToken)
      return true
    }
    return false
  } catch {
    clearRefreshPromise()
    return false
  }
}

const ensureRefreshed = async () => {
  if (!refreshingPromise) {
    refreshingPromise = runRefresh().finally(() => {
      refreshingPromise = null
    })
  }
  return refreshingPromise
}

const executeRequest = async <T>(options: RequestOptions, allowRetry: boolean): Promise<T> => {
  const method = (options.method || 'GET') as HttpMethod
  const url = buildUrl(options.path, options.params)
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-App-Client': getAppClient(),
    ...(options.header || {})
  }

  if (!options.skipAuth) {
    const token = getToken()
    if (token) {
      header.Authorization = `Bearer ${token}`
    }
  }

  const shouldAttachIdempotencyKey =
    method !== 'GET' &&
    !options.disableIdempotencyKey &&
    !header['Idempotency-Key']
  if (shouldAttachIdempotencyKey) {
    header['Idempotency-Key'] = options.idempotencyKey || createIdempotencyKey()
  }

  try {
    const res = await callRawRequest(options, url, method, header)

    const statusCode = Number(res.statusCode || 0)
    const body = (res.data || {}) as ApiResponse<T>
    if (statusCode < 200 || statusCode >= 300) {
      if (statusCode === 401 && !options.skipAuth && !options.disableRefreshRetry && allowRetry) {
        const refreshed = await ensureRefreshed()
        if (refreshed) {
          return executeRequest<T>(options, false)
        }
        clearAuthStorage()
      }
      const failMsg = getResponseMessage(body)
      throw new ApiError(failMsg === '请求失败' ? `请求失败(${statusCode})` : failMsg, { statusCode, code: body.code })
    }

    if (typeof body.code !== 'number') {
      throw new ApiError('响应格式错误')
    }

    if (!SUCCESS_CODES.has(body.code)) {
      if (body.code === 401 && !options.skipAuth && !options.disableRefreshRetry && allowRetry) {
        const refreshed = await ensureRefreshed()
        if (refreshed) {
          return executeRequest<T>(options, false)
        }
        clearAuthStorage()
      }
      throw new ApiError(getResponseMessage(body), { code: body.code, statusCode })
    }

    return body.data
  } catch (e: any) {
    if (e instanceof ApiError) {
      if (!options.silent) {
        uni.showToast({ title: e.message, icon: 'none' })
      }
      throw e
    }
    const msg = typeof e?.errMsg === 'string' ? e.errMsg : '网络异常'
    if (!options.silent) {
      uni.showToast({ title: msg, icon: 'none' })
    }
    throw new ApiError(msg)
  }
}

export const request = async <T>(options: RequestOptions): Promise<T> => {
  return executeRequest<T>(options, true)
}
