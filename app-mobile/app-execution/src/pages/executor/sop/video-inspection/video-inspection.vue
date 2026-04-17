<template>
  <view class="page">
    <!-- Search Bar -->
    <view class="search-wrap">
      <view class="search-box">
        <text class="search-icon">🔍</text>
        <input class="search-input" type="text" placeholder="请输入" v-model="keyword" />
      </view>
    </view>

    <!-- Breadcrumbs -->
    <view class="crumbs">
      <text class="crumb blue">武岗县全县项目</text>
      <text class="crumb separator">&gt;</text>
      <text class="crumb blue">城东片区</text>
      <text class="crumb separator">&gt;</text>
      <text class="crumb gray">高中学校</text>
    </view>

    <!-- Text Tabs -->
    <view class="tabs">
      <view class="tab-item" :class="{ active: currentTab === 'rectify' }" @click="currentTab = 'rectify'">
        <text>待整改</text>
      </view>
      <view class="tab-item" :class="{ active: currentTab === 'completed' }" @click="currentTab = 'completed'">
        <text>已完成</text>
      </view>
    </view>

    <!-- Task List -->
    <scroll-view scroll-y class="list-container">
      <view
        class="task-card"
        v-for="(item, index) in filteredList"
        :key="index"
        @click="handleItemClick(item)"
      >
        <view class="card-left-border"></view>
        <view class="card-content">
          <view class="card-header">
            <text class="card-title">{{ item.title }}</text>
            <text class="card-progress">{{ item.progress }}</text>
            <text class="card-status red" v-if="item.status === 'rectify'">待整改</text>
            <text class="card-status gray" v-else>已完成</text>
          </view>
          <view class="card-info">
            <view class="info-row">
              <view class="user-info">
                <view class="avatar">👤</view>
                <text class="username">{{ item.submitter }}提交</text>
              </view>
              <text class="time">{{ item.time }}</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- Bottom Button -->
    <view class="footer">
      <button class="start-btn" @click="handleStartNew">
        开始新视频巡检
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchVideoTaskList } from '@/common/video-inspection'

const keyword = ref('')
const currentTab = ref<'rectify' | 'completed'>('rectify')

const listData = ref<any[]>([])
const loading = ref(false)

const loadTasks = async () => {
  loading.value = true
  try {
    const status = currentTab.value === 'rectify' ? 'REJECTED' : 'COMPLETED'
    const res: any = await fetchVideoTaskList({
      status,
      keyword: keyword.value || undefined,
      page: 1,
      pageSize: 50
    })
    const list = Array.isArray(res?.list) ? res.list : []
    listData.value = list.map((item: any) => ({
      id: String(item.task_id || item.id),
      title: item.template_name || item.canteen_name || '-',
      progress: `${item.total_score ?? ''}分`,
      status: item.status === 'REJECTED' ? 'rectify' : 'completed',
      submitter: item.submitter_name || item.inspector_name || item.principal || '',
      time: item.submission_date || item.business_date || '',
      rawStatus: item.status
    }))
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onLoad(() => {
  loadTasks()
})

watch([currentTab, keyword], () => {
  loadTasks()
})

const filteredList = computed(() => {
  return listData.value.filter((item) => item.status === currentTab.value)
})

const handleStartNew = () => {
  uni.showToast({ title: '开始新视频巡检', icon: 'none' })
}

const handleItemClick = (item: any) => {
  if (item.status === 'rectify') {
    uni.navigateTo({
      url: `/pages/executor/sop/video-inspection/video-inspection-rectification/video-inspection-rectification?id=${item.id}`
    })
  } else {
    uni.navigateTo({
      url: `/pages/executor/sop/video-inspection/video-inspection-completed?id=${item.id}`
    })
  }
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #F7F9FB;
}

.search-wrap {
  padding: 20rpx 30rpx;
  background-color: #fff;
}

.search-box {
  background-color: #F7F8FA;
  height: 72rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  padding: 0 20rpx;

  .search-icon {
    font-size: 32rpx;
    color: #999;
    margin-right: 16rpx;
  }

  .search-input {
    flex: 1;
    font-size: 28rpx;
    color: #333;
  }
}

.crumbs {
  padding: 0 30rpx 20rpx;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  background-color: #fff;

  .crumb {
    font-size: 26rpx;
    color: #333;

    &.blue {
      color: #2561EF;
    }

    &.gray {
      color: #999999;
    }

    &.separator {
      color: #999999;
      margin: 0 10rpx;
    }
  }
}

.tabs {
  display: flex;
  background-color: #fff;
  border-bottom: 2rpx solid #F5F5F5;

  .tab-item {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 88rpx;
    font-size: 28rpx;
    color: #999;
    position: relative;

    &.active {
      color: #333;
      font-weight: 500;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60rpx;
        height: 4rpx;
        background-color: #333;
        border-radius: 2rpx;
      }
    }
  }
}

.list-container {
  flex: 1;
  padding: 24rpx 30rpx;
  box-sizing: border-box;
}

.task-card {
  background-color: #fff;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
  display: flex;
  overflow: hidden;
  position: relative;

  .card-left-border {
    width: 8rpx;
    background-color: #FFC107;
    flex-shrink: 0;
  }

  .card-content {
    flex: 1;
    padding: 24rpx;
  }

  .card-header {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;

    .card-title {
      font-size: 30rpx;
      color: #333;
      font-weight: 500;
      flex: 1;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .card-progress {
      font-size: 26rpx;
      color: #999;
      margin-right: 12rpx;
    }

    .card-status {
      font-size: 24rpx;
      padding: 2rpx 12rpx;
      border-radius: 20rpx;
    }

    .card-status.red {
      background-color: #FFEFE5;
      color: #FF7A45;
    }

    .card-status.gray {
      background-color: #F0F0F0;
      color: #999999;
    }
  }

  .card-info {
    .info-row {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .user-info {
        display: flex;
        align-items: center;

        .avatar {
          width: 40rpx;
          height: 40rpx;
          border-radius: 50%;
          background-color: #F5F5F5;
          display: flex;
          justify-content: center;
          align-items: center;
          margin-right: 12rpx;
        }

        .username {
          font-size: 26rpx;
          color: #666666;
        }
      }

      .time {
        font-size: 24rpx;
        color: #999999;
      }
    }
  }
}

.footer {
  padding: 16rpx 30rpx 30rpx;
  background-color: #F7F9FB;

  .start-btn {
    background-color: #2561EF;
    color: #fff;
    border-radius: 44rpx;
    font-size: 32rpx;
    height: 88rpx;
    display: flex;
    align-items: center;
    justify-content: center;

    &::after {
      border: none;
    }
  }
}
</style>