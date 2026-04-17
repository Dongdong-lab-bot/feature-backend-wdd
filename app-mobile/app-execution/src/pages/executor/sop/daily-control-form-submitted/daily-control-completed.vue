<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <!-- Header Info -->
      <view class="info-card">
        <view class="info-row">
          <view class="label"><text class="star">*</text>检查项目</view>
          <view class="value">{{ taskInfo.canteen_name || '--' }}</view>
        </view>
        <view class="info-row">
          <view class="label"><text class="star">*</text>开始时间</view>
          <view class="value">{{ formatTime(taskInfo.actual_start_time) }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
        <view class="info-row">
          <view class="label"><text class="star">*</text>检查人</view>
          <view class="value">{{ taskInfo.inspector_name || '--' }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
        <view class="info-row">
          <view class="label"><text class="star">*</text>完成项</view>
          <view class="value">{{ progressText }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
        <view class="info-row">
          <view class="label"><text class="star">*</text>提交时间</view>
          <view class="value">{{ formatTime(taskInfo.submission_date) }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
      </view>

      <!-- Content Section -->
      <view class="checklist">
        <view class="empty-text" v-if="!formSnapshot.length">暂无检查项</view>
        <view class="detail-card" v-for="(item, index) in formSnapshot" :key="item.item_id || index">
          <view class="item-title">{{ index + 1 }}、{{ item.content || '--' }}</view>
          
          <view class="radio-group">
            <view class="radio-item">
              <view class="radio-icon checked" :style="{ borderColor: item.is_qualified !== false ? '#52c41a' : '#ff4d4f', borderWidth: '10rpx' }"></view>
              <text>{{ item.is_qualified !== false ? '完成且合格' : '未完成' }}</text>
            </view>
          </view>

          <view class="result-box" v-if="item.is_qualified === false">
            <text class="result-text">{{ item.description || '暂无描述' }}</text>
            <view class="photo-list" v-if="item.photos && item.photos.length">
              <image class="photo-item" v-for="(photo, photoIndex) in item.photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
          </view>

          <!-- History Logs for this item -->
          <view v-for="(log, logIdx) in getLogsForItem(item.item_id)" :key="logIdx" class="history-log" :class="log.action === 'RECTIFY' ? 'feedback-box' : 'audit-opinion'">
            <view v-if="log.action === 'RECTIFY'">
              <view class="feedback-text">食堂整改反馈：{{ log.description || log.opinion || '已整改' }}</view>
              <view class="photo-list" v-if="log.photos && log.photos.length">
                <image class="photo-item" v-for="(photo, pIdx) in log.photos" :key="pIdx" :src="photo" mode="aspectFill"></image>
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
      </view>

    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchDailyTaskDetail } from '@/common/daily-control'

const taskInfo = ref<any>({})
const formSnapshot = ref<any[]>([])
const auditLogs = ref<Array<Record<string, any>>>([])

const progressText = computed(() => {
  if (!formSnapshot.value.length) return '--'
  const finished = formSnapshot.value.filter((item) => item.is_qualified !== undefined).length
  return `${finished}/${formSnapshot.value.length}`
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
    const data = await fetchDailyTaskDetail(id)
    taskInfo.value = data.task_info || {}
    formSnapshot.value = Array.isArray(data.form_snapshot) ? data.form_snapshot : []
    auditLogs.value = Array.isArray(data.audit_logs) ? data.audit_logs : []
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

.content {
  flex: 1;
  min-height: 0;
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
  border-bottom: 1rpx solid #f0f0f0;
  
  &:last-child {
    border-bottom: none;
  }
  
  .label {
    width: 160rpx;
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

.checklist {
  background: #f7f9fb;
}

.detail-card {
  background: #fff;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  text-align: center;
  color: #999;
  padding: 40rpx;
  font-size: 28rpx;
}

.item-title {
  font-size: 32rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 30rpx;
  line-height: 1.5;
}

.radio-group {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  
  .radio-item {
    display: flex;
    align-items: center;
    margin-right: 40rpx;
    
    .radio-icon {
      width: 32rpx;
      height: 32rpx;
      border-radius: 50%;
      border: 2rpx solid #ccc;
      margin-right: 12rpx;
      box-sizing: border-box;
    }
    
    text {
      font-size: 28rpx;
      color: #333;
    }
  }
}

.result-box {
  background: #f7f9fb;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  
  .result-text {
    font-size: 28rpx;
    color: #666;
    line-height: 1.5;
    display: block;
    margin-bottom: 16rpx;
  }
}

.photo-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  
  .photo-item {
    width: 160rpx;
    height: 160rpx;
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