<template>
  <SuccessPage 
    title="完成审核"
    :subtitle="['您已完成联合巡检整改审核']"
    @back="goBack"
  />
</template>

<script setup lang="ts">
import SuccessPage from '@/components/SuccessPage/SuccessPage.vue'

const goBack = () => {
  uni.navigateBack({
    delta: 2
  })
}
</script>
