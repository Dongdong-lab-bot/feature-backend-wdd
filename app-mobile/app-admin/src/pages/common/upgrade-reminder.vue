<template>
  <view class="page">
    <view class="mask">
      <view class="dialog">
        <view class="title">版本升级</view>
        <view class="line"></view>

        <view class="content">
          <view class="section">
            <text class="section-title">更新内容</text>
            <view class="notes">
              <text v-for="(n, idx) in notes" :key="idx" class="note">{{ idx + 1 }}.{{ n }}</text>
            </view>
          </view>

          <view class="checkbox-row" @click="dontRemind = !dontRemind">
            <view class="checkbox" :class="{ checked: dontRemind }"></view>
            <text class="checkbox-text">本次更新不再提醒</text>
          </view>
        </view>

        <view class="actions">
          <view class="action" @click="handleLater">
            <text class="action-text">以后再说</text>
          </view>
          <view class="vline"></view>
          <view class="action" @click="handleUpgrade">
            <text class="action-text primary">现在升级</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'

type UpdateInfo = {
  version: string
  notes: string[]
  downloadUrl?: string
}

const dontRemind = ref(false)
const info = ref<UpdateInfo>({
  version: '',
  notes: []
})

onLoad((options: any) => {
  const mock = typeof options?.mock === 'string' ? options.mock : ''
  if (mock === '1') {
    info.value = {
      version: '1.0.1',
      notes: ['优化部分服务使用体验；', '迭代了分享页信息展示更加清晰；'],
      downloadUrl: 'https://example.com'
    }
    return
  }

  const stored = uni.getStorageSync('reg_update_info')
  if (stored && typeof stored === 'object') {
    info.value = stored as UpdateInfo
  }
})

const notes = computed(() => {
  return Array.isArray(info.value.notes) && info.value.notes.length
    ? info.value.notes
    : ['优化部分服务使用体验；', '迭代了分享页信息展示更加清晰；']
})

const ignoreIfNeeded = () => {
  if (dontRemind.value && info.value.version) {
    uni.setStorageSync('reg_update_ignoreVersion', info.value.version)
  }
}

const handleLater = () => {
  ignoreIfNeeded()
  uni.navigateBack()
}

const handleUpgrade = () => {
  ignoreIfNeeded()
  const url = info.value.downloadUrl || ''
  if (!url) {
    uni.showToast({ title: '下载地址为空', icon: 'none' })
    return
  }
  const plusAny = (globalThis as any).plus
  if (plusAny?.runtime?.openURL) {
    plusAny.runtime.openURL(url)
    return
  }
  if (typeof window !== 'undefined' && typeof window.open === 'function') {
    window.open(url, '_blank')
    return
  }
  uni.showToast({ title: '请在浏览器打开下载链接', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: transparent;
}

.mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 60rpx;
  box-sizing: border-box;
}

.dialog {
  width: 100%;
  max-width: 560rpx;
  border-radius: 16rpx;
  background: #ffffff;
  overflow: hidden;
}

.title {
  padding: 32rpx 32rpx 22rpx;
  font-size: 32rpx;
  color: #2561ef;
  font-weight: 800;
}

.line {
  height: 1px;
  background: rgba(242, 242, 242, 0.5);
}

.content {
  padding: 22rpx 32rpx 10rpx;
  box-sizing: border-box;
}

.section-title {
  font-size: 26rpx;
  color: #333333;
  font-weight: 700;
}

.notes {
  margin-top: 14rpx;
}

.note {
  display: block;
  font-size: 24rpx;
  color: #333333;
  line-height: 40rpx;
}

.checkbox-row {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding-bottom: 6rpx;
}

.checkbox {
  width: 28rpx;
  height: 28rpx;
  border-radius: 999rpx;
  border: 2rpx solid #d9d9d9;
  box-sizing: border-box;
  position: relative;
}

.checkbox.checked {
  border-color: #2561ef;
}

.checkbox.checked::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: #2561ef;
}

.checkbox-text {
  font-size: 24rpx;
  color: #b3b3b3;
}

.actions {
  height: 96rpx;
  display: flex;
  align-items: center;
}

.action {
  flex: 1;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-text {
  font-size: 30rpx;
  color: #333333;
  font-weight: 700;
}

.action-text.primary {
  color: #2561ef;
}

.vline {
  width: 1px;
  height: 40rpx;
  background: rgba(242, 242, 242, 0.5);
}
</style>
