<template>
  <div class="details-container" v-loading="loading">
    <el-alert
      v-if="loadError"
      :title="loadError"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom:16px"
    />

    <template v-else>
      <div class="panel-container">
      <!-- ── 页面头部卡片 ── -->
      <div class="page-header-card">
        <h2 class="page-title">{{ titleText }}</h2>
        <div class="page-meta">
          <span class="meta-item">时间：{{ dateText }}</span>
          <span class="meta-item">提交人：{{ submitterText }}</span>
          <el-tag
            v-if="taskStatus"
            size="small"
            :type="taskStatus === 'COMPLETED' ? 'success' : (taskStatus === 'SUBMITTED' || taskStatus === 'RECTIFIED') ? 'warning' : 'danger'"
          >{{ statusText }}</el-tag>
          <span v-if="auditComment" class="audit-alert">审核意见：{{ auditComment }}</span>
        </div>
      </div>

      <!-- ── 主体布局 ── -->
      <div class="main-layout">
        <!-- 左侧大项导航 -->
        <div class="sidebar-card">
          <div class="sidebar-title">检查大项</div>
          <div
            v-for="category in categories"
            :key="category"
            class="sidebar-item"
            :class="{ active: currentCategory === category }"
            @click="currentCategory = category"
          >{{ category }}</div>
        </div>

        <!-- 右侧内容区 -->
        <div class="content-area">
          <!-- 列标题行（有整改列时显示） -->
          <div v-if="showRectificationCol" class="col-header-row">
            <div class="col-header-cell col-header-problem">问题详情</div>
            <div class="col-header-cell col-header-rectify">整改反馈</div>
          </div>

          <template v-if="currentItems.length">
            <div v-for="item in currentItems" :key="item.uid" class="item-card">
              <!-- 卡片头部 -->
              <div class="card-header">
                <span class="item-indicator" :style="{ background: item.color }"></span>
                <span class="item-title">{{ item.title }}</span>
                <div class="score-tags">
                  <el-tag size="small" type="info" effect="plain">满分 {{ item.fullScore }}</el-tag>
                  <el-tag
                    size="small"
                    :type="item.score < item.fullScore ? 'danger' : 'success'"
                    effect="plain"
                  >得分 {{ item.score }}</el-tag>
                </div>
              </div>

              <!-- 卡片体：左右分栏 -->
              <div class="card-body" :class="{ 'card-body-split': showRectificationCol }">
                <!-- 问题详情 -->
                <div class="problem-section">
                  <div class="section-label">问题描述</div>
                  <p class="section-text">{{ item.description || '暂无描述' }}</p>
                  <div class="photo-grid">
                    <template v-if="item.inspectionPhotos.length">
                      <el-image
                        v-for="p in item.inspectionPhotos"
                        :key="p"
                        :src="p"
                        class="photo-thumb"
                        fit="cover"
                        :preview-src-list="item.inspectionPhotos"
                      />
                    </template>
                    <span v-else class="no-photo-text">暂无图片</span>
                  </div>
                </div>

                <!-- 整改反馈 -->
                <div v-if="showRectificationCol" class="rectify-section">
                  <template v-if="canEditRectification">
                    <div class="section-label">整改描述</div>
                    <el-input
                      v-model="item.rectifyDesc"
                      type="textarea"
                      :rows="3"
                      resize="none"
                      placeholder="请输入整改描述"
                      style="margin-bottom:10px"
                    />
                    <div class="section-label">整改图片</div>
                    <div class="photo-grid">
                      <div
                        v-for="(photo, index) in item.rectificationPhotos"
                        :key="`${item.uid}-rp-${index}`"
                        class="photo-box"
                      >
                        <img :src="photo" class="photo-thumb" alt="整改图片" />
                        <button type="button" class="rm-photo" @click="removeRectificationPhoto(item.uid, index)">×</button>
                      </div>
                      <label
                        v-for="slot in Math.max(0, 3 - item.rectificationPhotos.length)"
                        :key="`${item.uid}-slot-${slot}`"
                        class="upload-trigger"
                      >
                        <input
                          class="upload-input"
                          type="file"
                          accept="image/*"
                          @change="handleRectificationPhotoChange($event, item.uid)"
                        />
                        <div class="upload-placeholder">
                          <el-icon><Plus /></el-icon>
                        </div>
                      </label>
                    </div>
                  </template>
                  <template v-else>
                    <div class="section-label">整改描述</div>
                    <p class="section-text">{{ item.rectifyDesc || '暂无' }}</p>
                    <div class="section-label" style="margin-top:10px">整改图片</div>
                    <div class="photo-grid">
                      <template v-if="item.rectificationPhotos.length">
                        <el-image
                          v-for="p in item.rectificationPhotos"
                          :key="p"
                          :src="p"
                          class="photo-thumb"
                          fit="cover"
                          :preview-src-list="item.rectificationPhotos"
                        />
                      </template>
                      <span v-else class="no-photo-text">暂无整改图片</span>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </template>
          <el-empty v-else description="暂无检查明细" style="padding:60px 0;background:#fff;border-radius:8px" />
        </div>
      </div>

      <!-- ── 底部操作栏 ── -->
      <div class="footer-bar">
        <el-button
          v-if="taskStatus === 'PENDING'"
          type="primary"
          :loading="submitLoading"
          @click="submitPending"
        >提交整改内容</el-button>
        <el-button
          v-if="taskStatus === 'REJECTED'"
          type="primary"
          :loading="submitLoading"
          :disabled="!hasEditableFeedback"
          @click="submitRectify"
        >提交整改内容</el-button>
        <span v-if="taskStatus === 'SUBMITTED'" class="status-tip submitted">已提交，等待监管端审核...</span>
        <span v-else-if="taskStatus === 'RECTIFIED'" class="status-tip rectified">整改已提交，等待复审...</span>
        <span v-else-if="taskStatus === 'COMPLETED'" class="status-tip completed">✓ 审核已通过，流程完成</span>
      </div>
      </div><!-- /panel-container -->
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture as _Picture, Plus } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getWeeklyInspectionTaskDetail, submitWeeklyInspectionTask, submitWeeklyReport, buildIdempotencyKey } from '@/api/inspection'
import { getStoredUserInfo } from '@/utils/auth-storage'

