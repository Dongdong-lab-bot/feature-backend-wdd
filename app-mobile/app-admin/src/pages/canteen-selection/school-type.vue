<template>
  <SelectionPage
    title="学校类型"
    :keyword="keyword"
    @update:keyword="keyword = $event"
    :crumbs="[project, area]"
    :items="filteredTypes"
    @select="handlePick"
    @submit="handleNext"
    @quickStart="quickStart"
    :buttonText="btnText"
  >
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

type TypeItem = {
  id: string
  name: string
  count: number
}

const moduleName = ref('video')
const project = ref('')
const area = ref('')
const keyword = ref('')

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
  if (options.project) project.value = decodeURIComponent(options.project)
  if (options.area) area.value = decodeURIComponent(options.area)
})

const types = ref<TypeItem[]>([
  { id: 't1', name: '高中学校', count: 10 },
  { id: 't2', name: '初中学校', count: 15 },
  { id: 't3', name: '小学学校', count: 20 },
  { id: 't4', name: '幼儿园', count: 25 }
])

const filteredTypes = computed(() => {
  const k = keyword.value.trim()
  if (!k) return types.value
  return types.value.filter((x) => x.name.includes(k))
})

const handlePick = (item: TypeItem) => {
  uni.navigateTo({
    url: `/pages/canteen-selection/school?module=${moduleName.value}&project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(area.value)}&type=${encodeURIComponent(item.name)}`
  })
}

const handleNext = () => {
  // Same logic as Area, immediate navigation preferred
  uni.showToast({ title: '请选择学校类型', icon: 'none' })
}

const quickStart = (item: any) => {
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(area.value)}&type=${encodeURIComponent('高中学校')}&school=${encodeURIComponent(item.name)}`
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
