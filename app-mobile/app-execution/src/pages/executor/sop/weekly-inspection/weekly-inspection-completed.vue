<template>
  <view class="page">
    <!-- Header Info -->
    <view class="info-card">
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查项目</view>
        <view class="value">{{ taskInfo.canteen_name || '--' }}</view>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>提交时间</view>
        <view class="value">{{ formatTime(taskInfo.submission_date) }}</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查人</view>
        <view class="value">{{ taskInfo.inspector_name || '--' }}</view>
        <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
      </view>
      <view class="info-row">
        <view class="label"><text class="star">*</text>检查得分</view>
        <view class="value">{{ scoreText }}</view>
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
        <view class="empty-tip" v-if="!currentCategoryItems.length">
          <text>暂无检查项</text>
        </view>
        <view class="question-item" v-for="(item, index) in currentCategoryItems" :key="item.item_id || index">
          <view class="question-title">
            <view class="red-bar"></view>
            <text>{{ index + 1 }}、{{ item.content || '--' }}（满分{{ item.total_score || 0 }}分）</text>
          </view>
          
          <view class="score-group">
            <view class="radio-item active">
              <view class="radio-circle checked"></view>
              <text>{{ item.score_given !== undefined ? item.score_given : '--' }}分</text>
            </view>
          </view>

          <!-- Original Issue (if any) -->
          <view class="issue-box" v-if="Number(item.score_given) < Number(item.total_score)">
            <view class="issue-text">{{ item.inspection_description || '暂无问题描述' }}</view>
            <view class="image-list" v-if="item.inspection_photos && item.inspection_photos.length">
              <image class="img" v-for="(photo, photoIndex) in item.inspection_photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
          </view>

          <!-- History Logs for this item -->
          <view v-for="(log, logIdx) in getLogsForItem(item.item_id)" :key="logIdx" class="history-log" :class="log.action === 'RECTIFY' ? 'feedback-box' : 'audit-opinion'">
            <view v-if="log.action === 'RECTIFY'">
              <view class="feedback-text">食堂整改反馈：{{ log.description || log.opinion || '已整改' }}</view>
              <view class="image-list" v-if="log.photos && log.photos.length">
                <image class="img" v-for="(photo, pIdx) in log.photos" :key="pIdx" :src="photo" mode="aspectFill"></image>
              </view>
              <view class="time-text">{{ formatTime(log.created_at) }}</view>
            </view>
            <view v-else>
              <text class="label">审核意见 ({{ log.action === 'PASS' ? '通过' : '驳回' }})：</text>
              <text class="text" :style="{ color: log.action === 'PASS' ? '#52c41a' : '#ff4d4f' }">{{ log.opinion || log.description || '--' }}</text>
              <view class="time-text">{{ formatTime(log.created_at) }}</view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchWeeklyTaskDetail } from '@/common/weekly-inspection'

const taskId = ref('')
const taskInfo = ref<any>({})
const allMinorItems = ref<any[]>([])
const auditLogs = ref<Array<Record<string, any>>>([])

const categories = computed(() => {
  const titles = allMinorItems.value.map((item) => item.majorTitle).filter(Boolean)
  return Array.from(new Set(titles))
})

const activeCategory = ref('')

const currentCategoryItems = computed(() => {
  if (!activeCategory.value) return allMinorItems.value
  return allMinorItems.value.filter((item) => item.majorTitle === activeCategory.value)
})

const scoreText = computed(() => {
  if (typeof taskInfo.value.total_score === 'number') return `${taskInfo.value.total_score}分`
  return '--'
})

const getLogsForItem = (itemId: string) => {
  return auditLogs.value.filter(l => !l.item_id || String(l.item_id) === String(itemId))
}

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

const loadDetail = async (id: string) => {
  try {
    const data = await fetchWeeklyTaskDetail(id)
    taskInfo.value = data.task_info || {}
    auditLogs.value = Array.isArray(data.audit_logs) ? data.audit_logs : []

    const majorItems = data.form_snapshot?.major_items || []
    const merged: any[] = []
    majorItems.forEach((major: any) => {
      ;(major.minor_items || []).forEach((minor: any) => {
        merged.push({
          ...minor,
          majorTitle: major.title || '未分类'
        })
      })
    })
    allMinorItems.value = merged
    activeCategory.value = categories.value[0] || ''
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

onLoad(async (options) => {
  const id = typeof options?.id === 'string' ? options.id : ''
  if (!id) {
    uni.showToast({ title: '缺少任务ID', icon: 'none' })
    return
  }
  taskId.value = id
  await loadDetail(id)
})
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

.question-item {
  margin-bottom: 40rpx;
}

.question-title {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20rpx;
  
  .red-bar {
    width: 6rpx;
    height: 28rpx;
    background: #ff4d4f;
    margin-right: 12rpx;
    margin-top: 8rpx;
  }
  
  text {
    flex: 1;
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
  }
}

.score-group {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  padding-left: 20rpx;
  
  .radio-item {
    display: flex;
    align-items: center;
    margin-right: 40rpx;
    
    .radio-circle {
      width: 32rpx;
      height: 32rpx;
      border-radius: 50%;
      border: 2rpx solid #d9d9d9;
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
  }
}

.issue-box {
  background: #fffbe6;
  padding: 24rpx;
  border-radius: 8rpx;
  margin-bottom: 20rpx;
  
  .issue-text {
    font-size: 28rpx;
    color: #d48806;
    margin-bottom: 16rpx;
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
  
  .label {
    font-size: 28rpx;
    color: #333;
    display: block;
    margin-bottom: 12rpx;
    font-weight: 500;
  }
  
  .text {
    font-size: 28rpx;
    line-height: 1.5;
  }
}

.feedback-box {
  background: #f6ffed;
  border-radius: 12rpx;
  padding: 24rpx;
  border: 1px solid #b7eb8f;
  
  .feedback-text {
    font-size: 28rpx;
    color: #52c41a;
    margin-bottom: 16rpx;
    font-weight: 500;
  }
}
</style>