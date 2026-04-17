<template>
  <view class="page">
    <!-- Header Info -->
    <view class="info-card">
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查项目</view>
        <view class="value">武岗一中一食堂</view>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>开始时间</view>
        <view class="value">01月20日 9:30</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查人</view>
        <view class="value">食安总监</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
    </view>

    <!-- Main Content with Sidebar -->
    <view class="main-container">
      <!-- Sidebar -->
      <scroll-view class="sidebar" scroll-y>
        <view 
          v-for="(item, index) in categories" 
          :key="index"
          class="sidebar-item"
          :class="{ active: activeCategory === item }"
          @click="activeCategory = item"
        >
          {{ item }}
        </view>
      </scroll-view>

      <!-- Right Content -->
      <scroll-view class="content-area" scroll-y>
        <view class="checklist">
          <!-- Item 1 -->
          <view class="check-item">
            <view class="item-title">
              <view class="red-bar"></view>
              <text>1、卫生清洁及时，地面无积水（满分6分）</text>
            </view>
            
            <view class="score-group">
              <view class="radio-item active">
                <view class="radio-circle checked"></view>
                <text>2分</text>
              </view>
              <view class="radio-item">
                <view class="radio-circle"></view>
                <text>4分</text>
              </view>
              <view class="radio-item">
                <view class="radio-circle"></view>
                <text>6分</text>
              </view>
            </view>

            <view class="input-area">
              <textarea class="textarea" placeholder="请输入" placeholder-style="color:#ccc" auto-height></textarea>
              <view class="upload-btn">
                <uni-icons type="plusempty" size="24" color="#2563eb"></uni-icons>
              </view>
            </view>
          </view>

          <!-- Item 2 -->
          <view class="check-item">
            <view class="item-title">
              <view class="yellow-bar"></view>
              <text>1、卫生清洁及时，地面无积水（满分6分）</text>
            </view>
            
            <view class="score-group">
              <view class="radio-item active">
                <view class="radio-circle checked"></view>
                <text>2分</text>
              </view>
              <view class="radio-item">
                <view class="radio-circle"></view>
                <text>4分</text>
              </view>
              <view class="radio-item">
                <view class="radio-circle"></view>
                <text>6分</text>
              </view>
            </view>

            <view class="input-area">
              <textarea class="textarea" placeholder="请输入" placeholder-style="color:#ccc" auto-height></textarea>
              <view class="upload-btn">
                <uni-icons type="plusempty" size="24" color="#2563eb"></uni-icons>
              </view>
            </view>
          </view>
          
          <!-- Item 3 -->
          <view class="check-item">
            <view class="item-title">
              <view class="blue-bar"></view>
              <text>1、卫生清洁及时，地面无积水（满分6分）</text>
            </view>
            
            <view class="score-group">
              <view class="radio-item active">
                <view class="radio-circle checked"></view>
                <text>2分</text>
              </view>
              <view class="radio-item">
                <view class="radio-circle"></view>
                <text>4分</text>
              </view>
              <view class="radio-item">
                <view class="radio-circle"></view>
                <text>6分</text>
              </view>
            </view>

            <view class="input-area">
              <textarea class="textarea" placeholder="请输入" placeholder-style="color:#ccc" auto-height></textarea>
              <view class="upload-btn">
                <uni-icons type="plusempty" size="24" color="#2563eb"></uni-icons>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- Footer -->
    <view class="footer">
      <button class="submit-btn" @click="submitChecklist">完成联合巡检</button>
      <view class="safe-area"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const categories = [
  '人员风险项',
  '食材风险项',
  '环境风险项',
  '设备风险项',
  '消费风险项'
]

const activeCategory = ref('环境风险项')

const submitChecklist = () => {
  uni.showToast({
    title: '已提交',
    icon: 'success'
  })

  setTimeout(() => {
    uni.navigateTo({
      url: '/pages/joint/submit-success'
    })
  }, 1000)
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.info-card {
  background: #fff;
  padding: 0 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.info-row {
  display: flex;
  align-items: center;
  height: 88rpx;
  border-bottom: 1rpx solid #f5f5f5;
  
  &:last-child {
    border-bottom: none;
  }
  
  .label {
    width: 180rpx;
    font-size: 28rpx;
    color: #333;
    display: flex;
    align-items: center;
    
    .star {
      color: #ff4d4f;
      margin-right: 4rpx;
    }
  }
  
  .value {
    flex: 1;
    font-size: 28rpx;
    color: #666;
    text-align: right;
  }
  
  .arrow {
    margin-left: 10rpx;
  }
}

.main-container {
  flex: 1;
  min-height: 0;
  display: flex;
  background: #f7f9fb;
}

.sidebar {
  width: 180rpx;
  background: #f0f2f5;
  height: 100%;
}

.sidebar-item {
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  color: #666;
  position: relative;
  
  &.active {
    background: #fff;
    color: #2563eb;
    font-weight: 500;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 30rpx;
      bottom: 30rpx;
      width: 6rpx;
      background: #2563eb;
      border-radius: 0 4rpx 4rpx 0;
    }
  }
}

.content-area {
  flex: 1;
  background: #fff;
  height: 100%;
}

.checklist {
  padding: 30rpx;
}

.check-item {
  margin-bottom: 40rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.item-title {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24rpx;
  
  .red-bar {
    width: 8rpx;
    height: 32rpx;
    background: #ff4d4f;
    margin-right: 12rpx;
    margin-top: 6rpx;
    border-radius: 4rpx;
  }
  
  .yellow-bar {
    width: 8rpx;
    height: 32rpx;
    background: #ff9f43;
    margin-right: 12rpx;
    margin-top: 6rpx;
    border-radius: 4rpx;
  }
  
  .blue-bar {
    width: 8rpx;
    height: 32rpx;
    background: #2563eb;
    margin-right: 12rpx;
    margin-top: 6rpx;
    border-radius: 4rpx;
  }
  
  text {
    flex: 1;
    font-size: 30rpx;
    color: #333;
    line-height: 1.5;
  }
}

.score-group {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
  padding-left: 20rpx;
}

.radio-item {
  display: flex;
  align-items: center;
  margin-right: 40rpx;
  
  .radio-circle {
    width: 32rpx;
    height: 32rpx;
    border-radius: 50%;
    border: 2rpx solid #ccc;
    margin-right: 12rpx;
    box-sizing: border-box;
    
    &.checked {
      border: 10rpx solid #2563eb;
    }
  }
  
  text {
    font-size: 28rpx;
    color: #333;
  }
  
  &.active text {
    color: #2563eb;
  }
}

.input-area {
  background: #f9fafb;
  border-radius: 8rpx;
  padding: 20rpx;
  
  .textarea {
    width: 100%;
    font-size: 28rpx;
    color: #333;
    min-height: 100rpx;
    margin-bottom: 20rpx;
  }
  
  .upload-btn {
    width: 120rpx;
    height: 120rpx;
    background: #fff;
    border: 2rpx dashed #ddd;
    border-radius: 8rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.footer {
  background: #fff;
  padding: 20rpx 30rpx;
  border-top: 1rpx solid #eee;
  
  .submit-btn {
    height: 88rpx;
    line-height: 88rpx;
    background: #2563eb;
    color: #fff;
    font-size: 32rpx;
    border-radius: 44rpx;
    
    &:active {
      opacity: 0.9;
    }
  }
  
  .safe-area {
    height: env(safe-area-inset-bottom);
  }
}
</style>
