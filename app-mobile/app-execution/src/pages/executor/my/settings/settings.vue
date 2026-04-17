<template>
  <view class="settings-page">

    <!-- 设置列表 -->
    <view class="settings-list">
      <!-- 账号安全分组 -->
      <view class="settings-group">
        <view 
          class="settings-item" 
          v-for="(item, index) in accountSettings" 
          :key="index"
          @click="handleItemClick(item)"
        >
          <text class="item-label">{{ item.label }}</text>
          <view class="item-right">
            <text class="item-value" v-if="item.value">{{ item.value }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </view>
      </view>

      <!-- 通知分组 -->
      <view class="settings-group">
        <view class="settings-item">
          <text class="item-label">消息通知</text>
          <switch 
            class="notification-switch"
            :checked="notificationEnabled"
            @change="toggleNotification"
            color="#2561EF"
          />
        </view>
      </view>

      <!-- 缓存和版本分组 -->
      <view class="settings-group">
        <view class="settings-item" @click="clearCache">
          <text class="item-label">清除缓存</text>
          <view class="item-right">
            <text class="item-value">{{ cacheSize }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </view>
        <view class="settings-item" @click="checkVersion">
          <text class="item-label">升级版本</text>
          <view class="item-right">
            <text class="item-value">{{ currentVersion }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </view>
      </view>

      <!-- 退出登录按钮 -->
      <view class="logout-section">
        <view class="logout-btn" @click="showLogoutModal = true">
          <text>退出账号</text>
        </view>
      </view>
    </view>

    <!-- 退出登录确认弹层 -->
    <view class="modal-overlay" v-if="showLogoutModal" @click="cancelLogout">
      <view class="modal-content" @click.stop>
        <view class="modal-body">
          <text class="modal-text">确定要退出当前账号吗？</text>
        </view>
        <view class="modal-actions">
          <view class="modal-action-btn cancel" @click="cancelLogout">
            <text>取消</text>
          </view>
          <view class="modal-action-divider"></view>
          <view class="modal-action-btn confirm" @click="confirmLogout">
            <text>确定</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { logout } from '@/common/auth'

// 账号相关设置项
const accountSettings = ref([
  {
    key: 'phone',
    label: '更改手机号码',
    value: '',
    path: '/pages/executor/my/change-phone/change-phone'
  },
  {
    key: 'password',
    label: '修改密码',
    value: '',
    path: '/pages/executor/my/change-password/change-password'
  }
])

// 通知开关状态
const notificationEnabled = ref(true)

// 缓存大小
const cacheSize = ref('9.2M')

// 当前版本
const currentVersion = ref('当前版本 2.8.9')

// 退出登录弹层
const showLogoutModal = ref(false)

// 返回上一页
const goBack = () => {
  uni.navigateBack()
}

// 处理设置项点击
const handleItemClick = (item: any) => {
  console.log('点击设置项:', item.label)
  
  if (item.path) {
    uni.navigateTo({
      url: item.path
    })
  } else {
    uni.showToast({
      title: `${item.label} 功能开发中`,
      icon: 'none'
    })
  }
}

// 切换通知开关
const toggleNotification = (e: any) => {
  notificationEnabled.value = e.detail.value
  console.log('通知开关:', notificationEnabled.value)
  
  uni.showToast({
    title: notificationEnabled.value ? '已开启通知' : '已关闭通知',
    icon: 'none'
  })
}

// 清除缓存
const clearCache = () => {
  uni.showLoading({
    title: '清除中...'
  })
  
  // 模拟清除缓存
  setTimeout(() => {
    uni.hideLoading()
    cacheSize.value = '0B'
    uni.showToast({
      title: '缓存已清除',
      icon: 'success'
    })
  }, 800)
}

// 检查版本更新
const checkVersion = () => {
  console.log('检查版本更新')
  
  uni.showToast({
    title: '已是最新版本',
    icon: 'none'
  })
  
  // TODO: 实现版本检查逻辑
  // uni.checkUpdate({
  //   success: (res) => {
  //     if (res.hasUpdate) {
  //       uni.showModal({
  //         title: '发现新版本',
  //         content: '是否更新到最新版本？',
  //         success: (updateRes) => {
  //           if (updateRes.confirm) {
  //             // 执行更新
  //           }
  //         }
  //       })
  //     }
  //   }
  // })
}

// 取消退出
const cancelLogout = () => {
  showLogoutModal.value = false
}

// 确认退出
const confirmLogout = () => {
  showLogoutModal.value = false
  
  uni.showLoading({
    title: '退出中...'
  })
  
  setTimeout(() => {
    uni.hideLoading()
    logout()
  }, 800)
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}


/* 设置列表 */
.settings-list {
  padding-top: 10px;
}

.settings-group {
  background-color: #ffffff;
  margin-bottom: 0;
}

.settings-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.settings-item:last-child {
  border-bottom: 1px solid #f0f0f0;
}

.item-label {
  font-size: 16px;
  color: #333;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-value {
  font-size: 14px;
  color: #999;
}

.arrow-icon {
  font-size: 20px;
  color: #ccc;
  transform: rotate(90deg);
}

/* 通知开关 */
.notification-switch {
  transform: scale(0.9);
}

/* 退出登录区域 */
.logout-section {
  padding: 20px;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 14px 0;
  background-color: #ffffff;
  border-radius: 12px;
  font-size: 16px;
  color: #ff4d4f;
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

.modal-text {
  font-size: 16px;
  color: #333;
  line-height: 1.5;
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