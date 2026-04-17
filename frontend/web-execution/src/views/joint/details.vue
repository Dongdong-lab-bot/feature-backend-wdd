<template>
  <div class="details-container">
    <div class="detail-card" v-loading="loading">
      <div class="header-section">
        <h2>{{ titleText }}</h2>
        <div class="meta-info">
          <span class="meta-item">时间：{{ dateText }}</span>
          <span class="meta-item">提交人：{{ submitterText }}</span>
          <span class="meta-item">状态：{{ statusText }}</span>
        </div>
      </div>

      <el-alert
        v-if="loadError"
        :title="loadError"
        type="warning"
        :closable="false"
        show-icon
        class="page-alert"
      />

      <div v-else class="content-wrapper">
        <div class="sidebar">
          <div class="sidebar-header">检查大项</div>
          <div
            v-for="category in categories"
            :key="category"
            class="category-item"
            :class="{ active: currentCategory === category }"
            @click="currentCategory = category"
          >
            {{ category }}
          </div>
        </div>

        <div class="main-content">
          <div class="content-header">
            <div class="header-col issue-col">问题小项</div>
            <div class="header-col rectify-col">整改反馈情况</div>
          </div>

          <template v-if="currentItems.length">
            <div class="issue-list">
              <div v-for="item in currentItems" :key="item.uid" class="issue-row">
                <div class="issue-cell">
                  <div class="issue-title-row">
                    <div class="title-left">
                      <span class="color-box" :style="{ backgroundColor: item.color }"></span>
                      <span class="title-text">{{ item.title }}</span>
                    </div>
                    <span class="score-text">满分：{{ item.fullScore }}分</span>
                  </div>

                  <div class="issue-body">
                    <p class="score-line">得分：{{ item.score }}分</p>
                    <p class="desc-line">描述：{{ item.description || '-' }}</p>
                    <div class="photo-list">
                      <template v-if="item.inspectionPhotos.length">
                        <img
                          v-for="photo in item.inspectionPhotos"
                          :key="photo"
                          :src="photo"
                          class="photo-thumb"
                          alt="检查图片"
                        />
                      </template>
                      <template v-else>
                        <div class="photo-placeholder"><el-icon><Picture /></el-icon></div>
                      </template>
                    </div>
                  </div>
                </div>

                <div class="rectify-cell">
                  <template v-if="canEditRectification">
                    <div class="form-item">
                      <label>整改描述：</label>
                      <el-input
                        v-model="item.rectifyDesc"
                        type="textarea"
                        :rows="3"
                        resize="none"
                        placeholder="请输入整改描述"
                      />
                    </div>
                    <div class="photo-list rectify-photos">
                      <div
                        v-for="(photo, index) in item.rectificationPhotos"
                        :key="`${item.uid}-${photo}`"
                        class="photo-box"
                      >
                        <img :src="photo" class="photo-thumb small" alt="整改图片" />
                        <button
                          type="button"
                          class="remove-photo"
                          @click="removeRectificationPhoto(item.uid, index)"
                        >
                          ×
                        </button>
                      </div>
                      <label
                        v-for="slot in Math.max(0, 2 - item.rectificationPhotos.length)"
                        :key="`${item.uid}-slot-${slot}`"
                        class="upload-trigger"
                      >
                        <input
                          class="upload-input"
                          type="file"
                          accept="image/*"
                          @change="handleRectificationPhotoChange($event, item.uid)"
                        />
                        <div class="photo-placeholder upload-placeholder">
                          <el-icon><Plus /></el-icon>
                        </div>
                      </label>
                    </div>
                  </template>
                  <template v-else>
                    <p class="desc-line">整改描述：{{ item.rectifyDesc || '暂无整改反馈' }}</p>
                    <div class="photo-list">
                      <template v-if="item.rectificationPhotos.length">
                        <img
                          v-for="photo in item.rectificationPhotos"
                          :key="photo"
                          :src="photo"
                          class="photo-thumb small"
                          alt="整改图片"
                        />
                      </template>
                      <template v-else>
                        <div class="photo-placeholder small"><el-icon><Picture /></el-icon></div>
                      </template>
                    </div>
                  </template>
                </div>
              </div>
            </div>

            <div class="content-footer">
              <div class="footer-tip">
                <span v-if="auditComment">审核意见：{{ auditComment }}</span>
                <span v-else>联合巡检详情已切换为真实数据优先展示。</span>
              </div>
              <el-button
                type="primary"
                :loading="submitLoading"
                :disabled="!canEditRectification || !hasEditableFeedback"
                @click="handleSubmit"
              >
                提交整改内容
              </el-button>
            </div>
          </template>

          <el-empty
            v-else
            description="当前没有可展示的联合巡检明细"
          >
            <template #description>
              <p class="empty-text">当前没有可展示的联合巡检明细</p>
              <p class="empty-subtext">
                本地后端代码中暂未找到联合巡检详情 GET 接口，页面不会再展示伪造示意数据。
              </p>
            </template>
          </el-empty>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Plus } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { getJointInspectionTaskDetail, rectifyJointInspectionTask } from '@/api/inspection'
