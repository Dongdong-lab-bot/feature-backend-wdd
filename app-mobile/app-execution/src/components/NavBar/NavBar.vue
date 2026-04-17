<template>
  <view class="nav-bar-wrapper">
    <!-- 固定定位时的占位符 -->
    <view v-if="fixed" class="nav-placeholder" :style="{ height: navBarHeight }"></view>
    
    <!-- 导航栏主体 -->
    <view 
      class="nav-bar" 
      :class="{ 'is-fixed': fixed }"
      :style="{ background: background, color: textColor }"
    >
      <view class="status-bar"></view>
      <view class="nav-content">
        <!-- 左侧区域 -->
        <view class="left" @click="handleBack">
          <image 
            v-if="showBack" 
            class="back-icon" 
            :src="backIconSrc" 
            mode="aspectFit" 
          />
          <slot name="left"></slot>
        </view>
        
        <!-- 中间标题 -->
        <view class="center">
          <text class="title" :style="{ color: textColor }">{{ title }}</text>
          <slot name="center"></slot>
        </view>
        
        <!-- 右侧区域 -->
        <view class="right">
          <slot name="right"></slot>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  showBack: {
    type: Boolean,
    default: true
  },
  background: {
    type: String,
    default: '#ffffff'
  },
  textColor: {
    type: String,
    default: '#111111'
  },
  fixed: {
    type: Boolean,
    default: false
  },
  // 自定义返回图标路径，如果传入则使用传入的，否则根据 textColor 自动判断（这里简单处理，默认黑色箭头）
  backIcon: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['back'])

// 计算属性：根据文字颜色判断是否需要白色箭头（这里仅做简单演示，实际项目可能需要更多图标资源）
const backIconSrc = computed(() => {
  if (props.backIcon) return props.backIcon
  // 如果背景是深色或文字是白色，可能需要白色箭头，这里默认统一用黑色箭头，
  // 实际项目中可以根据 props.textColor === '#ffffff' 来切换
  return '/static/login/back-arrow.svg'
})

const navBarHeight = 'calc(var(--status-bar-height) + 88rpx)'

const handleBack = () => {
  if (props.showBack) {
    emit('back')
    const pages = getCurrentPages()
    if (pages.length > 1) {
      uni.navigateBack()
    } else {
      // Fallback to home if no history
      uni.switchTab({ url: '/pages/executor/index/index' }).catch(() => {
        uni.reLaunch({ url: '/pages/executor/index/index' })
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.nav-bar-wrapper {
  /* 使得组件可以作为普通流元素存在 */
}

.nav-bar {
  width: 100%;
  box-sizing: border-box;
  z-index: 999;
}

.is-fixed {
  position: fixed;
  top: 0;
  left: 0;
}

.status-bar {
  height: var(--status-bar-height);
  width: 100%;
}

.nav-content {
  height: 88rpx;
  padding: 0 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
}

.left, .right {
  width: 88rpx;
  height: 100%;
  display: flex;
  align-items: center;
}

.right {
  justify-content: flex-end;
}

.center {
  flex: 1;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title {
  font-size: 36rpx;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.back-icon {
  width: 40rpx;
  height: 40rpx;
}
</style>
