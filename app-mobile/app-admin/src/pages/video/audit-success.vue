<template>
  <SuccessPage
    title="审核完成"
    subtitle="整改审核已完成"
    button-text="返回视频监控中心"
    @back="handleBack"
  />
</template>

<script setup lang="ts">
import SuccessPage from '@/components/SuccessPage/SuccessPage.vue'

const handleBack = () => {
  uni.navigateBack({
    delta: 2
  })
}
</script>
