<template>
  <view class="container">
    <view class="change-main">
      <view class="form-container">
        <view class="input-group">
          <view class="input-wrapper">
            <text class="country-code">+86</text>
            <view class="divider"></view>
            <input class="input" type="number" v-model="form.phone" placeholder="请输入您要修改的手机号码" maxlength="11" />
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
      </view>

      <button class="submit-btn" @click="handleConfirm">确定</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue';
import { sendSmsCode, changePhoneBySms } from '@/common/auth';

const countdown = ref(0);
let timer: number | null = null;

const form = reactive({
  phone: '',
  code: '',
  bizNo: ''
});

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
    const res: any = await sendSmsCode(form.phone, 'LOGIN');
    form.bizNo = res?.bizNo || '';
    countdown.value = 60;
    uni.showToast({ title: '验证码已发送', icon: 'none' });
    
    timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0 && timer) {
        clearInterval(timer);
        timer = null;
      }
    }, 1000) as unknown as number;
  } catch (error) {
    uni.showToast({ title: '发送失败', icon: 'none' });
  }
};

const handleConfirm = async () => {
  if (!form.phone || !form.code) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' });
    return;
  }
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '手机号码格式错误', icon: 'none' });
    return;
  }
  if (!/^\d{4,6}$/.test(form.code)) {
    uni.showToast({ title: '验证码格式错误', icon: 'none' });
    return;
  }
  
  try {
    await changePhoneBySms(form.phone, form.code, form.bizNo || '');
  } catch (error) {
    uni.showToast({ title: '修改失败', icon: 'none' });
    return;
  }
  
  uni.showToast({
    title: '手机号修改成功',
    icon: 'success',
    duration: 1500,
    success: () => {
      setTimeout(() => {
        uni.navigateBack();
      }, 1500);
    }
  });
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
}

.change-main {
  padding-top: 30rpx;
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
