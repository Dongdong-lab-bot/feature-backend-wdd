<template>
  <view class="page">
    <!-- Header Info -->
    <view class="info-card" v-if="taskInfo">
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查项目</view>
        <view class="value">{{ taskInfo.canteen_name || '--' }}</view>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>提交时间</view>
        <view class="value">{{ (taskInfo as any).submission_date || '--' }}</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查人</view>
        <view class="value">{{ taskInfo.inspector_name || '--' }}</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>总分</view>
        <view class="value">{{ taskInfo.total_score ?? '--' }}分</view>
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
            <view :class="getIssueTypeClass(item.issue_type)"></view>
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
            <view class="issue-text" v-if="item.inspection_description">{{ item.inspection_description }}</view>
            <view class="image-list" v-if="item.inspection_photos && item.inspection_photos.length">
              <image 
                class="img" 
                v-for="(pic, pIdx) in item.inspection_photos" 
                :key="pIdx"
                :src="pic" 
                mode="aspectFill"
              ></image>
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
import { fetchVideoTaskDetail } from '@/common/video-inspection'

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
    const res = await fetchVideoTaskDetail(taskId.value)
    taskInfo.value = res.task_info
    categories.value = res.form_snapshot?.major_items || []
    auditLogs.value = Array.isArray(res.audit_logs) ? res.audit_logs : []
    if (categories.value.length > 0) {
      activeCategory.value = categories.value[0].title
    }
  } catch (error) {
    console.error('Failed to load video task detail', error)
  }
})

const activeItems = computed(() => {
  const cat = categories.value.find(c => c.title === activeCategory.value)
  return cat ? cat.minor_items || [] : []
})

const getIssueTypeClass = (issueType?: string) => {
  if (issueType === 'RED_LINE') return 'red-bar'
  if (issueType === 'YELLOW_LINE') return 'yellow-bar'
  return 'blue-bar'
}

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
    margin-right: 10rpx;
  }
}

.main-container {
  flex: 1;
  min-height: 0;
  display: flex;
  background: #fff;
  margin-top: 20rpx;
}

.sidebar {
  width: 180rpx;
  background: #f7f9fb;
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
  height: 100%;
  padding: 30rpx;
  background: #fff;
}

.question-item {
  margin-bottom: 40rpx;
}

.question-title {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20rpx;
  font-size: 30rpx;
  color: #333;
  line-height: 1.5;
  
  .red-bar {
    width: 6rpx;
    height: 30rpx;
    background: #ff4d4f;
    margin-right: 16rpx;
    margin-top: 8rpx;
    flex-shrink: 0;
  }
  .yellow-bar {
    width: 6rpx;
    height: 30rpx;
    background: #faad14;
    margin-right: 16rpx;
    margin-top: 8rpx;
    flex-shrink: 0;
  }
  .blue-bar {
    width: 6rpx;
    height: 30rpx;
    background: #2563eb;
    margin-right: 16rpx;
    margin-top: 8rpx;
    flex-shrink: 0;
  }
}

.score-group {
  display: flex;
  justify-content: space-between;
  padding: 0 20rpx;
  margin-bottom: 24rpx;
}

.radio-item {
  display: flex;
  align-items: center;
  
  text {
    font-size: 28rpx;
    color: #666;
    margin-left: 12rpx;
  }
  
  &.active text {
    color: #333;
  }
}

.radio-circle {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  border: 2rpx solid #ccc;
  
  &.checked {
    border-color: #2563eb;
    background: #2563eb;
    position: relative;
    
    &::after {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 12rpx;
      height: 12rpx;
      background: #fff;
      border-radius: 50%;
    }
  }
}

.issue-box {
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  
  .issue-text {
    font-size: 28rpx;
    color: #333;
    margin-bottom: 20rpx;
    line-height: 1.5;
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
  background: #fffbf0;
  border-radius: 12rpx;
  padding: 20rpx;
  border: 1px solid #ffe58f;
  
  .feedback-title {
    font-size: 28rpx;
    color: #333;
    margin-bottom: 10rpx;
  }
  
  .feedback-text {
    font-size: 28rpx;
    color: #333;
    margin-bottom: 20rpx;
    line-height: 1.5;
  }
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  margin-bottom: 20rpx;
  
  .img {
    width: 160rpx;
    height: 160rpx;
    border-radius: 8rpx;
    background: #eee;
  }
}
</style>