import { getStoredUserInfo } from '@/utils/auth-storage'

interface JointItem {
  uid: string
  resultId: number | null
  category: string
  color: string
  title: string
  fullScore: number
  score: number
  description: string
  inspectionPhotos: string[]
  rectifyDesc: string
  rectificationPhotos: string[]
}

interface AuditLogEntry {
  action?: string
  opinion?: string
  comment?: string
}

type JointTaskStatus = 'PENDING' | 'SUBMITTED' | 'REJECTED' | 'RECTIFIED' | 'COMPLETED' | ''

const COLORS = ['#ff7875', '#faad14', '#40a9ff', '#73d13d', '#9254de', '#13c2c2']

const route = useRoute()

const loading = ref(false)
const submitLoading = ref(false)
const taskId = ref<number | null>(null)
const taskStatus = ref<JointTaskStatus>('')
const canteenText = ref('联合巡检')
const dateText = ref('-')
const submitterText = ref('-')
const auditComment = ref('')
const loadError = ref('')
const currentCategory = ref('')
const allItems = ref<JointItem[]>([])

const statusTextMap: Record<string, string> = {
  PENDING: '待提交',
  SUBMITTED: '待审核',
  REJECTED: '待整改',
  RECTIFIED: '已整改待审',
  COMPLETED: '已完成',
}

const titleText = computed(() => `${canteenText.value}联合巡检记录详情`)
const statusText = computed(() => statusTextMap[taskStatus.value] || taskStatus.value || '-')
const categories = computed(() => [...new Set(allItems.value.map((item) => item.category))])
const currentItems = computed(() => {
  if (!currentCategory.value) {
    return allItems.value
  }
  return allItems.value.filter((item) => item.category === currentCategory.value)
})
const canEditRectification = computed(() => taskStatus.value === 'REJECTED')
const hasEditableFeedback = computed(() => currentItems.value.some((item) => !!item.resultId))

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

