<template>
  <view class="page">
    <!-- Header Info -->
    <view class="info-card">
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查项目</view>
        <view class="value">{{ taskInfo?.canteen_name || '--' }}</view>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>提交时间</view>
        <view class="value">{{ formatTime(taskInfo?.submission_date) }}</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查人</view>
        <view class="value">{{ taskInfo?.inspector_name || '--' }}</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>总分</view>
        <view class="value">{{ taskInfo?.total_score ?? '--' }}分</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
    </view>

    <!-- Main Content with Sidebar -->
    <view class="main-container">
      <!-- Sidebar -->
      <scroll-view class="sidebar" scroll-y>
        <view 
          v-for="(cat, index) in categories" 
          :key="index"
          class="sidebar-item"
          :class="{ active: activeCategory === cat.title }"
          @click="activeCategory = cat.title"
        >
          {{ cat.title }}
        </view>
      </scroll-view>

      <!-- Right Content -->
      <scroll-view class="content-area" scroll-y>
        <view class="empty-tip" v-if="!activeItems.length">
          <text>暂无检查项</text>
        </view>
        <view class="question-item" v-for="(item, idx) in activeItems" :key="item.item_id">
          <view class="question-title">
            <view class="red-bar"></view>
            <text>{{ idx + 1 }}、{{ item.content }}（满分{{ item.total_score }}分）</text>
          </view>
          
          <view class="score-group">
            <view class="radio-item active">
              <view class="radio-circle checked"></view>
              <text>{{ item.score_given !== undefined ? item.score_given : '--' }}分</text>
            </view>
          </view>

          <!-- Original Issue -->
          <view class="issue-box" v-if="item.inspection_description || (item.inspection_photos && item.inspection_photos.length)">
            <view class="issue-text">{{ item.inspection_description || '暂无问题描述' }}</view>
            <view class="image-list" v-if="item.inspection_photos && item.inspection_photos.length">
              <image class="img" v-for="(pic, pIdx) in item.inspection_photos" :key="pIdx" :src="pic" mode="aspectFill"></image>
            </view>
          </view>

          <!-- History Logs for this item -->
          <view v-for="(log, logIdx) in getLogsForItem(item.item_id)" :key="logIdx" class="history-log" :class="log.action === 'RECTIFY' ? 'feedback-box' : 'audit-opinion'">
            <view v-if="log.action === 'RECTIFY'">
              <view class="feedback-title">食堂整改反馈：</view>
              <view class="feedback-text">{{ log.description || log.opinion || '已整改' }}</view>
              <view class="image-list" v-if="log.photos && log.photos.length">
                <image class="img" v-for="(pic, pIdx) in log.photos" :key="pIdx" :src="pic" mode="aspectFill"></image>
              </view>
              <view class="time-text">{{ formatTime(log.created_at) }}</view>
            </view>
            <view v-else>
              <text class="audit-title">审核意见 ({{ log.action === 'PASS' ? '通过' : '驳回' }})：</text>
              <text class="audit-text" :style="{ color: log.action === 'PASS' ? '#52c41a' : '#ff4d4f' }">{{ log.opinion || log.description || '--' }}</text>
              <view class="time-text">{{ formatTime(log.created_at) }}</view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchJointTaskDetail } from '@/common/joint-inspection'

const taskId = ref('')
const taskInfo = ref<any>(null)
const categories = ref<any[]>([])
const activeCategory = ref('')
const auditLogs = ref<Array<Record<string, any>>>([])

onLoad((options) => {
  if (options && options.id) {
    taskId.value = options.id
  }
})

const formatTime = (value?: string) => {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mi = String(date.getMinutes()).padStart(2, '0')
  return `${mm}月${dd}日 ${hh}:${mi}`
}

onMounted(async () => {
  if (!taskId.value) return
  try {
    const res = await fetchJointTaskDetail(taskId.value)
    taskInfo.value = res.task_info
    categories.value = res.form_snapshot?.major_items || []
    auditLogs.value = Array.isArray(res.audit_logs) ? res.audit_logs : []
    if (categories.value.length > 0) {
      activeCategory.value = categories.value[0].title
    }
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
})

const activeItems = computed(() => {
  const cat = categories.value.find(c => c.title === activeCategory.value)
  return cat ? cat.minor_items || [] : []
})

const getLogsForItem = (itemId: string) => {
  return auditLogs.value.filter(l => !l.item_id || String(l.item_id) === String(itemId))
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
  margin-bottom: 20rpx;
}

.info-row {
  display: flex;
  align-items: center;
  height: 100rpx;
  border-bottom: 1rpx solid #f5f5f5;
  
  &:last-child {
    border-bottom: none;
  }
  
  .label {
    width: 200rpx;
    font-size: 28rpx;
    color: #666;
    
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
    margin-right: 10rpx;
  }
}

.main-container {
  flex: 1;
  min-height: 0;
  display: flex;
  background: #fff;
}

.sidebar {
  width: 180rpx;
  background: #f7f9fb;
  height: 100%;
  
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
        border-radius: 0 6rpx 6rpx 0;
      }
    }
  }
}

.content-area {
  flex: 1;
  height: 100%;
  padding: 30rpx;
}

.question-item {
  margin-bottom: 40rpx;
}

.question-title {
  display: flex;
  margin-bottom: 30rpx;
  
  .red-bar {
    width: 6rpx;
    height: 32rpx;
    background: #ff4d4f;
    margin-right: 12rpx;
    margin-top: 6rpx;
    border-radius: 4rpx;
  }
  
  text {
    flex: 1;
    font-size: 30rpx;
    color: #333;
    line-height: 1.5;
    font-weight: 500;
  }
}

.score-group {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30rpx;
  padding: 0 20rpx;
}

.radio-item {
  display: flex;
  align-items: center;
  
  .radio-circle {
    width: 32rpx;
    height: 32rpx;
    border: 2rpx solid #ccc;
    border-radius: 50%;
    margin-right: 10rpx;
    
    &.checked {
      border-color: #2563eb;
      background: #2563eb;
      position: relative;
      
      &::after {
        content: '';
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 16rpx;
        height: 16rpx;
        background: #fff;
        border-radius: 50%;
      }
    }
  }
  
  text {
    font-size: 28rpx;
    color: #666;
  }
  
  &.active text {
    color: #333;
  }
}

.issue-box {
  background: #f0f7ff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  
  .issue-text {
    font-size: 28rpx;
    color: #333;
    line-height: 1.6;
    margin-bottom: 20rpx;
  }
}

.history-log {
  margin-bottom: 20rpx;
  
  .time-text {
    font-size: 24rpx;
    color: #999;
    margin-top: 12rpx;
    text-align: right;
  }
}

.audit-opinion {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  border: 1px solid #eee;
  
  .audit-title {
    font-size: 28rpx;
    color: #333;
    display: block;
    margin-bottom: 12rpx;
    font-weight: 500;
  }
  
  .audit-text {
    font-size: 28rpx;
    line-height: 1.5;
  }
}

.feedback-box {
  background: #fff9e6;
  border-radius: 12rpx;
  padding: 24rpx;
  border: 1px solid #ffe58f;
  
  .feedback-title {
    font-size: 28rpx;
    color: #333;
    margin-bottom: 12rpx;
  }
  
  .feedback-text {
    font-size: 28rpx;
    color: #666;
    margin-bottom: 20rpx;
    line-height: 1.6;
  }
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  
  .img {
    width: 140rpx;
    height: 140rpx;
    border-radius: 8rpx;
    background: #eee;
  }
}
</style>