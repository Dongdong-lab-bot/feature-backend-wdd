<template>
  <view class="page-container">
    <!-- 搜索框 -->
    <view class="search-container">
      <view class="search-input-wrapper">
        <text class="search-icon">🔍</text>
        <input
          v-model="searchText"
          placeholder="请输入"
          class="search-input"
          @input="onSearch"
        />
      </view>
    </view>

    <!-- 月份选择器 -->
    <view class="month-selector">
      <view class="month-nav" @click="changeMonth(-1)">
        <text class="arrow">&lt;</text>
      </view>
      <text class="month-text">{{ currentMonth }}</text>
      <view class="month-nav" @click="changeMonth(1)">
        <text class="arrow">&gt;</text>
      </view>
    </view>

    <!-- 面包屑导航 -->
    <view class="breadcrumbs">
      <text class="crumb active">武岗县全县项目</text>
      <text class="separator">&gt;</text>
      <text class="crumb active">城东片区</text>
      <text class="separator">&gt;</text>
      <text class="crumb">高中学校</text>
    </view>

    <!-- 报告列表 -->
    <scroll-view class="list-container" scroll-y="true">
      <view
        v-for="(report, index) in filteredReports"
        :key="index"
        class="report-card"
        @click="onReportClick(report)"
      >
        <view class="card-left">
          <view class="image-placeholder">
            <view class="play-icon-wrapper">
              <text class="play-icon">▶</text>
            </view>
          </view>
          <view class="tag-label">
            <text class="tag-icon">S</text>
            <text class="tag-text">字视价格合集</text>
          </view>
        </view>
        
        <view class="card-right">
          <text class="report-title">{{ report.title }}</text>
          <text class="reporter">报告人：{{ report.reporter }}</text>
        </view>
      </view>

      <!-- 空数据/底线 -->
      <view class="loading-more">
        <text class="loading-text">没有更多数据了～</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const searchText = ref('')
const currentMonth = ref('2020年1月')

const reports = ref([
  {
    id: 1,
    title: '武岗一中一食堂月调度报告',
    reporter: '食安总监',
    month: '2020-01'
  },
  {
    id: 2,
    title: '武岗一中一食堂月调度报告',
    reporter: '食安总监',
    month: '2020-01'
  },
  {
    id: 3,
    title: '武岗一中一食堂月调度报告',
    reporter: '食安总监',
    month: '2020-01'
  },
  {
    id: 4,
    title: '武岗一中一食堂月调度报告',
    reporter: '食安总监',
    month: '2020-01'
  },
  {
    id: 5,
    title: '武岗一中一食堂月调度报告',
    reporter: '食安总监',
    month: '2020-01'
  }
])

const filteredReports = computed(() => {
  if (!searchText.value) {
    return reports.value
  }
  return reports.value.filter(report =>
    report.title.includes(searchText.value) ||
    report.reporter.includes(searchText.value)
  )
})

const onSearch = (e: any) => {
  searchText.value = e.detail.value
}

const changeMonth = (delta: number) => {
  // Simple mock logic for month change
  // In real app, would use Date object manipulation
  if (delta > 0) {
    currentMonth.value = '2020年2月'
  } else {
    currentMonth.value = '2019年12月'
  }
}

const onReportClick = (report: any) => {
  uni.navigateTo({
    url: `/pages/executor/sop/monthly-scheduling/monthly-scheduling-detail/monthly-scheduling-detail?id=${report.id}&title=${encodeURIComponent(report.title)}&month=${report.month}`
  })
}
</script>

<style scoped lang="scss">
.page-container {
  height: 100vh;
  background-color: #F5F7FA;
  display: flex;
  flex-direction: column;
}

.search-container {
  padding: 20rpx 30rpx;
  background-color: #fff;
}

.search-input-wrapper {
  background-color: #F5F7FA;
  border-radius: 40rpx;
  padding: 0 30rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
}

.search-icon {
  font-size: 28rpx;
  color: #999;
  margin-right: 16rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.month-selector {
  background-color: #fff;
  padding: 20rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.month-nav {
  padding: 0 20rpx;
}

.arrow {
  color: #2561EF;
  font-weight: bold;
  font-size: 32rpx;
}

.month-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #2561EF;
  margin: 0 20rpx;
}

.breadcrumbs {
  padding: 20rpx 30rpx;
  background-color: #fff;
  display: flex;
  align-items: center;
  font-size: 26rpx;
}

.crumb {
  color: #999;
}

.crumb.active {
  color: #2561EF;
}

.separator {
  color: #ccc;
  margin: 0 10rpx;
}

.list-container {
  flex: 1;
  padding: 20rpx 30rpx;
  box-sizing: border-box;
}

.report-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  display: flex;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.02);
  border: 2rpx solid transparent;
  transition: all 0.3s;

  &.active {
    border-color: #2561EF;
    background-color: #F0F5FF;
  }
}

.card-left {
  position: relative;
  width: 240rpx;
  height: 160rpx;
  margin-right: 24rpx;
  flex-shrink: 0;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  background-color: #F0F2F5;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid #E4E7ED;
}

.play-icon-wrapper {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-icon {
  font-size: 24rpx;
  color: #ccc;
  margin-left: 4rpx;
}

.tag-label {
  position: absolute;
  bottom: -10rpx;
  left: 0;
  background-color: #fff;
  border: 1rpx solid #eee;
  border-radius: 4rpx;
  padding: 4rpx 8rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 2rpx 4rpx rgba(0,0,0,0.05);
  max-width: 100%;
}

.tag-icon {
  background-color: #00B578;
  color: #fff;
  font-size: 18rpx;
  padding: 2rpx 6rpx;
  border-radius: 4rpx;
  margin-right: 6rpx;
}

.tag-text {
  font-size: 20rpx;
  color: #666;
}

.card-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.report-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
  margin-bottom: 16rpx;
}

.reporter {
  font-size: 26rpx;
  color: #999;
}

.loading-more {
  text-align: center;
  padding: 30rpx 0;
}

.loading-text {
  font-size: 24rpx;
  color: #ccc;
}
</style>