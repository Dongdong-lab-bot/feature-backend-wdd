<template>
  <SuccessPage 
    title="完成审核"
    :subtitle="['您已日管控审核，', '可关注后续食堂整改反馈']"
    @back="goBack"
  />
</template>

<script setup lang="ts">
import SuccessPage from '@/components/SuccessPage/SuccessPage.vue'

const goBack = () => {
  // Try to go back to task list or home
  uni.navigateBack({
    delta: 2
  })
}
</script>