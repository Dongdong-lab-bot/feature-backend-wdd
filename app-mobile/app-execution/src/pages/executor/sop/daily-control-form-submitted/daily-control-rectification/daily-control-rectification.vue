<template>
  <view class="page">
    <!-- Breadcrumbs -->
    <view class="crumbs">
      <text class="crumb blue">武岗县全县项目</text>
      <text class="crumb separator">&gt;</text>
      <text class="crumb blue">城东片区</text>
      <text class="crumb separator">&gt;</text>
      <text class="crumb gray">高中学校</text>
    </view>

    <!-- Header Info -->
    <view class="header-card">
      <view class="header-title">{{ canteenName }}日管控检查表</view>
      <view class="header-date">{{ submitDate }}</view>
    </view>

    <!-- Global Reject Reason -->
    <view class="global-audit-box" v-if="globalRejectReason">
      <view class="audit-title">监管端整体驳回意见：</view>
      <view class="audit-text">{{ globalRejectReason }}</view>
    </view>

    <!-- Empty Tip -->
    <view class="empty-tip" v-if="!rectifyList.length">
      <text>暂无需要整改的检查项数据</text>
    </view>

    <!-- Rectification List -->
    <view class="rectify-list">
      <view class="rectify-item" v-for="(item, index) in rectifyList" :key="index">
        <view class="item-header">
          <text class="item-title">{{ index + 1 }}. {{ item.title }}</text>
          <text class="status-tag">不符合</text>
        </view>
        
        <!-- Original Issue -->
        <view class="issue-content">
          <text class="label">问题描述：</text>
          <text class="value">{{ item.issueDesc || '无' }}</text>
        </view>
        <view class="issue-photos" v-if="item.issuePhotos && item.issuePhotos.length > 0">
          <image 
            class="photo" 
            v-for="(img, i) in item.issuePhotos" 
            :key="i" 
            :src="img" 
            mode="aspectFill"
            @click="previewImage(item.issuePhotos, i)"
          ></image>
        </view>

        <!-- Audit Opinion (if rejected) -->
        <view class="audit-box" v-if="item.rejectReason">
          <view class="audit-title">监管端驳回意见：</view>
          <view class="audit-text">{{ item.rejectReason }}</view>
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
import { fetchDailyTaskDetail, rectifyDailyTask } from '@/common/daily-control'

interface RectifyItem {
  id: number
  title: string
  issueDesc: string
  issuePhotos: string[]
  rectifyDesc: string
  rectifyPhotos: string[]
  resultId: string
  rejectReason?: string
}

const taskId = ref<string>('')
const rectifyList = ref<RectifyItem[]>([])
const isReadonly = ref(false)
const canteenName = ref('武岗一中一食堂')
const submitDate = ref('2026-02-18')
const globalRejectReason = ref('')

