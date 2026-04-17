<template>
  <view class="container">
    <view class="risk-list">
      <view class="risk-item" v-for="(item, index) in riskList" :key="index">
        <!-- 左侧时间线 -->
        <view class="timeline">
          <view :class="['dot', index === 0 ? 'active' : '']"></view>
          <view class="line" v-if="index < riskList.length - 1"></view>
        </view>

        <!-- 右侧内容 -->
        <view class="content">
          <view class="content-left">
            <text class="title">{{ item.title }}</text>
            <text class="time">预警时间 {{ item.time }}</text>
            <text class="desc">{{ item.desc }}</text>
          </view>
          <view class="content-right">
            <view :class="['action-btn', item.type]">
              去处理+{{ item.score }}分
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const riskList = ref([
  {
    title: '晨检应检40人，实检20人',
    time: '09:01:01',
    desc: '根据历史员工数量及近期晨检情况分析',
    score: 3,
    type: 'red'
  },
  {
    title: '发现陌生人3次',
    time: '18:01:01',
    desc: '根据陌生人识别检测出，希望重视风险',
    score: 2,
    type: 'yellow'
  },
  {
    title: '发现着装不规范13次',
    time: '18:01:01',
    desc: '根据行为识别检测出，希望重视风险',
    score: 1,
    type: 'yellow'
  },
  {
    title: '发现油锅离岗1次',
    time: '18:01:01',
    desc: '根据行为识别检测出，希望重视风险',
    score: 1,
    type: 'red'
  }
])
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #FFFFFF;
  padding: 40rpx 32rpx;
}

.risk-list {
  display: flex;
  flex-direction: column;
}

.risk-item {
  display: flex;
  position: relative;
  min-height: 200rpx;
}

.timeline {
  width: 60rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 16rpx;
}

.dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  border: 4rpx solid #CCCCCC;
  background-color: #FFFFFF;
  margin-top: 8rpx;
  position: relative;
  z-index: 2;

  &.active {
    border-color: #2962FF;
    &::after {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 10rpx;
      height: 10rpx;
      background-color: #2962FF;
      border-radius: 50%;
    }
  }
}

.line {
  flex: 1;
  width: 0;
  border-left: 2rpx dashed #E0E0E0;
  margin-top: 8rpx;
  margin-bottom: 8rpx;
}

.content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  padding-bottom: 60rpx;
}

.content-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-right: 20rpx;
}

.title {
  font-size: 32rpx;
  color: #333333;
  font-weight: 500;
  margin-bottom: 12rpx;
  line-height: 1.4;
}

.time {
  font-size: 28rpx;
  color: #2962FF;
  margin-bottom: 12rpx;
}

.desc {
  font-size: 24rpx;
  color: #999999;
  line-height: 1.4;
}

.content-right {
  display: flex;
  align-items: flex-start;
  padding-top: 40rpx;
}

.action-btn {
  font-size: 24rpx;
  color: #FFFFFF;
  padding: 10rpx 20rpx;
  border-radius: 8rpx;
  white-space: nowrap;

  &.red {
    background-color: #FF6B6B;
  }

  &.yellow {
    background-color: #FFD56A;
  }
}
</style>