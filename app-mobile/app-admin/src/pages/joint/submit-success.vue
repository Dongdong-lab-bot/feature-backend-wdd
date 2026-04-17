<template>
  <SuccessPage 
    title="提交成功"
    :subtitle="['您的联合巡检检查结果已提交，', '关注后续食堂整改情况']"
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
