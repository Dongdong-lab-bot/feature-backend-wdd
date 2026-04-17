<template>
  <view class="page">
    <view class="mask">
      <view class="dialog">
        <view class="dialog-content">
          <text class="msg">{{ message }}</text>
        </view>
        <view class="divider"></view>
        <view class="confirm" @click="handleConfirm">
          <text class="confirm-text">确定</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

type AccountErrorType = 'expired' | 'occupied' | 'data'

const type = ref<AccountErrorType>('expired')

onLoad((options: any) => {
  const t = typeof options?.type === 'string' ? options.type : ''
  if (t === 'occupied' || t === 'data' || t === 'expired') {
    type.value = t
  }
})

const message = computed(() => {
  if (type.value === 'occupied') return '账户已在其他手机设备登录，请\n重新登录'
  if (type.value === 'data') return '请求失败，请退出后\n重新登录'
  return '你的登录状态已过期，请\n重新登录'
})

const handleConfirm = () => {
  uni.reLaunch({ url: '/pages/login/login' })
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

.dialog-content {
  padding: 48rpx 40rpx 36rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg {
  text-align: center;
  font-size: 28rpx;
  color: #333333;
  line-height: 44rpx;
  white-space: pre-line;
  font-weight: 600;
}

.divider {
  height: 1px;
  background: rgba(242, 242, 242, 0.5);
}

.confirm {
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-text {
  font-size: 32rpx;
  color: #2561ef;
  font-weight: 700;
}
</style>
