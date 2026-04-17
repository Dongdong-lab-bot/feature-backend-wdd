<template>
  <view class="page">
    <NavBar :title="pageTitle" />

    <view class="content">
      <view class="search-wrap">
        <view class="search-box">
          <image class="search-icon" src="/static/monthly/icon-search-gray.svg" mode="aspectFit" />
          <input 
            class="search-input" 
            v-model="keyword" 
            placeholder="请输入" 
            placeholder-style="color: #CCCCCC" 
          />
        </view>
      </view>

      <view class="crumbs" v-if="crumbs.length">
        <text 
          v-for="(crumb, index) in crumbs" 
          :key="index"
          class="crumb"
          :class="{ blue: index < crumbs.length - 1, gray: index === crumbs.length - 1 }"
        >
          {{ index > 0 ? '> ' : '' }}{{ crumb }}
        </text>
      </view>

      <view class="tabs">
        <view 
          class="tab-item" 
          v-for="tab in tabs" 
          :key="tab.value"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          <text class="tab-text">{{ tab.label }}</text>
          <view class="tab-line" v-if="activeTab === tab.value"></view>
        </view>
      </view>

      <scroll-view class="list" scroll-y>
        <view v-if="filteredList.length > 0">
          <view class="list-item" v-for="(item, index) in filteredList" :key="index" @click="handleItemClick(item)">
            <view class="item-top">
              <text class="item-title">{{ item.title }}</text>
              <view class="item-top-right">
                <text class="item-count">{{ item.count }}</text>
                <text class="item-status" :class="statusClassMap[item.status]">{{ item.statusText || statusTextMap[item.status] }}</text>
              </view>
            </view>
            <view class="item-bottom">
              <view class="submitter-info">
                <image class="avatar" :src="item.avatar || '/static/monthly/detail-photo.png'" mode="aspectFill" />
                <text class="submitter">{{ item.submitter }}</text>
              </view>
              <text class="time">{{ item.time }}</text>
            </view>
          </view>
        </view>
        <view v-else class="empty-tip">
          <text>没有更多数据了~</text>
        </view>
      </scroll-view>
    </view>

    <view class="footer">
      <button class="start-btn" @click="handleStartNew">
        {{ startBtnText }}
      </button>
      <view class="safe"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import NavBar from '../NavBar/NavBar.vue'
import { inspectionApi } from '@/api'
import type { InspectionModule, InspectionTaskItem } from '@/api/modules/inspection'

const props = defineProps<{
  moduleName: string
  refreshTrigger?: number
}>()

type TabStatus = 'todo' | 'pending' | 'rectify' | 'completed'

type ListItem = {
  id: string
  title: string
  count: string
  status: TabStatus
  statusText: string
  rawStatus: string
  tabKey: TabStatus
  submitter: string
  time: string
  avatar?: string
}

const pageTitle = ref('')
const keyword = ref('')
const activeTab = ref(props.moduleName === 'daily' ? 'todo' : 'pending')
const selectedSchool = ref('')
const crumbs = ref<string[]>([])

const handleCrumbsParam = () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const options = currentPage.options || {}
  
  if (options.school) {
    selectedSchool.value = decodeURIComponent(options.school)
  }
  if (options.crumbs) {
    try {
      crumbs.value = JSON.parse(decodeURIComponent(options.crumbs))
    } catch (e) {
      crumbs.value = []
    }
  } else {
    // 默认不显示面包屑
    crumbs.value = []
  }
}

const tabs = computed(() => {
  const baseTabs = [
    { label: '待审核', value: 'pending' },
    { label: '待整改', value: 'rectify' },
    { label: '已完成', value: 'completed' }
  ]
  if (props.moduleName === 'daily') {
    return [{ label: '待提交', value: 'todo' }, ...baseTabs]
  }
  return baseTabs
})

const listData = ref<ListItem[]>([])

const filteredList = computed(() => {
  return listData.value
})

const statusClassMap: Record<string, string> = {
  todo: 'status-gray',
  pending: 'status-orange',
  rectify: 'status-red',
  completed: 'status-green'
}

const statusTextMap: Record<string, string> = {
  todo: '待提交',
  pending: '待审核',
  rectify: '待整改',
  completed: '已完成'
}

const moduleConfig: Record<string, { title: string, btnText: string }> = {
  daily: { title: '日管控', btnText: '开始新日管控' },
  weekly: { title: '周排查', btnText: '开始新周排查' },
  joint: { title: '联合巡检', btnText: '开始新联合巡检' },
  video: { title: '视频监控中心', btnText: '开始新视频巡检' }
}

const startBtnText = computed(() => {
  return moduleConfig[props.moduleName]?.btnText || '开始'
})

const normalizeStatus = (status?: string): TabStatus => {
  if (!status) return 'todo'
  const s = status.toUpperCase()
  if (s === 'COMPLETED') return 'completed'
  if (s === 'REJECTED') return 'rectify'
  if (s === 'SUBMITTED' || s === 'RECTIFIED') return 'pending'
  return 'todo'
}

