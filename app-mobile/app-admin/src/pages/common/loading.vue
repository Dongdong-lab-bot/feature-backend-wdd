<template>
  <view class="page">
    <view class="header">
      <text class="title">消息</text>
    </view>

    <scroll-view
      class="body"
      scroll-y
      :refresher-enabled="mode === 'pull'"
      :refresher-triggered="refresherTriggered"
      refresher-default-style="none"
      @refresherpulling="onPulling"
      @refresherrefresh="onRefresh"
      @refresherrestore="onRestore"
      @refresherabort="onAbort"
    >
      <view slot="refresher" class="refresher">
        <text class="refresher-text">{{ refresherText }}</text>
        <view v-if="refresherState === 'refreshing'" class="refresher-loading">
          <view class="spinner small"></view>
          <text class="refresher-text">正在刷新</text>
        </view>
      </view>

      <view class="content">
        <view class="placeholder">
          <image class="placeholder-icon" src="/static/common/icon-image.svg" mode="aspectFit" />
        </view>
      </view>
    </scroll-view>

    <view v-if="mode === 'auto' && autoLoading" class="auto-loading">
      <view class="spinner"></view>
      <text class="auto-text">正在加载...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

type Mode = 'pull' | 'auto'
type RefresherState = 'pulling' | 'ready' | 'refreshing'

const mode = ref<Mode>('pull')

onLoad((options: any) => {
  const t = typeof options?.type === 'string' ? options.type : ''
  if (t === 'auto' || t === 'pull') {
    mode.value = t
  }
})

const refresherTriggered = ref(false)
const refresherState = ref<RefresherState>('pulling')
const refresherDy = ref(0)

const refresherText = computed(() => {
  if (refresherState.value === 'refreshing') return ''
  if (refresherState.value === 'ready') return '松开刷新'
  return '下拉刷新'
})

const onPulling = (e: any) => {
  const dy = Number(e?.detail?.dy || 0)
  refresherDy.value = dy
  if (refresherTriggered.value) return
  refresherState.value = dy > 60 ? 'ready' : 'pulling'
}

const onRefresh = async () => {
  refresherTriggered.value = true
  refresherState.value = 'refreshing'
  await new Promise((r) => setTimeout(r, 900))
  refresherTriggered.value = false
  refresherState.value = 'pulling'
}

const onRestore = () => {
  if (refresherTriggered.value) return
  refresherState.value = 'pulling'
}

const onAbort = () => {
  if (refresherTriggered.value) return
  refresherState.value = 'pulling'
}

const autoLoading = ref(false)
let unsubscribeNetwork: null | (() => void) = null

const runAutoLoad = async () => {
  autoLoading.value = true
  await new Promise((r) => setTimeout(r, 900))
  autoLoading.value = false
}

onMounted(() => {
  if (mode.value !== 'auto') return
  
  uni.getNetworkType({
    success: (res) => {
      if (res.networkType !== 'none') {
        runAutoLoad()
      }
    }
  })
  
  const cb = (res: any) => {
    if (res?.isConnected) {
      runAutoLoad()
    }
  }
  uni.onNetworkStatusChange(cb)
  unsubscribeNetwork = () => {
    if (typeof (uni as any).offNetworkStatusChange === 'function') {
      ;(uni as any).offNetworkStatusChange(cb)
    }
  }
})

onBeforeUnmount(() => {
  unsubscribeNetwork?.()
  unsubscribeNetwork = null
})
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #ffffff;
  display: flex;
  flex-direction: column;
}

.header {
  height: calc(var(--status-bar-height) + 88rpx);
  padding-top: var(--status-bar-height);
  padding-left: 30rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.title {
  font-size: 42rpx;
  font-weight: 700;
  color: #111111;
}

.body {
  flex: 1;
  min-height: 0;
}

.refresher {
  height: 120rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999999;
}

.refresher-text {
  font-size: 26rpx;
  font-weight: 600;
  color: #999999;
}

.refresher-loading {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.content {
  padding: 0 30rpx 30rpx;
  box-sizing: border-box;
}

.placeholder {
  margin-top: 60rpx;
  height: 760rpx;
  background: rgba(37, 97, 239, 0.08);
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  width: 120rpx;
  height: 120rpx;
}

.auto-loading {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
}

.auto-text {
  margin-top: 18rpx;
  font-size: 26rpx;
  color: #999999;
  font-weight: 600;
}

.spinner {
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  border: 4rpx solid rgba(0, 0, 0, 0.08);
  border-top-color: rgba(0, 0, 0, 0.35);
  animation: spin 1s linear infinite;
}

.spinner.small {
  width: 30rpx;
  height: 30rpx;
  border-width: 3rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
