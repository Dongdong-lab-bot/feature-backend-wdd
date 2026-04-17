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
              <text>{{ item.score_given !== undefined && item.score_given !== null ? item.score_given : (item.total_score || '--') }}分</text>
            </view>
          </view>

          <!-- Original Issue (if any) -->
          <view class="issue-box" v-if="item.inspection_description || (item.inspection_photos && item.inspection_photos.length)">
            <view class="issue-text" v-if="item.inspection_description">{{ item.inspection_description }}</view>
            <view class="image-list" v-if="item.inspection_photos && item.inspection_photos.length">
              <image class="img" v-for="(photo, photoIndex) in item.inspection_photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
          </view>

          <!-- History Logs for this item -->
          <view class="history-section" v-if="getLogsForItem(item.item_id).length > 0">
            <view v-for="(log, logIdx) in getLogsForItem(item.item_id)" :key="logIdx" class="history-log">
              <view class="log-header">
                <text class="log-title" :class="log.action === 'RECTIFY' ? 'rectify-title' : 'audit-title'">
                  {{ log.action === 'RECTIFY' ? '食堂整改提交' : (log.action === 'PASS' ? '审核通过' : '审核驳回') }}
                </text>
                <text class="log-time">{{ formatTime(log.created_at) }}</text>
              </view>
              <view class="log-content">
                <text class="log-text">{{ log.description || log.opinion || '--' }}</text>
                <view class="image-list" v-if="log.photos && log.photos.length">
                  <image 
                    v-for="(photo, pIdx) in log.photos" 
                    :key="pIdx" 
                    :src="photo" 
                    mode="aspectFill" 
                    class="img"
                  ></image>
                </view>
              </view>
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
import { inspectionApi } from '@/api'
import type { WeeklyTaskInfo, WeeklyTaskMinorItem } from '@/api/modules/inspection'

const taskId = ref('')
const taskInfo = ref<Partial<WeeklyTaskInfo>>({})
const allMinorItems = ref<Array<WeeklyTaskMinorItem & { majorTitle: string }>>([])
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
  return auditLogs.value.filter(l => !l.item_id || l.item_id === itemId)
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
  const data = await inspectionApi.getJointTaskDetail(id)
  taskInfo.value = data.task_info || {}
  auditLogs.value = Array.isArray(data.audit_logs) ? data.audit_logs : []

  const majorItems = data.form_snapshot?.major_items || []
  const merged: Array<WeeklyTaskMinorItem & { majorTitle: string }> = []
  majorItems.forEach((major: any) => {
    ;(major.minor_items || []).forEach((minor: any) => {
      // 容错处理：确保即使 score_given 丢失也能显示满分
      const actualScore = minor.score_given !== undefined && minor.score_given !== null 
        ? minor.score_given 
        : minor.total_score;

      merged.push({
        ...minor,
        score_given: actualScore,
        majorTitle: major.title || '未分类'
      })
    })
  })
  allMinorItems.value = merged
  activeCategory.value = categories.value[0] || ''
}

onLoad(async (options) => {
  const id = typeof options?.id === 'string' ? options.id : ''
  if (!id || id === 'undefined' || id === 'null') {
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

.history-section {
  margin-top: 30rpx;
  border-top: 1rpx solid #eee;
  padding-top: 20rpx;
}

.history-log {
  margin-bottom: 24rpx;
  background: #f4f8ff;
  border-radius: 12rpx;
  padding: 24rpx;
  border: 1px solid #d6e4ff;
  
  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12rpx;
    
    .log-title {
      font-size: 28rpx;
      font-weight: 500;
      color: #2b5fed;
    }
    
    .log-time {
      font-size: 24rpx;
      color: #999;
    }
  }
  
  .log-content {
    .log-text {
      font-size: 28rpx;
      color: #333;
      line-height: 1.5;
      display: block;
      margin-bottom: 16rpx;
    }
  }
}
</style>