interface AuditLogEntry {
  action?: string
  opinion?: string
  comment?: string
}

interface WeeklyMinorItem {
  uid: string
  itemId: number | null
  resultId: number | null
  category: string
  color: string
  title: string
  fullScore: number
  score: number
  enteredScore: number
  description: string
  inspectionPhotos: string[]
  rectifyDesc: string
  rectificationPhotos: string[]
}

type WeeklyTaskStatus = 'PENDING' | 'SUBMITTED' | 'REJECTED' | 'RECTIFIED' | 'COMPLETED' | ''

const COLORS = ['#ff7875', '#faad14', '#40a9ff', '#73d13d', '#9254de', '#13c2c2']

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitLoading = ref(false)
const taskId = ref<number | null>(null)
const taskStatus = ref<WeeklyTaskStatus>('')
const canteenText = ref('-')
const dateText = ref('-')
const submitterText = ref('-')
const auditComment = ref('')
const loadError = ref('')
const currentCategory = ref('')
const allItems = ref<WeeklyMinorItem[]>([])

const statusTextMap: Record<string, string> = {
  PENDING: '待整改',
  SUBMITTED: '待审核',
  REJECTED: '待整改',
  RECTIFIED: '待审核',
  COMPLETED: '已完成',
}

const titleText = computed(() => `${canteenText.value}周排查记录详情`)
const statusText = computed(() => statusTextMap[taskStatus.value] || taskStatus.value || '-')
const categories = computed(() => [...new Set(allItems.value.map((item) => item.category))])
const currentItems = computed(() => {
  if (!currentCategory.value) {
    return allItems.value
  }
  return allItems.value.filter((item) => item.category === currentCategory.value)
})
const canEditRectification = computed(() => taskStatus.value === 'REJECTED' || taskStatus.value === 'PENDING')
const canSubmit = computed(() => false)
const showRectificationCol = computed(() => ['PENDING', 'REJECTED', 'SUBMITTED', 'RECTIFIED', 'COMPLETED'].includes(taskStatus.value))
const hasEditableFeedback = computed(() => allItems.value.some((item) => item.rectifyDesc.trim() || item.rectificationPhotos.length > 0))

