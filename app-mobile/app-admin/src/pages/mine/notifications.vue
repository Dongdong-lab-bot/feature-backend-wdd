<template>
  <view class="page">
    <scroll-view class="body" scroll-y>
      <view class="list">
        <view class="item" v-for="item in list" :key="item.id" @click="handleOpen(item)">
          <view class="icon" :style="{ backgroundColor: item.iconBg }">
            <image class="icon-img" :src="item.iconSrc" mode="aspectFit" />
          </view>

          <view class="content">
            <text class="title">{{ item.title }}</text>
            <text class="desc">{{ item.desc }}</text>
          </view>

          <view v-if="item.unread" class="dot"></view>
          <text class="time">{{ item.time }}</text>
        </view>
      </view>

      <view class="bottom-tip">没有更多数据了～</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

type NoticeItem = {
  id: string
  title: string
  desc: string
  time: string
  unread: boolean
  iconSrc: string
  iconBg: string
}

const list = ref<NoticeItem[]>([
  {
    id: '1',
    title: '审批提醒',
    desc: '您有一条整改记录待审批',
    time: '10:30',
    unread: true,
    iconSrc: '/static/notice/icon-approve.svg',
    iconBg: '#2561EF'
  },
  {
    id: '2',
    title: '风险提醒',
    desc: '2026-02-19日管控未完成整改',
    time: '10:30',
    unread: true,
    iconSrc: '/static/notice/icon-danger.svg',
    iconBg: '#FA746B'
  },
  {
    id: '3',
    title: '预警提醒',
    desc: '2026-02-19日管控未完成整改',
    time: '10:30',
    unread: true,
    iconSrc: '/static/notice/icon-warning.svg',
    iconBg: '#FDDB78'
  },
  {
    id: '4',
    title: '系统通知',
    desc: '系统将于今晚 23:00-24:00 进行维护',
    time: '10:30',
    unread: true,
    iconSrc: '/static/notice/icon-normal.svg',
    iconBg: '#3DD4A7'
  }
])

const handleOpen = (item: NoticeItem) => {
  item.unread = false
  uni.showToast({ title: '详情开发中', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: rgba(242, 247, 251, 0.62);
}

.body {
  height: 100vh;
}

.list {
  padding-top: 24rpx;
}

.item {
  height: 160rpx;
  background: #ffffff;
  padding: 0 30rpx;
  display: flex;
  align-items: center;
  position: relative;
}

.item + .item {
  border-top: 1px solid #f2f2f2;
}

.icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-img {
  width: 40rpx;
  height: 40rpx;
}

.content {
  flex: 1;
  margin-left: 24rpx;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.title {
  font-size: 32rpx;
  color: #333333;
  font-weight: 600;
  line-height: 44rpx;
}

.desc {
  margin-top: 6rpx;
  font-size: 26rpx;
  color: #b3b3b3;
  line-height: 38rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.time {
  position: absolute;
  right: 30rpx;
  top: 48rpx;
  font-size: 24rpx;
  color: #b3b3b3;
}

.dot {
  position: absolute;
  right: 30rpx;
  top: 30rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: #f00;
}

.bottom-tip {
  padding: 28rpx 0 40rpx;
  text-align: center;
  font-size: 24rpx;
  color: #cccccc;
}
</style>
