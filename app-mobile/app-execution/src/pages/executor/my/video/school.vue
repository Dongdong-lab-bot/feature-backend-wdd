<template>
  <SelectionPage
    :title="type"
    :keyword="keyword"
    @update:keyword="keyword = $event"
    :crumbs="[project, area, type]"
    :items="filteredSchools"
    @select="handlePick"
    @submit="handleSubmit"
    @quickStart="quickStart"
    :buttonText="btnText"
    :buttonDisabled="!selectedId"
    listClass="school-list"
  >
    <template #item="{ item }">
      <view class="row" :class="{ active: item.id === selectedId }">
        <image class="row-avatar" :src="item.avatar" mode="aspectFill" />
        <view class="row-content">
          <text class="row-name">{{ item.name }}</text>
          <text class="row-addr">{{ item.addr }}</text>
        </view>
        <view class="row-tag" :class="item.statusClass">{{ item.statusText }}</view>
      </view>
    </template>
  </SelectionPage>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import SelectionPage from '@/components/SelectionPage/SelectionPage.vue'

type SchoolItem = {
  id: string
  name: string
  addr: string
  avatar: string
  statusText: string
  statusClass: string
}

const moduleName = ref('video')
const project = ref('')
const area = ref('')
const type = ref('')
const keyword = ref('')
const selectedId = ref('')
const selectedItem = ref<SchoolItem | null>(null)

const moduleBtnMap: Record<string, string> = {
  video: '开始视频查看',
  daily: '开始日管控',
  weekly: '开始周排查',
  joint: '开始联合巡检'
}

const targetMap: Record<string, string> = {
  video: '/pages/executor/my/video/view',
  daily: '/pages/daily/checklist-submit',
  weekly: '/pages/weekly/checklist-submit',
  joint: '/pages/joint/checklist-submit'
}

const btnText = computed(() => moduleBtnMap[moduleName.value] || '下一步')

onLoad((options: any) => {
  if (options.module) moduleName.value = options.module
  if (options.project) project.value = decodeURIComponent(options.project)
  if (options.area) area.value = decodeURIComponent(options.area)
  if (options.type) type.value = decodeURIComponent(options.type)
})

const schools = ref<SchoolItem[]>([
  { 
    id: 's1', 
    name: '武岗一中一食堂', 
    addr: '城东新区教育园区', 
    avatar: '/static/video/img-canteen.png',
    statusText: '检查中',
    statusClass: 'status-orange'
  },
  { 
    id: 's2', 
    name: '武岗一中二食堂', 
    addr: '城东新区教育园区', 
    avatar: '/static/video/img-canteen.png',
    statusText: '待整改',
    statusClass: 'status-red'
  },
  { 
    id: 's3', 
    name: '武岗二中食堂', 
    addr: '城西老城区', 
    avatar: '/static/video/img-canteen.png',
    statusText: '正常',
    statusClass: 'status-green'
  }
])

const filteredSchools = computed(() => {
  const k = keyword.value.trim()
  if (!k) return schools.value
  return schools.value.filter((x) => x.name.includes(k))
})

const handlePick = (item: SchoolItem) => {
  selectedId.value = item.id
  selectedItem.value = item
}

const handleSubmit = () => {
  if (!selectedItem.value) return
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(area.value)}&type=${encodeURIComponent(type.value)}&school=${encodeURIComponent(selectedItem.value.name)}`
  })
}

const quickStart = (item: any) => {
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?project=${encodeURIComponent(project.value)}&area=${encodeURIComponent(area.value)}&type=${encodeURIComponent('高中学校')}&school=${encodeURIComponent(item.name)}`
  })
}
</script>

<style lang="scss" scoped>
.row {
  display: flex;
  align-items: center;
  padding: 30rpx;
  background: #ffffff;
  border-bottom: 1px solid #f2f2f2;
  transition: all 0.3s;
  border: 2rpx solid transparent;
  
  &.active {
    background: #F2F8FF;
    border-color: #2561EF;
    border-radius: 12rpx;
  }
}

.row-avatar {
  width: 120rpx;
  height: 90rpx;
  border-radius: 8rpx;
  margin-right: 24rpx;
  background: #f0f0f0;
}

.row-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.row-name {
  font-size: 30rpx;
  color: #111111;
  font-weight: 500;
}

.row-addr {
  font-size: 24rpx;
  color: #999999;
}

.row-tag {
  font-size: 24rpx;
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  
  &.status-orange {
    color: #FF9F2E;
    background: #FFF5E5;
  }
  
  &.status-red {
    color: #FA746B;
    background: #FFF0EF;
  }
  
  &.status-green {
    color: #3DD4A7;
    background: #EAFBF6;
  }
}
</style>