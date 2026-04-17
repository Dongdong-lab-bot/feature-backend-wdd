<template>
  <InspectionList moduleName="daily" :refreshTrigger="refreshTrigger" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import InspectionList from '@/components/InspectionList/InspectionList.vue'

const refreshTrigger = ref(0)

onShow(() => {
  refreshTrigger.value++
})
</script>
