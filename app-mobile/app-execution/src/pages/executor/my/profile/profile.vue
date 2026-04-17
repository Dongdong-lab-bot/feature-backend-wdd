<template>
个人资料页面右上角有一个类似于铅笔的按钮进行编辑个人资料，把图标做上去就行  <view class="profile-page" :style="{ paddingTop: (statusBarHeight + 72) + 'px' }">

    <view class="custom-nav" :style="{ paddingTop: statusBarHeight + 'px', height: (statusBarHeight + 72) + 'px' }">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">‹</text>
      </view>
      <text class="nav-title">个人资料</text>
      <view class="edit-btn" @click="editProfile">
        <text class="edit-icon">✏</text>
      </view>
    </view>

    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="card-bg"></view>
      <view class="card-content">
        <!-- 头像 -->
        <view class="avatar-section">
          <image class="avatar" :src="userInfo.avatar" mode="aspectFill" />
        </view>
        
        <!-- 姓名和职位 -->
        <view class="info-section">
          <text class="username">{{ userInfo.username }}</text>
          <text class="position">{{ userInfo.position }}</text>
          <view class="status-tag" :class="userInfo.status">
            {{ userInfo.statusText }}
          </view>
        </view>
      </view>
    </view>

    <!-- 详细信息列表 -->
    <view class="detail-list">
      <view class="detail-item" v-for="(item, index) in detailList" :key="index">
        <text class="detail-label">{{ item.label }}</text>
        <text class="detail-value" :class="{ highlight: item.highlight }" @click="handleItemClick(item)">
          {{ item.value }}
        </text>
      </view>
    </view>

    <!-- 拨打电话弹层 -->
    <view class="modal-overlay" v-if="showPhoneModal" @click="closePhoneModal">
      <view class="modal-content" @click.stop>
        <view class="modal-body">
          <text class="modal-phone">{{ userInfo.phone }}</text>
        </view>
        <view class="modal-actions">
          <view class="modal-action-btn cancel" @click="closePhoneModal">
            <text>取消</text>
          </view>
          <view class="modal-action-divider"></view>
          <view class="modal-action-btn confirm" @click="makePhoneCall">
            <text>拨打</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUserInfo } from '@/common/auth'

const statusBarHeight = uni.getSystemInfoSync().statusBarHeight || 0

const goBack = () => {
  uni.navigateBack()
}

// 用户信息
const userInfo = ref({
  avatar: '/static/avatar-default.png',
  username: '未登录',
  position: '',
  status: 'active',
  statusText: '在职',
  phone: ''
})

// 详细信息列表
const detailList = ref([
  {
    key: 'email',
    label: '邮箱地址',
    value: '-',
    highlight: false
  },
  {
    key: 'phone',
    label: '手机号码',
    value: '-',
    highlight: true
  },
  {
    key: 'gender',
    label: '性别',
    value: '-',
    highlight: false
  },
  {
    key: 'department',
    label: '部门',
    value: '-',
    highlight: false
  },
  {
    key: 'position',
    label: '职位',
    value: '-',
    highlight: false
  },
  {
    key: 'district',
    label: '辖区',
    value: '-',
    highlight: false
  }
])

const fetchProfile = async () => {
  try {
    const res: any = await getUserInfo()
    if (res) {
      userInfo.value.username = res.realName || res.username || '未登录'
      userInfo.value.phone = res.mobile || '-'
      userInfo.value.statusText = res.status === 'ACTIVE' ? '在职' : '离职'
      userInfo.value.status = res.status === 'ACTIVE' ? 'active' : 'inactive'

      const roleText =
        res.roleType === 'REGULATOR'
          ? '监管人员'
          : res.roleType === 'EXECUTOR'
          ? '执行人员'
          : '食安总监'
      userInfo.value.position = roleText

      const phone = res.mobile || '-'
      const email = res.email || '-'
      const department = res.deptName || '-'
      const district = res.districtName || '-'

      detailList.value.forEach((item) => {
        if (item.key === 'phone') item.value = phone
        if (item.key === 'email') item.value = email
        if (item.key === 'department') item.value = department
        if (item.key === 'district') item.value = district
        if (item.key === 'position') item.value = roleText
      })
    }
  } catch (error) {
    console.error('fetch user info failed:', error)
  }
}

onMounted(() => {
  fetchProfile()
})

// 拨打电话弹层
const showPhoneModal = ref(false)

// 编辑资料
const editProfile = () => {
  uni.showToast({
    title: '编辑功能开发中',
    icon: 'none'
  })
  // TODO: 跳转到编辑页面
  // uni.navigateTo({
  //   url: '/pages/executor/my/profile/edit'
  // })
}

// 处理详情项点击
const handleItemClick = (item: any) => {
  if (item.key === 'phone') {
    showPhoneModal.value = true
  } else {
    uni.showToast({
      title: `${item.label}: ${item.value}`,
      icon: 'none'
    })
  }
}

// 关闭电话弹层
const closePhoneModal = () => {
  showPhoneModal.value = false
}

// 拨打电话
const makePhoneCall = () => {
  closePhoneModal()
  
  uni.makePhoneCall({
    phoneNumber: userInfo.value.phone,
    success: () => {
      console.log('拨打电话成功')
    },
    fail: (err) => {
      console.error('拨打电话失败:', err)
      uni.showToast({
        title: '拨打失败',
        icon: 'none'
      })
    }
  })
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background-color: #f2f7fb;
  padding-top: 44px;
}

/* 顶部自定义导航 */
.custom-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 44px;
  background-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 100;
}

.back-btn {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  font-size: 56rpx;
  color: #333333;
}

.nav-title {
  font-size: 44rpx;
  font-weight: 600;
  color: #333333;
}

.edit-btn {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-icon {
  font-size: 44rpx;
  color: #333333;
}

/* 顶部导航栏 */

/* 用户信息卡片 */
.user-card {
  position: relative;
  background-color: #ffffff;
  padding: 20px;
  margin: 10px;
  border-radius: 12px;
  overflow: hidden;
}

.card-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
}

.card-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-section {
  flex-shrink: 0;
  margin-left: auto;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #f0f0f0;
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.username {
  font-size: 20px;
  color: #333333;
  font-weight: 600;
}

.position {
  font-size: 14px;
  color: #666666;
}

.status-tag {
  display: inline-block;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  width: fit-content;
}

.status-tag.active {
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.status-tag.inactive {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

/* 详细信息列表 */
.detail-list {
  background-color: #ffffff;
  margin: 10px;
  border-radius: 12px;
  overflow: hidden;
}

.detail-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: #999;
}

.detail-value {
  font-size: 15px;
  color: #333;
}

.detail-value.highlight {
  color: #2561ef;
  font-weight: 500;
}

/* 弹层 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 260px;
  background-color: #ffffff;
  border-radius: 12px;
  overflow: hidden;
}

.modal-body {
  padding: 24px 20px;
  text-align: center;
}

.modal-phone {
  font-size: 18px;
  color: #333;
  font-weight: 500;
}

.modal-actions {
  display: flex;
  height: 50px;
}

.modal-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.modal-action-btn.cancel {
  color: #666;
}

.modal-action-btn.confirm {
  color: #2561ef;
  font-weight: 500;
}

.modal-action-divider {
  width: 1px;
  background-color: #f0f0f0;
}
</style>