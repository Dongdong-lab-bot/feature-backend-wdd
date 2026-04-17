export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

export type ApiResponse<T> = {
  code: number
  msg?: string
  message?: string
  data: T
}

export class ApiError extends Error {
  code?: number
  statusCode?: number

  constructor(message: string, extra?: { code?: number; statusCode?: number }) {
    super(message)
    this.name = 'ApiError'
    this.code = extra?.code
    this.statusCode = extra?.statusCode
  }
}

export type RequestOptions = {
  path: string
  method?: HttpMethod
  data?: any
  params?: Record<string, any>
  header?: Record<string, string>
  timeout?: number
  skipAuth?: boolean
  silent?: boolean
  disableRefreshRetry?: boolean
  idempotencyKey?: string
  disableIdempotencyKey?: boolean
}
