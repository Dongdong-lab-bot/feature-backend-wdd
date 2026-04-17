<template>
  <view class="page">
    <!-- Video Player Section -->
    <view class="video-container">
      <view v-if="!playParams" class="video-placeholder">
        <text>正在获取视频流...</text>
      </view>
      <view v-else class="video-mock">
        <text style="color: #409eff">🎥 海康监控画面 (Mock)</text>
        <text class="mock-info">设备序列号: {{ playParams.deviceSerial }}</text>
        
        <button 
          class="capture-btn" 
          @click="mockCapture" 
          :loading="capturing"
        >
          📸 抓拍取证
        </button>
      </view>
    </view>

    <!-- Main Content with Sidebar -->
    <view class="main-container">
      <!-- Sidebar -->
      <scroll-view class="sidebar" scroll-y>
        <view 
          v-for="(category, index) in categories" 
          :key="index"
          class="sidebar-item"
          :class="{ active: activeCategory === category.title }"
          @click="activeCategory = category.title"
        >
          {{ category.title }}
        </view>
      </scroll-view>

      <!-- Right Content -->
      <scroll-view class="content-area" scroll-y>
        <view class="checklist">
          <!-- Iterate over items in the active category -->
          <view 
            v-for="(item, itemIdx) in activeItems" 
            :key="item.item_id"
            class="check-item"
          >
            <view class="item-title">
              <view :class="getIssueTypeClass(item.issue_type)"></view>
              <text>{{ itemIdx + 1 }}、{{ item.content }}（满分{{ item.total_score }}分）</text>
            </view>
            
            <view class="score-group">
              <view 
                v-for="score in item.scoring_options" 
                :key="score"
                class="radio-item" 
                :class="{ active: item.score_given === score }"
                @click="item.score_given = score"
              >
                <view class="radio-circle" :class="{ checked: item.score_given === score }"></view>
                <text>{{ score }}分</text>
              </view>
            </view>

            <view class="input-area">
              <textarea 
                class="textarea" 
                v-model="item.inspection_description" 
                placeholder="请输入存在的问题（选填）" 
                placeholder-style="color:#ccc" 
                auto-height
              ></textarea>
              
              <!-- 展示抓拍的图片 -->
              <view class="photos-preview" v-if="item.inspection_photos && item.inspection_photos.length > 0">
                <image 
                  v-for="(pic, pIdx) in item.inspection_photos" 
                  :key="pIdx" 
                  :src="pic" 
                  class="preview-img"
                  mode="aspectFill"
                ></image>
              </view>

              <!-- 绑定抓拍按钮（如果想精确到把图片放在当前题下面） -->
              <view class="upload-btn" @click="bindCaptureToItem(item)">
                <uni-icons type="camera-filled" size="24" color="#2563eb"></uni-icons>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- Footer -->
    <view class="footer">
      <button class="submit-btn" @click="submitChecklist">完成视频巡检</button>
      <view class="safe-area"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getVideoPlayParams, captureVideoFrame, getVideoTaskDetail, submitVideoTask } from '@/api/modules/video'
import type { PlayParamsData, VideoTaskDetailData, VideoTaskMinorItem } from '@/api/modules/video'

// 假设从上个页面传过来的任务ID和摄像头 ID
const taskId = ref('') 
const cameraId = ref('camera_001')
const canteenId = ref('')

// 从页面路由参数中获取 taskId 或食堂信息
import { onLoad } from '@dcloudio/uni-app'
onLoad((options) => {
  if (options && options.id) {
    taskId.value = options.id
  }
  if (options && options.canteenId) {
    canteenId.value = options.canteenId
    // TODO: 如果是从“开始新巡检”进来的（没有 taskId 只有 canteenId）
    // 我们应该在这里调用一个 POST 接口去初始化一个任务，拿到 taskId 再继续。
    // 为了不阻塞当前测试，如果没有 taskId，我们 fallback 到刚才写死的测试数据 '1'
    if (!taskId.value) {
      taskId.value = '1'
    }
  }
  // 兜底：如果直接进入页面啥都没传，用 1
  if (!taskId.value) {
    taskId.value = '1'
  }
})

const playParams = ref<PlayParamsData | null>(null)
const capturing = ref(false)

// 任务和表单数据
const taskDetail = ref<VideoTaskDetailData | null>(null)
const categories = ref<any[]>([])
const activeCategory = ref('')

// 页面加载时获取任务详情并自动获取播放凭证
onMounted(async () => {
  // 获取任务详情
  try {
    const detailRes = await getVideoTaskDetail(taskId.value)
    taskDetail.value = detailRes
    categories.value = detailRes.form_snapshot?.major_items || []
    if (categories.value.length > 0) {
      activeCategory.value = categories.value[0].title
    }
  } catch (error) {
    console.error('获取视频任务详情失败', error)
  }

  // 获取视频凭证
  try {
    const res = await getVideoPlayParams({
      cameraId: cameraId.value,
      action: 'preview'
    })
    playParams.value = res as any
  } catch (error: any) {
    if (error.code === 40300) {
      playParams.value = {
        deviceSerial: 'MOCK_D20591677',
        channelNo: '1',
        oauthToken: 'mock_oauth_token_xxx',
        validCode: '123456'
      }
    }
  }
})

// 计算当前激活分类下的小项
const activeItems = computed(() => {
  const cat = categories.value.find(c => c.title === activeCategory.value)
  return cat ? cat.minor_items || [] : []
})

// 根据 issue_type 渲染不同颜色的竖条
const getIssueTypeClass = (issueType?: string) => {
  if (issueType === 'RED_LINE') return 'red-bar'
  if (issueType === 'YELLOW_LINE') return 'yellow-bar'
  return 'blue-bar' // 默认蓝条
}

