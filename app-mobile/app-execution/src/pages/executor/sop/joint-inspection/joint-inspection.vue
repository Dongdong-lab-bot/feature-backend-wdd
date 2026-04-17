<template>
  <view class="page-container">
    <!-- 搜索框 -->
    <view class="search-container">
      <view class="search-input-wrapper">
        <text class="search-icon">🔍</text>
        <input
          v-model="searchText"
          placeholder="请输入"
          class="search-input"
        />
      </view>
    </view>

    <!-- 面包屑导航 -->
    <view class="breadcrumbs">
      <text class="crumb active">武岗县全县项目</text>
      <text class="separator">&gt;</text>
      <text class="crumb active">城东片区</text>
      <text class="separator">&gt;</text>
      <text class="crumb">高中学校</text>
    </view>

    <!-- 标签页 -->
    <view class="tab-container">
      <view
        v-for="(tab, index) in tabs"
        :key="index"
        :class="['tab-item', { active: activeTab === index }]"
        @click="switchTab(index)"
      >
        <text :class="['tab-text', { active: activeTab === index }]">{{ tab.label }}</text>
      </view>
    </view>

    <!-- 巡检记录列表 -->
    <scroll-view class="list-container" scroll-y="true">
      <view
        v-for="(item, index) in filteredList"
        :key="index"
        class="list-item"
        @click="onItemClick(item)"
      >
        <view class="item-left-border"></view>
        <view class="item-content">
          <view class="item-header">
            <text class="inspection-name">{{ item.inspectionName }}</text>
            <view class="item-status-wrapper">
              <text class="progress-text">{{ item.progress }}/25</text>
              <text :class="['status-text', item.statusClass]">{{ item.statusText }}</text>
            </view>
          </view>

          <view class="item-footer">
            <view class="submitter-info">
              <view class="avatar-placeholder">👤</view>
              <text class="submitter-name">{{ item.submitter }}</text>
            </view>
            <text class="submit-time">{{ item.submitTime }}</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部按钮 -->
    <view class="bottom-action">
      <button class="start-btn" @click="startNewInspection">开始新联合巡检</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchJointTaskList } from '@/common/joint-inspection'

const searchText = ref('')
const activeTab = ref(0)

const tabs = ref([
  { key: 'pending', label: '待整改' },
  { key: 'completed', label: '已完成' }
])

const inspectionList = ref<any[]>([])
const loading = ref(false)

const loadJointTasks = async () => {
  loading.value = true
  try {
    const currentTab = tabs.value[activeTab.value]
    const status = currentTab?.key === 'pending' ? 'REJECTED' : 'COMPLETED'
    const res: any = await fetchJointTaskList({
      keyword: searchText.value || undefined,
      status: status,
      page: 1,
      pageSize: 50
    })
    const list = Array.isArray(res?.list) ? res.list : []
    inspectionList.value = list.map((item: any) => {
      const isCompleted = item.status === 'COMPLETED'
      return {
        id: item.task_id || item.id,
        inspectionName: item.template_name || item.canteen_name || '-',
        progress: item.total_score ?? 0,
        submitter: item.submitter_name || item.inspector_name || item.principal || '',
        submitTime: item.submission_date || item.business_date || '',
        status: isCompleted ? 'completed' : 'pending',
        statusText: isCompleted ? '已完成' : '待整改',
        statusClass: isCompleted ? 'completed' : 'pending'
      }
    })
  } catch (e) {
    uni.showToast({
      title: '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

onLoad(() => {
  loadJointTasks()
})

watch([searchText, activeTab], () => {
  loadJointTasks()
})

const filteredList = computed(() => {
  let list = inspectionList.value

  if (searchText.value) {
    list = list.filter(item =>
      item.inspectionName?.includes(searchText.value) ||
      item.submitter?.includes(searchText.value)
    )
  }

  const currentTab = tabs.value[activeTab.value]
  if (currentTab?.key === 'pending') {
    list = list.filter(item => item.status === 'pending')
  } else if (currentTab?.key === 'completed') {
    list = list.filter(item => item.status === 'completed')
  }

  return list
})

const switchTab = (index: number) => {
  if (activeTab.value !== index) {
    activeTab.value = index
  }
}

const onItemClick = (item: any) => {
  if (item.status === 'pending') {
    uni.navigateTo({
      url: `/pages/executor/sop/joint-inspection/joint-inspection-rectification/joint-inspection-rectification?id=${item.id}`
    })
  } else {
    uni.navigateTo({
      url: `/pages/executor/sop/joint-inspection/joint-inspection-completed?id=${item.id}`
    })
  }
}

const startNewInspection = () => {
  uni.showToast({
    title: '开始新联合巡检',
    icon: 'none'
  })
}
</script>

<style scoped lang="scss">
.page-container {
  min-height: 100vh;
  background-color: #F5F7FA;
  display: flex;
  flex-direction: column;
}

.search-container {
  padding: 20rpx 30rpx;
  background-color: #fff;
}

.search-input-wrapper {
  background-color: #F5F7FA;
  border-radius: 40rpx;
  padding: 0 30rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
}

.search-icon {
  font-size: 28rpx;
  color: #999;
  margin-right: 16rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.breadcrumbs {
  padding: 0 30rpx 20rpx;
  background-color: #fff;
  display: flex;
  align-items: center;
  font-size: 26rpx;
}

.crumb {
  color: #999;
}

.crumb.active {
  color: #2561ef;
}

.separator {
  color: #ccc;
  margin: 0 10rpx;
}

.tab-container {
  display: flex;
  background-color: #fff;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
  position: relative;
}

.tab-text {
  font-size: 30rpx;
  color: #999;
}

.tab-text.active {
  color: #333;
  font-weight: 500;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60rpx;
  height: 4rpx;
  background-color: #333;
  border-radius: 4rpx;
}

.list-container {
  flex: 1;
  padding: 24rpx 30rpx;
  box-sizing: border-box;
}

.list-item {
  background-color: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  display: flex;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.02);
}

.item-left-border {
  width: 8rpx;
  background-color: #F5A623; /* Yellow for pending */
  flex-shrink: 0;
}

.item-content {
  flex: 1;
  padding: 30rpx 24rpx;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
}

.inspection-name {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  flex: 1;
}

.item-status-wrapper {
  display: flex;
  align-items: center;
}

.progress-text {
  font-size: 32rpx;
  color: #999;
  margin-right: 16rpx;
}

.status-text {
  font-size: 26rpx;
}

.status-text.pending {
  color: #F56C6C;
}

.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submitter-info {
  display: flex;
  align-items: center;
}

.avatar-placeholder {
  width: 40rpx;
  height: 40rpx;
  background-color: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  margin-right: 12rpx;
}

.submitter-name {
  font-size: 26rpx;
  color: #666;
}

.submit-time {
  font-size: 24rpx;
  color: #999;
}

.bottom-action {
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background-color: #F5F7FA;
}

.start-btn {
  background-color: #2561EF;
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.start-btn::after {
  border: none;
}
</style>
