<template>
  <view class="page">
    <!-- Breadcrumbs -->
    <view class="crumbs">
      <text class="crumb blue">武岗县全县项目</text>
      <text class="crumb separator">&gt;</text>
      <text class="crumb blue crumb-link" @click="toggleTownOptions">{{ selectedTown }}</text>
      <text class="crumb separator">&gt;</text>
      <text class="crumb gray crumb-link" @click="toggleSchoolOptions">{{ selectedSchoolType }}</text>

      <view class="tag-row" v-if="showTownOptions">
        <view class="tag" v-for="item in townOptions" :key="item" :class="{ active: item === selectedTown }" @click="selectTown(item)">
          <text>{{ item }}</text>
        </view>
      </view>
      <view class="tag-row" v-if="showSchoolOptions">
        <view class="tag" v-for="item in schoolTypeOptions" :key="item" :class="{ active: item === selectedSchoolType }" @click="selectSchoolType(item)">
          <text>{{ item }}</text>
        </view>
      </view>
    </view>

    <!-- Header Info -->
    <view class="header-card">
      <view class="header-title">{{ canteenName }}周排查表</view>
      <view class="header-date">{{ submitDate }}</view>
    </view>

    <!-- Checklist -->
    <view class="check-list">
      <view class="check-item" v-for="(item, index) in checkItems" :key="index">
        <view class="item-header">
          <text class="item-title">{{ index + 1 }}. {{ item.title }}</text>
        </view>
        
        <view class="status-options">
          <view 
            class="option-btn" 
            :class="{ active: item.status === 'qualified', green: item.status === 'qualified' }"
            @click="selectStatus(index, 'qualified')"
          >
            <text class="icon" v-if="item.status === 'qualified'">✓</text>
            <text>符合</text>
          </view>
          <view 
            class="option-btn" 
            :class="{ active: item.status === 'unqualified', red: item.status === 'unqualified' }"
            @click="selectStatus(index, 'unqualified')"
          >
            <text class="icon" v-if="item.status === 'unqualified'">✕</text>
            <text>不符合</text>
          </view>
        </view>

        <!-- Issue Input (Only if Unqualified) -->
        <view class="issue-input" v-if="item.status === 'unqualified'">
          <view class="input-group">
            <view class="label">问题描述</view>
            <textarea 
              class="desc-input" 
              v-model="item.issueDesc" 
              placeholder="请输入问题描述" 
              placeholder-class="placeholder"
            />
          </view>
          
          <view class="input-group">
            <view class="label">问题照片</view>
            <view class="upload-box">
              <view 
                class="upload-item" 
                v-for="(img, i) in item.issuePhotos" 
                :key="i"
              >
                <image :src="img" mode="aspectFill" class="upload-img"></image>
                <view class="delete-btn" @click="deletePhoto(index, i)">×</view>
              </view>
              <view class="upload-btn" @click="chooseImage(index)">
                <text class="plus">+</text>
                <text class="upload-text">上传照片</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- Bottom Button -->
    <view class="footer">
      <button class="submit-btn" @click="handleSubmit">完成周排查</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { fetchWeeklyTaskDetail, submitWeeklyTask } from '@/common/weekly-inspection'


interface CheckItem {
  id: string
  title: string
  status: 'qualified' | 'unqualified' | ''
  issueDesc: string
  issuePhotos: string[]
}

const checkItems = ref<CheckItem[]>([])

const taskId = ref<string>('')
const canteenName = ref('武岗一中一食堂')
const submitDate = ref('2026-02-18')

