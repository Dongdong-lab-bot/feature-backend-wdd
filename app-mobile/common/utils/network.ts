type NetworkState = {
  isConnected: boolean
  networkType: string
}

let state: NetworkState = {
  isConnected: true,
  networkType: 'unknown'
}

let lastToastAt = 0

export const getNetworkState = () => state

export const setNetworkState = (next: Partial<NetworkState>) => {
  state = { ...state, ...next }
}

export const checkNetwork = (): Promise<NetworkState> => {
  return new Promise((resolve) => {
    uni.getNetworkType({
      success: (res) => {
        const next = {
          isConnected: res.networkType !== 'none',
          networkType: res.networkType
        }
        setNetworkState(next)
        resolve(getNetworkState())
      },
      fail: () => {
        const next = { isConnected: false, networkType: 'none' }
        setNetworkState(next)
        resolve(getNetworkState())
      }
    })
  })
}

const canToast = () => {
  const now = Date.now()
  if (now - lastToastAt < 1200) return false
  lastToastAt = now
  return true
}

export const toastNoNetwork = () => {
  if (!canToast()) return
  uni.showToast({ title: '网络好像有点问题，请检查后重试！', icon: 'none' })
}

export const toastRequestFailed = () => {
  if (!canToast()) return
  uni.showToast({ title: '请求失败', icon: 'none' })
}

export const ensureConnected = async () => {
  const s = await checkNetwork()
  if (!s.isConnected) {
    toastNoNetwork()
    return false
  }
  return true
}

export const setupNetworkMonitor = () => {
  checkNetwork()
  uni.onNetworkStatusChange((res) => {
    setNetworkState({ isConnected: res.isConnected, networkType: res.networkType })
  })
}

export const setupRequestInterceptor = () => {
  uni.addInterceptor('request', {
    invoke: () => {
      if (!getNetworkState().isConnected) {
        toastNoNetwork()
        return false
      }
    },
    fail: (err: any) => {
      if (!getNetworkState().isConnected) {
        toastNoNetwork()
        return
      }
      const msg = typeof err?.errMsg === 'string' ? err.errMsg : ''
      if (msg.includes('abort')) return
      toastRequestFailed()
    }
  })
}
