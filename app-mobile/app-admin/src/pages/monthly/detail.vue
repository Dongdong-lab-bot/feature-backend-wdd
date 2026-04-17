<template>
  <view class="page">
    <NavBar title="月调度" />

    <view class="panel">
      <view class="search-box">
        <image class="search-icon" src="/static/monthly/icon-search-gray.svg" mode="aspectFit" />
        <input
          class="search-input"
          v-model="keyword"
          placeholder="请输入关键词"
          placeholder-style="color: #CCCCCC"
          confirm-type="search"
          @confirm="handleSearch"
        />
      </view>

      <view class="crumbs">
        <text class="crumb blue" @click="handleCrumb('武岗县全县项目')">武岗县全县项目</text>
        <text class="crumb blue" @click="handleCrumb('城东片区')">&gt; 城东片区</text>
        <text class="crumb gray" @click="handleCrumb('高中学校')">&gt; 高中学校</text>
      </view>

      <view class="month-pill" @click="handleMonthPick">
        <text class="month-text">&lt;&nbsp;&nbsp; 2020年1月 &nbsp;&nbsp;&gt;</text>
      </view>
    </view>

    <scroll-view class="body" scroll-y>
      <view class="card" v-for="item in filteredList" :key="item.id" @click="handleOpen(item)">
        <view class="thumb">
          <image class="thumb-img" src="/static/monthly/cover.svg" mode="aspectFill" />
          <image class="play-icon" src="/static/monthly/icon-play.svg" mode="aspectFit" />
        </view>
        <view class="card-info">
          <text class="card-title">{{ item.title }}</text>
          <text class="card-sub">报告人：{{ item.reporter }}</text>
        </view>
      </view>

      <view class="bottom-tip">没有更多数据了～</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import NavBar from '../../components/NavBar/NavBar.vue'

type MonthlyReport = {
  id: string
  title: string
  reporter: string
}

const keyword = ref('')

const list = ref<MonthlyReport[]>([
  { id: '1', title: '武岗一中一食堂月调度报告', reporter: '食安总监' },
  { id: '2', title: '武岗一中二食堂月调度报告', reporter: '食安总监' },
  { id: '3', title: '武岗实验中学月调度报告', reporter: '食安总监' },
  { id: '4', title: '武岗初中一食堂月调度报告', reporter: '食安总监' }
])

const filteredList = computed(() => {
  const k = keyword.value.trim()
  if (!k) return list.value
  return list.value.filter((x) => x.title.includes(k))
})

const handleSearch = () => {
  if (!keyword.value.trim()) {
    uni.showToast({ title: '请输入关键词', icon: 'none' })
  }
}

const handleCrumb = (name: string) => {
  uni.showToast({ title: name, icon: 'none' })
}

const handleMonthPick = () => {
  uni.showToast({ title: '月份选择开发中', icon: 'none' })
}

const handleOpen = (item: MonthlyReport) => {
  uni.navigateTo({
    url: `/pages/monthly/detail-view?canteen=${encodeURIComponent(item.title.replace('月调度报告', ''))}&month=1月`
  })
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: rgba(41, 132, 248, 0.05);
  display: flex;
  flex-direction: column;
}

.header {
  height: calc(var(--status-bar-height) + 88rpx);
  padding-top: var(--status-bar-height);
  background: #ffffff;
  box-sizing: border-box;
}

.header-bar {
  height: 88rpx;
  padding: 0 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-between; 
  box-sizing: border-box;
}

.header-left,
.header-right {
  width: 88rpx;
  height: 100%;
  display: flex;
  align-items: center;
}

.header-right {
  justify-content: flex-end;
}

.back-icon {
  width: 40rpx; 
  height: 40rpx;
}

.header-title {
  font-size: 40rpx;
  color: #111111;
  font-weight: 700;
  flex: 1; 
  text-align: center;
}

.panel {
  background: #ffffff;
  padding: 18rpx 30rpx 18rpx;
  box-sizing: border-box;
}

.search-box {
  height: 80rpx;
  border-radius: 16rpx;
  border: 1px solid #f2f2f2;
  background: rgba(37, 97, 239, 0.04);
  display: flex;
  align-items: center;
  padding: 0 18rpx;
  box-sizing: border-box;
}

.search-icon {
  width: 36rpx;
  height: 36rpx;
  margin-right: 12rpx;
}

.search-input {
  flex: 1;
  height: 80rpx;
  font-size: 28rpx;
  color: #333333;
}

.crumbs {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.crumb {
  font-size: 24rpx;
}

.crumb.blue {
  color: #2561ef;
}

.crumb.gray {
  color: #999999;
}

.month-pill {
  margin: 14rpx auto 0;
  width: 240rpx;
  height: 52rpx;
  border-radius: 32rpx;
  background: rgba(108, 118, 244, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.month-text {
  font-size: 24rpx;
  color: #006ef1;
  font-weight: 700;
}

.body {
  flex: 1;
  min-height: 0;
  padding: 18rpx 30rpx 20rpx;
  box-sizing: border-box;
}

.card {
  height: 180rpx;
  border-radius: 16rpx;
  background: #ffffff;
  border: 1px solid #f2f2f2;
  padding: 20rpx;
  display: flex;
  align-items: center;
  margin-bottom: 18rpx;
  box-sizing: border-box;
}

.thumb {
  width: 190rpx;
  height: 160rpx;
  border-radius: 12rpx;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.thumb-img {
  width: 100%;
  height: 100%;
}

.play-icon {
  position: absolute;
  right: 14rpx;
  bottom: 14rpx;
  width: 40rpx;
  height: 40rpx;
}

.card-info {
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10rpx;
}

.card-title {
  font-size: 28rpx;
  color: #111111;
  font-weight: 600;
}

.card-sub {
  font-size: 24rpx;
  color: #999999;
}

.bottom-tip {
  padding: 26rpx 0 12rpx;
  text-align: center;
  font-size: 24rpx;
  color: #cccccc;
}
</style>
