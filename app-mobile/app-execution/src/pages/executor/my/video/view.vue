<template>
  <view class="page">
    <NavBar title="视频查看" />

    <view class="content">
      <view class="player">
        <image class="player-bg" src="/static/monthly/detail-photo.png" mode="aspectFill" />
        <view class="player-top">
          <text class="player-name">{{ activeCamera.name }}</text>
        </view>
        <view class="player-controls">
          <view class="play-wrap" @click="togglePlay">
            <image class="play-icon" src="/static/monthly/icon-play.svg" mode="aspectFit" />
          </view>
          <view class="progress-wrap">
            <view class="progress-track"></view>
            <view class="progress-current" :style="{ width: progressWidth }"></view>
          </view>
          <text class="time-text">00:14/02:56</text>
          <view class="full-wrap" @click="handleFullscreen">
            <image class="full-icon" src="/static/video/icon-fullscreen.svg" mode="aspectFit" />
          </view>
        </view>
      </view>

      <view class="body">
        <view class="left">
          <view
            class="left-item"
            v-for="(item, idx) in areas"
            :key="item"
            :class="{ active: idx === activeAreaIndex }"
            @click="activeAreaIndex = idx"
          >
            <text class="left-text">{{ item }}</text>
          </view>
        </view>

        <scroll-view class="right" scroll-y>
          <view class="grid">
            <view
              class="cell"
              v-for="cam in filteredCameras"
              :key="cam.id"
              :class="{ active: cam.id === activeCameraId }"
              @click="selectCamera(cam)"
            >
              <image class="cell-img" src="/static/monthly/detail-photo.png" mode="aspectFill" />
              <view v-if="cam.offline" class="offline-mask">
                <text class="offline-text">已离线</text>
              </view>
              <text class="cell-label">{{ cam.name }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>

    <view class="footer">
      <button class="capture-btn" @click="handleCapture">抓拍图片</button>
      <view class="safe"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import NavBar from '@/components/NavBar/NavBar.vue'
import { fetchCameraTree, getPlayParams, captureSnapshot } from '@/common/video'

type CameraItem = {
  id: string
  area: string
  name: string
  offline?: boolean
}

const project = ref('')
const area = ref('')
const type = ref('')
const school = ref('')

const loadCameraTree = async () => {
  try {
    const res: any = await fetchCameraTree()
    console.log('camera tree:', res)
  } catch (e) {
    uni.showToast({ title: '摄像头树加载失败', icon: 'none' })
  }
}

onLoad((options: any) => {
  const p = typeof options?.project === 'string' ? options.project : ''
  const a = typeof options?.area === 'string' ? options.area : ''
  const t = typeof options?.type === 'string' ? options.type : ''
  const s = typeof options?.school === 'string' ? options.school : ''

  const decode = (v: string) => {
    try {
      return decodeURIComponent(v)
    } catch {
      return v
    }
  }

  project.value = p ? decode(p) : ''
  area.value = a ? decode(a) : ''
  type.value = t ? decode(t) : ''
  school.value = s ? decode(s) : ''
  
  if (school.value) {
    uni.setNavigationBarTitle({ title: school.value })
  }

  loadCameraTree()
})

const areas = ['后厨', '凉菜间', '消洗间', '仓库', '留样间', '餐厅']
const activeAreaIndex = ref(0)
const activeCameraId = ref('c1')

const cameras = ref<CameraItem[]>([
  { id: 'c1', area: '后厨', name: '后厨全景' },
  { id: 'c2', area: '后厨', name: '切配区' },
  { id: 'c3', area: '后厨', name: '烹饪区' },
  { id: 'c4', area: '后厨', name: '出餐区' },
  { id: 'c5', area: '凉菜间', name: '凉菜专间', offline: true },
  { id: 'c6', area: '消洗间', name: '洗碗机' },
  { id: 'c7', area: '仓库', name: '主库房' },
])

const filteredCameras = computed(() => {
  const areaName = areas[activeAreaIndex.value]
  return cameras.value.filter(c => c.area === areaName)
})

const activeCamera = computed(() => {
  return cameras.value.find(c => c.id === activeCameraId.value) || cameras.value[0]
})

const progressWidth = ref('10%')
const isPlaying = ref(false)

const togglePlay = async () => {
  const cam = activeCamera.value
  if (!cam) return
  try {
    const res: any = await getPlayParams({
      cameraId: cam.id,
      action: 'preview'
    })
    console.log('play params:', res)
    isPlaying.value = !isPlaying.value
    uni.showToast({ title: '获取播放参数成功', icon: 'none' })
  } catch (e) {
    uni.showToast({ title: '获取播放参数失败', icon: 'none' })
  }
}

const handleFullscreen = () => {
  uni.showToast({ title: '全屏', icon: 'none' })
}

const selectCamera = (cam: CameraItem) => {
  activeCameraId.value = cam.id
}

const handleCapture = async () => {
  const cam = activeCamera.value
  if (!cam) return

  let imageBase64 = ''
  try {
    const payload = typeof btoa === 'function' ? btoa('safefood') : ''
    imageBase64 = `data:image/jpeg;base64,${payload}`
  } catch {
    imageBase64 = 'data:image/jpeg;base64,c2FmZWZvb2Q='
  }

  const timestamp = new Date().toISOString()

  try {
    const res: any = await captureSnapshot(cam.id, imageBase64, timestamp)
    console.log('capture result:', res)
    uni.showToast({ title: '抓拍成功', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '抓拍失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.player {
  width: 100%;
  height: 422rpx;
  background: #000;
  position: relative;
}

.player-bg {
  width: 100%;
  height: 100%;
  opacity: 0.8;
}

.player-top {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 80rpx;
  background: linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 100%);
  display: flex;
  align-items: center;
  padding: 0 30rpx;
  box-sizing: border-box;
}

.player-name {
  color: #fff;
  font-size: 30rpx;
  font-weight: 500;
}

.player-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 88rpx;
  background: linear-gradient(0deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 100%);
  display: flex;
  align-items: center;
  padding: 0 20rpx;
  box-sizing: border-box;
}

.play-wrap, .full-wrap {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-icon, .full-icon {
  width: 32rpx;
  height: 32rpx;
}

.progress-wrap {
  flex: 1;
  height: 4rpx;
  background: rgba(255,255,255,0.3);
  margin: 0 20rpx;
  position: relative;
  border-radius: 2rpx;
}

.progress-track {
  width: 100%;
  height: 100%;
}

.progress-current {
  height: 100%;
  background: #3DD4A7;
  position: absolute;
  left: 0;
  top: 0;
}

.time-text {
  font-size: 20rpx;
  color: #fff;
  margin-right: 10rpx;
}

.body {
  flex: 1;
  display: flex;
  border-top: 1px solid #f2f2f2;
}

.left {
  width: 180rpx;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.left-item {
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f9fb;
  border-bottom: 1px solid #fff;
  position: relative;
  
  &.active {
    background: #fff;
    
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 30rpx;
      bottom: 30rpx;
      width: 6rpx;
      background: #2561EF;
      border-radius: 0 4rpx 4rpx 0;
    }
    
    .left-text {
      color: #2561EF;
      font-weight: 500;
    }
  }
}

.left-text {
  font-size: 28rpx;
  color: #666;
}

.right {
  flex: 1;
  background: #fff;
  padding: 20rpx;
  box-sizing: border-box;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.cell {
  background: #f7f9fb;
  border-radius: 8rpx;
  overflow: hidden;
  position: relative;
  border: 2rpx solid transparent;
  
  &.active {
    border-color: #2561EF;
  }
}

.cell-img {
  width: 100%;
  height: 160rpx;
  display: block;
}

.offline-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 160rpx;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.offline-text {
  color: #fff;
  font-size: 24rpx;
}

.cell-label {
  display: block;
  height: 60rpx;
  line-height: 60rpx;
  text-align: center;
  font-size: 26rpx;
  color: #333;
  background: #fff;
}

.footer {
  height: calc(120rpx + constant(safe-area-inset-bottom));
  height: calc(120rpx + env(safe-area-inset-bottom));
  background: #fff;
  padding: 20rpx 30rpx;
  box-sizing: border-box;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.05);
}

.capture-btn {
  height: 80rpx;
  line-height: 80rpx;
  background: #2561EF;
  color: #fff;
  font-size: 30rpx;
  border-radius: 40rpx;
}

.safe {
  height: constant(safe-area-inset-bottom);
  height: env(safe-area-inset-bottom);
}
</style>