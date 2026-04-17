<template>
  <view class="test-play-container">
    <view class="header">
      <text class="title">海康视频流测试页</text>
    </view>

    <!-- 模拟表单输入 -->
    <view class="form-card">
      <view class="form-item">
        <text class="label">摄像头 ID (cameraId):</text>
        <input class="input" v-model="cameraId" placeholder="请输入摄像头ID" />
      </view>
      <button class="btn primary" @click="fetchPlayParams" :loading="loading">
        获取播放凭证
      </button>
    </view>

    <!-- 凭证结果展示 -->
    <view class="result-card" v-if="playParams">
      <text class="section-title">获取凭证成功 🎉</text>
      <text class="code-text">设备序列号: {{ playParams.deviceSerial }}</text>
      <text class="code-text">通道号: {{ playParams.channelNo }}</text>
      <text class="code-text" v-if="playParams.oauthToken">OAuth Token: (已获取)</text>
      <text class="code-text" v-if="playParams.validCode">验证码: {{ playParams.validCode }}</text>
    </view>

    <!-- 视频播放占位区 -->
    <view class="video-section">
      <text class="section-title">视频画面 (需要海康 SDK/插件支持)</text>
      <view class="video-placeholder">
        <text v-if="!playParams">暂无视频源</text>
        <text v-else style="color: #409eff">假装这里是海康的监控画面 🎥</text>
      </view>
      
      <button 
        class="btn success" 
        @click="mockCapture" 
        :disabled="!playParams"
        :loading="capturing"
      >
        📸 模拟抓拍
      </button>
    </view>

    <!-- 抓拍结果展示 -->
    <view class="result-card" v-if="capturedUrl">
      <text class="section-title">抓拍结果</text>
      <image class="preview-img" :src="capturedUrl" mode="aspectFit"></image>
      <text class="code-text" style="word-break: break-all; margin-top: 10rpx">URL: {{ capturedUrl }}</text>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { getVideoPlayParams, captureVideoFrame } from '@/api/modules/video'
import type { PlayParamsData } from '@/api/modules/video'

const cameraId = ref('camera_001')
const loading = ref(false)
const playParams = ref<PlayParamsData | null>(null)

const capturing = ref(false)
const capturedUrl = ref('')

// 获取播放凭证
const fetchPlayParams = async () => {
  if (!cameraId.value) {
    uni.showToast({ title: '请输入cameraId', icon: 'none' })
    return
  }
  
  loading.value = true
  try {
    const res = await getVideoPlayParams({
      cameraId: cameraId.value,
      action: 'preview'
    })
    
    // 如果没有抛出异常，说明请求成功（code: 20000）
    playParams.value = res as any
    uni.showToast({ title: '获取成功', icon: 'success' })

  } catch (error: any) {
    console.error('fetchPlayParams error:', error)
    
    // 拦截器抛出了 ApiError，检查是不是 40300 权限错误
    if (error.code === 40300) {
      uni.showToast({ title: '权限拦截，已启用 Mock 数据', icon: 'none' })
      playParams.value = {
        deviceSerial: 'MOCK_D20591677',
        channelNo: '1',
        oauthToken: 'mock_oauth_token_xxx',
        validCode: '123456'
      }
    } else {
      // 其他错误，拦截器已经弹窗了，这里不再重复弹，或者打印一下
      console.log('获取凭证失败:', error.message)
    }
  } finally {
    loading.value = false
  }
}

// 模拟抓拍
const mockCapture = async () => {
  if (!playParams.value) return
  
  capturing.value = true
  try {
    // 实际业务中，这里应该调用海康 SDK/插件 获取当前画面的 Base64
    const mockBase64 = 'data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
    
    const res = await captureVideoFrame(cameraId.value, {
      image_base64: mockBase64,
      timestamp: new Date().toISOString()
    })
    
    // 成功
    capturedUrl.value = (res as any).photo_url
    uni.showToast({ title: '抓拍成功', icon: 'success' })
    
  } catch (error: any) {
    console.error('mockCapture error:', error)
    
    if (error.code === 40300) {
      uni.showToast({ title: '权限拦截，已启用 Mock 图片', icon: 'none' })
      capturedUrl.value = 'https://dummyimage.com/600x400/000/fff&text=Mock+Capture+Image'
    } else {
      console.log('抓拍失败:', error.message)
    }
  } finally {
    capturing.value = false
  }
}
</script>

<style scoped>
.test-play-container {
  padding: 30rpx;
  min-height: 100vh;
  background-color: #f5f7fa;
}
.header {
  margin-bottom: 40rpx;
  text-align: center;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}
.form-card, .result-card, .video-section {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}
.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 30rpx;
}
.label {
  width: 180rpx;
  font-size: 28rpx;
  color: #666;
}
.input {
  flex: 1;
  height: 72rpx;
  border: 2rpx solid #dcdfe6;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
}
.btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: 40rpx;
  font-size: 30rpx;
  margin-top: 20rpx;
}
.btn.primary {
  background-color: #409eff;
  color: #fff;
}
.btn.success {
  background-color: #67c23a;
  color: #fff;
}
.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
  color: #333;
}
.code-text {
  display: block;
  font-size: 24rpx;
  color: #666;
  margin-bottom: 10rpx;
  font-family: monospace;
}
.video-placeholder {
  height: 400rpx;
  background-color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
}
.video-placeholder text {
  color: #909399;
  font-size: 28rpx;
}
.preview-img {
  width: 100%;
  height: 400rpx;
  border-radius: 12rpx;
  background-color: #eee;
}
</style>
