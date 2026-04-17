<template>
  <view class="page">
    <NavBar title="员工清单" />
    
    <!-- Search Bar -->
    <view class="search-container">
      <view class="search-box">
        <image class="search-icon" src="/static/monthly/icon-search-gray.svg" mode="aspectFit" />
        <input 
          class="search-input" 
          placeholder="请输入" 
          placeholder-style="color: #999"
          v-model="searchText"
          confirm-type="search"
        />
      </view>
    </view>

    <!-- Tabs -->
    <view class="tabs">
      <view 
        v-for="(tab, index) in tabs" 
        :key="index" 
        class="tab-item" 
        :class="{ active: currentTab === index }"
        @click="currentTab = index"
      >
        <text class="tab-text">{{ tab }}</text>
        <view class="tab-indicator" v-if="currentTab === index"></view>
      </view>
    </view>

    <!-- Employee List -->
    <scroll-view class="list-container" scroll-y>
      <view class="list-content">
        <view 
          v-for="(item, index) in employeeList" 
          :key="index" 
          class="employee-card"
          @click="goDetail(item)"
        >
          <image class="avatar" :src="item.avatar || '/static/mine/avatar.svg'" mode="aspectFill" />
          <view class="info">
            <view class="name-row">
              <text class="name">{{ item.name }}</text>
              <view class="health-badge" v-if="item.healthDays <= 30">
                <text class="badge-text">健康证余{{ item.healthDays }}天</text>
              </view>
            </view>
            <view class="detail-row">
              <text>{{ item.age }}岁</text>
              <text class="divider">|</text>
              <text>{{ item.position }}</text>
              <text class="divider">|</text>
              <text>加入{{ item.years }}年</text>
            </view>
          </view>
          <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
        </view>
        
        <view class="empty-text">没有更多数据了～</view>
      </view>
    </scroll-view>

    <!-- FAB -->
    <view class="fab" @click="goAdd">
      <view class="fab-icon">+</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import NavBar from '@/components/NavBar/NavBar.vue'

const searchText = ref('')
const currentTab = ref(0)
const tabs = ['正式', '临时', '关闭']

const employeeList = ref([
  {
    id: 1,
    name: '宇文姮',
    age: 48,
    position: '售卖员',
    years: 2,
    healthDays: 28,
    avatar: ''
  },
  {
    id: 2,
    name: '宇文姮',
    age: 48,
    position: '售卖员',
    years: 2,
    healthDays: 28,
    avatar: ''
  },
  {
    id: 3,
    name: '宇文姮',
    age: 48,
    position: '售卖员',
    years: 2,
    healthDays: 28,
    avatar: ''
  },
  {
    id: 4,
    name: '宇文姮',
    age: 48,
    position: '售卖员',
    years: 2,
    healthDays: 28,
    avatar: ''
  },
  {
    id: 5,
    name: '宇文姮',
    age: 48,
    position: '售卖员',
    years: 2,
    healthDays: 28,
    avatar: ''
  }
])

const goAdd = () => {
  uni.navigateTo({ url: '/pages/executor/my/employee/add-employee' })
}

const goDetail = (item: any) => {
  // Detail page logic if needed
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #F8F9FB;
  display: flex;
  flex-direction: column;
}

.search-container {
  padding: 20rpx 30rpx;
  background-color: #fff;
}

.search-box {
  height: 72rpx;
  background-color: #F5F6F8;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  padding: 0 30rpx;
  
  .search-icon {
    width: 32rpx;
    height: 32rpx;
    margin-right: 20rpx;
  }
  
  .search-input {
    flex: 1;
    font-size: 28rpx;
    color: #333;
  }
}

.tabs {
  display: flex;
  background-color: #fff;
  height: 88rpx;
  border-bottom: 1rpx solid #eee;
  
  .tab-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    
    .tab-text {
      font-size: 30rpx;
      color: #666;
      font-weight: 400;
    }
    
    &.active {
      .tab-text {
        color: #2561EF;
        font-weight: 500;
      }
    }
    
    .tab-indicator {
      position: absolute;
      bottom: 0;
      width: 40rpx;
      height: 4rpx;
      background-color: #2561EF;
      border-radius: 2rpx;
    }
  }
}

.list-container {
  flex: 1;
  height: 0; // Important for scroll-view in flex layout
}

.list-content {
  padding: 24rpx 30rpx 120rpx; // Bottom padding for FAB
}

.employee-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  
  .avatar {
    width: 96rpx;
    height: 96rpx;
    border-radius: 48rpx;
    margin-right: 24rpx;
    background-color: #f0f0f0;
  }
  
  .info {
    flex: 1;
    
    .name-row {
      display: flex;
      align-items: center;
      margin-bottom: 12rpx;
      
      .name {
        font-size: 32rpx;
        font-weight: 500;
        color: #333;
        margin-right: 16rpx;
      }
      
      .health-badge {
        background-color: #FFFBE6;
        padding: 4rpx 12rpx;
        border-radius: 8rpx;
        
        .badge-text {
          font-size: 22rpx;
          color: #FAAD14;
        }
      }
    }
    
    .detail-row {
      font-size: 24rpx;
      color: #999;
      display: flex;
      align-items: center;
      
      .divider {
        margin: 0 12rpx;
        color: #ddd;
      }
    }
  }
  
  .arrow {
    width: 32rpx;
    height: 32rpx;
  }
}

.empty-text {
  text-align: center;
  font-size: 24rpx;
  color: #999;
  padding: 30rpx 0;
}

.fab {
  position: fixed;
  right: 40rpx;
  bottom: 80rpx;
  width: 96rpx;
  height: 96rpx;
  background-color: #2561EF;
  border-radius: 50%;
  box-shadow: 0 8rpx 16rpx rgba(37, 97, 239, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  
  .fab-icon {
    color: #fff;
    font-size: 60rpx;
    line-height: 1;
    font-weight: 300;
    margin-top: -6rpx;
  }
}
</style>