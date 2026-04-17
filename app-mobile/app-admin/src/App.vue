<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { setupNetworkMonitor, setupRequestInterceptor } from '@common/utils/network'
import { checkUpdateOnLaunch } from './utils/update'

onLaunch(() => {
  console.log('App Launch')

  uni.setStorageSync('appClient', 'reg_app')

  setupNetworkMonitor()
  setupRequestInterceptor()

  const hasSeenGuide = uni.getStorageSync('reg_hasSeenGuide')
  const targetUrl = hasSeenGuide ? '/pages/login/login' : '/pages/login/guide'

  uni.reLaunch({
    url: targetUrl,
    complete: () => {
      checkUpdateOnLaunch()
    }
  })
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
