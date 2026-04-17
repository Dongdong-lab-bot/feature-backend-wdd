import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

export interface RequestConfig {
  appClient: string
  baseURL?: string
  includeTenantId?: boolean
}

export function createRequest(config: RequestConfig): AxiosInstance {
  const request = axios.create({
    baseURL: config.baseURL || import.meta.env.VITE_APP_BASE_API,
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json;charset=UTF-8'
    }
  })

  request.interceptors.request.use(
    (requestConfig) => {
      const token = localStorage.getItem('token')
      const isPublicRoute = requestConfig.url === '/auth/login' || requestConfig.url === '/auth/refresh'
      if (token && !isPublicRoute) {
        requestConfig.headers.Authorization = `Bearer ${token}`
      }

      requestConfig.headers['X-App-Client'] = config.appClient

      if (config.includeTenantId) {
        const tenantId = localStorage.getItem('tenant_id')
        if (tenantId) {
          requestConfig.headers['X-Tenant-ID'] = tenantId
        }
      }

      return requestConfig
    },
    (error: AxiosError) => {
      console.error('Request error:', error)
      return Promise.reject(error)
    }
  )

  request.interceptors.response.use(
    (response: AxiosResponse) => {
      if (response.config.responseType === 'blob') {
        return response
      }

      if (response.status === 200) {
        return response.data
      }

      ElMessage.error((response.data as any)?.message || 'Request failed')
      return Promise.reject(new Error((response.data as any)?.message || 'Request failed'))
    },
    (error: AxiosError) => {
      if (error.response) {
        const { status, data } = error.response as AxiosResponse

        switch (status) {
          case 401:
            ElMessage.error('Login expired, please login again')
            localStorage.removeItem('token')
            localStorage.removeItem('user_info')
            localStorage.removeItem('tenant_id')
            window.location.href = '/login'
            break
          case 403:
            ElMessage.error('No permission to access this resource')
            break
          case 404:
            ElMessage.error('Requested resource not found')
            break
          case 500:
            ElMessage.error('Internal server error')
            break
          case 502:
            ElMessage.error('Gateway error')
            break
          case 503:
            ElMessage.error('Service temporarily unavailable')
            break
          default:
            ElMessage.error((data as any)?.message || 'Request failed')
        }
      } else if (error.request) {
        ElMessage.error('Network connection failed, please check network')
      } else {
        ElMessage.error('Request configuration error')
      }

      return Promise.reject(error)
    }
  )

  return request
}

export function createRequestService(config: RequestConfig) {
  const request = createRequest(config)

  const service = async <T = any>(axiosConfig: AxiosRequestConfig): Promise<T> => {
    return request(axiosConfig) as unknown as Promise<T>
  }

  service.get = <T = any>(url: string, axiosConfig?: AxiosRequestConfig): Promise<T> => {
    return request.get(url, axiosConfig) as unknown as Promise<T>
  }

  service.post = <T = any>(url: string, data?: any, axiosConfig?: AxiosRequestConfig): Promise<T> => {
    return request.post(url, data, axiosConfig) as unknown as Promise<T>
  }

  service.put = <T = any>(url: string, data?: any, axiosConfig?: AxiosRequestConfig): Promise<T> => {
    return request.put(url, data, axiosConfig) as unknown as Promise<T>
  }

  service.del = <T = any>(url: string, axiosConfig?: AxiosRequestConfig): Promise<T> => {
    return request.delete(url, axiosConfig) as unknown as Promise<T>
  }

  service.instance = request

  return service
}

export type RequestService = ReturnType<typeof createRequestService>