const formatDate = (raw: string): string => {
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) {
    return raw || '-'
  }
  return `${date.getFullYear()}.${date.getMonth() + 1}.${date.getDate()}`
}

const normalizePhotoList = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return []
  }
  return value.map((item) => String(item)).filter(Boolean)
}

const resolveColor = (majorIndex: number, score: number, fullScore: number): string => {
  if (score <= 0) {
    return '#ff4d4f'
  }
  if (score < fullScore) {
    return '#faad14'
  }
  return COLORS[majorIndex % COLORS.length]
}

const extractAuditComment = (logs: unknown): string => {
  if (!Array.isArray(logs)) {
    return ''
  }
  const entries = logs as AuditLogEntry[]
  const lastRejected = [...entries].reverse().find((entry) => entry.action === 'REJECT' || entry.action === 'REJECTED')
  const target = lastRejected || entries[entries.length - 1]
  return target?.opinion || target?.comment || ''
}

const loadTaskDetail = async () => {
  const queryId = Number(route.query.id)
  if (!queryId) {
    ElMessage.warning('缺少任务ID，即将返回列表页')
    router.replace('/weekly/records')
    return
  }

  taskId.value = queryId
  loading.value = true
  loadError.value = ''

  try {
    const data = await getWeeklyInspectionTaskDetail(queryId) as Record<string, unknown>
    const info = data.task_info as Record<string, unknown> | undefined
    const snapshot = data.form_snapshot as Record<string, unknown> | undefined

    if (info) {
      taskStatus.value = String(info.status || '') as WeeklyTaskStatus
      canteenText.value = String(info.canteen_name || '-')
      submitterText.value = String(info.inspector_name || '-')
      dateText.value = formatDate(String(info.submission_date || info.actual_start_time || info.business_date || ''))
    }

    auditComment.value = extractAuditComment(data.audit_logs)

    const majorItems = Array.isArray(snapshot?.major_items) ? snapshot?.major_items as Array<Record<string, unknown>> : []
    const nextItems: WeeklyMinorItem[] = []

    majorItems.forEach((major, majorIndex) => {
      const category = String(major.title || major.major_item_name || `检查大项${majorIndex + 1}`)
      const minorItems = Array.isArray(major.minor_items) ? major.minor_items as Array<Record<string, unknown>> : []

      minorItems.forEach((minor, minorIndex) => {
        const score = Number(minor.score_given ?? minor.total_score ?? 0)
        const fullScore = Number(minor.total_score ?? 0)
        nextItems.push({
          uid: `${category}-${minor.item_id || minorIndex}`,
          itemId: typeof minor.item_id === 'number' ? minor.item_id : null,
          resultId: typeof minor.result_id === 'number' ? minor.result_id : null,
          category,
          color: resolveColor(majorIndex, score, fullScore),
          title: String(minor.content || minor.item_name || `检查项${minorIndex + 1}`),
          fullScore,
          score,
          enteredScore: minor.score_given != null ? Number(minor.score_given) : fullScore,
          description: String(minor.inspection_description || ''),
          inspectionPhotos: normalizePhotoList(minor.inspection_photos),
          rectifyDesc: String(minor.rectification_description || ''),
          rectificationPhotos: normalizePhotoList(minor.rectification_photos),
        })
      })
    })

    allItems.value = nextItems
    currentCategory.value = categories.value[0] || ''
  } catch {
    allItems.value = []
    loadError.value = '未读取到周排查详情，请稍后重试。'
  } finally {
    loading.value = false
  }
}

const updateItem = (uid: string, updater: (item: WeeklyMinorItem) => WeeklyMinorItem) => {
  allItems.value = allItems.value.map((item) => (item.uid === uid ? updater(item) : item))
}

const readAsDataUrl = (file: File): Promise<string> => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(String(reader.result || ''))
  reader.onerror = () => reject(reader.error)
  reader.readAsDataURL(file)
})

