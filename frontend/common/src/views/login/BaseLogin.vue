<template>
  <div class="login-container">
    <div class="login-content">
      <div class="system-title">{{ title }}</div>
      
      <div class="login-box">
        <div class="login-header">
          <span>登录</span>
        </div>
        
        <el-form :model="form" class="login-form" @submit.prevent="handleSubmit">
          <el-form-item>
            <el-input 
              v-model="form.username" 
              placeholder="请输入账号" 
              prefix-icon="User"
              size="large"
            />
          </el-form-item>
          
          <el-form-item>
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="请输入密码" 
              prefix-icon="Lock"
              show-password
              size="large"
            />
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="form.rememberMe">记住密码</el-checkbox>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              native-type="submit"
              :loading="loading" 
              class="login-btn"
              size="large"
            >
              登录
            </el-button>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              plain 
              @click="$emit('register')" 
              class="register-btn"
              size="large"
            >
              新用户注册
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'

interface Props {
  title?: string
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  title: '欢迎登录食安平台',
  loading: false
})

const emit = defineEmits(['login', 'register'])

const form = reactive({
  username: 'admin',
  password: '123',
  rememberMe: false
})

const handleSubmit = () => {
  emit('login', { ...form })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #409EFF;
  background-image: linear-gradient(to bottom right, #409EFF, #79bbff);
}

.login-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.system-title {
  font-size: 28px;
  font-weight: 500;
  color: #ffffff;
  letter-spacing: 1px;
  margin-bottom: 10px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.login-box {
  width: 400px;
  background: #ffffff;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.login-header {
  margin-bottom: 30px;
  text-align: left;
}

.login-header span {
  font-size: 24px;
  color: #409EFF;
  font-weight: 500;
}

.login-form .el-input {
  --el-input-height: 45px;
}

.login-btn {
  width: 100%;
  margin-bottom: 20px;
  background: #409EFF; /* Bright blue */
  border-color: #409EFF;
  color: #fff;
  transition: all 0.3s;
  font-size: 16px;
  letter-spacing: 4px;
  height: 45px;
}

.login-btn:hover {
  background: #66b1ff;
  border-color: #66b1ff;
  transform: translateY(-2px); /* Click/Hover animation */
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

.register-btn {
  width: 100%;
  font-size: 16px;
  height: 45px;
  background-color: #d9ecff;
  border-color: #d9ecff;
  color: #409EFF;
}

.register-btn:hover {
  background-color: #c6e2ff;
  border-color: #c6e2ff;
}
</style>
