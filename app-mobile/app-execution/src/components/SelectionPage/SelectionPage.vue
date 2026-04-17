<template>
  <view class="page">
    <NavBar :title="title" />

    <scroll-view class="body" scroll-y>
      <view class="search-wrap">
        <view class="search-box">
          <image class="search-icon" src="/static/monthly/icon-search-gray.svg" mode="aspectFit" />
          <input 
            class="search-input" 
            :value="keyword" 
            @input="onInput"
            :placeholder="placeholder" 
            placeholder-style="color: #CCCCCC" 
          />
        </view>
      </view>

      <view v-if="crumbs && crumbs.length" class="crumbs">
        <text 
          v-for="(crumb, index) in crumbs" 
          :key="index"
          class="crumb"
          :class="{ blue: index < crumbs.length - 1, gray: index === crumbs.length - 1 }"
        >
          {{ index > 0 ? '> ' : '' }}{{ crumb }}
        </text>
      </view>

      <view class="nearest">
        <text class="nearest-title">离你最近的项目：(选择后直接开始查看视频)</text>
        <view class="nearest-links">
          <text class="nearest-link" @click="emit('quickStart', { name: '武岗一中一食堂', dist: '58m' })">武岗一中一食堂（58m）</text>
          <text class="nearest-link" @click="emit('quickStart', { name: '武岗一中一食堂', dist: '3.6km' })">武岗一中一食堂（3.6km）</text>
        </view>
      </view>

      <view class="list" :class="listClass">
        <slot name="header-extra"></slot>
        <view v-if="items.length > 0">
          <view 
            v-for="(item, index) in items" 
            :key="item.id || index"
            class="list-item-wrapper"
            @click="onSelect(item)"
          >
            <slot name="item" :item="item" :index="index"></slot>
          </view>
        </view>
        <view v-else class="empty-tip">
          <text>暂无数据</text>
        </view>
      </view>
    </scroll-view>

    <view class="footer">
      <button 
        class="start-btn" 
        :disabled="buttonDisabled" 
        @click="emit('submit')"
      >
        {{ buttonText }}
      </button>
      <view class="safe"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import NavBar from '../NavBar/NavBar.vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入'
  },
  keyword: {
    type: String,
    default: ''
  },
  crumbs: {
    type: Array as PropType<string[]>,
    default: () => []
  },
  listClass: {
    type: String,
    default: ''
  },
  items: {
    type: Array as PropType<any[]>,
    default: () => []
  },
  buttonText: {
    type: String,
    default: '下一步'
  },
  buttonDisabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:keyword', 'select', 'submit', 'quickStart'])

const onInput = (e: any) => {
  emit('update:keyword', e.detail.value)
}

const onSelect = (item: any) => {
  emit('select', item)
}
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: rgba(242, 247, 251, 0.62);
  display: flex;
  flex-direction: column;
}

.body {
  flex: 1;
  min-height: 0;
}

.search-wrap {
  padding: 10rpx 30rpx 0;
}

.search-box {
  height: 80rpx;
  border-radius: 16rpx;
  border: 1px solid #f2f2f2;
  background: rgba(37, 97, 239, 0.04);
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
  padding: 20rpx 30rpx 0;
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

.nearest {
  padding: 24rpx 30rpx 0;
}

.nearest-title {
  font-size: 26rpx;
  color: #999999;
  margin-bottom: 16rpx;
  display: block;
}

.nearest-links {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.nearest-link {
  font-size: 26rpx;
  color: #2561ef;
}

.list {
  padding: 0;
}

.empty-tip {
  padding: 40rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
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
  
  &[disabled] {
    background: #cccccc;
    color: #ffffff;
  }
  
  &:active {
    opacity: 0.9;
  }
}

.safe {
  height: env(safe-area-inset-bottom);
}
</style>
