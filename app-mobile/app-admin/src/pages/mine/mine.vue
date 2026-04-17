<template>
  <view class="page">
    <NavBar title="监管者" :showBack="false">
      <template #right>
        <view class="nav-right-btn" @click="goSettings">
          <image class="setting-icon" src="/static/mine/icon-setting.svg" mode="aspectFit" />
        </view>
      </template>
    </NavBar>

    <view class="profile-card" @click="goProfile">
      <view class="profile-left">
        <image class="avatar" :src="profileCard.avatar" mode="aspectFit" />
        <view class="profile-info">
          <text class="role">{{ profileCard.role }}</text>
          <text class="name">{{ profileCard.name }}</text>
        </view>
      </view>
      <view class="status-tag" :class="{ disabled: profileCard.status !== '在职' }">{{ profileCard.status }}</view>
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

      <view class="menu-item" @click="goDataCenter">
        <view class="item-left">
          <image class="item-icon" src="/static/mine/icon-device.svg" mode="aspectFit" />
          <text class="item-title">智能化设备数据</text>
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
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NavBar from '../../components/NavBar/NavBar.vue'
import { authApi } from '@/api'

const currentUser = ref<any>(null)

const profileCard = computed(() => {
  const me = currentUser.value || {}
  const roleName = me.roleName || (me.roleType === 'REGULATOR' ? '监管人员' : '执行人员')
  return {
    avatar: '/static/mine/avatar.svg',
    role: roleName,
    name: me.realName || me.username || '未登录用户',
    status: me.status === 'DISABLED' ? '停用' : '在职'
  }
})

const syncCurrentUser = async () => {
  const cached = uni.getStorageSync('currentUser')
  if (cached && typeof cached === 'object') {
    currentUser.value = cached
  }
  try {
    const me = await authApi.getCurrentUser()
    currentUser.value = me
    uni.setStorageSync('currentUser', me)
  } catch {}
}

onShow(() => {
  syncCurrentUser()
})

const goProfile = () => {
  uni.navigateTo({ url: '/pages/mine/profile' })
}

const goSettings = () => {
  uni.navigateTo({ url: '/pages/mine/settings' })
}

const goNotifications = () => {
  uni.navigateTo({ url: '/pages/mine/notifications' })
}

const goDataCenter = () => {
  uni.switchTab({ url: '/pages/data/data-center' })
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
}

.profile-info {
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.role {
  font-size: 30rpx;
  color: #666666;
}

.name {
  font-size: 34rpx;
  color: #111111;
  font-weight: 600;
}

.status-tag {
  min-width: 74rpx;
  height: 42rpx;
  padding: 0 18rpx;
  border-radius: 22rpx;
  background: #3dd4a7;
  color: #ffffff;
  font-size: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.status-tag.disabled {
  background: #b9c2cf;
}
.menu-list {
  margin: 38rpx 30rpx 0;
  border-radius: 16rpx;
  overflow: hidden;
}

.menu-item {
  height: 96rpx;
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
  width: 32rpx;
  height: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon {
  width: 32rpx;
  height: 32rpx;
}

.badge {
  position: absolute;
  right: -10rpx;
  top: -8rpx;
  min-width: 24rpx;
  height: 24rpx;
  border-radius: 12rpx;
  background: #fa746b;
  color: #ffffff;
  font-size: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6rpx;
  box-sizing: border-box;
}

.item-title {
  margin-left: 22rpx;
  font-size: 30rpx;
  color: #333333;
}

.arrow {
  width: 16rpx;
  height: 24rpx;
  opacity: 0.8;
}
</style>