const handleRectificationPhotoChange = async (event: Event, uid: string) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }

  const targetItem = allItems.value.find((item) => item.uid === uid)
  if (!targetItem) {
    target.value = ''
    return
  }

  if (targetItem.rectificationPhotos.length >= 2) {
    ElMessage.warning('每项最多上传2张整改图片')
    target.value = ''
    return
  }

  const photo = await readAsDataUrl(file)
  updateItem(uid, (item) => ({
    ...item,
    rectificationPhotos: [...item.rectificationPhotos, photo],
  }))
  target.value = ''
}

const removeRectificationPhoto = (uid: string, index: number) => {
  updateItem(uid, (item) => ({
    ...item,
    rectificationPhotos: item.rectificationPhotos.filter((_, photoIndex) => photoIndex !== index),
  }))
}

const handleInspectionPhotoChange = async (event: Event, uid: string) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const targetItem = allItems.value.find((item) => item.uid === uid)
  if (!targetItem) { target.value = ''; return }

  if (targetItem.inspectionPhotos.length >= 3) {
    ElMessage.warning('每项最多上传3张检查图片')
    target.value = ''
    return
  }

  const photo = await readAsDataUrl(file)
  updateItem(uid, (item) => ({ ...item, inspectionPhotos: [...item.inspectionPhotos, photo] }))
  target.value = ''
}

const removeInspectionPhoto = (uid: string, index: number) => {
  updateItem(uid, (item) => ({
    ...item,
    inspectionPhotos: item.inspectionPhotos.filter((_, i) => i !== index),
  }))
}

