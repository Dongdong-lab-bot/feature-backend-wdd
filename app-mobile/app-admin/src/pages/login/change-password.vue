<template>
  <view class="container">
    <view class="form">
      <view class="input-wrapper">
        <input class="input" type="password" v-model="form.newPassword" placeholder="请输入新密码" />
      </view>

      <view class="input-wrapper">
        <input class="input" type="password" v-model="form.confirmPassword" placeholder="请再次输入密码" />
      </view>

      <button class="confirm-btn" @click="handleConfirm">确定</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { authApi } from '@/api'

const form = reactive({
  phone: '',
  resetToken: '',
  newPassword: '',
  confirmPassword: ''
});

onLoad((options: any) => {
  if (options.phone) {
    form.phone = decodeURIComponent(options.phone);
  }
  if (options.resetToken) {
    form.resetToken = decodeURIComponent(options.resetToken);
  }
});

const handleConfirm = async () => {
  if (!form.newPassword || !form.confirmPassword) {
    uni.showToast({ title: '请输入完整密码信息', icon: 'none' });
    return;
  }

  if (form.newPassword.length < 6) {
    uni.showToast({ title: '密码长度不能少于6位', icon: 'none' });
    return;
  }

  if (form.newPassword !== form.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' });
    return;
  }

  if (!form.phone || !form.resetToken) {
    uni.showToast({ title: '重置凭证无效，请重新验证', icon: 'none' });
    return;
  }

  uni.showLoading({ title: '提交中...' })
  try {
    await authApi.resetPassword({
      mobile: form.phone,
      newPassword: form.newPassword,
      resetToken: form.resetToken
    })
    uni.hideLoading()
    uni.showToast({
      title: '密码修改成功',
      icon: 'success',
      duration: 1200,
      success: () => {
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/login/login' });
        }, 1200);
      }
    });
  } catch {
    uni.hideLoading()
  }
};
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background-color: #ffffff;
  padding: 0 30rpx;
  box-sizing: border-box;
}

.form {
  padding-top: 120rpx;
}

.input-wrapper {
  display: flex;
  align-items: center;
  height: 88rpx;
  border: 1px solid #E4E4E4;
  border-radius: 16rpx;
  padding: 0 30rpx;
  background-color: #ffffff;
  margin-bottom: 30rpx;

  &:focus-within {
    border-color: #2561EF;
  }
}

.input {
  flex: 1;
  height: 100%;
  font-size: 30rpx;
  color: #333333;
}

.confirm-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 16rpx;
  background-color: #2561EF;
  color: #ffffff;
  font-size: 32rpx;
  box-shadow: 0 4rpx 12rpx rgba(37, 97, 239, 0.3);
  margin-top: 40rpx;
}

.confirm-btn:active {
  opacity: 0.9;
}
</style>
