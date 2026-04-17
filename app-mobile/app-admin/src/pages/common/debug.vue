<template>
  <view class="container">
    <view class="card">
      <view class="card-title">环境配置</view>

      <view class="field">
        <view class="label">接口地址（baseUrl）</view>
        <view class="desc">手机端请使用电脑局域网 IP + 端口，不要使用 127.0.0.1</view>
        <input class="input" v-model="baseUrl" placeholder="http://10.x.x.x:8000" />
        <view class="hint">当前生效：{{ effectiveBaseUrl }}</view>
      </view>

      <view class="actions">
        <button class="btn primary" @click="save">保存</button>
        <button class="btn" @click="useCurrentIp">使用当前IP</button>
        <button class="btn" @click="reset">恢复默认</button>
        <button class="btn" @click="test">测试连接</button>
      </view>

      <view class="meta">
        <view class="meta-item">appClient：{{ appClient }}</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const DEFAULT_BASE_URL = 'http://10.154.117.176:8000'

const normalizeBaseUrl = (value: string) => {
  let v = (value || '').trim()
  if (!v) return ''
  if (!/^https?:\/\//i.test(v)) {
    v = `http://${v}`
  }
  v = v.replace(/\/+$/, '')
  return v
}

const baseUrl = ref(normalizeBaseUrl(uni.getStorageSync('baseUrl')) || DEFAULT_BASE_URL)

const effectiveBaseUrl = computed(() => {
  return normalizeBaseUrl(uni.getStorageSync('baseUrl')) || DEFAULT_BASE_URL
})

const appClient = computed(() => uni.getStorageSync('appClient') || 'reg_app')

const useCurrentIp = () => {
  baseUrl.value = DEFAULT_BASE_URL
  uni.showToast({ title: '已填入当前IP', icon: 'none' })
}

const save = () => {
  const next = normalizeBaseUrl(baseUrl.value)
  if (!next) {
    uni.showToast({ title: '请输入接口地址', icon: 'none' })
    return
  }
  uni.setStorageSync('baseUrl', next)
  uni.showToast({ title: '已保存', icon: 'success' })
}

const reset = () => {
  uni.removeStorageSync('baseUrl')
  baseUrl.value = DEFAULT_BASE_URL
  uni.showToast({ title: '已恢复默认', icon: 'success' })
}

const test = () => {
  const url = normalizeBaseUrl(baseUrl.value) || DEFAULT_BASE_URL
  uni.showLoading({ title: '测试中...' })
  uni.request({
    url: `${url}/docs`,
    method: 'GET',
    success: (res) => {
      if (res.statusCode >= 200 && res.statusCode < 500) {
        uni.showToast({ title: '连接成功', icon: 'success' })
        return
      }
      uni.showToast({ title: `连接失败(${res.statusCode})`, icon: 'none' })
    },
    fail: (err) => {
      const msg = typeof err?.errMsg === 'string' ? err.errMsg : '连接失败'
      uni.showToast({ title: msg, icon: 'none' })
    },
    complete: () => {
      uni.hideLoading()
    }
  })
}
</script>

<style lang="scss" scoped>
.container {
  padding: 24rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 28rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333333;
  margin-bottom: 24rpx;
}

.field {
  margin-bottom: 28rpx;
}

.label {
  font-size: 28rpx;
  color: #333333;
  margin-bottom: 10rpx;
}

.desc {
  font-size: 24rpx;
  color: #999999;
  margin-bottom: 14rpx;
  line-height: 1.4;
}

.input {
  height: 84rpx;
  border: 1rpx solid #e6e6e6;
  border-radius: 12rpx;
  padding: 0 22rpx;
  font-size: 28rpx;
  background: #ffffff;
}

.hint {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #666666;
}

.actions {
  display: flex;
  gap: 16rpx;
}

.btn {
  flex: 1;
  height: 84rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f2f2f2;
  color: #333333;
}

.btn.primary {
  background: #2561ef;
  color: #ffffff;
}

.meta {
  margin-top: 22rpx;
}

.meta-item {
  font-size: 24rpx;
  color: #999999;
}
</style>
