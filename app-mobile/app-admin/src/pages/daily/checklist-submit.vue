<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <!-- Header Info -->
      <view class="info-card">
        <view class="info-row">
          <view class="label"><text class="star">*</text>检查项目</view>
          <view class="value">{{ canteenName }}</view>
        </view>
        <view class="info-row">
          <view class="label"><text class="star">*</text>开始时间</view>
          <view class="value">{{ submitDate }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
        <view class="info-row">
          <view class="label"><text class="star">*</text>检查人</view>
          <view class="value">{{ inspectorName }}</view>
          <uni-icons type="right" size="16" color="#999" class="arrow"></uni-icons>
        </view>
      </view>

      <!-- Checklist -->
      <view class="check-list">
        <view class="empty-tip" v-if="!checkItems.length && !loading">
          <text>暂无待填报的日管控检查项</text>
        </view>
        
        <view class="check-item" v-for="(item, index) in checkItems" :key="item.id">
          <view class="item-title">{{ index + 1 }}、{{ item.title }}</view>
          
          <view class="radio-group">
            <view class="radio-item" @click="item.status = 'qualified'">
              <view class="radio-icon" :class="{ checked: item.status === 'qualified' }"></view>
              <text>完成且合格</text>
            </view>
            <view class="radio-item" @click="item.status = 'unqualified'">
              <view class="radio-icon" :class="{ checked: item.status === 'unqualified' }"></view>
              <text>未完成</text>
            </view>
          </view>

          <!-- Input Area (Always visible) -->
          <view class="input-area" :class="{ 'has-content': !!item.issueDesc }">
            <textarea 
              class="textarea" 
              placeholder="请输入" 
              placeholder-style="color:#ccc" 
              v-model="item.issueDesc"
            ></textarea>
            
            <view class="photos-preview" v-if="item.issuePhotos && item.issuePhotos.length > 0">
              <view class="upload-item" v-for="(photo, pIdx) in item.issuePhotos" :key="pIdx">
                <image :src="photo" mode="aspectFill" class="preview-img" />
                <view class="delete-btn" @click="deletePhoto(index, pIdx)">×</view>
              </view>
            </view>

            <view class="upload-btn" @click="chooseImage(index)">
              <text class="plus-icon">+</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- Bottom Button -->
    <view class="footer">
      <button class="submit-btn" @click="submitChecklist" :disabled="submitting || checkItems.length === 0">
        {{ submitting ? '提交中...' : '完成日管控' }}
      </button>
      <view class="safe-area"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { inspectionApi } from '@/api'

interface CheckItem {
  id: string
  title: string
  status: 'qualified' | 'unqualified' | ''
  issueDesc: string
  issuePhotos: string[]
}

const canteenName = ref('加载中...')
const inspectorName = ref('加载中...')
const submitDate = ref('')
const taskId = ref<string>('')
const checkItems = ref<CheckItem[]>([])
const loading = ref(false)
const submitting = ref(false)

const formatTime = (date: Date) => {
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mi = String(date.getMinutes()).padStart(2, '0')
  return `${mm}月${dd}日 ${hh}:${mi}`
}

onLoad(async (options: any) => {
  submitDate.value = formatTime(new Date())
  const userInfo = uni.getStorageSync('userInfo') || {}
  inspectorName.value = userInfo?.realName || userInfo?.username || '食品安全员'

  if (options.id) {
    taskId.value = decodeURIComponent(options.id)
    await loadDetail(taskId.value)
  } else {
    uni.showToast({ title: '缺少任务ID', icon: 'none' })
  }
})

const loadDetail = async (id: string) => {
  loading.value = true
  try {
    const detailRes = await inspectionApi.getDailyTaskDetail(id)
    
    if (detailRes.task_info) {
      canteenName.value = detailRes.task_info.canteen_name || '--'
    }

    const snapshot = detailRes.form_snapshot || []

    checkItems.value = snapshot.map((item: any) => ({
      id: String(item.item_id),
      title: item.content || '未知检查项',
      status: item.is_qualified === true ? 'qualified' : (item.is_qualified === false ? 'unqualified' : ''),
      issueDesc: item.description || '',
      issuePhotos: Array.isArray(item.photos) ? item.photos : []
    }))

  } catch (error) {
    console.error('获取日管控任务失败:', error)
    uni.showToast({ title: '获取任务失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const chooseImage = (index: number) => {
  uni.chooseImage({
    count: 3,
    success: (res) => {
      const tempFilePaths = res.tempFilePaths as string[]
      checkItems.value[index].issuePhotos.push(...tempFilePaths)
    }
  })
}

const deletePhoto = (itemIndex: number, photoIndex: number) => {
  checkItems.value[itemIndex].issuePhotos.splice(photoIndex, 1)
}

const submitChecklist = async () => {
  if (!taskId.value) {
    uni.showToast({ title: '缺少任务ID', icon: 'none' })
    return
  }

  const unselected = checkItems.value.find(item => !item.status)
  if (unselected) {
    uni.showToast({
      title: `请选择第${checkItems.value.indexOf(unselected) + 1}项的检查结果`,
      icon: 'none'
    })
    return
  }

  const results = checkItems.value.map(item => ({
    item_id: item.id,
    is_qualified: item.status === 'qualified',
    description: item.issueDesc || undefined,
    photos: item.issuePhotos || []
  }))

  const userInfo = uni.getStorageSync('userInfo') || {}
  const submitterId = userInfo?.id ? String(userInfo.id) : 'user-canteen-1'

  submitting.value = true
  try {
    await inspectionApi.submitDailyTask(taskId.value, {
      submitter_id: submitterId,
      actual_start_time: new Date().toISOString(),
      results
    })

    uni.showToast({
      title: '已提交',
      icon: 'success'
    })

    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch (error) {
    console.error('提交失败:', error)
    uni.showToast({ title: '提交失败', icon: 'none' })
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

.check-list {
  background: #fff;
  padding: 30rpx;
}

.empty-tip {
  text-align: center;
  padding: 60rpx 0;
  color: #999;
  font-size: 28rpx;
}

.check-item {
  margin-bottom: 40rpx;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.item-title {
  font-size: 30rpx;
  color: #333;
  margin-bottom: 30rpx;
  line-height: 1.5;
}

.radio-group {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
  padding-left: 20rpx;
  
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
      color: #666;
    }
  }
}

.input-area {
  position: relative;
  background: #f8faff;
  border-radius: 12rpx;
  padding: 24rpx;
  min-height: 200rpx;
  
  &.has-content {
    .textarea {
      color: #333;
    }
  }
  
  .textarea {
    width: 100%;
    min-height: 100rpx;
    font-size: 28rpx;
    line-height: 1.5;
    color: #333;
  }
  
  .photos-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
    margin-top: 16rpx;
  }
  
  .upload-item {
    position: relative;
    width: 140rpx;
    height: 140rpx;

    .preview-img {
      width: 100%;
      height: 100%;
      border-radius: 8rpx;
    }

    .delete-btn {
      position: absolute;
      top: -10rpx;
      right: -10rpx;
      width: 36rpx;
      height: 36rpx;
      background-color: rgba(0, 0, 0, 0.5);
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24rpx;
    }
  }
  
  .upload-btn {
    position: absolute;
    right: 24rpx;
    bottom: 24rpx;
    width: 60rpx;
    height: 60rpx;
    background: #fff;
    border: 2rpx dashed #2563eb;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .plus-icon {
      font-size: 40rpx;
      color: #2563eb;
      font-weight: 300;
      margin-bottom: 6rpx; /* 微调垂直居中 */
    }
  }
}

.footer {
  background: #fff;
  padding: 20rpx 30rpx;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.05);
  
  .submit-btn {
    background: #2563eb;
    color: #fff;
    border-radius: 12rpx;
    font-size: 32rpx;
    height: 88rpx;
    line-height: 88rpx;
    
    &::after {
      border: none;
    }
    
    &:active {
      opacity: 0.9;
    }
    
    &[disabled] {
      background: #a0c0f9;
    }
  }
  
  .safe-area {
    height: env(safe-area-inset-bottom);
  }
}
</style>
