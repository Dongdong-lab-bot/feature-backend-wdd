<template>
  <view class="page-container">
    <!-- 顶部导航栏 -->
    <view class="custom-nav-bar">
      <view class="nav-content">
        <text class="page-title">武岗实验中学SOP</text>
        <view class="right-icons">
          <image src="/static/images/search.png" class="nav-icon" mode="aspectFit" />
          <image src="/static/images/more-dots.png" class="nav-icon" mode="aspectFit" />
        </view>
      </view>
    </view>

    <!-- 进度卡片 -->
    <view class="progress-section">
      <view class="progress-card">
        <view class="progress-fill" style="width: 90%"></view>
        <text class="progress-text">今日SOP已完成 18/20</text>
      </view>
    </view>

    <!-- 功能入口 -->
    <view class="function-grid">
      <view class="grid-item" @click="navigateTo('/pages/executor/sop/daily-control-form-submitted/task-list')">
        <view class="icon-wrapper blue">
          <image src="/static/home/icon-daily.svg" class="grid-icon-img" mode="aspectFit" />
        </view>
        <text class="grid-label">日管控提报</text>
      </view>
      <view class="grid-item" @click="navigateTo('/pages/executor/sop/weekly-inspection/weekly-inspection')">
        <view class="icon-wrapper pink">
          <image src="/static/home/icon-weekly.svg" class="grid-icon-img" mode="aspectFit" />
        </view>
        <text class="grid-label">周排查整改</text>
      </view>
      <view class="grid-item" @click="navigateTo('/pages/executor/sop/monthly-scheduling/monthly-scheduling')">
        <view class="icon-wrapper green">
          <image src="/static/home/icon-monthly.svg" class="grid-icon-img" mode="aspectFit" />
        </view>
        <text class="grid-label">月调度学习</text>
      </view>
      <view class="grid-item" @click="navigateTo('/pages/executor/sop/joint-inspection/joint-inspection')">
        <view class="icon-wrapper yellow">
          <image src="/static/home/icon-joint.svg" class="grid-icon-img" mode="aspectFit" />
        </view>
        <text class="grid-label">联合巡检整改</text>
      </view>
      <view class="grid-item" @click="navigateTo('/pages/executor/sop/video-inspection/video-inspection')">
        <view class="icon-wrapper purple">
          <image src="/static/mine/icon-video.svg" class="grid-icon-img" mode="aspectFit" />
        </view>
        <text class="grid-label">视频巡检</text>
      </view>
    </view>

    <!-- SOP列表 -->
    <scroll-view class="list-container" scroll-y="true">
      <view class="sop-item" v-for="(sop, index) in sopList" :key="index">
        <view class="item-left">
          <view class="file-icon">
            <image src="/static/sop/icon-doc.svg" class="file-icon-img" mode="aspectFit" />
          </view>
        </view>
        <view class="item-center">
          <text class="sop-title">{{ sop.title }}</text>
          <text class="sop-info">{{ sop.uploader }} 于 {{ sop.uploadTime }} 上传</text>
        </view>
        <view class="item-right">
          <view class="status-tag">
            <text class="status-text">{{ sop.statusText || '已完成' }}</text>
          </view>
          <view class="more-btn" @click.stop="showMoreActions(sop)">
            <image src="/static/sop/icon-more.svg" class="more-icon" mode="aspectFit" />
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      sopList: [
        {
          id: 1,
          title: '晨检记录表',
          status: 'completed',
          statusText: '已完成',
          uploader: '李凡凡',
          uploadTime: '2022-01-09 10:45'
        },
        {
          id: 2,
          title: '餐饮具消毒记录',
          status: 'completed',
          statusText: '已完成',
          uploader: '王小明',
          uploadTime: '2022-01-08 14:30'
        },
        {
          id: 3,
          title: '食品留样记录',
          status: 'draft',
          statusText: '草稿',
          uploader: '张三',
          uploadTime: '2022-01-07 09:15'
        },
        {
          id: 4,
          title: '陪餐记录',
          status: 'completed',
          statusText: '已完成',
          uploader: '李四',
          uploadTime: '2022-01-06 16:20'
        },
        {
          id: 5,
          title: '废弃物处置记录',
          status: 'review',
          statusText: '审核中',
          uploader: '赵五',
          uploadTime: '2022-01-05 11:10'
        }
      ]
    }
  },
  methods: {
    showMoreActions(sop) {
      uni.showActionSheet({
        itemList: ['编辑', '删除'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 编辑
            this.navigateTo(`/pages/executor/sop/edit?id=${sop.id}`)
          } else if (res.tapIndex === 1) {
            // 删除
            uni.showModal({
              title: '提示',
              content: '确定要删除该SOP吗？',
              success: (res) => {
                if (res.confirm) {
                  const index = this.sopList.findIndex(item => item.id === sop.id)
                  if (index > -1) {
                    this.sopList.splice(index, 1)
                  }
                }
              }
            })
          }
        }
      })
    },
    navigateTo(url) {
      uni.navigateTo({
        url: url,
        fail: (err) => {
          console.error('Navigation failed:', err)
          uni.showToast({
            title: '页面开发中',
            icon: 'none'
          })
        }
      })
    }
  }
}
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  background-color: #F5F7FA;
  display: flex;
  flex-direction: column;
}

