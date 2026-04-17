<template>
  <view class="page">
    <NavBar title="数据中心" :showBack="false" />

    <scroll-view class="body" scroll-y>
      <view class="summary-card">
        <view class="month-switch">
          <text class="month-text">&lt;&nbsp;&nbsp; 2020年1月 &nbsp;&nbsp;&gt;</text>
        </view>

        <view class="pie-wrap">
          <image class="pie-main" src="/static/data/pie-main.svg" mode="aspectFit" />
          <image class="pie-alert" src="/static/data/pie-alert.svg" mode="aspectFit" />
          <image class="pie-inner" src="/static/data/pie-inner.svg" mode="aspectFit" />
          <view class="pie-center">
            <text class="days"><text class="days-num">24</text>天</text>
            <text class="days-label">食堂监管</text>
          </view>

          <view class="normal-tip">
            <image class="tip-line" src="/static/data/line-normal.svg" mode="aspectFit" />
            <text class="tip-text blue">SOP正常20家</text>
          </view>
          <view class="alert-tip">
            <image class="tip-line" src="/static/data/line-alert.svg" mode="aspectFit" />
            <text class="tip-text red">sop异常6家</text>
          </view>
        </view>
      </view>

      <view class="metrics-card">
        <view class="metrics-grid">
          <view class="metric-item" v-for="item in metrics" :key="item.label">
            <text class="metric-label">{{ item.label }}</text>
            <view class="metric-value-row">
              <text class="metric-value" :class="{ red: item.danger }">{{ item.value }}</text>
              <text v-if="item.unit" class="metric-unit" :class="{ red: item.danger }">{{ item.unit }}</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import NavBar from '../../components/NavBar/NavBar.vue'

const metrics = [
  { label: '日管控完成', value: '26家' },
  { label: '周排查完成', value: '20家' },
  { label: '月调度', value: '20家' },
  { label: '常规问题', value: '240个' },
  { label: '红线问题', value: '3', unit: '个', danger: true },
  { label: '黄线问题', value: '3', unit: '个', danger: true },
  { label: '视频在线率', value: '95.2%' }
]
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.body {
  flex: 1;
  min-height: 0;
  padding: 20rpx;
  box-sizing: border-box;
}

.summary-card {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 24rpx;
}

.month-switch {
  width: 220rpx;
  height: 56rpx;
  border-radius: 12rpx;
  background: #f7f9fb;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.month-text {
  font-size: 24rpx;
  color: #111111;
  font-weight: 600;
}

.pie-wrap {
  margin-top: 16rpx;
  height: 258rpx;
  position: relative;
}

.pie-main,
.pie-alert {
  position: absolute;
  left: 50%;
  top: 12rpx;
  width: 256rpx;
  height: 256rpx;
  transform: translateX(-50%);
}

.pie-inner {
  position: absolute;
  left: 50%;
  top: 52rpx;
  width: 184rpx;
  height: 184rpx;
  transform: translateX(-50%);
}

.pie-center {
  position: absolute;
  left: 50%;
  top: 102rpx;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.days {
  font-size: 28rpx;
  color: #111111;
  font-weight: 600;
}

.days-num {
  font-size: 48rpx;
  font-weight: 700;
}

.days-label {
  font-size: 24rpx;
  color: #999999;
  margin-top: 4rpx;
}

.normal-tip {
  position: absolute;
  left: 0;
  bottom: 34rpx;
  width: 188rpx;
}

.alert-tip {
  position: absolute;
  right: 0;
  top: 58rpx;
  width: 188rpx;
}

.tip-line {
  width: 100%;
  height: 38rpx;
}

.tip-text {
  position: absolute;
  top: -8rpx;
  font-size: 24rpx;
  font-weight: 600;
}

.tip-text.blue {
  left: 8rpx;
  color: #2561ef;
}

.tip-text.red {
  right: 2rpx;
  color: #fa746b;
}

.metrics-card {
  margin-top: 16rpx;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 16rpx;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10rpx;
}

.metric-item {
  height: 108rpx;
  border-radius: 12rpx;
  background: #f7f9fb;
  padding: 16rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-label {
  font-size: 22rpx;
  color: #999999;
}

.metric-value-row {
  display: flex;
  align-items: baseline;
}

.metric-value {
  font-size: 36rpx;
  color: #111111;
  font-weight: 700;
  line-height: 1;
}

.metric-unit {
  margin-left: 4rpx;
  font-size: 22rpx;
  color: #111111;
}

.metric-value.red,
.metric-unit.red {
  color: #fa746b;
}
</style>
