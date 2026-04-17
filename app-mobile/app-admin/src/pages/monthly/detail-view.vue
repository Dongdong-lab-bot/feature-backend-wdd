<template>
  <view class="page">
    <NavBar title="月调度详情" />

    <scroll-view class="body" scroll-y>
      <view class="top-card">
        <text class="top-title">{{ reportTitle }}</text>
        <view class="dot"></view>
      </view>

      <view class="info-card">
        <view class="info-row">
          <text class="info-label">报告人：</text>
          <text class="info-value">{{ reporter }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">参会人：</text>
          <text class="info-value">{{ attendees }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">会议时间：</text>
          <text class="info-value">{{ meetingTime }}</text>
        </view>
      </view>

      <view class="section-title">主要内容</view>

      <view class="content-block">
        <text class="content-text">
          一、总体概述
        </text>
        <text class="content-text">
          {{ sectionOne }}
        </text>
      </view>

      <image class="photo" src="/static/monthly/detail-photo.png" mode="aspectFill" />

      <view class="content-block">
        <text class="content-text">
          二、一食堂日管控执行情况
        </text>
        <text class="content-text">
          {{ sectionTwo }}
        </text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import NavBar from '../../components/NavBar/NavBar.vue'
import { monthlyApi } from '@/api'

const canteen = ref('武岗一中一食堂')
const monthLabel = ref('1月')

const reporter = ref('食安总监')
const attendees = ref('校长、副校长、后勤主任、食堂经理、食品安全员')
const meetingTime = ref('2021年2月1日')
const sectionOne = ref('本月，学校一食堂与二食堂整体运行平稳，食品安全和卫生管理基本符合《学校食品安全与营养健康管理规定》及本校食堂管理制度要求。两个食堂均严格执行“日管控、周排查、月调度”工作机制，未发生食品安全事故。通过日常巡查与专项检查相结合，及时发现并整改部分操作不规范、设施老化等问题，保障了师生饮食安全。')
const sectionTwo = ref('执行率：全月31天，日管控记录完整，执行率达100%。主要管控内容：每日晨检（员工健康状况）：全员持有效健康证上岗，无发热、腹泻等异常情况；食材验收：严格执行索证索票制度，冷链食品查验齐全；加工过程：生熟分开、烧熟煮透，留样规范（每餐≥125克，48小时留存）。')

const toDate = (d: Date) => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const resolveNodeId = () => {
  if (canteen.value.includes('二食堂')) return 'canteen_102'
  return 'canteen_101'
}

const buildPreviewPayload = () => {
  const end = new Date()
  const start = new Date(end.getFullYear(), end.getMonth(), 1)
  // 后端实际需要的格式: start_date, end_date, data_sources (canteen_id 数组)
  return {
    start_date: toDate(start),
    end_date: toDate(end),
    data_sources: [1, 2, 3] // 临时写死食堂ID数组，后续可从 canteen 中解析
  }
}

const loadPreview = async () => {
  const data = await monthlyApi.previewMonthlyReport(buildPreviewPayload())
  if (typeof data?.markdown === 'string' && data.markdown.trim()) {
    sectionOne.value = data.markdown.slice(0, 220)
  }
  if (Array.isArray(data?.canteen_summary) && data.canteen_summary.length) {
    const lines = data.canteen_summary
      .slice(0, 3)
      .map((x: any) => `${x.canteen_name}：任务${x.task_count}次，问题${x.issue_count}项`)
    sectionTwo.value = lines.join('；')
  } else if (Array.isArray(data?.issue_ranking) && data.issue_ranking.length) {
    const top = data.issue_ranking[0]
    sectionTwo.value = `高频问题：${top.content}（${top.issue_count}次）`
  }
}

onLoad(async (options: any) => {
  const c = typeof options?.canteen === 'string' ? options.canteen : ''
  const m = typeof options?.month === 'string' ? options.month : ''

  if (c) {
    try {
      canteen.value = decodeURIComponent(c)
    } catch {
      canteen.value = c
    }
  }

  if (m) {
    try {
      monthLabel.value = decodeURIComponent(m)
    } catch {
      monthLabel.value = m
    }
  }
  try {
    await loadPreview()
  } catch {}
})

const reportTitle = computed(() => `${canteen.value}${monthLabel.value}月调度记录详情`)
</script>

<style lang="scss" scoped>
.page {
  height: 100vh;
  background: rgba(41, 132, 248, 0.05);
  display: flex;
  flex-direction: column;
}

.body {
  flex: 1;
  min-height: 0;
  background: #ffffff;
}

.top-card {
  padding: 22rpx 30rpx 12rpx;
}

.top-title {
  font-size: 28rpx;
  color: #2561ef;
  font-weight: 600;
}

.dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 999rpx;
  background: #2561ef;
  margin: 8rpx auto 0;
}

.info-card {
  padding: 18rpx 30rpx 10rpx;
}

.info-row {
  display: flex;
  align-items: flex-start;
  line-height: 44rpx;
}

.info-label {
  font-size: 24rpx;
  color: #999999;
  flex-shrink: 0;
}

.info-value {
  font-size: 24rpx;
  color: #333333;
  flex: 1;
}

.section-title {
  padding: 16rpx 30rpx 10rpx;
  font-size: 28rpx;
  color: #111111;
  font-weight: 600;
}

.content-block {
  padding: 0 30rpx 12rpx;
}

.content-text {
  font-size: 24rpx;
  color: #999999;
  line-height: 44rpx;
  display: block;
}

.photo {
  margin: 12rpx 30rpx;
  width: 690rpx;
  height: 372rpx;
  border-radius: 12rpx;
}
</style>
