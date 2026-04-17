<template>
  <view class="container">
    <view class="change-main">
      <view class="form-container">
        <!-- 旧密码 -->
        <view class="input-group">
          <view class="input-wrapper">
            <input 
              class="input" 
              type="password" 
              v-model="form.oldPassword" 
              placeholder="请输入旧密码" 
              placeholder-style="color: #999"
            />
          </view>
        </view>

        <!-- 新密码 -->
        <view class="input-group">
          <view class="input-wrapper">
            <input 
              class="input" 
              type="password" 
              v-model="form.newPassword" 
              placeholder="请输入新密码" 
              placeholder-style="color: #999"
            />
          </view>
        </view>

        <!-- 确认密码 -->
        <view class="input-group">
          <view class="input-wrapper">
            <input 
              class="input" 
              type="password" 
              v-model="form.confirmPassword" 
              placeholder="请再次输入密码" 
              placeholder-style="color: #999"
            />
          </view>
        </view>
      </view>

      <button class="submit-btn" @click="handleConfirm">确定</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { changePassword, logout } from '@/common/auth';

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const handleConfirm = async () => {
  // 非空校验
  if (!form.oldPassword || !form.newPassword || !form.confirmPassword) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' });
    return;
  }

  // 新旧密码不能相同
  if (form.oldPassword === form.newPassword) {
    uni.showToast({ title: '新密码不能与旧密码相同', icon: 'none' });
    return;
  }

  // 两次密码一致性校验
  if (form.newPassword !== form.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' });
    return;
  }

  try {
    await changePassword(form.oldPassword, form.newPassword);
  } catch (error: any) {
    const errMsg = error?.msg || error?.message || '修改失败，请检查原密码';
    uni.showToast({ title: errMsg, icon: 'none' });
    return;
  }

  uni.showToast({
    title: '密码修改成功，请重新登录',
    icon: 'success',
    duration: 1500,
    success: () => {
      setTimeout(() => {
        logout();
      }, 1500);
    }
  });
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

.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 88rpx;
  padding-top: var(--status-bar-height);
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  z-index: 100;
}

.back-btn {
  position: absolute;
  left: 10rpx;
  bottom: 0;
  width: 88rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  width: 24rpx;
  height: 24rpx;
}

.title {
  font-size: 36rpx;
  font-weight: 500;
  color: #333;
}

.change-main {
  min-height: 100vh;
  padding-top: 40rpx;
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

.input {
  flex: 1;
  font-size: 30rpx;
  height: 100%;
  color: #333;
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background-color: #2561EF;
  border-radius: 16rpx;
  font-size: 32rpx;
  color: #fff;
  box-shadow: 0 4rpx 12rpx rgba(37, 97, 239, 0.3);
  
  &:active {
    opacity: 0.9;
  }
}
</style>
