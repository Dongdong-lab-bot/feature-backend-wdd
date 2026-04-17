<template>
  <view class="guide-container">
    <swiper class="swiper" :indicator-dots="true" :autoplay="false" :duration="500" indicator-active-color="#007aff">
      <swiper-item v-for="(item, index) in guideList" :key="index">
        <view class="swiper-item">
          <view class="content-wrapper">
            <image :src="item.src" mode="widthFix" class="guide-image"></image>
            <view class="text-container">
              <text class="title">{{ item.title }}</text>
              <text class="subtitle">{{ item.subtitle }}</text>
            </view>
          </view>
          
          <!-- 最后一页显示按钮 -->
          <view v-if="index === guideList.length - 1" class="btn-container">
            <button class="start-btn" @click="handleStart">立即体验</button>
          </view>
        </view>
      </swiper-item>
    </swiper>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const guideList = ref([
  {
    src: '/static/guide/guide_daily.svg',
    title: '日周月管控',
    subtitle: '日管控 周排查 月调度 全闭环管理'
  },
  {
    src: '/static/guide/guide_ledger.svg',
    title: '电子台账',
    subtitle: '全真实台账 自动设备数据关联'
  },
  {
    src: '/static/guide/guide_sop.svg',
    title: 'SOP流程管理',
    subtitle: '食堂管理流程一目了然 清晰执行跟进'
  }
]);

const handleStart = () => {
  // Navigate to login page
  // Using reLaunch to close all pages and open the login page
  uni.reLaunch({
    url: '/pages/login/login'
  });
};
</script>

<style lang="scss" scoped>
.guide-container {
  width: 100vw;
  height: 100vh;
  background-color: #ffffff;
}

.swiper {
  width: 100%;
  height: 100%;
}

.swiper-item {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 100rpx; /* Adjust spacing to make room for button or visual balance */
  padding: 0 40rpx;
}

.guide-image {
  width: 500rpx; /* Adjust size as needed based on SVG dimensions */
  height: auto;
  margin-bottom: 60rpx;
}

.text-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 20rpx;
}

.subtitle {
  font-size: 28rpx;
  color: #666666;
  line-height: 1.5;
}

.btn-container {
  position: absolute;
  bottom: 150rpx;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
}

.start-btn {
  width: 320rpx;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 44rpx;
  font-size: 32rpx;
  background-color: #007aff;
  box-shadow: 0 4rpx 12rpx rgba(0, 122, 255, 0.3);
}
</style>