const loadDetail = async (id: string) => {
  try {
    uni.showLoading({ title: '加载中...' })
    const res = await fetchWeeklyTaskDetail(id)
    const taskInfo = res.task_info || res.data?.task_info || res
    const snapshot = res.form_snapshot || res.data?.form_snapshot || taskInfo.form_snapshot
    
    if (taskInfo.canteen_name || taskInfo.canteen_name_snapshot) {
      canteenName.value = taskInfo.canteen_name || taskInfo.canteen_name_snapshot
    }
    if (taskInfo.business_date) {
      submitDate.value = taskInfo.business_date
    }

    const majorItems = Array.isArray(snapshot?.major_items) ? snapshot.major_items : (Array.isArray(snapshot) ? snapshot : [])
    const allItems: any[] = []
    majorItems.forEach((major: any) => {
      const items = Array.isArray(major.minor_items) ? major.minor_items : (Array.isArray(major.items) ? major.items : [])
      allItems.push(...items)
    })

    if (allItems.length > 0) {
      checkItems.value = allItems.map((item: any) => ({
        id: String(item.item_id),
        title: item.content || '未知检查项',
        status: item.is_qualified === true ? 'qualified' : (item.is_qualified === false ? 'unqualified' : ''),
        issueDesc: item.description || '',
        issuePhotos: Array.isArray(item.photos) ? item.photos : []
      }))
    }
  } catch (err) {
    console.error('加载周排查详情失败:', err)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

onLoad((options: any) => {
  if (options?.taskId || options?.id) {
    taskId.value = String(options.taskId || options.id)
    loadDetail(taskId.value)
  }
})

const townOptions = ['城东片区', '城西片区', '城中片区', '城南片区', '城北片区']
const schoolTypeOptions = ['高中学校', '初中学校', '小学']
const selectedTown = ref(townOptions[0])
const selectedSchoolType = ref(schoolTypeOptions[0])
const showTownOptions = ref(false)
const showSchoolOptions = ref(false)
const toggleTownOptions = () => { showTownOptions.value = !showTownOptions.value; showSchoolOptions.value = false }
const toggleSchoolOptions = () => { showSchoolOptions.value = !showSchoolOptions.value; showTownOptions.value = false }
const selectTown = (item: string) => { selectedTown.value = item; showTownOptions.value = false }
const selectSchoolType = (item: string) => { selectedSchoolType.value = item; showSchoolOptions.value = false }

const selectStatus = (index: number, status: 'qualified' | 'unqualified') => {
  checkItems.value[index].status = status
  if (status === 'qualified') {
    // Clear issue data if switching to qualified
    checkItems.value[index].issueDesc = ''
    checkItems.value[index].issuePhotos = []
  }
}

const chooseImage = (index: number) => {
  uni.chooseImage({
    count: 3,
    success: (res) => {
      checkItems.value[index].issuePhotos.push(...res.tempFilePaths)
    }
  })
}

const deletePhoto = (itemIndex: number, photoIndex: number) => {
  checkItems.value[itemIndex].issuePhotos.splice(photoIndex, 1)
}

const handleSubmit = async () => {
  // Validate
  const unselected = checkItems.value.find(item => !item.status)
  if (unselected) {
    uni.showToast({
      title: `请完成第${checkItems.value.indexOf(unselected) + 1}项检查`,
      icon: 'none'
    })
    return
  }

  const incompleteIssue = checkItems.value.find(item => item.status === 'unqualified' && (!item.issueDesc || item.issuePhotos.length === 0))
  if (incompleteIssue) {
    uni.showToast({
      title: '请完善不符合项的问题描述和照片',
      icon: 'none'
    })
    return
  }

  if (!taskId.value) {
    uni.showToast({ title: '缺少任务ID，无法提交', icon: 'none' })
    return
  }

  const results = checkItems.value.map(item => ({
    item_id: Number(item.id),
    is_qualified: item.status === 'qualified',
    description: item.status === 'unqualified' ? item.issueDesc : null,
    photos: item.status === 'unqualified' ? item.issuePhotos : []
  }))

  uni.showLoading({ title: '提交中...' })
  try {
    const submitterId = uni.getStorageSync('userId') || undefined
    await submitWeeklyTask(taskId.value, {
      actualStartTime: new Date().toISOString(),
      results,
      submitterId
    })
    uni.hideLoading()
    uni.showToast({
      title: '提交成功',
      icon: 'success'
    })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (e) {
    uni.hideLoading()
    uni.showToast({ title: '提交失败', icon: 'none' })
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #F7F8FA;
  padding-bottom: 120rpx;
}

.crumbs {
  padding: 20rpx 30rpx;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  background-color: #fff;

  .crumb {
    font-size: 26rpx;
    color: #333;
    
    &.blue {
      color: #2561EF;
    }
    
    &.gray {
      color: #999999;
    }
    
    &.separator {
      color: #999999;
      margin: 0 10rpx;
    }
  }

  .tag-row {
    width: 100%;
    margin-top: 12rpx;
    display: flex;
    flex-wrap: wrap;
    gap: 12rpx;
  }

  .tag {
    padding: 8rpx 20rpx;
    border-radius: 24rpx;
    border: 1rpx solid #e0e0e0;
    background-color: #f5f5f5;
    font-size: 24rpx;
    color: #666666;

    &.active {
      border-color: #2561EF;
      background-color: #e6efff;
      color: #2561EF;
    }
  }
}

.header-card {
  background-color: #fff;
  padding: 30rpx;
  margin-top: 2rpx;
  border-bottom: 1rpx solid #eee;

  .header-title {
    font-size: 34rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 10rpx;
  }

  .header-date {
    font-size: 26rpx;
    color: #999;
  }
}

.check-list {
  padding: 20rpx 30rpx;
}

.check-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;

  .item-header {
    margin-bottom: 24rpx;
    .item-title {
      font-size: 30rpx;
      font-weight: 500;
      color: #333;
    }
  }

  .status-options {
    display: flex;
    gap: 24rpx;
    margin-bottom: 20rpx;

    .option-btn {
      flex: 1;
      height: 72rpx;
      border-radius: 36rpx;
      background-color: #F7F8FA;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28rpx;
      color: #666;
      border: 2rpx solid transparent;
      transition: all 0.2s;

      &.active {
        font-weight: 500;
        
        &.green {
          background-color: rgba(76, 175, 80, 0.1);
          color: #4CAF50;
          border-color: #4CAF50;
        }
        
        &.red {
          background-color: rgba(255, 107, 107, 0.1);
          color: #FF6B6B;
          border-color: #FF6B6B;
        }
      }

      .icon {
        margin-right: 8rpx;
        font-size: 28rpx;
      }
    }
  }

  .issue-input {
    margin-top: 24rpx;
    padding-top: 24rpx;
    border-top: 1rpx dashed #eee;
    animation: fadeIn 0.3s ease;

    .input-group {
      margin-bottom: 24rpx;

      &:last-child {
        margin-bottom: 0;
      }

      .label {
        font-size: 26rpx;
        color: #666;
        margin-bottom: 16rpx;
      }

      .desc-input {
        width: 100%;
        height: 140rpx;
        background-color: #F7F8FA;
        border-radius: 8rpx;
        padding: 20rpx;
        font-size: 28rpx;
        color: #333;
        box-sizing: border-box;
      }
    }

    .upload-box {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;

      .upload-item {
        position: relative;
        width: 140rpx;
        height: 140rpx;

        .upload-img {
          width: 100%;
          height: 100%;
          border-radius: 8rpx;
        }

        .delete-btn {
          position: absolute;
          top: -10rpx;
          right: -10rpx;
          width: 36rpx;
          height: 36rpx;
          background-color: rgba(0, 0, 0, 0.5);
          color: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24rpx;
        }
      }

      .upload-btn {
        width: 140rpx;
        height: 140rpx;
        background-color: #F7F8FA;
        border-radius: 8rpx;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2rpx dashed #ddd;

        .plus {
          font-size: 40rpx;
          color: #999;
          margin-bottom: 4rpx;
        }

        .upload-text {
          font-size: 22rpx;
          color: #999;
        }
      }
    }
  }
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #fff;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);

  .submit-btn {
    background-color: #2561EF;
    color: #fff;
    border-radius: 44rpx;
    height: 88rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32rpx;
    font-weight: 500;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10rpx); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
