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
import SelectionPage from '../../components/SelectionPage/SelectionPage.vue'

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
  video: '/pages/video/view',
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
    url: `/pages/canteen-selection/school-type?module=${moduleName.value}&project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(item.name)}`
  })
}

const handleNext = () => {
  if (!selectedArea.value) {
    uni.showToast({ title: '请选择片区', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: `/pages/canteen-selection/school-type?module=${moduleName.value}&project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(selectedArea.value)}`
  })
}

const quickStart = (item: any) => {
  // item is { name, dist }
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?project=${encodeURIComponent(project.value)}&area=${encodeURIComponent('城东片区')}&type=${encodeURIComponent('高中学校')}&school=${encodeURIComponent(item.name)}`
  })
}
</script>

<style lang="scss" scoped>
:deep(.list) {
  margin-top: 10rpx;
  background: #ffffff;
}

:deep(.list-item-wrapper + .list-item-wrapper) {
  border-top: 1px solid #f2f2f2;
}

.row {
  height: 88rpx;
  padding: 0 30rpx;
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.divider {
  height: 1px;
  background: #f2f2f2;
  margin-left: 30rpx;
}

.row-icon {
  width: 40rpx;
  height: 40rpx;
  margin-right: 20rpx;
}

.row-title {
  flex: 1;
  font-size: 28rpx;
  color: #333333;
  font-weight: 500;
}

.row-sub {
  font-size: 24rpx;
  color: #999999;
  margin-right: 12rpx;
}

.row-arrow {
  width: 24rpx;
  height: 24rpx;
}
</style>
