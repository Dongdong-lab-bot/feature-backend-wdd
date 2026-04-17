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
import NavBar from '../../components/NavBar/NavBar.vue'

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
})

const areas = ref<string[]>(['售卖间', '洗消间', '烹饪间', '大厅', '库房'])
const activeAreaIndex = ref(2)

const cameras = ref<CameraItem[]>([
  { id: 'c1', area: '烹饪间', name: '烹饪区一画面' },
  { id: 'c2', area: '烹饪间', name: '烹饪区二画面' },
  { id: 'c3', area: '烹饪间', name: '烹饪区三画面' },
  { id: 'c4', area: '烹饪间', name: '烹饪区四画面', offline: true },
  { id: 'c5', area: '售卖间', name: '售卖间一画面' },
  { id: 'c6', area: '洗消间', name: '洗消间一画面' },
  { id: 'c7', area: '大厅', name: '大厅一画面' },
  { id: 'c8', area: '库房', name: '库房一画面' }
])

const activeCameraId = ref('c1')

const filteredCameras = computed(() => {
  const a = areas.value[activeAreaIndex.value]
  return cameras.value.filter((x) => x.area === a)
})

const activeCamera = computed(() => {
  return cameras.value.find((x) => x.id === activeCameraId.value) || cameras.value[0]
})

const isPlaying = ref(false)
const progressWidth = computed(() => (isPlaying.value ? '28%' : '20%'))

const togglePlay = () => {
  isPlaying.value = !isPlaying.value
}

const handleFullscreen = () => {
  uni.showToast({ title: '全屏开发中', icon: 'none' })
}

const selectCamera = (cam: CameraItem) => {
  if (cam.offline) {
    uni.showToast({ title: '该通道已离线', icon: 'none' })
    return
  }
  activeCameraId.value = cam.id
}

const handleCapture = () => {
  const itemList = ['相册', '拍照', '文件']
  uni.showActionSheet({
    itemList,
    success: (res) => {
      const picked = itemList[res.tapIndex]
      const ctx = school.value ? `（${school.value}）` : ''
      uni.showToast({ title: `${picked}${ctx}`, icon: 'none' })
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: rgba(242, 247, 251, 0.62);
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.player {
  height: 420rpx;
  background: #000;
  position: relative;
}

.player-bg {
  width: 100%;
  height: 100%;
  opacity: 0.95;
}

.player-top {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 64rpx;
  padding: 0 30rpx;
  box-sizing: border-box;
}

.player-name {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
}

.player-controls {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 64rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.play-wrap {
  width: 52rpx;
  height: 52rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14rpx;
}

.play-icon {
  width: 36rpx;
  height: 36rpx;
}

.progress-wrap {
  flex: 1;
  height: 8rpx;
  position: relative;
  margin-right: 16rpx;
}

.progress-track {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  border-radius: 999rpx;
  background: rgba(215, 215, 215, 1);
}

.progress-current {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 999rpx;
  background: #ff6262;
}

.time-text {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.95);
  width: 150rpx;
  text-align: right;
}

.full-wrap {
  width: 52rpx;
  height: 52rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 10rpx;
}

.full-icon {
  width: 30rpx;
  height: 30rpx;
}

.body {
  flex: 1;
  min-height: 0;
  display: flex;
  background: #ffffff;
}

.left {
  width: 180rpx;
  border-right: 1px solid #f2f2f2;
}

.left-item {
  height: 96rpx;
  padding-left: 24rpx;
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.left-item.active {
  background: rgba(37, 97, 239, 0.06);
}

.left-text {
  font-size: 26rpx;
  color: #333333;
  font-weight: 600;
}

.right {
  flex: 1;
  min-height: 0;
}

.grid {
  padding: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 18rpx;
  box-sizing: border-box;
}

.cell {
  width: calc(50% - 9rpx);
  height: 220rpx;
  border: 2rpx solid transparent;
  box-sizing: border-box;
  position: relative;
}

.cell.active {
  border-color: #2561ef;
}

.cell-img {
  width: 100%;
  height: 170rpx;
  background: #f2f2f2;
}

.cell-label {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 50rpx;
  line-height: 50rpx;
  font-size: 24rpx;
  color: #333333;
  text-align: center;
  background: #ffffff;
  border: 1px solid #f2f2f2;
  box-sizing: border-box;
}

.offline-mask {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 170rpx;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}

.offline-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
}

.footer {
  background: rgba(242, 247, 251, 0.62);
  padding: 16rpx 30rpx 0;
  box-sizing: border-box;
}

.capture-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 16rpx;
  background: #2561ef;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
  box-shadow: 0 10rpx 30rpx rgba(37, 97, 239, 0.35);
}

.safe {
  height: calc(20rpx + env(safe-area-inset-bottom));
}
</style>
