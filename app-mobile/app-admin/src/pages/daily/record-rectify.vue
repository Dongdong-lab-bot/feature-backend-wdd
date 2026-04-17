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
        <view class="empty-text" v-if="!unqualifiedItems.length">暂无不合格项</view>
        <view class="detail-card" v-for="(item, index) in unqualifiedItems" :key="item.item_id || index">
          <view class="item-title">{{ index + 1 }}、{{ item.content || '--' }}</view>
          
          <view class="radio-group">
            <view class="radio-item">
              <view class="radio-icon checked" style="border-color:#ff4d4f; border-width: 10rpx;"></view>
              <text>未完成</text>
            </view>
          </view>

          <view class="result-box">
            <text class="result-text">{{ item.description || '暂无描述' }}</text>
            <view class="photo-list" v-if="item.photos && item.photos.length">
              <image class="photo-item" v-for="(photo, photoIndex) in item.photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
          </view>

          <!-- Audit Opinion History (if any) -->
          <view class="audit-opinion" v-if="getRejectLog(item.item_id)">
            <text class="label">前次审核意见：</text>
            <text class="text">{{ getRejectLog(item.item_id) }}</text>
          </view>

          <!-- Feedback Section (if any rectification happened) -->
          <view class="feedback-box" v-if="getRectifyLog(item.item_id)">
            <view class="feedback-text">食堂整改反馈：{{ getRectifyLog(item.item_id)?.description || '已整改' }}</view>
            <view class="photo-list" v-if="getRectifyLog(item.item_id)?.photos?.length">
              <image class="photo-item" v-for="(photo, photoIndex) in getRectifyLog(item.item_id)?.photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
          </view>
        </view>
      </view>

      <view class="audit-input-area" v-if="taskInfo.status === 'RECTIFIED'">
        <text class="label">整改审核意见请输入：</text>
        <textarea class="textarea" v-model="auditOpinion" placeholder="" auto-height></textarea>
      </view>
      
      <view class="audit-actions" v-if="taskInfo.status === 'RECTIFIED'">
        <view class="radio-item" :class="{ active: currentAction === 'PASS' }" @click="currentAction = 'PASS'">
          <view class="radio-icon" :class="{ checked: currentAction === 'PASS' }"></view>
          <text>审核通过</text>
        </view>
        <view class="radio-item" :class="{ active: currentAction === 'REJECT' }" @click="currentAction = 'REJECT'">
          <view class="radio-icon" :class="{ checked: currentAction === 'REJECT' }"></view>
          <text>审核驳回</text>
        </view>
      </view>

    </scroll-view>

    <view class="footer" v-if="taskInfo.status === 'RECTIFIED'">
      <button class="submit-btn" :disabled="submitting" :class="{ disabled: submitting }" @click="handleCompleteAudit">
        {{ submitting ? '提交中...' : '完成审核' }}
      </button>
      <view class="safe-area"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { inspectionApi } from '@/api'
import type { DailyTaskFormItem, DailyTaskInfo } from '@/api/modules/inspection'

const taskInfo = ref<Partial<DailyTaskInfo>>({})
const formSnapshot = ref<DailyTaskFormItem[]>([])
const auditOpinion = ref('')
const auditLogs = ref<Array<Record<string, any>>>([])
const taskId = ref('')
const submitting = ref(false)
const currentAction = ref<'PASS'|'REJECT'>('PASS')

const unqualifiedItems = computed(() => {
  return formSnapshot.value.filter(item => item.is_qualified === false)
})

const progressText = computed(() => {
  if (!formSnapshot.value.length) return '--'
  const finished = formSnapshot.value.filter((item) => item.is_qualified !== undefined).length
  return `${finished}/${formSnapshot.value.length}`
})

const getRejectLog = (itemId: string | number) => {
  const log = [...auditLogs.value].reverse().find(l => l.action === 'REJECT' && (!l.item_id || String(l.item_id) === String(itemId)))
  return log ? log.opinion : ''
}

const getRectifyLog = (itemId: string | number) => {
  const log = [...auditLogs.value].reverse().find(l => l.action === 'RECTIFY' && (!l.item_id || String(l.item_id) === String(itemId)))
  return log ? log : null
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
  const data = await inspectionApi.getDailyTaskDetail(id)
  taskInfo.value = data.task_info || {}
  
  const snapshot = Array.isArray(data.form_snapshot) ? data.form_snapshot : []
  formSnapshot.value = snapshot.map(item => {
    let isQ = item.is_qualified
    if (isQ === 1 || isQ === 'true' || isQ === '1') isQ = true
    else if (isQ === 0 || isQ === 'false' || isQ === '0') isQ = false
    else isQ = undefined
    
    return {
      ...item,
      is_qualified: isQ
    }
  })
  
  auditLogs.value = Array.isArray(data.audit_logs) ? data.audit_logs : []
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

const getAuditorId = () => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  const userId = userInfo?.id
  if (userId !== undefined && userId !== null && `${userId}`.trim()) return `${userId}`
  return ''
}

const handleCompleteAudit = async () => {
  if (!taskId.value) {
    uni.showToast({ title: '缺少任务ID', icon: 'none' })
    return
  }
  const auditorId = getAuditorId()
  if (!auditorId) {
    uni.showToast({ title: '缺少审核人信息，请重新登录', icon: 'none' })
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    await inspectionApi.auditDailyTask(taskId.value, {
      auditor_id: auditorId,
      action: currentAction.value,
      opinion: auditOpinion.value.trim() || (currentAction.value === 'PASS' ? '整改通过' : '整改驳回')
    })
    uni.showToast({ title: '审核完成', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/daily/audit-success'
      })
    }, 500)
  } finally {
    submitting.value = false
  }
}
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

.audit-opinion {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  
  .label {
    font-size: 28rpx;
    color: #333;
    display: block;
    margin-bottom: 12rpx;
    font-weight: 500;
  }
  
  .text {
    font-size: 28rpx;
    color: #ff4d4f;
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

.audit-input-area {
  background: #fff;
  padding: 30rpx;
  margin-top: 20rpx;
  
  .label {
    font-size: 28rpx;
    color: #333;
    font-weight: 500;
    margin-bottom: 20rpx;
    display: block;
  }
  
  .textarea {
    width: 100%;
    min-height: 120rpx;
    background: #f7f9fb;
    border-radius: 12rpx;
    padding: 24rpx;
    font-size: 28rpx;
    box-sizing: border-box;
  }
}

.audit-actions {
  display: flex;
  padding: 30rpx;
  background: #fff;
  justify-content: center;
  gap: 60rpx;
  
  .radio-item {
    display: flex;
    align-items: center;
    
    .radio-icon {
      width: 36rpx;
      height: 36rpx;
      border-radius: 50%;
      border: 2rpx solid #ccc;
      margin-right: 12rpx;
      box-sizing: border-box;
      
      &.checked {
        border: 10rpx solid #2563eb;
      }
    }
    
    text {
      font-size: 30rpx;
      color: #333;
    }
  }
}

.footer {
  background: #fff;
  padding: 20rpx 30rpx;
  border-top: 1rpx solid #eee;
  
  .submit-btn {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    background: #2563eb;
    color: #fff;
    border-radius: 44rpx;
    font-size: 32rpx;
    border: none;
    
    &:active {
      opacity: 0.8;
    }
  }
  
  .safe-area {
    padding-bottom: env(safe-area-inset-bottom);
  }
}
</style>