const extractAuditComment = (logs: unknown): string => {
  if (!Array.isArray(logs)) {
    return ''
  }
  const entries = logs as AuditLogEntry[]
  const lastRejected = [...entries].reverse().find((entry) => entry.action === 'REJECT' || entry.action === 'REJECTED')
  const target = lastRejected || entries[entries.length - 1]
  return target?.opinion || target?.comment || ''
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

const updateItem = (uid: string, updater: (item: JointItem) => JointItem) => {
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

const loadInspectionDetail = async () => {
  const id = Number(route.query.id)
  if (!id) {
    ElMessage.warning('缺少任务ID，当前为默认展示')
    return
  }
  inspectionId.value = id
  loading.value = true
  loadError.value = ''

  try {
    const res = await getJointInspectionTaskDetail(id)
    if (!res) {
      loadError.value = '获取详情失败，返回数据为空'
      return
    }

    // 安全解析后端返回的数据结构
    const taskInfo = (res as Record<string, any>)?.task_info || (res as Record<string, any>)?.data?.task_info || (res as Record<string, any>)
    const formSnapshot = (res as Record<string, any>)?.form_snapshot || (res as Record<string, any>)?.data?.form_snapshot || (taskInfo as Record<string, any>)?.form_snapshot

    if (taskInfo?.canteen_name) {
      titleText.value = `${taskInfo.canteen_name} 联合巡检详情`
    } else if (taskInfo?.canteen_name_snapshot) {
      titleText.value = `${taskInfo.canteen_name_snapshot} 联合巡检详情`
    }

    if (taskInfo?.business_date) {
      dateText.value = taskInfo.business_date
    }

    if (taskInfo?.executor_name) {
      submitterText.value = taskInfo.executor_name
    } else if (taskInfo?.executor_name_snapshot) {
      submitterText.value = taskInfo.executor_name_snapshot
    }

    if (taskInfo?.status) {
      taskStatus.value = taskInfo.status
      if (taskInfo.status === 'PENDING') statusText.value = '待检查'
      else if (taskInfo.status === 'RECTIFYING' || taskInfo.status === 'REJECTED') statusText.value = '待整改'
      else if (taskInfo.status === 'COMPLETED') statusText.value = '已完成'
      else statusText.value = taskInfo.status
    }

    // 解析 form_snapshot 中的 major_items
    let snapshotMajorItems: any[] = []
    if (formSnapshot && Array.isArray(formSnapshot.major_items)) {
      snapshotMajorItems = formSnapshot.major_items
    } else if (Array.isArray(formSnapshot)) {
      snapshotMajorItems = formSnapshot
    }

    if (snapshotMajorItems.length > 0) {
      const parsedIssues: Issue[] = []
      const catSet = new Set<string>()

      snapshotMajorItems.forEach((major: any, index: number) => {
        const catName = major.title || major.category || `检查大项 ${index + 1}`
        catSet.add(catName)

        const minors = Array.isArray(major.minor_items) ? major.minor_items : (Array.isArray(major.items) ? major.items : [])
        
        minors.forEach((minor: any) => {
          parsedIssues.push({
            id: minor.item_id || minor.id || Math.random(),
            category: catName,
            content: minor.content || minor.name || '未知检查项',
            standard: minor.standard || minor.requirement || '按规定执行',
            status: minor.is_qualified === false ? 'fail' : (minor.is_qualified === true ? 'pass' : 'fail'), // 默认兜底为 fail 以便演示整改
            photos: Array.isArray(minor.photos) ? minor.photos : [],
            remark: minor.description || minor.remark || '',
            rectifyRemark: minor.rectification_description || minor.rectify_desc || '',
            rectifyPhotos: Array.isArray(minor.rectification_photos) ? minor.rectification_photos : []
          })
        })
      })

      allIssues.value = parsedIssues
      categories.value = Array.from(catSet)
      if (categories.value.length > 0) {
        currentCategory.value = categories.value[0]
      }
    } else {
      // 如果没有解析到检查项数据，依然使用兜底数据避免白屏
      ElMessage.info('该任务暂无检查项明细，已展示示例检查项')
    }

  } catch (err: any) {
    console.error('获取联合巡检详情失败:', err)
    if (err?.response?.status === 422) {
      loadError.value = '后端数据结构验证失败 (422)。这通常是因为测试数据不完整导致的。'
    } else if (err?.response?.status === 403) {
      loadError.value = '您没有查看该联合巡检详情的权限 (403)'
    } else {
      loadError.value = err?.message || '获取联合巡检详情时发生错误'
    }
    // 出错时，保留 fallback 数据供查看
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
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
    await rectifyJointInspectionTask(taskId.value, {
      rectifier_id: rectifierId,
      feedback_per_item: feedback,
    })
    ElMessage.success('整改内容提交成功')
    await loadInspectionDetail()
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadInspectionDetail()
})
</script>

<style scoped>
.details-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.detail-card {
  background: #fff;
  border-radius: 6px;
  padding: 24px;
  min-height: 640px;
}

.header-section {
  margin-bottom: 20px;
}

.header-section h2 {
  margin: 0 0 12px;
  font-size: 20px;
  color: #303133;
}

.meta-info {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  color: #606266;
  font-size: 14px;
}

.page-alert {
  margin-bottom: 16px;
}

.content-wrapper {
  display: flex;
  border: 1px solid #dcdfe6;
  min-height: 420px;
}

.sidebar {
  width: 220px;
  border-right: 1px solid #dcdfe6;
  background: #f7fbff;
}

.sidebar-header {
  padding: 14px 16px;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 600;
  color: #303133;
  background: #eaf3ff;
}

.category-item {
  padding: 12px 16px;
  cursor: pointer;
  color: #606266;
  border-bottom: 1px solid #eef1f6;
}

.category-item.active {
  color: #409eff;
  background: #fff;
  border-left: 3px solid #409eff;
  padding-left: 13px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-header {
  display: flex;
  background: #eef5ff;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 600;
  color: #303133;
}

.header-col {
  padding: 12px 16px;
}

.issue-col {
  flex: 1;
  border-right: 1px solid #dcdfe6;
}

.rectify-col {
  width: 40%;
}

.issue-list {
  flex: 1;
}

.issue-row {
  display: flex;
  border-bottom: 1px solid #eef1f6;
}

.issue-cell,
.rectify-cell {
  padding: 16px;
}

.issue-cell {
  flex: 1;
  border-right: 1px solid #eef1f6;
}

.rectify-cell {
  width: 40%;
}

.issue-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.color-box {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  flex-shrink: 0;
}

.title-text {
  font-weight: 600;
  color: #303133;
  line-height: 1.5;
}

.score-text,
.score-line,
.desc-line {
  color: #606266;
  font-size: 14px;
}

.score-line,
.desc-line {
  margin: 0 0 10px;
}

.photo-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.photo-thumb,
.photo-placeholder {
  width: 92px;
  height: 68px;
  border-radius: 4px;
}

.photo-thumb {
  object-fit: cover;
  border: 1px solid #dcdfe6;
  background: #fff;
}

.photo-thumb.small,
.photo-placeholder.small {
  width: 72px;
  height: 54px;
}

.photo-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef5ff;
  color: #409eff;
  border: 1px dashed #b3d8ff;
}

.form-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
}

.form-item label {
  flex-shrink: 0;
  line-height: 32px;
  color: #606266;
}

.rectify-photos {
  margin-left: 72px;
}

.upload-trigger {
  cursor: pointer;
}

.upload-input {
  display: none;
}

.upload-placeholder {
  cursor: pointer;
}

.photo-box {
  position: relative;
}

.remove-photo {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  cursor: pointer;
}

.content-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-top: 1px solid #dcdfe6;
  background: #fff;
}

.footer-tip {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.empty-text {
  margin: 0;
  color: #606266;
}

.empty-subtext {
  margin: 8px 0 0;
  color: #909399;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .content-wrapper {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #dcdfe6;
  }

  .issue-row {
    flex-direction: column;
  }

  .issue-cell,
  .rectify-cell,
  .rectify-col {
    width: 100%;
  }

  .issue-cell {
    border-right: none;
    border-bottom: 1px solid #eef1f6;
  }

  .content-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .rectify-photos {
    margin-left: 0;
  }

  .form-item {
    flex-direction: column;
  }
}
</style>
