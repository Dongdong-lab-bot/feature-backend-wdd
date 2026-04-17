<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <!-- Header Info -->
      <view class="header-card">
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
          <view class="label"><text class="star">*</text>检查项目</view>
          <view class="value">{{ formSnapshot.length ? `${formSnapshot.length}/${formSnapshot.length}` : '--' }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
      </view>

      <!-- Checklist (Readonly from execution submission) -->
      <view class="check-list">
        <view class="empty-tip" v-if="!formSnapshot.length">暂无检查项数据</view>
        
        <view class="check-item" v-for="(item, index) in formSnapshot" :key="item.item_id || index">
          <view class="item-title">{{ index + 1 }}、{{ item.content || '--' }}</view>
          
          <view class="radio-group">
            <view class="radio-item">
              <view class="radio-circle" :class="{ checked: item.is_qualified === tru }"></view>
              <text>完成且合格</text>
            </view>
            <view class="radio-item">
              <view class="radio-circle" :class="{ checked: item.is_qualified === false }"></view>
              <text>未完成</text>
            </view>
          </view>

          <!-- Issue Box (Show if there is description or photos) -->
          <view class="issue-box" v-if="item.description || (item.photos && item.photos.length)">
            <view class="issue-text" v-if="item.description">{{ item.description }}</view>
            <view class="image-list" v-if="item.photos && item.photos.length">
              <image 
                v-for="(img, i) in item.photos" 
                :key="i" 
                :src="img" 
                mode="aspectFill" 
                class="img"
              ></image>
            </view>
          </view>
        </view>
      </view>

      <!-- Remove audit-section from scroll-view -->
      <view class="safe-bottom-space"></view>
    </scroll-view>

    <!-- Footer Area (Audit Input + Buttons) -->
    <view class="footer-area">
      <view class="audit-input-wrap">
        <text class="audit-label">审核意见请输入：</text>
        <textarea 
          class="audit-textarea" 
          v-model="auditOpinion" 
          placeholder="若需驳回请填写意见..." 
          placeholder-style="color:#ccc; font-size:28rpx;"
          auto-height
        />
      </view>
      <view class="footer-buttons">
        <button class="btn-reject" @click="handleReject" :disabled="submitting">
          提交意见
        </button>
        <button class="btn-pass" @click="handlePass" :disabled="submitting">
          完成审核
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { inspectionApi } from '@/api'
import type { DailyTaskFormItem, DailyTaskInfo } from '@/api/modules/inspection'

const taskInfo = ref<Partial<DailyTaskInfo>>({})
const formSnapshot = ref<DailyTaskFormItem[]>([])
const auditOpinion = ref('')
const taskId = ref('')
const submitting = ref(false)

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
  
  // 处理后端返回类型不一致的情况，强制转换为前端需要的严格布尔值
  const snapshot = Array.isArray(data.form_snapshot) ? data.form_snapshot : []
  formSnapshot.value = snapshot.map(item => {
    let isQ = item.is_qualified
    if (isQ === 1 || isQ === 'true' || isQ === '1') isQ = true
    else if (isQ === 0 || isQ === 'false' || isQ === '0') isQ = false
    else isQ = undefined // 未设置的情况
    
    return {
      ...item,
      is_qualified: isQ
    }
  })
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
  return 'auditor-default'
}

const submitAudit = async (action: 'PASS' | 'REJECT') => {
  if (!taskId.value) {
    uni.showToast({ title: '缺少任务ID', icon: 'none' })
    return
  }
  
  if (action === 'REJECT' && !auditOpinion.value.trim()) {
    uni.showToast({ title: '审核不通过时，请填写审核意见', icon: 'none' })
    return
  }

  const auditorId = getAuditorId()
  if (submitting.value) return
  submitting.value = true
  
  try {
    await inspectionApi.auditDailyTask(taskId.value, {
      auditor_id: auditorId,
      action: action,
      opinion: auditOpinion.value.trim() || (action === 'PASS' ? '审核通过' : '')
    })
    
    uni.showToast({ 
      title: action === 'PASS' ? '已完成审核' : '已驳回整改', 
      icon: 'success' 
    })
    
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch (error) {
    console.error('Audit failed:', error)
    uni.showToast({ title: '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

const handlePass = () => {
  submitAudit('PASS')
}

const handleReject = () => {
  submitAudit('REJECT')
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background-color: #F7F8FA;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  min-height: 0;
}

.header-card {
  background-color: #fff;
  padding: 0 30rpx;
  border-bottom: 1rpx solid #eee;

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
      color: #666;
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
}

.check-list {
  padding: 20rpx 30rpx;
}

.empty-tip {
  text-align: center;
  padding: 60rpx 0;
  color: #999;
  font-size: 28rpx;
}

.check-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;

  .item-title {
    font-size: 30rpx;
    font-weight: 500;
    color: #333;
    margin-bottom: 24rpx;
    line-height: 1.5;
  }

  .radio-group {
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
        border: 2rpx solid #ccc;
        margin-right: 12rpx;
        box-sizing: border-box;
        
        &.checked {
          border-color: #2563eb;
          position: relative;
          
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

  .issue-box {
    background: #f8faff;
    border-radius: 8rpx;
    padding: 24rpx;
    margin-top: 16rpx;
    
    .issue-text {
      font-size: 28rpx;
      color: #666;
      line-height: 1.5;
      margin-bottom: 16rpx;
      
      &:last-child {
        margin-bottom: 0;
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
  }
}

.footer-area {
  background-color: #fff;
  padding: 30rpx 30rpx calc(20rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #eee;

  .audit-input-wrap {
    display: flex;
    align-items: flex-start;
    margin-bottom: 30rpx;
    
    .audit-label {
      font-size: 28rpx;
      color: #333;
      white-space: nowrap;
      margin-right: 10rpx;
      line-height: 40rpx;
    }
    
    .audit-textarea {
      flex: 1;
      font-size: 28rpx;
      color: #333;
      line-height: 40rpx;
      min-height: 80rpx;
      padding: 0;
    }
  }

  .footer-buttons {
    display: flex;
    gap: 30rpx;

    button {
      flex: 1;
      height: 88rpx;
      border-radius: 16rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32rpx;
      font-weight: 500;
      
      &::after {
        border: none;
      }
      
      &[disabled] {
        opacity: 0.6;
      }
    }

    .btn-reject {
      background-color: #fff;
      color: #2561EF;
      border: 2rpx solid #2561EF;
    }

    .btn-pass {
      background-color: #2561EF;
      color: #fff;
    }
  }
}
</style>