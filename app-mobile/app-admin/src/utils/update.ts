export type UpdateInfo = {
  version: string
  notes: string[]
  downloadUrl?: string
}

const isAlreadyOpen = () => {
  try {
    const pages = (getCurrentPages?.() as any[]) || []
    return pages.some((p) => p?.route === 'pages/common/upgrade-reminder')
  } catch {
    return false
  }
}

export const setLatestUpdateInfo = (info: UpdateInfo) => {
  uni.setStorageSync('reg_update_latest', info)
}

export const getLatestUpdateInfo = (): UpdateInfo | null => {
  const stored = uni.getStorageSync('reg_update_latest')
  if (!stored || typeof stored !== 'object') return null
  const v = (stored as any).version
  const notes = (stored as any).notes
  if (typeof v !== 'string' || !Array.isArray(notes)) return null
  return stored as UpdateInfo
}

export const promptUpgrade = (info: UpdateInfo) => {
  const ignore = uni.getStorageSync('reg_update_ignoreVersion')
  if (typeof ignore === 'string' && ignore && ignore === info.version) return
  if (isAlreadyOpen()) return
  uni.setStorageSync('reg_update_info', info)
  uni.navigateTo({ url: '/pages/common/upgrade-reminder' })
}

export const checkUpdateOnLaunch = () => {
  const latest = getLatestUpdateInfo()
  if (!latest) return
  promptUpgrade(latest)
}