const loadTaskDetail = async (id: string) => {
  try {
    const res: any = await fetchDailyTaskDetail(id)
    const taskInfo = res.task_info || res.data?.task_info || res
    const snapshot = res.form_snapshot || res.data?.form_snapshot || taskInfo.form_snapshot
    const auditLogs = Array.isArray(res.audit_logs || res.data?.audit_logs) ? (res.audit_logs || res.data?.audit_logs) : []

    if (taskInfo.canteen_name || taskInfo.canteen_name_snapshot) {
      canteenName.value = taskInfo.canteen_name || taskInfo.canteen_name_snapshot
    }
    if (taskInfo.business_date) {
      submitDate.value = taskInfo.business_date
    }

    // Extract global reject reason
    const globalRejects = auditLogs.filter((log: any) => log.action === 'REJECT' && (!log.item_id || log.item_id === ''))
    if (globalRejects.length > 0) {
      const latestGlobalReject = globalRejects[globalRejects.length - 1]
      globalRejectReason.value = latestGlobalReject.opinion || latestGlobalReject.description || ''
    }

    const rawItems: any[] = []

    if (Array.isArray(snapshot?.major_items)) {
      snapshot.major_items.forEach((major: any) => {
        const minors = Array.isArray(major.minor_items)
          ? major.minor_items
          : Array.isArray(major.items)
          ? major.items
          : []
        minors.forEach((minor: any) => {
          if (minor) rawItems.push(minor)
        })
      })
    } else if (Array.isArray(snapshot)) {
      rawItems.push(...snapshot)
    }

    const filteredItems = rawItems.filter((item: any) => {
      if (!item) return false
      
      // Coerce is_qualified
      let isQ = item.is_qualified
      if (isQ === 1 || isQ === 'true' || isQ === '1') isQ = true
      else if (isQ === 0 || isQ === 'false' || isQ === '0') isQ = false
      
      if (isQ === false) return true
      
      if (item.score_given !== undefined && item.total_score !== undefined) {
        return Number(item.score_given) < Number(item.total_score)
      }
      return false
    })

    const items = filteredItems.length > 0 ? filteredItems : rawItems

    rectifyList.value = items.map((item: any, index: number) => {
      const resultId = item.result_id || ''
      const itemLogs = auditLogs.filter(log => !log.item_id || log.item_id === resultId)
      const rejects = itemLogs.filter(log => log.action === 'REJECT')
      const latestReject = rejects.length > 0 ? rejects[rejects.length - 1] : null

      return {
        id: index + 1,
        title: item.content || item.name || '',
        issueDesc: item.description || item.inspection_description || '',
        issuePhotos: Array.isArray(item.photos)
          ? item.photos
          : Array.isArray(item.inspection_photos)
          ? item.inspection_photos
          : [],
        rectifyDesc: item.rectification_description || '',
        rectifyPhotos: Array.isArray(item.rectification_photos) ? item.rectification_photos : [],
        resultId: resultId,
        rejectReason: latestReject ? (latestReject.opinion || latestReject.description) : ''
      }
    })
  } catch (e) {
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
  // Validate
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

  const feedbackPerItem = rectifyList.value.map(item => ({
    result_id: Number(item.resultId) || 0,
    description: item.rectifyDesc,
    photos: item.rectifyPhotos
  }))

  uni.showLoading({ title: '提交中...' })
  try {
    const userInfo = uni.getStorageSync('userInfo') || {}
    const rectifierId = userInfo?.id ? String(userInfo.id) : '1'
    await rectifyDailyTask(taskId.value, { feedbackPerItem, rectifierId })
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

.crumbs {
  padding: 20rpx 30rpx;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  background-color: #fff;

  .crumb {
    font-size: 26rpx;
    color: #333;
    
    &.blue {
      color: #2561EF;
    }
    
    &.gray {
      color: #999999;
    }
    
    &.separator {
      color: #999999;
      margin: 0 10rpx;
    }
  }
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

.global-audit-box {
  background-color: #fff1f0;
  border: 1rpx solid #ffa39e;
  border-radius: 12rpx;
  padding: 24rpx;
  margin: 20rpx 30rpx;

  .audit-title {
    font-size: 28rpx;
    color: #ff4d4f;
    font-weight: 500;
    margin-bottom: 12rpx;
  }

  .audit-text {
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
  }
}

.empty-tip {
  text-align: center;
  padding: 60rpx 0;
  color: #999;
  font-size: 28rpx;
}

.rectify-list {
  padding: 20rpx 30rpx;
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

  .audit-box {
    background-color: #fff1f0;
    border: 1rpx solid #ffa39e;
    border-radius: 8rpx;
    padding: 20rpx;
    margin-bottom: 30rpx;

    .audit-title {
      font-size: 26rpx;
      color: #ff4d4f;
      font-weight: 500;
      margin-bottom: 12rpx;
    }

    .audit-text {
      font-size: 28rpx;
      color: #333;
      line-height: 1.5;
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
          font-size: 24rpx;
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
        border: 2rpx dashed #ddd;

        .plus {
          font-size: 48rpx;
          color: #999;
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
  background-color: #fff;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);

  .submit-btn {
    background-color: #2561EF;
    color: #fff;
    border-radius: 44rpx;
    height: 88rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32rpx;
    font-weight: 500;
  }
}
</style>
