<template>
  <BaseLogin
    title="欢迎登录食安平台执行端"
    :loading="loading"
    @login="handleLogin"
    @register="handleRegister"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import BaseLogin from '@common/views/login/BaseLogin.vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const handleLogin = async (formData: any) => {
  if (!formData.username || !formData.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  
  loading.value = true
  try {
    await userStore.login({
      username: formData.username,
      password: formData.password,
      app_client: 'exec_web'
    })
    
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error: any) {
    console.error(error)
    // 错误处理已经在 request.ts 中统一处理了，这里只需要处理特定逻辑
    // 如果是 403，提示特定信息
    if (error.response?.status === 403) {
      ElMessage.error('无权访问执行端系统，请确认账号类型')
    }
  } finally {
    loading.value = false
  }
}

const handleRegister = () => {
  ElMessage.info('注册功能开发中...')
}
</script>
