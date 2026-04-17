<template>
  <view class="page">
    <NavBar title="sop任务中心">
      <template #right>
        <view class="nav-right-btn" @click="handleSearch">
          <image class="nav-search-icon" src="/static/home/icon-search.svg" mode="aspectFit" />
        </view>
      </template>
    </NavBar>

    <view class="crumbs">
      <text class="crumb active" @click="handleCrumb('武岗县全县项目')">武岗县全县项目</text>
      <text class="crumb" @click="handleCrumb('城东片区')">&gt; 城东片区</text>
      <text class="crumb" @click="handleCrumb('高中学校')">&gt; 高中学校</text>
    </view>

    <view class="tabs">
      <view class="tab" :class="{ active: activeTab === 'pending' }" @click="setTab('pending')">
        <image class="tab-icon" src="/static/sop/icon-pending.svg" mode="aspectFit" />
        <text class="tab-text">未完成任务</text>
      </view>
      <view class="tab" :class="{ active: activeTab === 'done' }" @click="setTab('done')">
        <image class="tab-icon" src="/static/sop/icon-completed.svg" mode="aspectFit" />
        <text class="tab-text">已完成任务</text>
      </view>
    </view>

    <scroll-view class="body" scroll-y>
      <view class="card" v-for="item in list" :key="item.id" @click="handleOpen(item)">
        <view class="card-left">
          <view class="doc-wrap">
            <image class="doc-icon" src="/static/sop/icon-doc.svg" mode="aspectFit" />
          </view>
          <view class="card-info">
            <view class="card-title-row">
              <text class="card-title">{{ item.name }}</text>
              <view class="badge" :class="{ done: activeTab === 'done' }">
                <text class="badge-text" :class="{ done: activeTab === 'done' }">
                  {{ activeTab === 'pending' ? `还有${item.pendingCount}项任务未完成` : `已完成${item.doneCount || 0}项任务` }}
                </text>
              </view>
            </view>
            <text class="card-sub">{{ item.sub }}</text>
          </view>
        </view>
        <view class="more-wrap" @click.stop="handleMore(item)">
          <image class="more-icon" src="/static/sop/icon-more.svg" mode="aspectFit" />
        </view>
      </view>

      <view class="bottom-tip">没有更多数据了～</view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import NavBar from '../../components/NavBar/NavBar.vue'

type TabKey = 'pending' | 'done'

type SopItem = {
  id: string
  name: string
  sub: string
  pendingCount: number
  doneCount?: number
}

const activeTab = ref<TabKey>('pending')

const pendingList: SopItem[] = [
  { id: '1', name: '武岗实验中学', pendingCount: 3, sub: '食品安全员 于 2026-01-09 10:45 更新' },
  { id: '2', name: '武岗实验中学', pendingCount: 3, sub: '食品安全员 于 2026-01-09 10:45 更新' },
  { id: '3', name: '武岗实验中学', pendingCount: 3, sub: '食品安全员 于 2026-01-09 10:45 更新' },
  { id: '4', name: '武岗实验中学', pendingCount: 3, sub: '食品安全员 于 2026-01-09 10:45 更新' }
]

const doneList: SopItem[] = [
  { id: 'd1', name: '武岗实验中学', pendingCount: 0, doneCount: 3, sub: '食品安全员 于 2026-01-09 10:45 更新' },
  { id: 'd2', name: '武岗实验中学', pendingCount: 0, doneCount: 3, sub: '食品安全员 于 2026-01-09 10:45 更新' }
]

const list = computed(() => (activeTab.value === 'pending' ? pendingList : doneList))

const setTab = (tab: TabKey) => {
  activeTab.value = tab
}

const handleSearch = () => {
  uni.showToast({ title: '搜索开发中', icon: 'none' })
}

const handleCrumb = (name: string) => {
  uni.showToast({ title: name, icon: 'none' })
}

const handleOpen = (_item: SopItem) => {
  uni.navigateTo({
    url: `/pages/sop/single-canteen-sop?canteen=${encodeURIComponent(_item.name)}&tab=${activeTab.value}`
  })
}

const handleMore = (item: SopItem) => {
  const itemList = ['权限管理', '下载', '收藏', '移动至', '重命名', '删除']
  uni.showActionSheet({
    itemList,
    success: (res) => {
      const picked = itemList[res.tapIndex]
      if (picked === '删除') {
        uni.showModal({
          title: '',
          content: '确定要删除此文件吗？',
          confirmColor: '#2561EF',
          success: (r) => {
            if (r.confirm) {
              uni.showToast({ title: `已删除：${item.name}`, icon: 'none' })
            }
          }
        })
        return
      }
      uni.showToast({ title: `${picked}：${item.name}`, icon: 'none' })
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.nav-right-btn {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-search-icon {
  width: 36rpx;
  height: 36rpx;
}

.crumbs {
  background: #ffffff;
  padding: 12rpx 30rpx 18rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  box-sizing: border-box;
}

.crumb {
  font-size: 28rpx;
  color: #999999;
  font-weight: 600;
}

.crumb.active {
  color: #2561ef;
}

.tabs {
  background: #ffffff;
  padding: 10rpx 30rpx 18rpx;
  display: flex;
  justify-content: space-between;
}

.tab {
  width: 300rpx;
  height: 98rpx;
  border-radius: 16rpx;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
}

.tab-icon {
  width: 46rpx;
  height: 46rpx;
}

.tab-text {
  font-size: 26rpx;
  color: #333333;
  font-weight: 600;
}

.tab.active {
  background: #f7f9fb;
}

.body {
  flex: 1;
  min-height: 0;
  padding: 14rpx 24rpx 20rpx;
  box-sizing: border-box;
}

.card {
  height: 160rpx;
  background: #ffffff;
  border-radius: 16rpx;
  padding: 22rpx 18rpx 22rpx 22rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
  box-sizing: border-box;
}

.card-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.doc-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  background: #eff4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.doc-icon {
  width: 40rpx;
  height: 46rpx;
}

.card-info {
  margin-left: 18rpx;
  flex: 1;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.card-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #111111;
  max-width: 240rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  height: 40rpx;
  border-radius: 12rpx;
  padding: 0 14rpx;
  background: rgba(250, 116, 107, 0.12);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.badge-text {
  font-size: 24rpx;
  color: #fa746b;
  font-weight: 600;
}

.badge.done {
  background: rgba(61, 212, 167, 0.14);
}

.badge-text.done {
  color: #3dd4a7;
}

.card-sub {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #b3b3b3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more-wrap {
  width: 64rpx;
  height: 120rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.more-icon {
  width: 28rpx;
  height: 28rpx;
  opacity: 0.8;
}

.bottom-tip {
  padding: 26rpx 0 12rpx;
  text-align: center;
  font-size: 24rpx;
  color: #c2c2c2;
}
</style>
