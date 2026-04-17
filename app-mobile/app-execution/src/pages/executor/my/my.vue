<template>
  <view class="page">
    <NavBar title="我的" :showBack="false">
      <template #right>
        <view class="nav-right-btn" @click="goSettings">
          <image class="setting-icon" src="/static/mine/icon-setting.svg" mode="aspectFit" />
        </view>
      </template>
    </NavBar>

    <view class="profile-card" @click="goProfile">
      <view class="profile-left">
        <image class="avatar" src="/static/mine/avatar.svg" mode="aspectFit" />
        <view class="profile-info">
          <view class="name-row">
            <text class="name">李明明</text>
            <view class="status-tag">在职</view>
          </view>
          <text class="role">食安总监</text>
        </view>
      </view>
    </view>

    <view class="menu-list">
      <view class="menu-item" @click="goNotifications">
        <view class="item-left">
          <view class="icon-wrap">
            <image class="item-icon" src="/static/mine/icon-notice.svg" mode="aspectFit" />
            <view class="badge">3</view>
          </view>
          <text class="item-title">消息通知与预警</text>
        </view>
        <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>

      <view class="menu-item" @click="goEmployee">
        <view class="item-left">
          <image class="item-icon" src="/static/mine/icon-employee.svg" mode="aspectFit" />
          <text class="item-title">员工管理</text>
        </view>
        <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>

      <view class="menu-item" @click="goDataCenter">
        <view class="item-left">
          <image class="item-icon" src="/static/mine/icon-device.svg" mode="aspectFit" />
          <text class="item-title">智能化设备数据</text>
        </view>
        <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>

      <view class="menu-item" @click="goVideo">
        <view class="item-left">
          <image class="item-icon" src="/static/mine/icon-video.svg" mode="aspectFit" />
          <text class="item-title">食堂视频查看</text>
        </view>
        <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>

      <view class="menu-item" @click="goAbout">
        <view class="item-left">
          <image class="item-icon" src="/static/mine/icon-about.svg" mode="aspectFit" />
          <text class="item-title">关于我们</text>
        </view>
        <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import NavBar from '@/components/NavBar/NavBar.vue'

const goProfile = () => {
  uni.navigateTo({ url: '/pages/executor/my/profile/profile' })
}

const goSettings = () => {
  uni.navigateTo({ url: '/pages/executor/my/settings/settings' })
}

const goNotifications = () => {
  uni.navigateTo({ url: '/pages/executor/my/notifications/notifications' })
}

const goEmployee = () => {
  uni.navigateTo({ url: '/pages/executor/my/employee/employee' })
}

const goDataCenter = () => {
  uni.switchTab({ url: '/pages/executor/sop/single-canteen/single-canteen' })
}

const goVideo = () => {
  uni.navigateTo({ url: '/pages/executor/my/video/area?module=video' })
}

const goAbout = () => {
  uni.showToast({ title: '关于我们开发中', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f7f9fb;
}

.nav-right-btn {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.setting-icon {
  width: 38rpx;
  height: 38rpx;
}

.profile-card {
  margin: 20rpx 30rpx 0;
  background: #ffffff;
  border-radius: 16rpx;
  height: 208rpx;
  padding: 0 36rpx 0 30rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-left {
  display: flex;
  align-items: center;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
}

.profile-info {
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.name {
  font-size: 34rpx;
  color: #111111;
  font-weight: 600;
}

.status-tag {
  height: 36rpx;
  padding: 0 12rpx;
  border-radius: 4rpx;
  background: #FFF7E6;
  color: #FAAD14;
  font-size: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.role {
  font-size: 28rpx;
  color: #999999;
}

.menu-list {
  margin: 38rpx 30rpx 0;
  border-radius: 16rpx;
  overflow: hidden;
}

.menu-item {
  height: 112rpx;
  background: #ffffff;
  padding: 0 24rpx 0 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f2f2f2;
  box-sizing: border-box;
}

.menu-item:last-child {
  border-bottom: none;
}

.item-left {
  display: flex;
  align-items: center;
}

.icon-wrap {
  position: relative;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
}

.item-icon {
  width: 40rpx;
  height: 40rpx;
  margin-right: 24rpx;
}

.icon-wrap .item-icon {
  margin-right: 0;
}

.badge {
  position: absolute;
  right: -10rpx;
  top: -8rpx;
  min-width: 28rpx;
  height: 28rpx;
  border-radius: 14rpx;
  background: #ff4d4f;
  color: #ffffff;
  font-size: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6rpx;
  box-sizing: border-box;
  z-index: 1;
}

.item-title {
  font-size: 30rpx;
  color: #333333;
}

.arrow {
  width: 16rpx;
  height: 24rpx;
  opacity: 0.3;
}
</style>
