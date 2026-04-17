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
      <button class="submit-btn" @click="submitChecklist">完成周排查</button>
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
      url: '/pages/weekly/submit-success'
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
    color: #333;
    text-align: right;
  }
  
  .arrow {
    margin-left: 10rpx;
  }
}

.main-container {
  flex: 1;
  display: flex;
  min-height: 0;
  margin-top: 20rpx;
  background: #fff;
}

.sidebar {
  width: 180rpx;
  background: #fff;
  border-right: 1rpx solid #f0f0f0;
  
  .sidebar-item {
    height: 100rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26rpx;
    color: #333;
    position: relative;
    
    &.active {
      background: #e6f0ff;
      color: #2563eb;
      font-weight: 500;
    }
  }
}

.content-area {
  flex: 1;
  padding: 30rpx;
  background: #fff;
}

.check-item {
  margin-bottom: 40rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.item-title {
  display: flex;
  margin-bottom: 20rpx;
  
  .red-bar {
    width: 6rpx;
    background: #ff4d4f;
    margin-right: 12rpx;
    height: 32rpx;
    margin-top: 6rpx;
  }
  
  .yellow-bar {
    width: 6rpx;
    background: #f59e0b;
    margin-right: 12rpx;
    height: 32rpx;
    margin-top: 6rpx;
  }
  
  .blue-bar {
    width: 6rpx;
    background: #2563eb;
    margin-right: 12rpx;
    height: 32rpx;
    margin-top: 6rpx;
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
  margin-bottom: 30rpx;
  padding-left: 18rpx;
  
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
      
      &.checked {
        border-color: #2563eb;
        background: #2563eb;
      }
    }
    
    text {
      font-size: 28rpx;
      color: #333;
    }
  }
}

.input-area {
  background: #f7f9fb;
  border-radius: 8rpx;
  padding: 20rpx;
  min-height: 160rpx;
  position: relative;
  
  .textarea {
    width: 100%;
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
  }
  
  .upload-btn {
    position: absolute;
    right: 20rpx;
    bottom: 20rpx;
    width: 64rpx;
    height: 64rpx;
    border-radius: 50%;
    border: 2rpx dashed #2563eb;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fff;
  }
}

.footer {
  background: #fff;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + constant(safe-area-inset-bottom));
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #f0f0f0;
  
  .submit-btn {
    height: 88rpx;
    line-height: 88rpx;
    background: #2563eb;
    color: #fff;
    font-size: 32rpx;
    border-radius: 12rpx;
    
    &::after {
      border: none;
    }
  }
}
</style>