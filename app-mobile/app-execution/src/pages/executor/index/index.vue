<template>
  <view class="container">
    <!-- 顶部导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-content">
        <text class="nav-title">食安执行端</text>
        <view class="nav-icons">
          <uni-icons type="search" size="24" color="#333" class="icon-item" @click="openSearch"></uni-icons>
        </view>
      </view>
    </view>

    <!-- 滚动内容区 -->
    <scroll-view class="content-scroll" scroll-y :style="{ marginTop: (statusBarHeight + 44) + 'px' }">
      <!-- 顶部得分区域 -->
      <view class="score-section">
        <view class="canteen-bg-text">武岗一中二食堂</view>
        <view class="score-circle">
          <text class="score-num">79</text>
          <text class="score-unit">分</text>
        </view>
      </view>

      <!-- 任务列表 -->
      <view class="task-list">
        <view class="task-item" v-for="(item, index) in tasks" :key="index" @click="handleTaskClick(item)">
          <text class="task-name">{{ item.name }}</text>
          <view class="task-action">
            <view v-if="item.actionType === 'btn'" class="action-btn">{{ item.actionText }}</view>
            <text v-else class="action-text">{{ item.actionText }}</text>
            <uni-icons type="right" size="16" color="#CCCCCC" class="arrow-icon"></uni-icons>
          </view>
        </view>
      </view>
      
      <!-- 底部留白 -->
      <view class="bottom-padding"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const statusBarHeight = uni.getSystemInfoSync().statusBarHeight || 0

const tasks = ref([
  { id: 1, name: '1、人员风险6项', actionText: '去优化', actionType: 'btn', path: '/pages/executor/index/risk-reminder' },
  { id: 2, name: '2、食材风险3项', actionText: '去优化', actionType: 'btn' },
  { id: 3, name: '3、环境风险8项', actionText: '去优化', actionType: 'btn' },
  { id: 4, name: '4、电子台账风险5项', actionText: '去优化', actionType: 'btn' },
  { id: 5, name: '5、周排查整改待完成', actionText: '去整改', actionType: 'text' },
  { id: 6, name: '6、月调度报告待查看', actionText: '去查看', actionType: 'text' }
])

const handleTaskClick = (item: any) => {
  if (item.path) {
    uni.navigateTo({ url: item.path })
  } else {
    uni.showToast({ title: '功能开发中', icon: 'none' })
  }
}

const openSearch = () => {
  uni.showToast({ title: '搜索', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #F4F7FB;
  position: relative;
}

/* 导航栏 */
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background-color: #FFFFFF;
  z-index: 100;
}

.nav-content {
  height: 44px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32rpx;
}

.nav-title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333333;
}

.nav-icons {
  display: flex;
  align-items: center;
  gap: 32rpx;
}

.icon-item {
  display: flex;
}

/* 内容区 */
.content-scroll {
  height: calc(100vh - 44px);
  box-sizing: border-box;
}

.score-section {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 360rpx;
  margin-top: 20rpx;
}

.canteen-bg-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48rpx;
  color: #E6EBF5;
  font-weight: bold;
  white-space: nowrap;
  letter-spacing: 4rpx;
  z-index: 0;
}

.score-circle {
  position: relative;
  z-index: 1;
  width: 240rpx;
  height: 240rpx;
  background: linear-gradient(135deg, #4A84FF 0%, #2962FF 100%);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 16rpx 32rpx rgba(41, 98, 255, 0.3);
}

.score-num {
  font-size: 72rpx;
  font-weight: bold;
  color: #FFFFFF;
}

.score-unit {
  font-size: 36rpx;
  font-weight: bold;
  color: #FFFFFF;
  margin-top: 20rpx;
  margin-left: 4rpx;
}

/* 任务列表 */
.task-list {
  padding: 0 32rpx;
  margin-top: 20rpx;
}

.task-item {
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.02);
}

.task-name {
  font-size: 32rpx;
  color: #333333;
  font-weight: 500;
}

.task-action {
  display: flex;
  align-items: center;
}

.action-btn {
  background-color: #FFD56A;
  color: #FFFFFF;
  font-size: 24rpx;
  padding: 8rpx 20rpx;
  border-radius: 8rpx;
  margin-right: 12rpx;
}

.action-text {
  color: #8C98FF;
  font-size: 28rpx;
  margin-right: 12rpx;
}

.arrow-icon {
  margin-top: 2rpx;
}

.bottom-padding {
  height: 40rpx;
}
</style>