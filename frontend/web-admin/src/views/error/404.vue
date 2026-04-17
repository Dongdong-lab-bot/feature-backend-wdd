<template>
  <div class="error-container">
    <div class="error-content">
      <h1>404</h1>
      <h3>抱歉，页面不存在</h3>
      <p>您访问的页面可能已被删除或不存在</p>
      <el-button type="primary" @click="goBack">返回上一页</el-button>
      <el-button @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.error-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f4f5;
}

.error-content {
  text-align: center;
}

.error-content h1 {
  font-size: 120px;
  color: #909399;
  margin: 0;
  line-height: 1;
}

.error-content h3 {
  font-size: 24px;
  color: #303133;
  margin: 20px 0 10px;
}

.error-content p {
  font-size: 14px;
  color: #909399;
  margin-bottom: 30px;
}

.error-content .el-button {
  margin: 0 8px;
}
</style>
