let refreshPromise = null;

function getBaseUrl() {
  return uni.getStorageSync('baseUrl') || 'http://127.0.0.1:8000'
}

function getAppClient() {
  return uni.getStorageSync('appClient') || 'reg_app'
}

function getAuthStorageKeys(appClient = getAppClient()) {
  return {
    accessTokenKey: `${appClient}_accessToken`,
    refreshTokenKey: `${appClient}_refreshToken`,
    userInfoKey: `${appClient}_userInfo`,
    permissionsKey: `${appClient}_permissions`,
    tenantIdKey: `${appClient}_tenant_id`
  }
}

export function clearAuthStorage(appClient = getAppClient()) {
  const { accessTokenKey, refreshTokenKey, userInfoKey, permissionsKey, tenantIdKey } =
    getAuthStorageKeys(appClient)

  uni.removeStorageSync(accessTokenKey)
  uni.removeStorageSync(refreshTokenKey)
  uni.removeStorageSync(userInfoKey)
  uni.removeStorageSync(permissionsKey)
  uni.removeStorageSync(tenantIdKey)
}

export function logoutToLogin() {
  clearAuthStorage()
  uni.reLaunch({ url: '/pages/login/login' })
}

export function setTokenPair(payload, appClient = getAppClient()) {
  const { accessTokenKey, refreshTokenKey } = getAuthStorageKeys(appClient)

  if (payload?.accessToken) {
    uni.setStorageSync(accessTokenKey, payload.accessToken)
  }

  if (payload?.refreshToken) {
    uni.setStorageSync(refreshTokenKey, payload.refreshToken)
  }
}

function isAuthLoginUrl(url = '') {
  return url.includes('/auth/login')
}

function isAuthRefreshUrl(url = '') {
  return url.includes('/auth/refresh')
}

function doRefresh() {
  const appClient = getAppClient()
  const { refreshTokenKey } = getAuthStorageKeys(appClient)
  const refreshToken = uni.getStorageSync(refreshTokenKey)

  if (!refreshToken) {
    logoutToLogin()
    return Promise.reject(new Error('refresh token missing'))
  }

  const BASE_URL = getBaseUrl()

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}/api/v1/auth/refresh`,
      method: 'POST',
      header: { 'X-App-Client': appClient, 'Content-Type': 'application/json;charset=UTF-8' },
      data: { refreshToken },
      success: (res) => {
        const data = res && res.data && res.data.data
        if (res.statusCode === 200 && data && data.accessToken) {
          setTokenPair(data, appClient)
          resolve(data.accessToken)
          return
        }
        logoutToLogin()
        reject(new Error('refresh failed'))
      },
      fail: () => {
        logoutToLogin()
        reject(new Error('refresh failed'))
      }
    })
  })
}

export function request(urlOrOptions, configOptions) {
  let options = {}
  if (typeof urlOrOptions === 'string') {
    options = Object.assign({}, configOptions, { url: urlOrOptions })
  } else {
    options = urlOrOptions || {}
  }

  return new Promise((resolve, reject) => {
    const BASE_URL = getBaseUrl()
    const appClient = getAppClient()

    const { accessTokenKey } = getAuthStorageKeys(appClient)
    const accessToken = uni.getStorageSync(accessTokenKey)

    const headers = Object.assign({}, options.header || {}, {
      'X-App-Client': appClient
    })

    const isPublicRoute = isAuthLoginUrl(options.url) || isAuthRefreshUrl(options.url)

    if (accessToken && !isPublicRoute) {
      headers.Authorization = `Bearer ${accessToken}`
    }

    const pathStr = options.url || ''
    const url = pathStr.startsWith('http') ? pathStr : `${BASE_URL}${pathStr}`

    uni.request({
      ...options,
      url,
      header: headers,
      success: (res) => {
        if (res.statusCode !== 401 || isPublicRoute) {
          resolve(res)
          return
        }

        if (isAuthRefreshUrl(options.url)) {
          logoutToLogin()
          reject(res)
          return
        }

        if (!refreshPromise) {
          refreshPromise = doRefresh().finally(() => {
            refreshPromise = null
          })
        }

        refreshPromise
          .then((newToken) => {
            const retryHeaders = Object.assign({}, headers, { Authorization: `Bearer ${newToken}` })
            uni.request({
              ...options,
              url,
              header: retryHeaders,
              success: (retryRes) => resolve(retryRes),
              fail: (err) => reject(err)
            })
          })
          .catch((err) => reject(err))
      },
      fail: (err) => reject(err)
    })
  })
}