const submitPending = async () => {
  if (!taskId.value) { ElMessage.error('任务ID无效，无法提交'); return }

  const hasValidItem = allItems.value.some((item) => item.itemId !== null)
  if (!hasValidItem) { ElMessage.warning('暂无可提交的检查项'); return }

  const currentUser = getStoredUserInfo<{ username?: string; id?: number }>()
  const inspectorId = currentUser?.username || (currentUser?.id ? String(currentUser.id) : 'unknown')

  const results = allItems.value
    .filter((item) => item.itemId !== null)
    .map((item) => ({
      item_id: item.itemId as number,
      score_given: item.enteredScore,
      description: item.rectifyDesc.trim() || item.description.trim() || undefined,
      photos: item.inspectionPhotos.length ? item.inspectionPhotos : undefined,
      rectification_description: item.rectifyDesc.trim() || undefined,
      rectification_photos: item.rectificationPhotos.length ? item.rectificationPhotos : undefined,
    }))

  submitLoading.value = true
  try {
    await submitWeeklyReport(
      taskId.value,
      {
        inspector_id: inspectorId,
        actual_start_time: new Date().toISOString(),
        results,
      },
      buildIdempotencyKey()
    )
    ElMessage.success('整改内容提交成功')
    await loadTaskDetail()
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

const submitReport = async () => {
  if (!taskId.value) { ElMessage.error('任务ID无效，无法提交'); return }
  if (!canSubmit.value) { ElMessage.warning('当前状态不可提交'); return }

  const hasValidItem = allItems.value.some((item) => item.itemId !== null)
  if (!hasValidItem) { ElMessage.warning('暂无可提交的检查项'); return }

  const currentUser = getStoredUserInfo<{ username?: string; id?: number }>()
  const inspectorId = currentUser?.username || (currentUser?.id ? String(currentUser.id) : 'unknown')

  const results = allItems.value
    .filter((item) => item.itemId !== null)
    .map((item) => ({
      item_id: item.itemId as number,
      score_given: item.enteredScore,
      description: item.description.trim() || undefined,
      photos: item.inspectionPhotos.length ? item.inspectionPhotos : undefined,
    }))

  submitLoading.value = true
  try {
    await submitWeeklyReport(
      taskId.value,
      {
        inspector_id: inspectorId,
        actual_start_time: new Date().toISOString(),
        results,
      },
      buildIdempotencyKey()
    )
    ElMessage.success('检查报告提交成功')
    await loadTaskDetail()
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

const submitRectify = async () => {
  if (!taskId.value) {
    ElMessage.error('任务ID无效，无法提交整改')
    return
  }
  if (!canEditRectification.value) {
    ElMessage.warning('当前状态不可提交整改')
    return
  }

  const feedback = allItems.value
    .filter((item) => item.resultId && item.rectifyDesc.trim())
    .map((item) => ({
      result_id: item.resultId as number,
      description: item.rectifyDesc.trim(),
      photos: item.rectificationPhotos,
    }))

  if (!feedback.length) {
    ElMessage.warning('请至少填写一条整改描述')
    return
  }

  const currentUser = getStoredUserInfo<{ username?: string; id?: number }>()
  const rectifierId = currentUser?.username || (currentUser?.id ? String(currentUser.id) : 'unknown')

  submitLoading.value = true
  try {
    await submitWeeklyInspectionTask(taskId.value, {
      rectifier_id: rectifierId,
      feedback_per_item: feedback,
    })
    ElMessage.success('整改内容提交成功')
    await loadTaskDetail()
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadTaskDetail()
})
</script>

<style scoped>
.details-container {
  background: #E5E7EB;
  min-height: calc(100vh - 84px);
  padding: 20px;
}

/* ── Panel container (统一大白容器) ────────────────────── */
.panel-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

/* ── Page header card ──────────────────────────────────── */
.page-header-card {
  background: #fff;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #E5E7EB;
  margin-bottom: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px;
}

.page-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 14px;
  color: #666;
}

.meta-item {
  color: #606266;
}

.audit-alert {
  color: #e6a23c;
  font-size: 13px;
}

/* ── Main layout ─────────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 0;
  border-bottom: 1px solid #E5E7EB;
}

/* ── Sidebar panel ────────────────────────────────────── */
.sidebar-card {
  background: #F9FAFB;
  border-right: 1px solid #E5E7EB;
  overflow: hidden;
  align-self: stretch;
}

.sidebar-title {
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 700;
  color: #6B7280;
  border-bottom: 1px solid #E5E7EB;
  background: #F3F4F6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-item {
  padding: 11px 16px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  border-bottom: 1px solid #EAECEF;
  transition: all 0.15s;
}

.sidebar-item:last-child {
  border-bottom: none;
}

.sidebar-item:hover {
  background: #EFF6FF;
  color: #2563EB;
}

.sidebar-item.active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
  border-left: 3px solid #2563EB;
  padding-left: 13px;
}

/* ── Content area ────────────────────────────────── */
.content-area {  background: #F3F4F6;
  padding: 16px;  min-width: 0;
}

.col-header-row {
  display: flex;
  margin-bottom: 8px;
  gap: 8px;
}

.col-header-cell {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
}

.col-header-problem {
  flex: 0 0 calc(55% - 4px);
}

.col-header-rectify {
  flex: 1;
}

/* ── Item cards (card-in-card) ───────────────────────────── */
.item-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1px solid #E5E7EB;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.item-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 3px;
}

.item-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  line-height: 1.5;
}

.score-tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.card-body {
  padding: 14px 16px;
}

.card-body-split {
  display: flex;
  padding: 0;
}

.problem-section {
  flex: 0 0 55%;
  padding: 14px 16px;
  border-right: 1px solid #f0f2f5;
}

.rectify-section {
  flex: 1;
  padding: 14px 16px;
}

.section-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  margin-bottom: 6px;
}

.section-text {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 10px;
}

.no-photo-text {
  font-size: 13px;
  color: #909399;
}

/* ── Photos ──────────────────────────────────────── */
.photo-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.photo-thumb {
  width: 72px;
  height: 54px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  cursor: pointer;
}

.photo-box {
  position: relative;
  width: 72px;
  height: 54px;
}

.rm-photo {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

.upload-trigger {
  cursor: pointer;
}

.upload-input {
  display: none;
}

.upload-placeholder {
  width: 72px;
  height: 54px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  background: #fafafa;
}

/* ── Footer bar ──────────────────────────────────── */
.footer-bar {
  margin-top: 0;
  padding: 14px 24px;
  background: #fff;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

.status-tip {
  font-size: 14px;
}

.status-tip.submitted {
  color: #409eff;
}

.status-tip.rectified {
  color: #e6a23c;
}

.status-tip.completed {
  color: #67c23a;
}
</style>
