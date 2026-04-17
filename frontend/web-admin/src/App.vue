<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

onMounted(() => {
  // 应用启动时，尝试从本地存储恢复用户信息
  userStore.initUserInfo()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
}

/* 全局字体层次规范 */
.text-primary {
  color: #303133;
  font-weight: 600;
}

.text-regular {
  color: #606266;
  font-weight: 400;
}

.text-secondary {
  color: #909399;
  font-weight: 400;
}

/* 标题字体规范 */
h1, .h1 {
  font-size: 18px;
  font-weight: 600;
  color: #222;
  letter-spacing: 0.5px;
  line-height: 1.4;
}

h2, .h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  letter-spacing: 0.3px;
  line-height: 1.4;
}

h3, .h3 {
  font-size: 14px;
  font-weight: 600;
  color: #4A8BFE;
  line-height: 1.5;
}

/* Element Plus 组件字体优化 */
:deep(.el-table) {
  font-size: 13px;
  line-height: 1.6;
}

:deep(.el-table th) {
  font-weight: 600;
  color: #303133;
}

:deep(.el-table td) {
  color: #606266;
}

:deep(.el-button) {
  font-weight: 500;
  letter-spacing: 0.3px;
}
</style>
