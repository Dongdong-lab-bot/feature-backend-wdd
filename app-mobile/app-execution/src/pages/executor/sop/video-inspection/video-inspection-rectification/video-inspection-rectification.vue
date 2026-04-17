<template>
  <view class="page">
    <!-- Header Info -->
    <view class="header-card">
      <view class="header-title">{{ canteenName }}视频巡检表</view>
      <view class="header-date">{{ submitDate }}</view>
    </view>

    <!-- Rectification List -->
    <view class="rectify-list">
      <view class="rectify-item" v-for="(item, index) in rectifyList" :key="index">
        <view class="item-header">
          <text class="item-title">{{ index + 1 }}. {{ item.title }}</text>
          <text class="status-tag">不符合</text>
        </view>
        
        <view class="issue-content">
          <text class="label">问题描述：</text>
          <text class="value">{{ item.issueDesc }}</text>
        </view>
        
        <view class="issue-photos">
          <image 
            class="photo" 
            v-for="(img, i) in item.issuePhotos" 
            :key="i" 
            :src="img" 
            mode="aspectFill"
            @click="previewImage(item.issuePhotos, i)"
          ></image>
        </view>

        <!-- Rectification Form -->
        <view class="rectify-form">
          <view class="form-label">整改说明</view>
          <textarea 
            v-if="!isReadonly"
            class="rectify-input" 
            v-model="item.rectifyDesc" 
            placeholder="请输入整改说明" 
            placeholder-class="placeholder"
          />
          <view class="readonly-text" v-else>{{ item.rectifyDesc || '无' }}</view>
          
          <view class="form-label">整改照片</view>
          <view class="upload-box" v-if="!isReadonly || item.rectifyPhotos.length > 0">
            <view 
              class="upload-item" 
              v-for="(img, i) in item.rectifyPhotos" 
              :key="i"
            >
              <image :src="img" mode="aspectFill" class="upload-img" @click="previewImage(item.rectifyPhotos, i)"></image>
              <view class="delete-btn" @click="deletePhoto(index, i)" v-if="!isReadonly">×</view>
            </view>
            <view class="upload-btn" @click="chooseImage(index)" v-if="!isReadonly">
              <text class="plus">+</text>
              <text class="upload-text">上传照片</text>
            </view>
          </view>
        </view>
      </view>
      <view v-if="rectifyList.length === 0" class="empty-tip">
        <text>该任务暂无检查项明细</text>
      </view>
    </view>

    <!-- Bottom Button -->
    <view class="footer" v-if="!isReadonly">
      <button class="submit-btn" @click="handleSubmit">完成整改反馈</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchVideoTaskDetail, rectifyVideoTask, type VideoRectifyItem } from '@/common/video-inspection'

interface RectifyItem {
  id: number
  title: string
  issueDesc: string
  issuePhotos: string[]
  rectifyDesc: string
  rectifyPhotos: string[]
  resultId: string | number
}

const taskId = ref<string>('')
const rectifyList = ref<RectifyItem[]>([])
const canteenName = ref('武岗一中一食堂')
const submitDate = ref('2026-02-18')
const isReadonly = ref(false)

const loadTaskDetail = async (id: string) => {
  try {
    const res: any = await fetchVideoTaskDetail(id)
    const taskInfo = res.task_info || res.data?.task_info || res
    const snapshot = res.form_snapshot || res.data?.form_snapshot || taskInfo.form_snapshot

    if (taskInfo.canteen_name || taskInfo.canteen_name_snapshot) {
      canteenName.value = taskInfo.canteen_name || taskInfo.canteen_name_snapshot
    }
    if (taskInfo.business_date) {
      submitDate.value = taskInfo.business_date
    }

    const majorItems = Array.isArray(snapshot?.major_items) ? snapshot.major_items : (Array.isArray(snapshot) ? snapshot : [])
    const minorItems: any[] = []
    
    majorItems.forEach((major: any) => {
      const items = Array.isArray(major.minor_items) ? major.minor_items : (Array.isArray(major.items) ? major.items : [])
      items.forEach((minor: any) => {
        // 提取不合格项
        const isUnqualified = minor.is_qualified === false || 
                              (minor.score_given !== undefined && minor.total_score !== undefined && Number(minor.score_given) < Number(minor.total_score))
        
        if (minor && isUnqualified) {
          minorItems.push(minor)
        }
      })
    })

    rectifyList.value = minorItems.map((item: any, index: number) => ({
      id: index + 1,
      title: item.content || item.name || '',
      issueDesc: item.inspection_description || item.description || item.remark || '',
      issuePhotos: Array.isArray(item.inspection_photos) ? item.inspection_photos : (Array.isArray(item.photos) ? item.photos : []),
      rectifyDesc: item.rectification_description || item.rectify_desc || '',
      rectifyPhotos: Array.isArray(item.rectification_photos) ? item.rectification_photos : [],
      resultId: item.result_id || item.item_id || ''
    }))
  } catch (e) {
    console.error('Failed to load video task detail:', e)
    uni.showToast({ title: '加载详情失败', icon: 'none' })
  }
}

