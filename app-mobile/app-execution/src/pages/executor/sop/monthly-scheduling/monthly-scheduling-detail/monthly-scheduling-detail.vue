<template>
  <view class="page-container">
    <!-- 报告标题 -->
    <view class="report-title-section">
      <text class="report-title">{{ reportDetail.title }}</text>
      <view class="title-dot"></view>
    </view>

    <!-- 详情内容 -->
    <scroll-view class="content-container" scroll-y="true">
      <view class="detail-section">
        <!-- 基本信息 -->
        <view class="info-section">
          <view class="info-item">
            <text class="info-label">报告人：</text>
            <text class="info-value">{{ reportDetail.reporter }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">参会人：</text>
            <text class="info-value">{{ reportDetail.participants }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">会议时间：</text>
            <text class="info-value">{{ reportDetail.meetingTime }}</text>
          </view>
        </view>

        <!-- 主要内容标题 -->
        <view class="content-title">
          <text class="title-text">主要内容</text>
        </view>

        <!-- 内容详情 -->
        <view class="content-detail">
          <view class="content-section">
            <text class="section-title">一、总体概述</text>
            <text class="section-content">{{ reportDetail.overview }}</text>
          </view>

          <!-- 图片 -->
          <view class="content-image" v-if="reportDetail.imageUrl">
            <image :src="reportDetail.imageUrl" class="detail-image" mode="aspectFit" />
          </view>

          <view class="content-section">
            <text class="section-title">二、一食堂日管控执行情况</text>
            <text class="section-content">{{ reportDetail.canteen1Control }}</text>
          </view>

          <view class="content-section">
            <text class="section-title">三、二食堂日管控执行情况</text>
            <text class="section-content">{{ reportDetail.canteen2Control }}</text>
          </view>

          <view class="content-section">
            <text class="section-title">四、存在问题及整改措施</text>
            <text class="section-content">{{ reportDetail.issues }}</text>
          </view>

          <view class="content-section">
            <text class="section-title">五、下月工作计划</text>
            <text class="section-content">{{ reportDetail.nextMonthPlan }}</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { previewMonthlyReport, exportMonthlyReport } from '@/common/monthly-report'

interface ReportDetail {
  id: number
  title: string
  reporter: string
  participants: string
  meetingTime: string
  imageUrl: string
  overview: string
  canteen1Control: string
  canteen2Control: string
  issues: string
  nextMonthPlan: string
}

const reportDetail = ref<ReportDetail>({
  id: 0,
  title: '',
  reporter: '',
  participants: '',
  meetingTime: '',
  imageUrl: '',
  overview: '',
  canteen1Control: '',
  canteen2Control: '',
  issues: '',
  nextMonthPlan: ''
})

const currentMonth = ref<string>('')
const canteenIds = ref<number[]>([1])

onLoad((options: any) => {
  if (options.id) {
    reportDetail.value.id = Number(options.id)
  }
  if (options.title) {
    reportDetail.value.title = decodeURIComponent(options.title)
  }
  if (options.month) {
    currentMonth.value = options.month
  }
  loadReportDetail()
})

const getPeriod = () => {
  let startDate = '2026-01-01'
  let endDate = '2026-01-31'
  if (currentMonth.value) {
    const [yearStr, monthStr] = currentMonth.value.split('-')
    const year = Number(yearStr)
    const month = Number(monthStr)
    if (year && month) {
      const first = new Date(year, month - 1, 1)
      const last = new Date(year, month, 0)
      const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`)
      startDate = `${year}-${pad(first.getMonth() + 1)}-${pad(first.getDate())}`
      endDate = `${year}-${pad(last.getMonth() + 1)}-${pad(last.getDate())}`
    }
  }
  return { startDate, endDate }
}

const loadReportDetail = async () => {
  const { startDate, endDate } = getPeriod()
  try {
    const res: any = await previewMonthlyReport({
      startDate,
      endDate,
      dataSources: canteenIds.value
    })
    console.log('monthly preview data:', res)

    if (!reportDetail.value.overview) {
      reportDetail.value.reporter = '食安总监'
      reportDetail.value.participants = '校长、副校长、后勤主任、食堂经理、食品安全员'
      reportDetail.value.meetingTime = '2021年2月1日'
      reportDetail.value.overview = '本月，学校一食堂与二食堂整体运行平稳，食品安全和卫生管理基本符合《学校食品安全与营养健康管理规定》及本校食堂管理制度要求。两个食堂均严格执行"日管控、周排查、月调度"工作机制，未发生食品安全事故。通过日常巡查与专项检查相结合，及时发现并整改部分操作不规范、设施老化等问题，保障了师生饮食安全。'
      reportDetail.value.canteen1Control = '执行率：全月31天，日管控记录完整，执行率达100%。主要管控内容：每日晨检（员工健康状况）：全员持有效健康证上岗，无发热、腹泻等异常情况；食材验收：严格执行索证索票制度，冷链食品查验齐全；加工过程：生熟分开、烧熟煮透，留样规范（每餐≥125克，48小时保存）；餐具消毒：高温消毒，符合卫生标准；环境卫生：地面、墙面、操作台清洁卫生，无积水、无异味。'
      reportDetail.value.canteen2Control = '执行率：全月31天，日管控记录完整，执行率达100%。主要管控内容：每日晨检（员工健康状况）：全员持有效健康证上岗，无发热、腹泻等异常情况；食材验收：严格执行索证索票制度，冷链食品查验齐全；加工过程：生熟分开、烧熟煮透，留样规范；餐具消毒：高温消毒，符合卫生标准；环境卫生：地面、墙面、操作台清洁卫生。'
      reportDetail.value.issues = '1. 一食堂部分操作台面老化，建议更换；2. 二食堂通风设施需加强清洁；3. 员工食品安全培训有待加强。整改措施：1. 计划于下月采购新操作台面；2. 增加每周通风设施清洁频次；3. 组织员工参加市级食品安全培训。'
      reportDetail.value.nextMonthPlan = '1. 继续强化日管控、周排查工作；2. 完成食堂设施更新改造；3. 组织春季食品安全专项检查；4. 开展员工技能提升培训；5. 完善食品安全应急预案。'
    }
  } catch (e) {
    uni.showToast({ title: '生成预览失败', icon: 'none' })
  }
}

const handleExport = async () => {
  const { startDate, endDate } = getPeriod()
  uni.showLoading({ title: '导出中...' })
  try {
    await exportMonthlyReport({
      startDate,
      endDate,
      dataSources: canteenIds.value,
      exportFormat: 'pdf'
    })
    uni.hideLoading()
    uni.showToast({ title: '导出成功', icon: 'success' })
  } catch (e) {
    uni.hideLoading()
    uni.showToast({ title: '导出失败', icon: 'none' })
  }
}
</script>

<style scoped lang="scss">
.page-container {
  height: 100vh;
  background-color: #fff; /* Changed to white to match cleaner look if needed, or keep gray */
  display: flex;
  flex-direction: column;
}

.report-title-section {
  background-color: #fff;
  padding: 40rpx 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.report-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #2561EF;
  line-height: 1.4;
  text-align: center;
  margin-bottom: 16rpx;
}

.title-dot {
  width: 12rpx;
  height: 12rpx;
  background-color: #2561EF;
  border-radius: 50%;
}

.content-container {
  flex: 1;
  padding: 0 30rpx;
  box-sizing: border-box;
  padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
}

.detail-section {
  background-color: #fff;
  padding: 20rpx 0;
}

.info-section {
  margin-bottom: 40rpx;
  padding: 0 10rpx;
}

.info-item {
  display: flex;
  margin-bottom: 20rpx;
  align-items: flex-start;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.info-label {
  font-size: 28rpx;
  color: #999;
  min-width: 150rpx;
  flex-shrink: 0;
}

.info-value {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  flex: 1;
}

.content-title {
  margin-bottom: 30rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid #eee;
}

.title-text {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  position: relative;
  padding-left: 20rpx;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 6rpx;
    bottom: 6rpx;
    width: 8rpx;
    background-color: #2561EF;
    border-radius: 4rpx;
  }
}

.content-detail {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.content-section {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #2561ef;
}

.section-content {
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
  text-align: justify;
}

.content-image {
  display: flex;
  justify-content: center;
  margin: 20rpx 0;
}

.detail-image {
  width: 100%;
  max-width: 600rpx;
  height: 300rpx;
  border-radius: 8rpx;
  background-color: #f5f5f5;
}
</style>
