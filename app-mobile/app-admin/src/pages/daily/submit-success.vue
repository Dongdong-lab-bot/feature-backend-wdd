<template>
  <SuccessPage 
    title="提交成功"
    :subtitle="['您的日管控检查结果已提交，', '关注后续上级审核']"
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