onLoad((options) => {
  if (options?.id) {
    taskId.value = String(options.id)
    loadTaskDetail(taskId.value)
  }
  if (options?.readonly === 'true') {
    isReadonly.value = true
  }
})

const previewImage = (urls: string[], current: number) => {
  uni.previewImage({
    urls,
    current
  })
}

const chooseImage = (index: number) => {
  uni.chooseImage({
    count: 3,
    success: (res) => {
      rectifyList.value[index].rectifyPhotos.push(...res.tempFilePaths)
    }
  })
}

const deletePhoto = (itemIndex: number, photoIndex: number) => {
  rectifyList.value[itemIndex].rectifyPhotos.splice(photoIndex, 1)
}

const handleSubmit = async () => {
  const incomplete = rectifyList.value.some(item => !item.rectifyDesc || item.rectifyPhotos.length === 0)
  if (incomplete) {
    uni.showToast({
      title: '请完善所有整改项',
      icon: 'none'
    })
    return
  }

  if (!taskId.value) {
    uni.showToast({ title: '缺少任务ID，无法提交', icon: 'none' })
    return
  }

  const feedbackPerItem: VideoRectifyItem[] = rectifyList.value
    .filter(item => item.resultId && item.rectifyDesc.trim())
    .map(item => ({
      result_id: String(item.resultId),
      description: item.rectifyDesc,
      photos: item.rectifyPhotos
    }))

  uni.showLoading({ title: '提交中...' })
  try {
    const rectifierId = uni.getStorageSync('userId') || undefined
    await rectifyVideoTask(taskId.value, { feedbackPerItem, rectifierId })
    uni.hideLoading()
    uni.showToast({
      title: '整改反馈成功',
      icon: 'success'
    })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (e) {
    uni.hideLoading()
    uni.showToast({ title: '提交失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #F7F8FA;
  padding-bottom: 120rpx;
}

.header-card {
  background-color: #fff;
  padding: 30rpx;
  margin-top: 2rpx;
  border-bottom: 1rpx solid #eee;

  .header-title {
    font-size: 34rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 10rpx;
  }

  .header-date {
    font-size: 26rpx;
    color: #999;
  }
}

.rectify-list {
  padding: 20rpx 30rpx;
}

.empty-tip {
  text-align: center;
  color: #999;
  margin-top: 40rpx;
  font-size: 28rpx;
}

.rectify-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;

  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20rpx;

    .item-title {
      font-size: 30rpx;
      font-weight: 500;
      color: #333;
      flex: 1;
      margin-right: 20rpx;
    }

    .status-tag {
      font-size: 24rpx;
      color: #FF6B6B;
      background-color: rgba(255, 107, 107, 0.1);
      padding: 4rpx 12rpx;
      border-radius: 8rpx;
    }
  }

  .issue-content {
    margin-bottom: 20rpx;
    
    .label {
      font-size: 28rpx;
      color: #666;
    }
    
    .value {
      font-size: 28rpx;
      color: #333;
    }
  }

  .issue-photos {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
    margin-bottom: 30rpx;

    .photo {
      width: 160rpx;
      height: 160rpx;
      border-radius: 8rpx;
      background-color: #f5f5f5;
    }
  }

  .rectify-form {
    border-top: 1rpx solid #eee;
    padding-top: 30rpx;

    .form-label {
      font-size: 28rpx;
      font-weight: 500;
      color: #333;
      margin-bottom: 16rpx;
      
      &::before {
        content: '*';
        color: #FF6B6B;
        margin-right: 4rpx;
      }
    }

    .rectify-input {
      width: 100%;
      height: 160rpx;
      background-color: #F7F8FA;
      border-radius: 8rpx;
      padding: 20rpx;
      font-size: 28rpx;
      color: #333;
      margin-bottom: 24rpx;
      box-sizing: border-box;
    }

    .readonly-text {
      width: 100%;
      background-color: #F7F8FA;
      border-radius: 8rpx;
      padding: 20rpx;
      font-size: 28rpx;
      color: #333;
      box-sizing: border-box;
      margin-bottom: 24rpx;
      min-height: 80rpx;
    }

    .upload-box {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;

      .upload-item {
        position: relative;
        width: 160rpx;
        height: 160rpx;

        .upload-img {
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
        }
      }

      .upload-btn {
        width: 160rpx;
        height: 160rpx;
        background-color: #F7F8FA;
        border-radius: 8rpx;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;

        .plus {
          font-size: 48rpx;
          color: #ccc;
          margin-bottom: 8rpx;
        }

        .upload-text {
          font-size: 24rpx;
          color: #999;
        }
      }
    }
  }
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background-color: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);

  .submit-btn {
    background-color: #2561EF;
    color: #fff;
    border-radius: 44rpx;
    font-size: 32rpx;
    height: 88rpx;
    line-height: 88rpx;
    text-align: center;
  }
}
</style>