const resolveTabKey = (statusText?: string, rawStatus?: string): TabStatus => {
  const text = (statusText || '').trim()
  if (text === '待检查' || text === '待提交' || text === '待上报' || text === '待签字') return 'todo'
  if (text === '待整改') return 'rectify'
  if (text === '已完成') return 'completed'
  if (text === '待审核' || text === '已改待审') return 'pending'
  return normalizeStatus(rawStatus)
}

const formatCount = (task: InspectionTaskItem) => {
  if (task.completion_progress) return task.completion_progress
  if (typeof task.total_score === 'number') return `${task.total_score}分`
  return '--'
}

const mapTabToStatus = (tab: string): string => {
  if (tab === 'todo') return 'PENDING'
  if (tab === 'pending') return 'SUBMITTED'
  if (tab === 'rectify') return 'REJECTED'
  if (tab === 'completed') return 'COMPLETED'
  return ''
}

const loadTasks = async () => {
  const moduleName = props.moduleName as InspectionModule | 'video'
  const currentStatus = mapTabToStatus(activeTab.value)
  
  // 对于视频巡检，使用专有的 API
  if (moduleName === 'video') {
    const { getVideoTasks } = await import('@/api/modules/video')
    try {
      let rawVideoList: any[] = []
      if (activeTab.value === 'pending') {
        const [res1, res2] = await Promise.all([
          getVideoTasks({
            status: 'SUBMITTED',
            keyword: selectedSchool.value || keyword.value.trim(),
            page: 1,
            page_size: 50
          }),
          getVideoTasks({
            status: 'RECTIFIED',
            keyword: selectedSchool.value || keyword.value.trim(),
            page: 1,
            page_size: 50
          })
        ])
        rawVideoList = [...(res1.list || []), ...(res2.list || [])]
      } else {
        const data = await getVideoTasks({
          status: currentStatus,
          keyword: selectedSchool.value || keyword.value.trim(),
          page: 1,
          page_size: 50
        })
        rawVideoList = data.list || []
      }
      
      listData.value = rawVideoList.map((task: any) => ({
        id: task.task_id,
        title: task.template_name || task.canteen_name || '视频巡检任务',
        count: formatCount(task),
        status: normalizeStatus(task.status),
        // 如果后端没有返回 status_text，或者返回的是原生的英文，这里强制转成中文兜底
        statusText: task.status_text && task.status_text !== task.status ? task.status_text : statusTextMap[normalizeStatus(task.status)],
        rawStatus: String(task.status || ''),
        tabKey: resolveTabKey(task.status_text, task.status),
        submitter: task.submitter_name || task.inspector_name || '未设置',
        time: task.submission_date || ''
      }))
    } catch (e) {
      console.error('Failed to load video tasks:', e)
      listData.value = []
    }
    return
  }

  let rawList: any[] = []
  
  if (activeTab.value === 'pending') {
    // 待审核需要同时获取 SUBMITTED 和 RECTIFIED 的任务
    const [res1, res2] = await Promise.all([
      inspectionApi.getInspectionTasks(moduleName, {
        status: 'SUBMITTED',
        keyword: selectedSchool.value || keyword.value.trim(),
        page: 1,
        page_size: 50
      }),
      inspectionApi.getInspectionTasks(moduleName, {
        status: 'RECTIFIED',
        keyword: selectedSchool.value || keyword.value.trim(),
        page: 1,
        page_size: 50
      })
    ])
    rawList = [...(res1.list || []), ...(res2.list || [])]
  } else {
    const data = await inspectionApi.getInspectionTasks(moduleName, {
      status: currentStatus,
      keyword: selectedSchool.value || keyword.value.trim(),
      page: 1,
      page_size: 50
    })
    rawList = data.list || []
  }

  listData.value = rawList.map((task) => ({
    id: String(task.task_id ?? task.id ?? ''),
    title: task.template_name || task.canteen_name || '巡检任务',
    count: formatCount(task),
    status: normalizeStatus(task.status),
    statusText: task.status_text || '',
    rawStatus: String(task.status || ''),
    tabKey: resolveTabKey(task.status_text, task.status),
    submitter: task.submitter_name || '未设置',
    time: task.submission_date || ''
  }))
}

watch(
  () => [props.moduleName, props.refreshTrigger, activeTab.value, keyword.value],
  async ([moduleName]) => {
    const config = moduleConfig[moduleName as string]
    if (config) {
      pageTitle.value = config.title
    }
    handleCrumbsParam()
    await loadTasks()
  },
  { immediate: true }
)

watch(
  () => props.moduleName,
  (moduleName) => {
    const config = moduleConfig[moduleName]
    if (config) pageTitle.value = config.title
  },
  { immediate: true }
)

const handleStartNew = () => {
  uni.navigateTo({
    url: `/pages/canteen-selection/area?module=${props.moduleName}`
  })
}

