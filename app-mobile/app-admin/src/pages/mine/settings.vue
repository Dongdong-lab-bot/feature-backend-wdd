<template>
  <view class="container">
    <view class="menu-list">
      <!-- 更改手机号码 -->
      <view class="menu-item" @click="handleNavigate('/pages/mine/change-phone')">
        <view class="left">
          <text class="label">更改手机号码</text>
        </view>
        <view class="right">
          <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit"></image>
        </view>
      </view>

      <!-- 修改密码 -->
      <view class="menu-item" @click="handleNavigate('/pages/mine/change-password')">
        <view class="left">
          <text class="label">修改密码</text>
        </view>
        <view class="right">
          <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit"></image>
        </view>
      </view>

      <!-- 消息通知 -->
      <view class="menu-item">
        <view class="left">
          <text class="label">消息通知</text>
        </view>
        <view class="right">
          <switch :checked="isNotificationEnabled" @change="toggleNotification" color="#2561EF" style="transform:scale(0.8)" />
        </view>
      </view>

      <!-- 清除缓存 -->
      <view class="menu-item" @click="handleClearCache">
        <view class="left">
          <text class="label">清除缓存</text>
        </view>
        <view class="right">
          <text class="value">{{ cacheSize }}</text>
          <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit"></image>
        </view>
      </view>

      <!-- 升级版本 -->
      <view class="menu-item" @click="handleUpgrade">
        <view class="left">
          <text class="label">升级版本</text>
        </view>
        <view class="right">
          <text class="value" @longpress="handleDebug">当前版本 {{ version }}</text>
          <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit"></image>
        </view>
      </view>
    </view>

    <!-- 退出账号 -->
    <view class="logout-btn" @click="handleLogout">
      <text>退出账号</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { authApi } from '@/api'
import { clearAuthStorage } from '@/api/request/config'

const version = ref('2.8.9')
const cacheSize = ref('0M')
const isNotificationEnabled = ref(true)

onMounted(() => {
  calculateCacheSize()
  getSystemVersion()
})

// 计算缓存大小
const calculateCacheSize = () => {
  try {
    const res = uni.getStorageInfoSync()
    if (res && res.currentSize) {
      // currentSize 单位是 KB
      const size = res.currentSize
      if (size > 1024) {
        cacheSize.value = (size / 1024).toFixed(1) + 'M'
      } else {
        cacheSize.value = size.toFixed(1) + 'K'
      }
    } else {
      cacheSize.value = '0M'
    }
  } catch (e) {
    cacheSize.value = '0M'
  }
}

// 获取版本号
const getSystemVersion = () => {
  // 实际项目中可从 manifest.json 或 uni.getSystemInfo 获取
  // version.value = '2.8.9'
}

// 页面跳转
const handleNavigate = (url: string) => {
  uni.navigateTo({ url })
}

// 切换通知
const toggleNotification = (e: any) => {
  isNotificationEnabled.value = e.detail.value
  uni.showToast({
    title: isNotificationEnabled.value ? '已开启通知' : '已关闭通知',
    icon: 'none'
  })
}

// 清除缓存
const handleClearCache = () => {
  uni.showModal({
    title: '提示',
    content: '确定要清除本地缓存吗？',
    confirmColor: '#2561EF',
    success: (res) => {
      if (res.confirm) {
        // 保留必要的登录信息，如 token, userInfo
        const token = uni.getStorageSync('token')
        const refreshToken = uni.getStorageSync('refreshToken')
        const userInfo = uni.getStorageSync('userInfo')
        const currentUser = uni.getStorageSync('currentUser')
        const permissions = uni.getStorageSync('permissions')
        const baseUrl = uni.getStorageSync('baseUrl') // 保留环境配置
        
        uni.clearStorageSync()
        
        // 恢复必要信息
        if (token) uni.setStorageSync('token', token)
        if (refreshToken) uni.setStorageSync('refreshToken', refreshToken)
        if (userInfo) uni.setStorageSync('userInfo', userInfo)
        if (currentUser) uni.setStorageSync('currentUser', currentUser)
        if (permissions) uni.setStorageSync('permissions', permissions)
        if (baseUrl) uni.setStorageSync('baseUrl', baseUrl)
        
        calculateCacheSize()
        uni.showToast({ title: '清除成功', icon: 'success' })
      }
    }
  })
}

// 升级版本
const handleUpgrade = () => {
  uni.showToast({ title: '当前已是最新版本', icon: 'none' })
}

// 退出登录
const handleLogout = () => {
  uni.showModal({
    title: '',
    content: '确定要退出当前账号吗？',
    confirmColor: '#2561EF',
    success: (res) => {
      if (res.confirm) {
        uni.showLoading({ title: '退出中...' })
        ;(async () => {
          try {
            await authApi.logout()
          } catch {}

          clearAuthStorage()
          uni.removeStorageSync('currentUser')
          uni.removeStorageSync('permissions')

          uni.hideLoading()
          uni.reLaunch({
            url: '/pages/login/login',
            success: () => {
              uni.showToast({ title: '退出成功', icon: 'success' })
            }
          })
        })()
      }
    }
  })
}

// 长按版本号进入调试页
const handleDebug = () => {
  uni.navigateTo({ url: '/pages/common/debug' })
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #F5F5F5;
  padding-top: 20rpx;
}

.menu-list {
  background-color: #FFFFFF;
}

.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100rpx;
  padding: 0 30rpx;
  background-color: #FFFFFF;
  position: relative;
  
  &:active {
    background-color: #f9f9f9;
  }

  &::after {
    content: '';
    position: absolute;
    left: 30rpx;
    right: 0;
    bottom: 0;
    height: 1rpx;
    background-color: #E5E5E5;
    transform: scaleY(0.5);
  }

  &:last-child::after {
    display: none;
  }

  .left {
    .label {
      font-size: 30rpx;
      color: #333333;
    }
  }

  .right {
    display: flex;
    align-items: center;
    
    .value {
      font-size: 28rpx;
      color: #999999;
      margin-right: 16rpx;
    }
    
    .arrow {
      width: 24rpx;
      height: 24rpx;
      opacity: 0.4;
    }
  }
}

.logout-btn {
  margin-top: 60rpx;
  height: 100rpx;
  background-color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:active {
    background-color: #f9f9f9;
  }
  
  text {
    font-size: 32rpx;
    color: #FA746B;
  }
}
</style>
