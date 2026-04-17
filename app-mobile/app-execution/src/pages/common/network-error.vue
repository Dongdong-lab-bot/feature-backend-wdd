<template>
  <view class="page">
    <view class="center">
      <view class="wifi-wrap">
        <image class="wifi" src="/static/common/icon-wifi.svg" mode="aspectFit" />
        <view class="dot">
          <image class="close" src="/static/common/icon-close.svg" mode="aspectFit" />
        </view>
      </view>
      <text class="text">网络无连接，请检查网络设置</text>
      <button class="btn" @click="handleRefresh">点击刷新</button>
    </view>
  </view>
</template>

<script setup lang="ts">
const checkConnected = (): Promise<boolean> => {
  return new Promise((resolve) => {
    uni.getNetworkType({
      success: (res) => resolve(res.networkType !== 'none'),
      fail: () => resolve(false)
    })
  })
}

const handleRefresh = async () => {
  const connected = await checkConnected()
  if (!connected) {
    uni.showToast({ title: '网络好像有点问题，请检查后重试！', icon: 'none' })
    return
  }
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.center {
  width: 100%;
  padding: 0 30rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateY(-60rpx);
}

.wifi-wrap {
  width: 150rpx;
  height: 136rpx;
  position: relative;
  opacity: 0.3;
}

.wifi {
  width: 150rpx;
  height: 136rpx;
}

.dot {
  position: absolute;
  left: 50%;
  top: 64%;
  transform: translate(-50%, -50%);
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close {
  width: 28rpx;
  height: 28rpx;
}

.text {
  margin-top: 18rpx;
  font-size: 26rpx;
  color: #b3b3b3;
  font-weight: 600;
}

.btn {
  margin-top: 22rpx;
  width: 220rpx;
  height: 70rpx;
  line-height: 70rpx;
  border-radius: 8rpx;
  border: 1px solid #2561ef;
  background: #ffffff;
  color: #2561ef;
  font-size: 28rpx;
  font-weight: 600;
}
</style>