const handleItemClick = (item: ListItem) => {
  if (!item.id || item.id === 'undefined' || item.id === 'null') {
    uni.showToast({ title: '任务ID缺失，无法打开详情', icon: 'none' })
    return
  }
  let url = ''
  if (props.moduleName === 'daily') {
    if (item.rawStatus === 'PENDING') {
      // 传递必要参数以便 checklist-submit.vue 自动加载任务
      url = `/pages/daily/checklist-submit?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'SUBMITTED') {
      url = `/pages/daily/record-audit?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'REJECTED' || item.rawStatus === 'RECTIFIED') {
      url = `/pages/daily/record-rectify?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'COMPLETED') {
      url = `/pages/daily/record-completed?id=${encodeURIComponent(item.id)}`
    }
  } else if (props.moduleName === 'weekly') {
    if (item.rawStatus === 'PENDING') {
      url = `/pages/weekly/checklist-submit?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'SUBMITTED' || item.rawStatus === 'REJECTED' || item.rawStatus === 'RECTIFIED') {
      url = `/pages/weekly/record-rectify?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'COMPLETED') {
      url = `/pages/weekly/record-completed?id=${encodeURIComponent(item.id)}`
    }
  } else if (props.moduleName === 'joint') {
    if (item.rawStatus === 'PENDING') {
      url = `/pages/joint/checklist-submit?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'SUBMITTED' || item.rawStatus === 'REJECTED' || item.rawStatus === 'RECTIFIED') {
      url = `/pages/joint/record-rectify?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'COMPLETED') {
      url = `/pages/joint/record-completed?id=${encodeURIComponent(item.id)}`
    }
  } else if (props.moduleName === 'video') {
    if (item.rawStatus === 'PENDING') {
      url = `/pages/video/checklist-submit?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'SUBMITTED' || item.rawStatus === 'REJECTED' || item.rawStatus === 'RECTIFIED') {
      url = `/pages/video/record-rectify?id=${encodeURIComponent(item.id)}`
    } else if (item.rawStatus === 'COMPLETED') {
      url = `/pages/video/record-completed?id=${encodeURIComponent(item.id)}`
    }
  }
  
  if (url) {
    uni.navigateTo({ url })
  }
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.search-wrap {
  padding: 10rpx 30rpx 0;
  background: #fff;
}

.search-box {
  height: 80rpx;
  border-radius: 16rpx;
  background: #f7f9fb;
  display: flex;
  align-items: center;
  padding: 0 18rpx;
  box-sizing: border-box;
}

.search-icon {
  width: 36rpx;
  height: 36rpx;
  margin-right: 12rpx;
}

.search-input {
  flex: 1;
  height: 80rpx;
  font-size: 28rpx;
  color: #333;
}

.crumbs {
  padding: 20rpx 30rpx;
  background: #fff;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10rpx;
}

.crumb {
  font-size: 26rpx;
  font-weight: 500;
  
  &.blue {
    color: #2561ef;
  }
  
  &.gray {
    color: #666666;
  }
}

.tabs {
  display: flex;
  background: #fff;
  padding: 0 30rpx;
  border-bottom: 1px solid #f2f2f2;
}

.tab-item {
  flex: 1;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  font-size: 28rpx;
  color: #666;
  
  &.active {
    color: #2561ef;
    font-weight: 600;
  }
}

.tab-line {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background: #2561ef;
  border-radius: 2rpx;
}

.list {
  flex: 1;
  padding: 24rpx 30rpx;
  box-sizing: border-box;
}

.list-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx 30rpx 30rpx 40rpx;
  margin-bottom: 24rpx;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 30rpx;
    bottom: 30rpx;
    width: 8rpx;
    background: #ff6b6b; // Default red line
    border-radius: 0 4rpx 4rpx 0;
  }
}

.item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.item-title {
  font-size: 32rpx;
  color: #333;
  font-weight: 600;
  flex: 1;
}

.item-top-right {
  display: flex;
  align-items: center;
}

.item-count {
  font-size: 36rpx;
  color: #999;
  margin-right: 24rpx;
}

.item-status {
  font-size: 26rpx;
  
  &.status-orange { color: #ff9f43; }
  &.status-red { color: #ff6b6b; }
  &.status-green { color: #2ecc71; }
  &.status-gray { color: #666; }
}

.item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.submitter-info {
  display: flex;
  align-items: center;
}

.avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  margin-right: 16rpx;
}

.submitter {
  font-size: 26rpx;
  color: #666;
}

.time {
  font-size: 24rpx;
  color: #ccc;
}

.empty-tip {
  padding: 60rpx;
  text-align: center;
  color: #999;
  font-size: 26rpx;
}

.footer {
  background: #ffffff;
  padding: 20rpx 30rpx;
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.05);
}

.start-btn {
  height: 88rpx;
  background: #2561ef;
  border-radius: 44rpx;
  font-size: 32rpx;
  color: #ffffff;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  
  &:active {
    opacity: 0.9;
  }
}

.safe {
  height: env(safe-area-inset-bottom);
}
</style>
