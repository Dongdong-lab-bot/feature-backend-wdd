<template>
  <view class="login-page">
    <view class="form">
      <input class="input" v-model="username" placeholder="用户名" />
      <input class="input" v-model="password" placeholder="密码" password />
      <button class="btn" @click="doLogin">登录</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { login } from '@/common/auth'

const username = ref('')
const password = ref('')

async function doLogin() {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请输入账号密码', icon: 'none' }); return
  }
  try {
    await login(username.value, password.value)
    uni.showToast({ title: '登录成功', icon: 'success' })
    if (uni.switchTab) uni.switchTab({ url: '/pages/executor/index/index' })
    else uni.reLaunch({ url: '/pages/executor/index/index' })
  } catch (e: any) {
    console.error('登录失败:', e)
    uni.showToast({ 
      title: e?.msg || e?.message || '登录失败，请检查网络和服务器配置', 
      icon: 'none' 
    })
  }
}
</script>

<style scoped>
.login-page { padding: 24rpx }
.form { display: flex; flex-direction: column; gap: 16rpx }
.input { height: 80rpx; border: 2rpx solid #e0e0e0; border-radius: 12rpx; padding: 0 24rpx }
.btn { height: 88rpx; border-radius: 44rpx; background: #2561EF; color: #fff; }
</style>