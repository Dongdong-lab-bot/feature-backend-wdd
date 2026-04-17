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
      <text class="debug-link" @click="handleDebug">接口配置</text>
      <text class="register-link" @click="handleRegister">注册新用户</text>
    </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { authApi } from '@/api'

type LoginMode = 'phone' | 'password';

const loginMode = ref<LoginMode>('phone');
const isPrivacyChecked = ref(false);
const countdown = ref(0);
let timer: any = null;

const phoneForm = reactive({
  phone: '',
  code: '',
  bizNo: ''
});

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
  phoneForm.bizNo = '';
  pwdForm.account = '';
  pwdForm.password = '';
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
    const data = await authApi.sendSms({
      mobile: phoneForm.phone,
      scene: 'LOGIN'
    })
    phoneForm.bizNo = data.bizNo
    countdown.value = data.retryAfterSeconds > 0 ? data.retryAfterSeconds : 60
    uni.showToast({ title: '验证码已发送', icon: 'none' });
    timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) {
        clearInterval(timer);
      }
    }, 1000);
  } catch {}
};

// 隐私协议勾选
const togglePrivacy = () => {
  isPrivacyChecked.value = !isPrivacyChecked.value;
};

const syncLoginContext = async () => {
  const [meResult, permissionsResult] = await Promise.allSettled([
    authApi.getCurrentUser(),
    authApi.getPermissions()
  ]);

  if (meResult.status === 'fulfilled') {
    uni.setStorageSync('currentUser', meResult.value);
  }

  if (permissionsResult.status === 'fulfilled') {
    uni.setStorageSync('permissions', permissionsResult.value);
  }
};

// 登录提交
const handleLogin = async () => {
  if (!isPrivacyChecked.value) {
    uni.showToast({ title: '请先同意用户隐私政策', icon: 'none' });
    return;
  }

  if (loginMode.value === 'phone') {
    if (!phoneForm.phone || !phoneForm.code) {
      uni.showToast({ title: '请填写完整信息', icon: 'none' });
      return;
    }
    if (!phoneForm.bizNo) {
      uni.showToast({ title: '请先获取验证码', icon: 'none' });
      return;
    }
    uni.showLoading({ title: '登录中...' })
    try {
      await authApi.loginBySms({
        mobile: phoneForm.phone,
        code: phoneForm.code,
        bizNo: phoneForm.bizNo
      })
      await syncLoginContext()
      uni.hideLoading()
      uni.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1200,
        success: () => {
          setTimeout(() => {
            uni.switchTab({ url: '/pages/index/index' });
          }, 1200);
        }
      });
    } catch {
      uni.hideLoading()
    }
    return
  } else {
    if (!pwdForm.account || !pwdForm.password) {
      uni.showToast({ title: '请填写完整信息', icon: 'none' });
      return;
    }
  }

  uni.showLoading({ title: '登录中...' })
  try {
    await authApi.login({
      username: pwdForm.account,
      password: pwdForm.password
    })
    await syncLoginContext()
    uni.hideLoading()
    uni.showToast({
      title: '登录成功',
      icon: 'success',
      duration: 1200,
      success: () => {
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' });
        }, 1200);
      }
    });
  } catch {
    uni.hideLoading()
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
  height: 24rpx;
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
  margin-bottom: 60rpx;
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
  background-color: #fff;
  transition: border-color 0.3s;
  
  &:focus-within {
    border-color: #2561EF;
  }
}

.country-code {
  font-size: 30rpx;
  color: #666;
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
  font-size: 30rpx;
  height: 100%;
  color: #333;
}

.code-btn {
  font-size: 28rpx;
  color: #2561EF;
  font-weight: 500;
  
  &.disabled {
    color: #999999;
  }
}

.extra-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20rpx;
  padding: 0 10rpx;
}

.action-text {
  font-size: 26rpx;
  color: #999;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background-color: #2561EF;
  border-radius: 16rpx;
  font-size: 32rpx;
  margin-top: 40rpx;
  margin-bottom: 40rpx;
  box-shadow: 0 4rpx 12rpx rgba(37, 97, 239, 0.3);
  
  &:active {
    opacity: 0.9;
  }
}

.privacy-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 30rpx;
  margin-top: 20rpx;
}

.forget-inline {
  margin-left: auto;
  font-size: 26rpx;
  color: #999999;
}

.checkbox-icon {
  width: 32rpx;
  height: 32rpx;
  margin-right: 12rpx;
}

.privacy-text {
  font-size: 24rpx;
  display: flex;
  align-items: center;
  
  .gray {
    color: #999999;
  }
  
  .blue {
    color: #2561EF;
  }
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 40rpx;
  padding: 0 10rpx;
}

.switch-mode, .register-link {
  font-size: 28rpx;
  color: #2561EF;
}

.debug-link {
  font-size: 28rpx;
  color: #7f8aa0;
}
</style>
