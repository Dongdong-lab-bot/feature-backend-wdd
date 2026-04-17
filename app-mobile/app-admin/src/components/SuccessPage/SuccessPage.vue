<template>
  <view class="page">
    <view class="content">
      <view class="success-icon-wrap">
        <icon type="success" size="70" color="#38d49a" />
      </view>
      <view class="title">{{ title }}</view>
      <view class="subtitle" v-for="(line, index) in subtitleLines" :key="index">
        {{ line }}
      </view>
      
      <button class="back-btn" @click="goBack">{{ buttonText }}</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: [String, Array],
    default: () => []
  },
  buttonText: {
    type: String,
    default: '返回'
  },
  backDelta: {
    type: Number,
    default: 2
  }
})

const subtitleLines = computed(() => {
  if (Array.isArray(props.subtitle)) {
    return props.subtitle
  }
  if (typeof props.subtitle === 'string' && props.subtitle) {
    return [props.subtitle]
  }
  return []
})

const emit = defineEmits(['back'])

const goBack = () => {
  // If parent wants to handle back, it can listen to @back
  // Otherwise we provide a default fallback
  emit('back')
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: #ffffff;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 180rpx;
}

.success-icon-wrap {
  margin-bottom: 40rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.title {
  font-size: 40rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 30rpx;
}

.subtitle {
  font-size: 28rpx;
  color: #999;
  line-height: 1.5;
}

.back-btn {
  margin-top: 80rpx;
  width: 600rpx;
  height: 88rpx;
  line-height: 88rpx;
  background: #ffffff;
  color: #2563eb;
  border: 1rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 32rpx;
  
  &:active {
    background: #f5f5f5;
  }
  
  &::after {
    border: none;
  }
}
</style>
