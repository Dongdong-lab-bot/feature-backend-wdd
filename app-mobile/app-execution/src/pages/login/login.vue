<template>
  <view class="container">
    <view class="back-btn" @click="handleBack">
      <image src="/static/login/back-arrow.svg" mode="widthFix" class="back-icon"></image>
    </view>
    <view class="login-main">

    <view class="header">
      <text class="title">{{ loginMode === 'phone' ? '手机验证码登录' : '账号密码登录' }}</text>
    </view>

    <view v-if="loginMode === 'phone'" class="form-container">
      <view class="input-group">
        <view class="input-wrapper">
          <text class="country-code">+86</text>
          <view class="divider"></view>
          <input class="input" type="number" v-model="phoneForm.phone" placeholder="请输入手机号" maxlength="11" />
        </view>
      </view>
      <view class="input-group">
        <view class="input-wrapper">
          <input class="input" type="number" v-model="phoneForm.code" placeholder="请输入验证码" maxlength="6" />
          <view class="code-btn" :class="{ 'disabled': countdown > 0 }" @click="handleGetCode">
            {{ countdown > 0 ? `${countdown}s后重试` : '获取验证码' }}
          </view>
        </view>
      </view>
    </view>

    <view v-else class="form-container">
      <view class="input-group">
        <view class="input-wrapper">
          <input class="input" type="text" v-model="pwdForm.account" placeholder="请输入账号/手机号" />
        </view>
      </view>
      <view class="input-group">
        <view class="input-wrapper">
          <input class="input" type="password" v-model="pwdForm.password" placeholder="请输入密码" />
        </view>
      </view>
    </view>

    <view class="privacy-container" @click="togglePrivacy">
      <image
        :src="isPrivacyChecked ? '/static/login/checkbox-checked.svg' : '/static/login/checkbox-unchecked.svg'" 
        class="checkbox-icon"
      ></image>
      <view class="privacy-text">
        <text class="gray">我已阅读并同意</text>
        <text class="blue" @click.stop="handlePrivacyLink">《用户隐私政策》</text>
      </view>
      <text v-if="loginMode === 'password'" class="forget-inline" @click.stop="handleForgetPwd">忘记密码？</text>
    </view>

    <button class="submit-btn" @click="handleLogin">登录</button>

    <view class="footer-actions">
      <text class="switch-mode" @click="toggleMode">{{ loginMode === 'phone' ? '账号密码登录' : '手机验证码登录' }}</text>
      <text class="debug-link" @click="handleDebug">环境配置</text>
      <text class="register-link" @click="handleRegister">注册新用户</text>
    </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { login, loginBySms, sendSmsCode } from '@/common/auth';

type LoginMode = 'phone' | 'password';

const loginMode = ref<LoginMode>('phone');
const isPrivacyChecked = ref(false);

const phoneForm = reactive({
  phone: '',
  code: '',
  bizNo: ''
});

const countdown = ref(0);
let timer: number | null = null;

const pwdForm = reactive({
  account: '',
  password: ''
});

// 切换登录模式
const toggleMode = () => {
  loginMode.value = loginMode.value === 'phone' ? 'password' : 'phone';
  // 清空表单
  phoneForm.phone = '';
  phoneForm.code = '';
  pwdForm.account = '';
  pwdForm.password = '';
};

// 隐私协议勾选
const togglePrivacy = () => {
  isPrivacyChecked.value = !isPrivacyChecked.value;
};

// 获取验证码
const handleGetCode = async () => {
  if (countdown.value > 0) return;

  if (!phoneForm.phone) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }

  if (!/^1[3-9]\d{9}$/.test(phoneForm.phone)) {
    uni.showToast({ title: '手机号格式错误', icon: 'none' });
    return;
  }

  try {
    const res: any = await sendSmsCode(phoneForm.phone, 'LOGIN');
    phoneForm.bizNo = res?.bizNo || '';
    countdown.value = 60;
    uni.showToast({ title: '验证码已发送', icon: 'none' });

    timer = setInterval(() => {
      countdown.value -= 1;
      if (countdown.value <= 0 && timer) {
        clearInterval(timer);
        timer = null;
      }
    }, 1000) as unknown as number;
  } catch (error) {
    uni.showToast({ title: '发送失败', icon: 'none' });
  }
};