.custom-nav-bar {
  background-color: #fff;
  padding: 44px 30rpx 20rpx 30rpx; /* Adjust top padding for status bar */
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.right-icons {
  display: flex;
  gap: 30rpx;
}

.nav-icon {
  width: 40rpx;
  height: 40rpx;
}

.progress-section {
  padding: 20rpx 30rpx;
  background-color: #fff;
}

.progress-card {
  height: 88rpx;
  background: #E6F7FF;
  border-radius: 16rpx;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(90deg, #00C6FF 0%, #007AFF 100%);
  z-index: 1;
  border-radius: 0 16rpx 16rpx 0;
}

.progress-text {
  position: relative;
  z-index: 2;
  font-size: 30rpx;
  font-weight: 500;
  color: #fff;
  text-shadow: 0 2rpx 4rpx rgba(0, 122, 255, 0.2);
}

.function-grid {
  display: flex;
  justify-content: space-between;
  padding: 30rpx 40rpx;
  background-color: #fff;
  margin-bottom: 20rpx;
}

.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20%;
}

.icon-wrapper {
  width: 100rpx;
  height: 100rpx;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
}

.icon-wrapper.blue {
  background-color: #E6F4FF;
}

.icon-wrapper.pink {
  background-color: #FFF0F0;
}

.icon-wrapper.green {
  background-color: #E6FFFB;
}

.icon-wrapper.yellow {
  background-color: #FFFBE6;
}

.icon-wrapper.purple {
  background-color: #F3E8FF;
}

.grid-icon-img {
  width: 52rpx;
  height: 52rpx;
}

.grid-label {
  font-size: 24rpx;
  color: #333;
}

.list-container {
  flex: 1;
  width: 100%; 
}

.sop-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 32rpx 40rpx;
  margin: 0 30rpx 24rpx 30rpx; 
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.02);
  box-sizing: border-box; 
}

.item-left {
  margin-right: 24rpx;
}

.file-icon {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F7F8FA;
  border-radius: 12rpx;
}

.file-icon-img {
  width: 48rpx;
  height: 48rpx;
}

.item-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-right: 20rpx;
}

.sop-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 12rpx;
  line-height: 1.4;
}

.sop-info {
  font-size: 24rpx;
  color: #999;
}

.item-right {
  display: flex;
  align-items: center;
}

.more-btn {
  width: 40rpx;
  height: 40rpx;
  margin-left: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.more-icon {
  width: 100%;
  height: 100%;
}

.status-tag {
  background-color: #E6FFEA;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
}

.status-text {
  font-size: 24rpx;
  color: #00B578;
}
</style>