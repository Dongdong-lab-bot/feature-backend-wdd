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

    <!-- Reject Reason (if previously rejected) -->
    <view class="reject-banner" v-if="latestRejectLog">
      <view class="reject-header">
        <uni-icons type="info-filled" color="#ff4d4f" size="18"></uni-icons>
        <text class="reject-title">上一次审核驳回原因</text>
        <text class="reject-time">{{ formatTime(latestRejectLog.created_at) }}</text>
      </view>
      <view class="reject-content">{{ latestRejectLog.opinion || '未提供原因' }}</view>
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
            <view class="radio-item" v-for="option in item.scoring_options || []" :key="option" :class="{ active: Number(option) === Number(item.score_given) }">
              <view class="radio-circle" :class="{ checked: Number(option) === Number(item.score_given) }"></view>
              <text>{{ option }}分</text>
            </view>
          </view>

          <!-- Original Issue -->
          <view class="issue-box" v-if="Number(item.score_given) < Number(item.total_score)">
            <view class="issue-title">原扣分情况：</view>
            <view class="issue-text" v-if="item.inspection_description">{{ item.inspection_description }}</view>
            <view class="image-list" v-if="item.inspection_photos && item.inspection_photos.length">
              <image class="img" v-for="(photo, photoIndex) in item.inspection_photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
          </view>

          <!-- Rectification Feedback -->
          <view class="feedback-box" v-if="Number(item.score_given) < Number(item.total_score)">
            <view class="feedback-title">本次整改提交：</view>
            <view class="feedback-text">{{ item.rectification_description || '暂无整改说明' }}</view>
            <view class="image-list" v-if="item.rectification_photos && item.rectification_photos.length">
              <image class="img" v-for="(photo, photoIndex) in item.rectification_photos" :key="photoIndex" :src="photo" mode="aspectFill"></image>
            </view>
            
            <!-- Per-item Audit Actions inside Feedback Box -->
            <view class="audit-action-group">
              <view class="radio-item" :class="{ active: itemAuditStatus[item.item_id] === 'PASS' }" @click="setItemAudit(item.item_id, 'PASS')">
                <view class="radio-circle" :class="{ checked: itemAuditStatus[item.item_id] === 'PASS' }"></view>
                <text>通过</text>
              </view>
              <view class="radio-item" :class="{ active: itemAuditStatus[item.item_id] === 'REJECT' }" @click="setItemAudit(item.item_id, 'REJECT')">
                <view class="radio-circle" :class="{ checked: itemAuditStatus[item.item_id] === 'REJECT' }"></view>
                <text>驳回</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- Audit Input Area -->
    <view class="opinion-wrap">
      <text class="opinion-label">审核意见：</text>
      <textarea class="opinion-input" v-model="auditOpinion" placeholder="请输入审核意见" auto-height />
    </view>

    <!-- Footer -->
    <view class="footer">
      <view class="left-actions">
        <button class="action-btn pass" @click="handlePassAll">全部通过</button>
        <button class="action-btn reject" @click="handleRejectAll">全部驳回</button>
      </view>
      <button class="submit-btn" :disabled="submitting" @click="handleComplete">{{ submitting ? '提交中...' : '完成审核' }}</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getVideoTaskDetail, auditVideoTask } from '@/api/modules/video'
import type { VideoTaskDetailData, VideoTaskMinorItem } from '@/api/modules/video'

const taskId = ref('')
const submitting = ref(false)
const taskInfo = ref<Partial<VideoTaskDetailData['task_info']>>({})
const allMinorItems = ref<Array<VideoTaskMinorItem & { majorTitle: string }>>([])
const latestRejectLog = ref<any>(null)
const auditOpinion = ref('')

type AuditAction = 'PASS' | 'REJECT'
const itemAuditStatus = ref<Record<string, AuditAction>>({})

const setItemAudit = (itemId: string, action: AuditAction) => {
  itemAuditStatus.value[itemId] = action
}

const handlePassAll = () => {
  allMinorItems.value.forEach(item => {
    if (Number(item.score_given) < Number(item.total_score)) {
      itemAuditStatus.value[item.item_id] = 'PASS'
    }
  })
}