// 登录提交
const handleLogin = async () => {
  if (!isPrivacyChecked.value) {
    uni.showToast({ title: '请先同意用户隐私政策', icon: 'none' });
    return;
  }

  try {
    if (loginMode.value === 'phone') {
      if (!phoneForm.phone || !phoneForm.code) {
        uni.showToast({ title: '请填写完整信息', icon: 'none' });
        return;
      }
      await loginBySms(phoneForm.phone, phoneForm.code, phoneForm.bizNo || '');
    } else {
      if (!pwdForm.account || !pwdForm.password) {
        uni.showToast({ title: '请填写完整信息', icon: 'none' });
        return;
      }
      await login(pwdForm.account, pwdForm.password);
    }

    uni.showToast({ title: '登录成功', icon: 'success' });
    setTimeout(() => {
      uni.switchTab({ url: '/pages/executor/index/index' });
    }, 1500);
  } catch (error: any) {
    console.error('登录失败:', error);
    uni.showToast({ 
      title: error?.msg || error?.message || '登录失败，请重试', 
      icon: 'none' 
    });
  }
};

const handleBack = () => {
  uni.navigateBack();
};

const handleRegister = () => {
  uni.navigateTo({ url: '/pages/login/register' });
};

const handleDebug = () => {
  uni.navigateTo({ url: '/pages/common/debug' });
};

const handleForgetPwd = () => {
  uni.navigateTo({ url: '/pages/login/forget-password' });
};

const handlePrivacyLink = () => {
  uni.showToast({ title: '查看隐私政策', icon: 'none' });
};
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #ffffff;
  padding: 0 30rpx;
  box-sizing: border-box;
  position: relative;
}

.back-btn {
  position: absolute;
  top: 52rpx;
  top: calc(var(--status-bar-height) + 12rpx);
  left: 10rpx;
  width: 44rpx;
  height: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.back-icon {
  width: 24rpx;
  height: auto;
}

.login-main {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 80rpx;
}

.title {
  font-size: 48rpx;
  font-weight: 500;
  color: #000;
}

.form-container {
  margin-bottom: 40rpx;
}

.input-group {
  margin-bottom: 30rpx;
}

.input-wrapper {
  display: flex;
  align-items: center;
  height: 88rpx;
  border: 1px solid #E4E4E4;
  border-radius: 16rpx;
  padding: 0 30rpx;
  background-color: #ffffff;

  &:focus-within {
    border-color: #2561EF;
  }
}

.country-code {
  font-size: 30rpx;
  color: #666666;
  margin-right: 20rpx;
}

.divider {
  width: 1rpx;
  height: 30rpx;
  background-color: #E4E4E4;
  margin-right: 20rpx;
}

.input {
  flex: 1;
  height: 100%;
  font-size: 30rpx;
  color: #333333;
}

.code-btn {
  font-size: 28rpx;
  color: #2561EF;
  font-weight: 500;
}

.code-btn.disabled {
  color: #999999;
}

.privacy-container {
  display: flex;
  align-items: center;
  margin-bottom: 60rpx;
  font-size: 26rpx;
}

.checkbox-icon {
  width: 32rpx;
  height: 32rpx;
  margin-right: 12rpx;
}

.privacy-text {
  flex: 1;
  display: flex;
  align-items: center;
}

.gray {
  color: #999999;
}

.blue {
  color: #2561EF;
}

.forget-inline {
  color: #666666;
  margin-left: auto;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 16rpx;
  background-color: #2561EF;
  color: #ffffff;
  font-size: 32rpx;
  box-shadow: 0 4rpx 12rpx rgba(37, 97, 239, 0.3);
  margin-bottom: 40rpx;
}

.submit-btn:active {
  opacity: 0.9;
}

.footer-actions {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 28rpx;
}

.switch-mode {
  color: #666666;
  padding-right: 20rpx;
  border-right: 1px solid #E4E4E4;
}

.debug-link {
  color: #666666;
  padding: 0 20rpx;
  border-right: 1px solid #E4E4E4;
}

.register-link {
  color: #2561EF;
  padding-left: 20rpx;
}
</style>
