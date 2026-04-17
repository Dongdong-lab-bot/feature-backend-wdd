<template>
  <view class="page">
    <NavBar title="首页" :showBack="false">
      <template #right>
        <view class="nav-right-container">
          <image class="nav-icon" src="/static/home/icon-search.svg" mode="aspectFit" />
          <image class="nav-icon" src="/static/home/icon-expand.svg" mode="aspectFit" />
        </view>
      </template>
    </NavBar>
    <scroll-view class="body" scroll-y>
      <view class="score-card">
        <text class="card-title">食安指数中心</text>
        <view class="score-grid">
          <view class="score-item" v-for="item in scoreList" :key="item.name">
            <text class="school-name">{{ item.name }}</text>
            <view class="progress-track">
              <view class="progress-fill" :style="{ width: `${item.score}%`, backgroundColor: item.color }"></view>
            </view>
            <text class="score-text">{{ item.score }}分</text>
          </view>
        </view>
      </view>

      <view class="panel">
        <text class="panel-title">常用功能</text>
        <view class="feature-grid">
          <view class="feature-item" v-for="item in featureList" :key="item.title" @click="goPage(item.path)">
            <view class="feature-icon-wrap" :style="{ backgroundColor: item.bg }">
              <image class="feature-icon" :src="item.icon" mode="aspectFit" />
            </view>
            <text class="feature-title">{{ item.title }}</text>
          </view>
        </view>
      </view>

      <view class="module-card blue-card" @click="goPage('/pages/video/task-list')">
        <text class="module-title">视频监控中心</text>
        <view class="module-links">
          <text class="module-link">视频查看</text>
          <text class="module-link">视频巡检</text>
        </view>
        <image class="eye-icon" src="/static/home/icon-eye.png" mode="aspectFit" />
      </view>

      <view class="module-card orange-card" @click="goPage('/pages/sop/canteen-sop')">
        <text class="module-title">SOP标准执行中心</text>
        <view class="module-links">
          <text class="module-link">视频查看</text>
          <text class="module-link">视频巡检</text>
        </view>
        <image class="arrow-icon" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import NavBar from '../../components/NavBar/NavBar.vue'

const scoreList = [
  { name: '武岗一中一食堂', score: 92, color: '#56DB9E' },
  { name: '武岗初中一食堂', score: 72, color: '#FFD55E' },
  { name: '武岗实验一食堂', score: 89, color: '#56DB9E' },
  { name: '武岗初中二食堂', score: 70, color: '#FFD55E' },
  { name: '武岗一中二食堂', score: 88, color: '#56DB9E' },
  { name: '武岗创新二食堂', score: 68, color: '#FF8686' },
  { name: '武岗一中三食堂', score: 88, color: '#56DB9E' },
  { name: '武岗创新一食堂', score: 68, color: '#FF8686' }
]

const featureList = [
  { title: '日管控', path: '/pages/daily/task-list', icon: '/static/home/icon-daily.svg', bg: '#EAF2FF' },
  { title: '周排查', path: '/pages/weekly/task-list', icon: '/static/home/icon-weekly.svg', bg: '#FFECE8' },
  { title: '月调度', path: '/pages/monthly/detail', icon: '/static/home/icon-monthly.svg', bg: '#E8FBF3' },
  { title: '联合巡检', path: '/pages/joint/task-list', icon: '/static/home/icon-joint.svg', bg: '#FFF6D9' }
]

const goPage = (path: string) => {
  uni.navigateTo({ url: path })
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.nav-right-container {
  display: flex;
  align-items: center;
  gap: 26rpx;
}

.nav-icon {
  width: 36rpx;
  height: 36rpx;
}

.body {
  flex: 1;
  min-height: 0;
  padding: 20rpx 24rpx 8rpx;
  box-sizing: border-box;
  background: #f7f9fb;
}

.score-card {
  border-radius: 20rpx;
  background: linear-gradient(135deg, #00ccff 0%, #2561ef 100%);
  padding: 24rpx;
  box-shadow: 0 10rpx 24rpx rgba(37, 97, 239, 0.12);
  margin-bottom: 18rpx;
}

.card-title {
  font-size: 46rpx;
  font-weight: 700;
  color: #ffffff;
}

.score-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-top: 14rpx;
}

.score-item {
  width: 48%;
  margin-top: 12rpx;
}

.school-name {
  display: block;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
  text-align: center;
}

.progress-track {
  width: 100%;
  height: 20rpx;
  border-radius: 100rpx;
  margin-top: 6rpx;
  background: rgba(255, 255, 255, 0.95);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 100rpx;
}

.score-text {
  display: block;
  margin-top: 2rpx;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
  text-align: center;
}

.panel {
  border-radius: 20rpx;
  background: #ffffff;
  padding: 24rpx;
  margin-bottom: 18rpx;
}

.panel-title {
  font-size: 52rpx;
  font-weight: 700;
  color: #111111;
}

.feature-grid {
  margin-top: 24rpx;
  display: flex;
  justify-content: space-between;
}

.feature-item {
  width: 23%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.feature-icon-wrap {
  width: 88rpx;
  height: 88rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-icon {
  width: 38rpx;
  height: 38rpx;
}

.feature-title {
  margin-top: 14rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: #111111;
  white-space: nowrap;
}

.module-card {
  border-radius: 20rpx;
  padding: 26rpx 24rpx;
  position: relative;
  overflow: hidden;
  margin-bottom: 18rpx;
}

.blue-card {
  background: linear-gradient(135deg, #00ccff 0%, #2561ef 100%);
  box-shadow: 0 10rpx 24rpx rgba(37, 97, 239, 0.12);
}

.orange-card {
  background: linear-gradient(135deg, #ffb13a 0%, #ff7f3f 100%);
  box-shadow: 0 10rpx 24rpx rgba(255, 149, 63, 0.2);
}

.module-title {
  font-size: 52rpx;
  font-weight: 700;
  color: #ffffff;
}

.module-links {
  margin-top: 16rpx;
  display: flex;
  gap: 26rpx;
}

.module-link {
  color: #ffffff;
  font-size: 38rpx;
  font-weight: 600;
}

.eye-icon {
  position: absolute;
  right: 14rpx;
  top: -18rpx;
  width: 210rpx;
  height: 140rpx;
}

.arrow-icon {
  position: absolute;
  right: 24rpx;
  bottom: 10rpx;
  width: 108rpx;
  height: 108rpx;
  opacity: 0.85;
}
</style>