const handleRejectAll = () => {
  allMinorItems.value.forEach(item => {
    if (Number(item.score_given) < Number(item.total_score)) {
      itemAuditStatus.value[item.item_id] = 'REJECT'
    }
  })
}

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
    const data = await getVideoTaskDetail(id)
    taskInfo.value = data.task_info || {}

    const majorItems = data.form_snapshot?.major_items || []
    const merged: Array<VideoTaskMinorItem & { majorTitle: string }> = []
    majorItems.forEach((major: any) => {
      ;(major.minor_items || []).forEach((minor: any) => {
        // Handle missing score_given by defaulting to total_score
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
    
    const logs = Array.isArray(data.audit_logs) ? data.audit_logs : []
    const rejects = logs.filter(log => log.action === 'REJECT')
    if (rejects.length > 0) {
      latestRejectLog.value = rejects[rejects.length - 1]
    }
  } catch (error) {
    console.error('Failed to load video task detail', error)
  }
}

const getAuditorId = () => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  const userId = userInfo?.id
  if (userId !== undefined && userId !== null && `${userId}`.trim()) return `${userId}`
  return ''
}

const handleComplete = async () => {
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
  
  // 校验所有存在问题（失分）的项是否都已选择了通过或驳回
  const missingAudit = allMinorItems.value.find(item => 
    Number(item.score_given) < Number(item.total_score) && !itemAuditStatus.value[item.item_id]
  )
  if (missingAudit) {
    uni.showToast({ title: '请对所有扣分项进行审核(通过/驳回)', icon: 'none' })
    return
  }

  // 只要有一个驳回，整体状态就是驳回
  const isAnyRejected = allMinorItems.value.some(item => itemAuditStatus.value[item.item_id] === 'REJECT')
  const finalAction = isAnyRejected ? 'REJECT' : 'PASS'

  submitting.value = true
  try {
    await auditVideoTask(taskId.value, {
      auditor_id: auditorId,
      action: finalAction,
      opinion: auditOpinion.value.trim() || (finalAction === 'PASS' ? '整改通过' : '整改驳回')
    })
    uni.showToast({ title: '审核完成', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({
        url: '/pages/video/audit-success'
      })
    }, 500)
  } catch (error) {
    uni.showToast({ title: '审核失败', icon: 'none' })
  } finally {
    submitting.value = false
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

.reject-banner {
  background: #fff1f0;
  border: 1rpx solid #ffa39e;
  border-radius: 8rpx;
  margin: 20rpx 30rpx 0;
  padding: 20rpx;
  
  .reject-header {
    display: flex;
    align-items: center;
    margin-bottom: 12rpx;
    
    .reject-title {
      font-size: 28rpx;
      color: #ff4d4f;
      font-weight: 500;
      margin-left: 8rpx;
      flex: 1;
    }
    
    .reject-time {
      font-size: 24rpx;
      color: #999;
    }
  }
  
  .reject-content {
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
    padding-left: 44rpx;
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
  margin-bottom: 20rpx;
  
  .red-bar {
    width: 6rpx;
    background: #ff4d4f;
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
      box-sizing: border-box;
      position: relative;
      
      &.checked {
        border-color: #2563eb;
        
        &::after {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 16rpx;
          height: 16rpx;
          background: #2563eb;
          border-radius: 50%;
        }
      }
    }
    
    text {
      font-size: 28rpx;
      color: #333;
    }
    
    &.active text {
      color: #333;
    }
  }
}

.issue-box {
  background: #f7f9fb;
  border-radius: 8rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  
  .issue-title {
    font-size: 28rpx;
    color: #ff4d4f;
    margin-bottom: 10rpx;
    font-weight: 500;
  }
  
  .issue-text {
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
    margin-bottom: 20rpx;
  }
}

.feedback-box {
  background: #f0f7ff;
  border-radius: 8rpx;
  padding: 20rpx;
  
  .feedback-title {
    font-size: 28rpx;
    color: #2563eb;
    margin-bottom: 10rpx;
    font-weight: 500;
  }
  
  .feedback-text {
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
    margin-bottom: 20rpx;
  }
}

.audit-action-group {
  display: flex;
  justify-content: flex-end;
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx dashed #d6e4ff;
  
  .radio-item {
    display: flex;
    align-items: center;
    margin-left: 40rpx;
    
    .radio-circle {
      width: 32rpx;
      height: 32rpx;
      border-radius: 50%;
      border: 2rpx solid #ccc;
      margin-right: 12rpx;
      box-sizing: border-box;
      position: relative;
      
      &.checked {
        border-color: #2563eb;
        
        &::after {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 16rpx;
          height: 16rpx;
          background: #2563eb;
          border-radius: 50%;
        }
      }
    }
    
    text {
      font-size: 28rpx;
      color: #333;
    }
  }
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 20rpx;
  
  .img {
    width: 140rpx;
    height: 140rpx;
    border-radius: 8rpx;
    background: #eee;
  }
}

.opinion-wrap {
  background: #fff;
  margin-top: 20rpx;
  padding: 24rpx 30rpx;
}

.opinion-label {
  font-size: 28rpx;
  color: #333;
}

.opinion-input {
  margin-top: 12rpx;
  width: 100%;
  min-height: 120rpx;
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
}

.footer {
  padding: 20rpx 30rpx;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 20rpx;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.05);
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  
  .left-actions {
    display: flex;
    flex-direction: column;
    gap: 16rpx;
    
    .action-btn {
      width: 160rpx;
      height: 60rpx;
      line-height: 60rpx;
      font-size: 24rpx;
      color: #2563eb;
      background: #eef4ff;
      border: none;
      border-radius: 8rpx;
      margin: 0;
      
      &::after {
        border: none;
      }
    }
  }
  
  .submit-btn {
    flex: 1;
    height: 88rpx;
    line-height: 88rpx;
    background: #2563eb;
    color: #fff;
    font-size: 32rpx;
    border-radius: 12rpx;
    margin: 0;
    
    &::after {
      border: none;
    }
  }

  .submit-btn[disabled] {
    opacity: 0.7;
  }
}
</style>