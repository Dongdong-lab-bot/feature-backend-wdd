export type ApiResponse<T = any> = {
  code: number
  msg: string
  data: T
}

/**
 * 统一接口请求封装
 * - 自动拼 baseUrl
 * - 自动带 Authorization 和 X-App-Client
 */
export function apiRequest<T = any>(
  path: string,
  opts: Omit<UniApp.RequestOptions, 'url'> = {}
): Promise<T> {
  const baseUrl = uni.getStorageSync('baseUrl')
  const token = uni.getStorageSync('token')
  const appClient = uni.getStorageSync('appClient') || 'exec_app'

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${baseUrl}${path}`,
      method: opts.method || 'GET',
      data: opts.data || {},
      header: {
        'Authorization': token ? `Bearer ${token}` : '',
        'X-App-Client': appClient,
        'Content-Type': 'application/json',
        ...(opts.header || {})
      },
      success: ({ data, statusCode }) => {
        const res = data as any

        // 兼容不同的后端返回结构：
        // 1. 如果有 code 并且是 200 或 20000，返回 data 或本身
        // 2. 如果直接返回数组或对象（没有 code 包装层），且 HTTP 状态码为 200，直接返回
        if (statusCode === 200) {
          if (res && (res.code === 200 || res.code === 20000)) {
            resolve(res.data !== undefined ? res.data : res)
          } else if (res && typeof res.code === 'number' && res.code !== 200 && res.code !== 20000) {
            reject(res)
          } else {
            // 直接返回业务数据（如后端 FastAPI 直接返回 List 或 dict 时）
            resolve(res)
          }
        } else {
          reject(res)
        }
      },
      fail: reject
    })
  })
}