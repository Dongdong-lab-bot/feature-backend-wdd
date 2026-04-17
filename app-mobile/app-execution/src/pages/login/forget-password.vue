<template>
  <view class="container">
    <view class="form">
      <view class="input-wrapper">
        <text class="country-code">+86</text>
        <view class="divider"></view>
        <input class="input" type="number" v-model="form.phone" placeholder="请输入手机号" maxlength="11" />
      </view>

      <view class="input-wrapper">
        <input class="input" type="number" v-model="form.code" placeholder="请输入验证码" maxlength="6" />
        <text class="code-btn" :class="{ disabled: countdown > 0 }" @click="handleGetCode">
          {{ countdown > 0 ? `${countdown}s后重试` : '获取验证码' }}
        </text>
      </view>

      <button class="next-btn" @click="handleNext">下一步</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref, onUnmounted } from 'vue';
import { sendSmsCode, verifyResetCode } from '@/common/auth';

const form = reactive({
  phone: '',
  code: '',
  bizNo: ''
});

const countdown = ref(0);
let timer: number | null = null;

const handleGetCode = async () => {
  if (countdown.value > 0) return;

  if (!form.phone) {
    uni.showToast({ title: '请输入手机号', icon: 'none' });
    return;
  }

  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '手机号格式错误', icon: 'none' });
    return;
  }

  try {
    const res: any = await sendSmsCode(form.phone, 'RESET_PASSWORD');
    form.bizNo = res?.bizNo || '';
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

const handleNext = async () => {
  if (!form.phone || !form.code) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' });
    return;
  }

  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '手机号格式错误', icon: 'none' });
    return;
  }

  if (!/^\d{4,6}$/.test(form.code)) {
    uni.showToast({ title: '验证码格式错误', icon: 'none' });
    return;
  }

  let resetToken = '';
  try {
    const res: any = await verifyResetCode(form.phone, form.code, form.bizNo);
    resetToken = res?.resetToken || '';
  } catch (error) {
    uni.showToast({ title: '验证失败', icon: 'none' });
    return;
  }

  uni.showToast({ title: '验证成功', icon: 'success' });
  
  setTimeout(() => {
    uni.navigateTo({
      url: `/pages/login/change-password?phone=${form.phone}&resetToken=${resetToken}`
    });
  }, 1000);
};

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
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

.next-btn {
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

.next-btn:active {
  opacity: 0.9;
}
</style>
