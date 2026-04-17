<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>智慧食安监管平台</h2>
        <p>监管端管理系统</p>
      </div>
      <el-form ref="formRef" :model="formData" :rules="rules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'
import { REG_REFRESH_TOKEN_KEY } from '@/utils/auth-storage'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive({
  username: 'admin',
  password: 'admin123'
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await axios.post('/api/auth/login', {
        username: formData.username,
        password: formData.password,
        app_client: 'reg_app'
      })
      const { data } = res.data
      if (!data?.accessToken) {
        ElMessage.error('登录失败，请检查账号密码')
        return
      }
      const user = {
        id: String(data.userInfo.id),
        username: formData.username,
        nickname: formData.username,
        permissions: ['*:*:*'],
        tenantId: String(data.userInfo.tenantId)
      }
      userStore.login(data.accessToken, user)
      localStorage.setItem(REG_REFRESH_TOKEN_KEY, data.refreshToken)
      ElMessage.success('登录成功')
      router.push('/')
    } catch (err: any) {
      const msg = err.response?.data?.msg || '账号或密码错误'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #5B9DFF 0%, #4A8FFF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}
</style>
