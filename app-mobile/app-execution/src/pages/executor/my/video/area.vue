<template>
  <SelectionPage
    title="片区"
    :keyword="keyword"
    @update:keyword="keyword = $event"
    :items="filteredAreas"
    @select="handlePick"
    @submit="handleNext"
    @quickStart="quickStart"
    :buttonText="btnText"
  >
    <template #header-extra>
      <view class="row" @click="handleProject">
        <image class="row-icon" src="/static/video/icon-home.svg" mode="aspectFit" />
        <text class="row-title">{{ project }}</text>
      </view>
      <view class="divider"></view>
    </template>

    <template #item="{ item }">
      <view class="row">
        <image class="row-icon" src="/static/video/icon-home.svg" mode="aspectFit" />
        <text class="row-title">{{ item.name }}</text>
        <text class="row-sub">{{ item.count }}所学校</text>
        <image class="row-arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
      </view>
    </template>
  </SelectionPage>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import SelectionPage from '@/components/SelectionPage/SelectionPage.vue'

type AreaItem = {
  id: string
  name: string
  count: number
}

const moduleName = ref('video')
const project = ref('武岗县全县项目')
const keyword = ref('')
const selectedArea = ref('')

const moduleBtnMap: Record<string, string> = {
  video: '开始视频查看',
  daily: '开始日管控',
  weekly: '开始周排查',
  joint: '开始联合巡检'
}

const targetMap: Record<string, string> = {
  video: '/pages/executor/my/video/view',
  daily: '/pages/daily/record-audit',
  weekly: '/pages/weekly/checklist-submit',
  joint: '/pages/joint/checklist-submit'
}

const btnText = computed(() => moduleBtnMap[moduleName.value] || '下一步')

onLoad((options: any) => {
  if (options.module) moduleName.value = options.module
  const p = typeof options?.project === 'string' ? options.project : ''
  if (p) {
    try {
      project.value = decodeURIComponent(p)
    } catch {
      project.value = p
    }
  }
})

const areas = ref<AreaItem[]>([
  { id: 'a1', name: '城东片区', count: 30 },
  { id: 'a2', name: '城西片区', count: 30 },
  { id: 'a3', name: '城南片区', count: 30 },
  { id: 'a4', name: '城北片区', count: 30 },
  { id: 'a5', name: '城东片区', count: 30 }
])

const filteredAreas = computed(() => {
  const k = keyword.value.trim()
  if (!k) return areas.value
  return areas.value.filter((x) => x.name.includes(k))
})

const handleProject = () => {
  uni.showToast({ title: project.value, icon: 'none' })
}

const handlePick = (item: AreaItem) => {
  selectedArea.value = item.name
  uni.navigateTo({
    url: `/pages/executor/my/video/school-type?module=${moduleName.value}&project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(item.name)}`
  })
}

const handleNext = () => {
  // If no area selected but button clicked, maybe prompt or just go to next step (logic from admin)
  // Admin logic didn't have implementation in handleNext shown in snippet, assuming it handles selection or toast
  if (!selectedArea.value) {
     uni.showToast({ title: '请选择片区', icon: 'none' })
     return
  }
  // In handlePick we navigate, so handleNext might be for button at bottom if selection is done differently
  // For now, let's assume list click is the primary way
}

const quickStart = (item: any) => {
  // Quick start logic - bypass selection
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?project=${encodeURIComponent(project.value)}&area=城东片区&type=高中学校&school=${encodeURIComponent(item.name)}`
  })
}
</script>

<style lang="scss" scoped>
.row {
  display: flex;
  align-items: center;
  height: 112rpx;
  padding: 0 30rpx;
  background: #ffffff;
}

.row-icon {
  width: 36rpx;
  height: 36rpx;
  margin-right: 20rpx;
}

.row-title {
  flex: 1;
  font-size: 30rpx;
  color: #111111;
}

.row-sub {
  font-size: 26rpx;
  color: #999999;
  margin-right: 10rpx;
}

.row-arrow {
  width: 32rpx;
  height: 32rpx;
}

.divider {
  height: 20rpx;
  background: #f7f9fb;
}
</style>