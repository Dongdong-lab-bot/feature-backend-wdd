<template>
  <view class="page">
    <NavBar title="新增员工" />
    
    <scroll-view class="content" scroll-y>
      <view class="section-title">基础信息</view>
      
      <view class="form-group">
        <!-- Name -->
        <view class="form-item">
          <view class="label">
            <text class="required">*</text>
            <text>姓名</text>
          </view>
          <input class="input" placeholder="请输入" placeholder-style="color: #ccc" v-model="form.name" />
        </view>
        
        <!-- Phone -->
        <view class="form-item">
          <view class="label">
            <text class="required">*</text>
            <text>手机号码</text>
          </view>
          <input class="input" type="number" placeholder="请输入" placeholder-style="color: #ccc" v-model="form.phone" maxlength="11" />
        </view>
        
        <!-- Gender -->
        <picker mode="selector" :range="genderOptions" @change="onGenderChange">
          <view class="form-item">
            <view class="label">
              <text>性别</text>
            </view>
            <view class="value-box">
              <text :class="form.gender ? 'value' : 'placeholder'">{{ form.gender || '请选择' }}</text>
              <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
            </view>
          </view>
        </picker>
        
        <!-- Birth Date -->
        <picker mode="date" @change="onDateChange">
          <view class="form-item">
            <view class="label">
              <text>出生日期</text>
            </view>
            <view class="value-box">
              <text :class="form.birthDate ? 'value' : 'placeholder'">{{ form.birthDate || '请选择' }}</text>
              <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
            </view>
          </view>
        </picker>
        
        <!-- Position -->
        <picker mode="selector" :range="positionOptions" @change="onPositionChange">
          <view class="form-item no-border">
            <view class="label">
              <text>岗位</text>
            </view>
            <view class="value-box">
              <text :class="form.position ? 'value' : 'placeholder'">{{ form.position || '请选择' }}</text>
              <image class="arrow" src="/static/home/icon-arrow.svg" mode="aspectFit" />
            </view>
          </view>
        </picker>
      </view>
      
      <!-- Photos -->
      <view class="photo-group">
        <view class="photo-item">
          <text class="photo-label">健康证照片</text>
          <view class="add-btn" @click="addPhoto('health')">
             <view class="plus-icon">+</view>
             <text>添加</text>
          </view>
        </view>
         <view class="photo-item">
          <text class="photo-label">人脸照片</text>
          <view class="add-btn" @click="addPhoto('face')">
             <view class="plus-icon">+</view>
             <text>添加</text>
          </view>
        </view>
         <view class="photo-item no-border">
          <text class="photo-label">身份证照片</text>
          <view class="add-btn" @click="addPhoto('idCard')">
             <view class="plus-icon">+</view>
             <text>添加</text>
          </view>
        </view>
      </view>

    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import NavBar from '@/components/NavBar/NavBar.vue'

const form = reactive({
  name: '',
  phone: '',
  gender: '',
  birthDate: '',
  position: ''
})

const genderOptions = ['男', '女']
const positionOptions = ['店长', '厨师', '服务员', '保洁', '其他']

const onGenderChange = (e: any) => {
  form.gender = genderOptions[e.detail.value]
}

const onDateChange = (e: any) => {
  form.birthDate = e.detail.value
}

const onPositionChange = (e: any) => {
  form.position = positionOptions[e.detail.value]
}

const addPhoto = (type: string) => {
  uni.chooseImage({
    count: 1,
    success: (res) => {
      console.log(`Uploaded ${type} photo`, res.tempFilePaths[0])
      uni.showToast({ title: '已选择照片', icon: 'success' })
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #F8F9FB;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  padding: 0;
}

.section-title {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  margin: 30rpx 30rpx 20rpx 30rpx; 
}

.form-group, .photo-group {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 0 30rpx;
  margin: 0 30rpx 30rpx 30rpx; 
  box-sizing: border-box; 
}

.form-item, .photo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100rpx;
  border-bottom: 1rpx solid #eee;
  
  &.no-border {
    border-bottom: none;
  }
}

.label, .photo-label {
  font-size: 30rpx;
  color: #333;
  display: flex;
  align-items: center;
  
  .required {
    color: #FF4D4F;
    margin-right: 4rpx;
    font-size: 30rpx;
    // Adjust vertical alignment if needed
  }
}

.input {
  text-align: right;
  font-size: 30rpx;
  color: #333;
  flex: 1;
  margin-left: 40rpx;
  padding-right: 4rpx; 
}

.value-box {
  display: flex;
  align-items: center;
  
  .value {
    font-size: 30rpx;
    color: #333;
  }
  
  .placeholder {
    font-size: 30rpx;
    color: #ccc;
  }
  
  .arrow {
    width: 32rpx;
    height: 32rpx;
    margin-left: 12rpx;
  }
}

.add-btn {
  display: flex;
  align-items: center;
  
  .plus-icon {
    width: 32rpx;
    height: 32rpx;
    border: 2rpx solid #2561EF;
    border-radius: 50%;
    color: #2561EF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28rpx;
    margin-right: 8rpx;
    line-height: 1;
    padding-bottom: 4rpx; // optical adjustment
  }
  
  text {
    font-size: 28rpx;
    color: #2561EF;
  }
}
</style>