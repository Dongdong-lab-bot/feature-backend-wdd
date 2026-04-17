<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { setupNetworkMonitor, setupRequestInterceptor } from '@common/utils/network'

onLaunch(() => {
  console.log('App Launch')

  uni.setStorageSync('appClient', 'exec_app')

  if (!uni.getStorageSync('baseUrl')) {
    uni.setStorageSync('baseUrl', 'http://127.0.0.1:8000')
  }

  setupNetworkMonitor()
  setupRequestInterceptor()

  // 判断是否首次启动（避免与监管端同浏览器/同设备测试时缓存串号）
  const hasSeenGuide = uni.getStorageSync('exec_hasSeenGuide')

  if (!hasSeenGuide) {
    // 首次启动，跳转到引导页
    uni.reLaunch({
      url: '/pages/login/guide'
    })
  } else {
    // 非首次启动，跳转到登录页
    uni.reLaunch({
      url: '/pages/login/login'
    })
  }
})

onShow(() => {
  console.log('App Show')
})

onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss">
@import './uni.scss';

page {
  background-color: $uni-bg-color;
  font-size: $uni-font-size-base;
  color: $uni-text-color;
}
</style>