// 记录当前准备抓拍的题目
const currentCaptureItem = ref<VideoTaskMinorItem | null>(null)

// 绑定抓拍按钮到某道题
const bindCaptureToItem = (item: VideoTaskMinorItem) => {
  currentCaptureItem.value = item
  mockCapture() // 触发抓拍
}

// 全局抓拍按钮（如果没有指定题目，就塞到当前分类的第一题，或者只存不绑）
const mockCapture = async () => {
  if (!playParams.value) return
  
  capturing.value = true
  try {
    const mockBase64 = 'data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
    const res = await captureVideoFrame(cameraId.value, {
      image_base64: mockBase64,
      timestamp: new Date().toISOString()
    })
    
    const photoUrl = (res as any).photo_url
    attachPhotoToItem(photoUrl)
    uni.showToast({ title: '抓拍成功', icon: 'success' })
    
  } catch (error: any) {
    if (error.code === 40300) {
      const mockUrl = 'https://dummyimage.com/600x400/000/fff&text=Mock+Capture+Image'
      attachPhotoToItem(mockUrl)
      uni.showToast({ title: '抓拍成功(Mock)', icon: 'success' })
    } else {
      uni.showToast({ title: '抓拍失败', icon: 'none' })
    }
  } finally {
    capturing.value = false
    currentCaptureItem.value = null // 抓拍完重置
  }
}

// 将抓拍到的照片挂载到具体的题目上
const attachPhotoToItem = (photoUrl: string) => {
  let targetItem = currentCaptureItem.value
  // 如果没有从题目的相机按钮点进来，默认给当前分类第一题
  if (!targetItem && activeItems.value.length > 0) {
    targetItem = activeItems.value[0]
  }
  
  if (targetItem) {
    if (!targetItem.inspection_photos) {
      targetItem.inspection_photos = []
    }
    targetItem.inspection_photos.push(photoUrl)
  }
}

const submitChecklist = async () => {
  // 收集所有题目数据
  const results: any[] = []
  categories.value.forEach(cat => {
    (cat.minor_items || []).forEach((item: VideoTaskMinorItem) => {
      // 只有填了分或者拍了照才算作结果提交
      if (item.score_given !== undefined || (item.inspection_photos && item.inspection_photos.length > 0)) {
        results.push({
          item_id: item.item_id,
          score_given: item.score_given || 0,
          description: item.inspection_description || '',
          photos: item.inspection_photos || []
        })
      }
    })
  })

  try {
    const userInfo = uni.getStorageSync('userInfo') || {}
    await submitVideoTask(taskId.value, {
      inspector_id: userInfo?.id ? `${userInfo.id}` : 'user-regulator-1',
      actual_start_time: new Date().toISOString(),
      results
    })
    
    uni.showToast({ title: '已提交', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/video/submit-success' })
    }, 1000)
  } catch (error) {
    uni.showToast({ title: '提交失败', icon: 'none' })
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

.video-container {
  width: 100%;
  height: 420rpx;
  background: #000;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-placeholder text {
  color: #909399;
  font-size: 28rpx;
}

.video-mock {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.mock-info {
  color: #fff;
  font-size: 24rpx;
  margin: 20rpx 0;
  font-family: monospace;
}

.capture-btn {
  background-color: #67c23a;
  color: #fff;
  font-size: 28rpx;
  border-radius: 40rpx;
  padding: 0 40rpx;
  height: 64rpx;
  line-height: 64rpx;
}

.video-cover {
  width: 100%;
  height: 100%;
  opacity: 0.8;
}

.video-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 20rpx;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
  z-index: 2;
}

.video-label {
  color: #fff;
  font-size: 28rpx;
  margin-bottom: 20rpx;
  display: block;
}

.video-controls {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.play-btn {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-icon {
  transform: rotate(0deg); /* Adjust if needed */
}

.progress-bar {
  flex: 1;
  height: 4rpx;
  background: rgba(255,255,255,0.3);
  border-radius: 2rpx;
  position: relative;
}

.progress-inner {
  width: 30%;
  height: 100%;
  background: #ff4d4f;
  border-radius: 2rpx;
}

.time-text {
  color: #fff;
  font-size: 24rpx;
  font-family: monospace;
}

.center-play {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.main-container {
  flex: 1;
  min-height: 0;
  display: flex;
  background: #fff;
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

.checklist {
  padding-bottom: 30rpx;
}

.check-item {
  margin-bottom: 40rpx;
}

.item-title {
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
    background: #ff9f43;
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

.input-area {
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 20rpx;
  position: relative;
  min-height: 160rpx;
  
  .textarea {
    width: 100%;
    font-size: 28rpx;
    color: #333;
    line-height: 1.5;
  }
  
  .upload-btn {
    position: absolute;
    right: 20rpx;
    bottom: 20rpx;
    width: 60rpx;
    height: 60rpx;
    border: 2rpx dashed #2563eb;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
  }
}

.footer {
  padding: 20rpx 30rpx;
  background: #fff;
  border-top: 1rpx solid #eee;
}

.submit-btn {
  height: 88rpx;
  background: #2563eb;
  color: #fff;
  border-radius: 44rpx;
  font-size: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  
  &:active {
    opacity: 0.9;
  }
}

.photos-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 16rpx;
}

.preview-img {
  width: 120rpx;
  height: 120rpx;
  border-radius: 8rpx;
  background-color: #eee;
}

.safe-area {
  height: env(safe-area-inset-bottom);
}
</style>