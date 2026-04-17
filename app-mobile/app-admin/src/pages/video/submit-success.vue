<template>
  <SuccessPage
    title="提交成功"
    subtitle="视频巡检表已提交成功"
    button-text="返回视频监控中心"
    @back="handleBack"
  />
</template>

<script setup lang="ts">
import SuccessPage from '@/components/SuccessPage/SuccessPage.vue'

const handleBack = () => {
  uni.reLaunch({
    url: '/pages/video/task-list'
  })
}
</script>
