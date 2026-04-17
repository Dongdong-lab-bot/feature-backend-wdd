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
import SelectionPage from '../../components/SelectionPage/SelectionPage.vue'

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
  video: '查看视频监控',
  daily: '查看日管控',
  weekly: '查看周排查',
  joint: '查看联合巡检'
}

const targetMap: Record<string, string> = {
  video: '/pages/video/task-list',
  daily: '/pages/daily/task-list',
  weekly: '/pages/weekly/task-list',
  joint: '/pages/joint/task-list'
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

const handleSubmit = async () => {
  if (!selectedItem.value) return
  
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?school=${encodeURIComponent(selectedItem.value.name)}&crumbs=${encodeURIComponent(JSON.stringify([project.value, area.value, type.value, selectedItem.value.name]))}`
  })
}

const quickStart = (item: any) => {
  const target = targetMap[moduleName.value] || targetMap.video
  uni.navigateTo({
    url: `${target}?school=${encodeURIComponent(item.name)}&crumbs=${encodeURIComponent(JSON.stringify([project.value, area.value, type.value, item.name]))}`
  })
}
</script>

<style lang="scss" scoped>
/* Override default list styles for card layout */
:deep(.school-list) {
  padding: 24rpx 30rpx;
  background: transparent;
}

:deep(.list-item-wrapper) {
  margin-bottom: 24rpx;
  background: #ffffff;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.row {
  display: flex;
  align-items: center;
  padding: 24rpx;
  border: 2px solid transparent;
  border-radius: 16rpx;
  transition: all 0.2s;
  
  &.active {
    border-color: #2561ef;
    background: rgba(37, 97, 239, 0.04);
  }
}

.row-avatar {
  width: 120rpx;
  height: 90rpx;
  border-radius: 8rpx;
  margin-right: 20rpx;
  background: #f2f2f2;
}

.row-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 90rpx;
}

.row-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #333333;
}

.row-addr {
  font-size: 24rpx;
  color: #999999;
}

.row-tag {
  font-size: 24rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  
  &.status-orange {
    color: #ff9f43;
    background: rgba(255, 159, 67, 0.1);
  }
  
  &.status-red {
    color: #ff6b6b;
    background: rgba(255, 107, 107, 0.1);
  }
  
  &.status-green {
    color: #2ecc71;
    background: rgba(46, 204, 113, 0.1);
  }
}
</style>
