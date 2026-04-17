<template>
  <view class="container">
    <!-- 顶部导航栏 -->
    <view class="nav-bar">
      <view class="left" @click="handleBack">
        <image src="/static/login/back-arrow.svg" mode="widthFix" class="back-icon"></image>
      </view>
      <text class="title">个人资料</text>
      <view class="right" @click="handleEdit">
        <image src="/static/mine/icon-edit.svg" mode="widthFix" class="edit-icon"></image>
      </view>
    </view>

    <!-- 内容区域 -->
    <view class="content">
      <!-- 个人信息卡片 -->
      <view class="profile-card">
        <image :src="userInfo.avatar || '/static/mine/avatar.svg'" mode="aspectFill" class="avatar"></image>
        <view class="info">
          <view class="name-row">
            <text class="name">{{ userInfo.name }}</text>
            <view class="status-tag">{{ userInfo.status }}</view>
          </view>
          <text class="position">{{ userInfo.position }}</text>
        </view>
      </view>

      <!-- 详细资料列表 -->
      <view class="detail-list">
        <view class="list-item">
          <text class="label">性别</text>
          <text class="value">{{ userInfo.gender }}</text>
        </view>
        <view class="list-item">
          <text class="label">年龄</text>
          <text class="value">{{ userInfo.age }}</text>
        </view>
        <view class="list-item" @click="handleCall">
          <text class="label">手机号码</text>
          <text class="value link">{{ userInfo.phone }}</text>
        </view>
        <view class="list-item">
          <text class="label">邮箱地址</text>
          <text class="value">{{ userInfo.email }}</text>
        </view>
        <view class="list-item">
          <text class="label">辖区</text>
          <text class="value">{{ userInfo.area }}</text>
        </view>
        <view class="list-item">
          <text class="label">部门</text>
          <text class="value">{{ userInfo.department }}</text>
        </view>
        <view class="list-item">
          <text class="label">职位</text>
          <text class="value">{{ userInfo.position }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { authApi } from '@/api'

const userInfo = ref({
  avatar: '',
  name: '未设置',
  position: '未设置',
  gender: '未设置',
  age: '--',
  phone: '未设置',
  email: '未设置',
  area: '未设置',
  department: '未设置',
  status: '在职'
})

const toGenderText = (value?: string | null) => {
  if (!value) return '未设置'
  if (value === 'M' || value === '男') return '男'
  if (value === 'F' || value === '女') return '女'
  return value
}

const toAgeText = (birthday?: string | null) => {
  if (!birthday) return '--'
  // 修复 iOS 下 new Date 解析 YYYY-MM-DD 格式报错 (NaN) 的问题
  const birth = new Date(birthday.replace(/-/g, '/'))
  if (Number.isNaN(birth.getTime())) return '--'
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const md = today.getMonth() - birth.getMonth()
  if (md < 0 || (md === 0 && today.getDate() < birth.getDate())) {
    age -= 1
  }
  return age >= 0 ? String(age) : '--'
}

const applyUser = (user: any) => {
  userInfo.value.name = user.realName || user.username || userInfo.value.name
  userInfo.value.phone = user.mobile || userInfo.value.phone
  userInfo.value.status = user.status === 'ACTIVE' ? '在职' : '停用'
  userInfo.value.gender = toGenderText(user.gender)
  userInfo.value.age = toAgeText(user.birthday)
  userInfo.value.email = user.email || '未设置'
  userInfo.value.area = user.canteenScope || '未设置'
  userInfo.value.department = user.orgName || '未设置'
  userInfo.value.position = user.roleName || (user.roleType === 'REGULATOR' ? '监管人员' : '执行人员')
}

const loadProfile = async () => {
  const cached = uni.getStorageSync('currentUser')
  if (cached && typeof cached === 'object') {
    applyUser(cached)
  }

  try {
    const me = await authApi.getCurrentUser()
    applyUser(me)
    uni.setStorageSync('currentUser', me)
  } catch {}
}

onMounted(() => {
  loadProfile()
})

const handleBack = () => {
  uni.navigateBack()
}

const handleEdit = () => {
  uni.showToast({ title: '编辑功能开发中', icon: 'none' })
}

const handleCall = () => {
  if (!/^\d{6,20}$/.test(userInfo.value.phone)) {
    uni.showToast({ title: '暂无可拨打手机号', icon: 'none' })
    return
  }
  uni.makePhoneCall({
    phoneNumber: userInfo.value.phone
  })
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #F5F7FA;
}

.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 88rpx;
  padding-top: var(--status-bar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 30rpx;
  padding-right: 30rpx;
  background-color: #ffffff;
  z-index: 100;

  .title {
    font-size: 36rpx;
    font-weight: 500;
    color: #333333;
  }

  .back-icon {
    width: 24rpx;
    height: 24rpx;
  }

  .edit-icon {
    width: 32rpx;
    height: 32rpx;
  }
  
  .left, .right {
    width: 88rpx;
    height: 88rpx;
    display: flex;
    align-items: center;
    
    // 让点击区域更大
    justify-content: flex-start; 
  }
  
  .right {
    justify-content: flex-end;
  }
}

.content {
  padding-top: calc(var(--status-bar-height) + 88rpx);
}

.profile-card {
  margin: 20rpx 30rpx;
  background: #ffffff;
  border-radius: 16rpx;
  padding: 30rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);

  .avatar {
    width: 112rpx;
    height: 112rpx;
    border-radius: 50%;
    margin-right: 30rpx;
    background-color: #f0f0f0;
  }

  .info {
    flex: 1;
    
    .name-row {
      display: flex;
      align-items: center;
      margin-bottom: 12rpx;
      
      .name {
        font-size: 36rpx;
        font-weight: 600;
        color: #333333;
        margin-right: 16rpx;
      }
      
      .status-tag {
        font-size: 24rpx;
        color: #FFC71C;
        background: rgba(255, 199, 28, 0.1);
        padding: 4rpx 12rpx;
        border-radius: 4rpx;
      }
    }
    
    .position {
      font-size: 28rpx;
      color: #999999;
    }
  }
}

.detail-list {
  background: #ffffff;
  margin-top: 20rpx;
  padding: 0 30rpx;

  .list-item {
    display: flex;
    align-items: center;
    height: 100rpx;
    border-bottom: 1rpx solid #F0F0F0;
    
    &:last-child {
      border-bottom: none;
    }

    .label {
      width: 160rpx;
      font-size: 30rpx;
      color: #999999;
    }

    .value {
      flex: 1;
      font-size: 30rpx;
      color: #333333;
      
      &.link {
        color: #2561EF;
      }
    }
  }
}
</style>
