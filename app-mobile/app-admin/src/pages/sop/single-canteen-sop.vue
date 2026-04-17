<template>
  <view class="page">
    <NavBar :title="headerTitle">
      <template #right>
        <view class="nav-right-btn" @click="handleSearch">
          <image class="nav-search-icon" src="/static/home/icon-search.svg" mode="aspectFit" />
        </view>
      </template>
    </NavBar>

    <scroll-view class="body" scroll-y>
      <view class="card" v-for="item in sopList" :key="item.id" @click="handleOpen(item)">
        <view class="card-left">
          <view class="doc-wrap">
            <image class="doc-icon" src="/static/sop/icon-doc.svg" mode="aspectFit" />
          </view>
          <view class="card-info">
            <view class="card-title-row">
              <text class="card-title">{{ item.title }}</text>
              <view class="tag">
                <text class="tag-text">{{ item.statusText }}</text>
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
      <view class="bottom-space"></view>
    </scroll-view>

    <view class="fab" @click="handleAdd">
      <image class="fab-icon" src="/static/sop/icon-add.svg" mode="aspectFit" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import NavBar from '../../components/NavBar/NavBar.vue'

type SopDocItem = {
  id: string
  title: string
  statusText: string
  sub: string
}

const canteenName = ref('武岗实验中学')

onLoad((options: any) => {
  const name = typeof options?.canteen === 'string' ? options.canteen : ''
  if (name) {
    try {
      canteenName.value = decodeURIComponent(name)
    } catch {
      canteenName.value = name
    }
  }
})

const headerTitle = computed(() => `${canteenName.value}SOP`)

const sopList = ref<SopDocItem[]>([
  { id: '1', title: '留样台账记录', statusText: '已完成', sub: '李凡凡 于 2022-01-09 10:45 上传' },
  { id: '2', title: '留样台账记录', statusText: '已完成', sub: '李凡凡 于 2022-01-09 10:45 上传' },
  { id: '3', title: '留样台账记录', statusText: '已完成', sub: '李凡凡 于 2022-01-09 10:45 上传' },
  { id: '4', title: '留样台账记录', statusText: '已完成', sub: '李凡凡 于 2022-01-09 10:45 上传' },
  { id: '5', title: '留样台账记录', statusText: '已完成', sub: '李凡凡 于 2022-01-09 10:45 上传' }
])

const handleSearch = () => {
  uni.showToast({ title: '搜索开发中', icon: 'none' })
}

const handleOpen = (_item: SopDocItem) => {
  uni.showToast({ title: '详情开发中', icon: 'none' })
}

const handleMore = (item: SopDocItem) => {
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
              uni.showToast({ title: `已删除：${item.title}`, icon: 'none' })
            }
          }
        })
        return
      }
      uni.showToast({ title: `${picked}：${item.title}`, icon: 'none' })
    }
  })
}

const handleAdd = () => {
  uni.showActionSheet({
    itemList: ['上传文件', '新建文件夹'],
    success: (res) => {
      const picked = res.tapIndex === 0 ? '上传文件' : '新建文件夹'
      uni.showToast({ title: `${picked}开发中`, icon: 'none' })
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
  max-width: 260rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag {
  height: 40rpx;
  border-radius: 12rpx;
  padding: 0 14rpx;
  background: rgba(61, 212, 167, 0.14);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.tag-text {
  font-size: 24rpx;
  color: #3dd4a7;
  font-weight: 600;
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

.bottom-space {
  height: calc(120rpx + env(safe-area-inset-bottom));
}

.fab {
  position: fixed;
  right: 40rpx;
  bottom: calc(40rpx + env(safe-area-inset-bottom));
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  background: #2561ef;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10rpx 30rpx rgba(37, 97, 239, 0.35);
}

.fab-icon {
  width: 44rpx;
  height: 44rpx;
}
</style>
