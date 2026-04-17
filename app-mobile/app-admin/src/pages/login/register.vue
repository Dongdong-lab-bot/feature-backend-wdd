<template>
  <view class="container">
    <view class="back-btn" @click="handleBack">
      <image src="/static/login/back-arrow.svg" mode="widthFix" class="back-icon"></image>
    </view>

    <view class="register-main">
      <view class="header">
        <text class="title">注册账号</text>
      </view>

      <view class="form-container">
        <view class="input-group">
          <view class="input-wrapper">
            <text class="country-code">+86</text>
            <view class="divider"></view>
            <input class="input" type="number" v-model="form.phone" placeholder="请输入手机号码" maxlength="11" />
          </view>
        </view>

        <view class="input-group">
          <view class="input-wrapper">
            <input class="input" type="number" v-model="form.code" placeholder="请输入验证码" maxlength="6" />
            <view class="code-btn" :class="{ 'disabled': countdown > 0 }" @click="handleGetCode">
              {{ countdown > 0 ? `${countdown}s后重试` : '获取验证码' }}
            </view>
          </view>
        </view>

        <view class="input-group">
          <view class="input-wrapper">
            <input class="input" type="password" v-model="form.password" placeholder="请输入密码" />
          </view>
        </view>

        <view class="input-group">
          <view class="input-wrapper">
            <input class="input" type="text" v-model="form.inviteCode" placeholder="请输入企业邀请码" />
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
      </view>

      <button class="submit-btn" @click="handleRegister">立即注册</button>

      <view class="footer-actions">
        <text class="login-link" @click="handleGoLogin">已有账号，去登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue';
import { authApi } from '@/api'

const isPrivacyChecked = ref(false);
const countdown = ref(0);
let timer: any = null;

const form = reactive({
  phone: '',
  code: '',
  password: '',
  inviteCode: '',
  bizNo: ''
});

const handleBack = () => {
  uni.navigateBack();
};

const handleGoLogin = () => {
  uni.navigateBack();
};

const handleGetCode = async () => {
  if (countdown.value > 0) return;
  if (!form.phone) {
    uni.showToast({ title: '请输入手机号码', icon: 'none' });
    return;
  }
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '手机号码格式错误', icon: 'none' });
    return;
  }

  try {
    const data = await authApi.sendSms({
      mobile: form.phone,
      scene: 'REGISTER'
    })
    form.bizNo = data.bizNo
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

const togglePrivacy = () => {
  isPrivacyChecked.value = !isPrivacyChecked.value;
};

const handlePrivacyLink = () => {
  uni.showToast({ title: '查看隐私政策', icon: 'none' });
};

const handleRegister = async () => {
  if (!isPrivacyChecked.value) {
    uni.showToast({ title: '请先同意用户隐私政策', icon: 'none' });
    return;
  }
  if (!form.phone || !form.code || !form.password || !form.inviteCode) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' });
    return;
  }
  if (!form.bizNo) {
    uni.showToast({ title: '请先获取验证码', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '注册中...' });
  try {
    await authApi.register({
      mobile: form.phone,
      code: form.code,
      bizNo: form.bizNo,
      password: form.password,
      inviteCode: form.inviteCode
    })
    uni.hideLoading()
    uni.showToast({
      title: '注册成功',
      icon: 'success',
      duration: 1200,
      success: () => {
        setTimeout(() => {
          uni.navigateBack();
        }, 1200);
      }
    });
  } catch {
    uni.hideLoading()
  }
};

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
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

.register-main {
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

.privacy-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 40rpx;
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

.submit-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background-color: #2561EF;
  border-radius: 16rpx;
  font-size: 32rpx;
  color: #fff;
  margin-bottom: 40rpx;
  box-shadow: 0 4rpx 12rpx rgba(37, 97, 239, 0.3);
  
  &:active {
    opacity: 0.9;
  }
}

.footer-actions {
  display: flex;
  justify-content: center;
  margin-top: 20rpx;
}

.login-link {
  font-size: 28rpx;
  color: #2561EF;
}
</style>
