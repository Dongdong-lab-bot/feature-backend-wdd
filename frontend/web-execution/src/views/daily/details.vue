<template>
  <div class="app-container">
    <div class="detail-card" v-loading="loading">
      <div class="header-section">
        <h2>{{ titleText }}</h2>
        <div class="meta-info">
          <span class="label">时间：</span>
          <span class="value">{{ dateText }}</span>
          <span class="label ml-20">提交人：</span>
          <span class="value">{{ submitterText }}</span>
        </div>
      </div>

      <template v-if="taskStatus === 'NO_TASK'">
        <div class="no-task-banner">
          <el-icon style="margin-right:6px"><InfoFilled /></el-icon>
          正在创建今日任务，请稍候...
        </div>
      </template>

      <template v-else>
        <div class="body-layout">
          <div class="items-area">
            <div class="items-grid">
              <div
                v-for="(item, index) in formItems"
                :key="`item-${index}-${item.item_id}`"
                class="item-card"
                :class="{ 'item-qualified': item.is_qualified === true, 'item-unqualified': item.is_qualified === false }"
              >
                <div class="item-title">{{ index + 1 }}、{{ item.content }}</div>

                <template v-if="taskStatus !== 'PENDING'">
                  <div v-if="item.description" class="item-desc">说明：{{ item.description }}</div>
                </template>

                <div class="photo-row">
                  <!-- REJECTED：分行展示「整改前」只读 + 「整改后」可添加 -->
                  <template v-if="taskStatus === 'REJECTED'">
                    <div class="photo-sections">
                      <div class="photo-section">
                        <span class="photo-section-label">整改前</span>
                        <div class="photo-list">
                          <div
                            v-for="(photo, pi) in item.originalPhotos"
                            :key="`orig-${pi}`"
                            class="photo-box"
                          >
                            <el-image :src="photo" class="photo-thumb" fit="cover" :preview-src-list="item.originalPhotos" :initial-index="pi" preview-teleported />
                          </div>
                          <div v-if="!item.originalPhotos.length" class="photo-placeholder photo-empty">
                            <el-icon><Picture /></el-icon>
                          </div>
                        </div>
                      </div>
                      <div class="photo-section">
                        <span class="photo-section-label">整改后</span>
                        <div class="photo-list">
                          <div
                            v-for="(photo, pi) in item.photos"
                            :key="`rect-${pi}`"
                            class="photo-box"
                          >
                            <img :src="photo" class="photo-thumb" alt="整改照片" />
                            <button
                              type="button"
                              class="remove-photo"
                              @click="removePhoto(item, pi)"
                            >×</button>
                          </div>
                          <label class="upload-trigger">
                            <input
                              class="upload-input"
                              type="file"
                              accept="image/*"
                              @change="handlePhotoChange($event, item)"
                            />
                            <div class="photo-add-btn"><el-icon><Plus /></el-icon></div>
                          </label>
                        </div>
                      </div>
                    </div>
                  </template>
                  <!-- PENDING：正常上传/删除 -->
                  <template v-else-if="taskStatus === 'PENDING'">
                    <div
                      v-for="(photo, pi) in item.photos.slice(0, 2)"
                      :key="pi"
                      class="photo-box"
                    >
                      <img :src="photo" class="photo-thumb" alt="照片" />
                      <button
                        type="button"
                        class="remove-photo"
                        @click="removePhoto(item, pi)"
                      >×</button>
                    </div>
                    <label
                      v-for="slot in Math.max(0, 2 - item.photos.length)"
                      :key="`slot-${slot}`"
                      class="upload-trigger"
                    >
                      <input
                        class="upload-input"
                        type="file"
                        accept="image/*"
                        @change="handlePhotoChange($event, item)"
                      />
                      <div class="photo-placeholder"><el-icon><Picture /></el-icon></div>
                    </label>
                  </template>
                  <!-- RECTIFIED/COMPLETED：分行只读展示 -->
                  <template v-else>
                    <template v-if="item.rectificationPhotos.length > 0">
                      <div class="photo-sections">
                        <div class="photo-section">
                          <span class="photo-section-label">整改前</span>
                          <div class="photo-list">
                            <div v-for="(photo, pi) in item.originalPhotos" :key="`ro-${pi}`" class="photo-box">
                              <el-image :src="photo" class="photo-thumb" fit="cover" :preview-src-list="item.originalPhotos" :initial-index="pi" preview-teleported />
                            </div>
                            <div v-if="!item.originalPhotos.length" class="photo-placeholder photo-empty">
                              <el-icon><Picture /></el-icon>
                            </div>
                          </div>
                        </div>
                        <div class="photo-section">
                          <span class="photo-section-label">整改后</span>
                          <div class="photo-list">
                            <div v-for="(photo, pi) in item.rectificationPhotos" :key="`rp-${pi}`" class="photo-box">
                              <el-image :src="photo" class="photo-thumb" fit="cover" :preview-src-list="item.rectificationPhotos" :initial-index="pi" preview-teleported />
                            </div>
                            <div v-if="!item.rectificationPhotos.length" class="photo-placeholder photo-empty">
                              <el-icon><Picture /></el-icon>
                            </div>
                          </div>
                        </div>
                      </div>
                    </template>
                    <template v-else>
                      <div v-for="(photo, pi) in item.photos.slice(0, 2)" :key="pi" class="photo-box">
                        <el-image :src="photo" class="photo-thumb" fit="cover" :preview-src-list="item.photos" :initial-index="pi" preview-teleported />
                      </div>
                      <template v-if="!item.photos.length">
                        <div class="photo-placeholder"><el-icon><Picture /></el-icon></div>
                        <div class="photo-placeholder"><el-icon><Picture /></el-icon></div>
                      </template>
                    </template>
                  </template>
                </div>
              </div>
            </div>
            <div v-if="!loading && formItems.length === 0" class="empty-tip">暂无检查项数据</div>
          </div>

          <div class="right-panel">
            <template v-if="taskStatus === 'PENDING'">
              <div class="panel-block blue-panel">
                <div class="panel-label panel-label-light">填写说明:</div>
                <div class="panel-note">请为每项检查上传现场图片，确认无误后提交。</div>
              </div>
              <div class="panel-footer pending-footer">
                <el-button
                  type="primary"
                  :loading="submitLoading"
                  class="submit-btn"
                  @click="handleInitialSubmit"
                >提交</el-button>
              </div>
            </template>
            <template v-else-if="taskStatus === 'SUBMITTED'">
              <div class="panel-block blue-panel">
                <div class="panel-note" style="text-align:center;padding:24px 0;">已提交，等待监管端审核中…</div>
              </div>
            </template>
            <template v-else-if="taskStatus === 'REJECTED'">
              <div class="panel-block blue-panel">
                <div class="panel-label panel-label-light">审核评论:</div>
                <el-input
                  v-model="auditComment"
                  type="textarea"
                  :rows="6"
                  readonly
                  resize="none"
                  placeholder="暂无审核评论"
                  class="panel-textarea pending-textarea"
                />
                <div class="panel-label panel-label-light">整改回复:</div>
                <el-input
                  v-model="rectifyDesc"
                  type="textarea"
                  :rows="8"
                  resize="none"
                  placeholder="请填写整改回复内容"
                  class="panel-textarea pending-textarea"
                  :readonly="isRectified"
                />
              </div>
              <div class="panel-footer pending-footer">
                <el-button
                  v-if="!isRectified"
                  type="primary"
                  :loading="submitLoading"
                  class="submit-btn"
                  @click="handleSubmit"
                >提交整改</el-button>
                <span v-else class="rectified-tag">已提交整改</span>
              </div>
            </template>
            <template v-else>
              <div class="panel-block blue-panel">
                <div class="panel-note" style="text-align:center;padding:24px 0;">
                  {{ taskStatus === 'COMPLETED' ? '已完成' : '已提交整改，等待复审' }}
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 历史整改记录（在 body-layout 下方整行展示） -->
        <div v-if="rectifyHistory.length" class="rectify-history">
          <div class="rh-title">历史整改记录</div>
          <div
            v-for="(entry, idx) in rhPagedHistory"
            :key="idx"
            class="rh-item"
          >
            <div class="rh-header">
              <span class="rh-round">第 {{ (rhCurrentPage - 1) * 3 + idx + 1 }} 次整改</span>
              <span class="rh-time">{{ entry.rectified_at ? entry.rectified_at.slice(0, 16).replace('T', ' ') : '' }}</span>
            </div>
            <div v-if="entry.desc" class="rh-desc">整改说明：{{ entry.desc }}</div>
            <div v-if="entry.photos.length" class="rh-photos">
              <div v-for="(p, pi) in entry.photos" :key="pi" class="photo-box">
                <el-image
                  :src="p"
                  class="photo-thumb"
                  fit="cover"
                  :preview-src-list="entry.photos"
                  :initial-index="pi"
                  preview-teleported
                />
              </div>
            </div>
          </div>
          <el-pagination
            v-if="rectifyHistory.length > 3"
            v-model:current-page="rhCurrentPage"
            :page-size="3"
            :total="rectifyHistory.length"
            layout="prev, pager, next"
            class="rh-pagination"
            small
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled, Picture, Plus } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getDailyControlTaskDetail, rectifyDailyControlTask, startDailyControlTask, submitDailyControlTask } from '@/api/inspection'
import { getStoredUserInfo } from '@/utils/auth-storage'

interface FormItem {
  item_id: number | null
  result_id: number | null
  content: string
  is_qualified: boolean | null
  description: string
  photos: string[]          // PENDING：原始照片；REJECTED：整改时新增照片
  originalPhotos: string[] // REJECTED：只读的整改前照片
  rectificationPhotos: string[] // 整改后上传的照片（只读展示）
  rectification_description: string | null
}

interface AuditLogEntry {
  action?: string
  opinion?: string
  comment?: string
  auditor_id?: string
  created_at?: string
  audited_at?: string
  rectifier_id?: string
  rectified_at?: string
  items?: { result_id: number; description: string; photos: string[] }[]
}

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitLoading = ref(false)
const taskId = ref<number | null>(null)
const taskStatus = ref('')
const canteenText = ref('-')
const dateText = ref('-')
const submitterText = ref('-')
const formItems = ref<FormItem[]>([])
const auditLogs = ref<AuditLogEntry[]>([])
const auditComment = ref('')
const rectifyDesc = ref('')
const isRectified = ref(false)

const titleText = computed(() => `${canteenText.value}食堂日管控记录`)

// 从 audit_logs 中提取所有 RECTIFY 条目展示历史
const rectifyHistory = computed(() => {
  return auditLogs.value
    .filter(l => l.action === 'RECTIFY')
    .map(l => ({
      rectified_at: l.rectified_at || '',
      desc: l.items?.map(i => i.description).filter(Boolean).find(Boolean) || '',
      photos: l.items?.flatMap(i => i.photos || []) || [],
    }))
})

const RH_PAGE_SIZE = 3
const rhCurrentPage = ref(1)
const rhPagedHistory = computed(() => {
  const start = (rhCurrentPage.value - 1) * RH_PAGE_SIZE
  return rectifyHistory.value.slice(start, start + RH_PAGE_SIZE)
})

const loadDetail = async () => {
  const queryId = Number(route.query.id)
  const templateId = Number(route.query.templateId)
  loading.value = true
  try {
    // 确定有效 taskId：优先用 URL 中的 id，否则按 templateId 创建/获取今日任务
    let effectiveTaskId = queryId || 0
    if (!effectiveTaskId && templateId) {
      try {
        const startResp = await startDailyControlTask(templateId) as Record<string, unknown>
        effectiveTaskId = Number(startResp?.task_id ?? 0)
        if (!effectiveTaskId) throw new Error('no task_id')
      } catch {
        ElMessage.warning('无法创建今日任务，请联系管理员确认模板配置')
        router.replace('/daily/checklist')
        return
      }
    }
    if (!effectiveTaskId) {
      ElMessage.warning('缺少任务ID，即将返回列表')
      router.replace('/daily/checklist')
      return
    }
    taskId.value = effectiveTaskId
    const data = await getDailyControlTaskDetail(effectiveTaskId) as Record<string, unknown>
    if (!data) return

    const info = data.task_info as Record<string, unknown> | undefined
    if (info) {
      taskStatus.value = String(info.status || '')
      canteenText.value = String(info.canteen_name || '-')
      submitterText.value = String(info.inspector_name || '-')
      const rawDate = String(info.submission_date || info.actual_start_time || '')
      const dt = new Date(rawDate)
      dateText.value = Number.isNaN(dt.getTime())
        ? rawDate.slice(0, 10) || '-'
        : `${dt.getFullYear()}.${dt.getMonth() + 1}.${dt.getDate()}`
    }

    const snapshot = data.form_snapshot as Array<Record<string, unknown>> | undefined
    if (Array.isArray(snapshot)) {
      console.log('[DEBUG] API返回的原始snapshot数据:', JSON.parse(JSON.stringify(snapshot)))
      console.log('[DEBUG] 原始snapshot中每个item的result_id字段:', snapshot.map((item, idx) => ({
        index: idx,
        content: item.content,
        item_id: item.item_id,
        hasResultId: 'result_id' in item,
        result_id_value: item.result_id,
        allKeys: Object.keys(item)
      })))
      formItems.value = snapshot.map((item) => ({
        item_id: item.item_id ? Number(item.item_id) : null,
        result_id: item.result_id ? Number(item.result_id) : null,
        content: String(item.content || '-'),
        is_qualified: typeof item.is_qualified === 'boolean' ? item.is_qualified : null,
        description: item.description ? String(item.description) : '',
        photos: Array.isArray(item.photos) ? (item.photos as string[]) : [],
        originalPhotos: [],
        rectificationPhotos: Array.isArray(item.rectification_photos) ? (item.rectification_photos as string[]) : [],
        rectification_description: item.rectification_description ? String(item.rectification_description) : null,
      }))
      console.log('[DEBUG] 转换后的formItems (包含result_id):', formItems.value.map(i => ({
        item_id: i.item_id,
        result_id: i.result_id,
        content: i.content
      })))
    
    

      if (taskStatus.value === 'PENDING') {
        formItems.value = formItems.value.map(item => ({
          ...item,
          is_qualified: item.is_qualified ?? true,
        }))
      }

      // REJECTED 状态：原始照片保留只读，清空 photos 供整改时新增
      if (taskStatus.value === 'REJECTED') {
        formItems.value = formItems.value.map(item => ({
          ...item,
          originalPhotos: [...item.photos],
          photos: [],
        }))
      }
      // RECTIFIED/COMPLETED 状态：只读展示整改前+整改后
      if (['RECTIFIED', 'COMPLETED', 'SIGNED', 'ARCHIVED'].includes(taskStatus.value)) {
        formItems.value = formItems.value.map(item => ({
          ...item,
          originalPhotos: [...item.photos],
        }))
      }

      // 如果有整改描述，取第一条填入右侧（仅非 REJECTED 状态）
      if (taskStatus.value !== 'REJECTED') {
        const firstRectify = formItems.value.find((i) => i.rectification_description)
        if (firstRectify?.rectification_description) {
          rectifyDesc.value = firstRectify.rectification_description
          isRectified.value = true
        }
      } else {
        // REJECTED 状态下清空 isRectified，允许重新提交整改
        isRectified.value = false
        rectifyDesc.value = ''
      }
    }

    // 从 audit_logs 取最近一条审核意见
const logs = data.audit_logs as AuditLogEntry[] | undefined
    if (Array.isArray(logs) && logs.length > 0) {
      auditLogs.value = logs
      const lastReject = [...logs].reverse().find(
        (l) => l.action === 'REJECT' || l.action === 'REJECTED'
      )
      const entry = lastReject || logs[logs.length - 1]
      auditComment.value = entry.opinion || entry.comment || ''
    }
  } catch {
    ElMessage.warning('获取任务详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleInitialSubmit = async () => {
  if (!taskId.value) {
    ElMessage.warning('当前模板暂无待提交任务，暂不能提交，只能填写预览')
    return
  }
  const items = formItems.value
  if (items.length === 0) {
    ElMessage.warning('检查项数据未加载，请刷新页面')
    return
  }
  if (items.some(item => item.item_id === null)) {
    ElMessage.warning('存在无效检查项，暂无法提交')
    return
  }
  const currentUser = getStoredUserInfo<{ username?: string; id?: number }>()
  const submitterId = currentUser?.username || (currentUser?.id ? String(currentUser.id) : 'unknown')
  const results = items.map((i) => ({
    item_id: i.item_id as number,
    is_qualified: true,
    description: '',
    photos: i.photos,
  }))
  submitLoading.value = true
  try {
    await submitDailyControlTask(taskId.value, {
      submitter_id: submitterId,
      actual_start_time: new Date().toISOString(),
      results,
    })
    ElMessage.success('日管控提交成功')
    router.replace('/daily/records')
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!taskId.value) return
  if (!rectifyDesc.value.trim()) {
    ElMessage.warning('请填写整改回复内容')
    return
  }

  const resultIds = formItems.value
    .filter((i) => i.result_id !== null)
    .map((i) => ({ result_id: i.result_id as number, description: rectifyDesc.value.trim(), photos: i.photos }))

  console.log('[DEBUG handleSubmit] formItems中的result_id值:', formItems.value.map(i => i.result_id))
  console.log('[DEBUG handleSubmit] 过滤后的resultIds:', resultIds)

  if (resultIds.length === 0) {
    ElMessage.warning('当前任务暂无可整改项（检查项未提交结果）')
    return
  }

  const currentUser = getStoredUserInfo<{ username?: string; id?: number }>()
  const rectifierId = currentUser?.username || (currentUser?.id ? String(currentUser.id) : 'unknown')

  submitLoading.value = true
  try {
    await rectifyDailyControlTask(taskId.value, {
      rectifier_id: rectifierId,
      feedback_per_item: resultIds,
    })
    ElMessage.success('整改回复提交成功')
    isRectified.value = true
    await loadDetail()
  } catch {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

const handlePhotoChange = async (event: Event, item: FormItem) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  // PENDING 状态限制 2 张；REJECTED 不限张数
  if (taskStatus.value === 'PENDING' && item.photos.length >= 2) {
    ElMessage.warning('每项最多上传2张图片')
    target.value = ''
    return
  }
  const maxSizeBytes = 2 * 1024 * 1024 // 2MB
  if (file.size > maxSizeBytes) {
    ElMessage.warning('图片大小不能超过2MB，请压缩后重试')
    target.value = ''
    return
  }
  const dataUrl = await readAsDataUrl(file)
  item.photos = [...item.photos, dataUrl]
  target.value = ''
}

const removePhoto = (item: FormItem, index: number) => {
  item.photos = item.photos.filter((_, photoIndex) => photoIndex !== index)
}

const readAsDataUrl = (file: File): Promise<string> => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(String(reader.result || ''))
  reader.onerror = () => reject(reader.error)
  reader.readAsDataURL(file)
})

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.detail-card {
  background: #fff;
  border-radius: 4px;
  padding: 24px;
  min-height: 600px;
}

.header-section {
  margin-bottom: 24px;
}

.header-section h2 {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin: 0 0 12px;
}

.meta-info {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.meta-info .label {
  color: #606266;
}

.ml-20 {
  margin-left: 40px;
}

.body-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

/* 左侧检查项网格 */
.items-area {
  flex: 1;
  min-width: 0;
}

.items-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.item-card {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px 14px;
  background: #f5f7fa;
}

.item-card.item-unqualified {
  border-color: #ffa0a0;
  background: #fff0f0;
}

.item-card.item-qualified {
  border-color: #b7e4c7;
  background: #f0fff4;
}

.item-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 10px;
  line-height: 1.5;
  word-break: break-all;
}

.item-editor-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.editor-label {
  flex-shrink: 0;
  font-size: 13px;
  color: #606266;
}

.radio-group {
  display: flex;
  gap: 14px;
}

.item-desc-input {
  margin-bottom: 10px;
}

.item-desc {
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.photo-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.photo-sections {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.photo-section {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.photo-section-label {
  flex-shrink: 0;
  font-size: 12px;
  color: #909399;
  line-height: 56px;
  width: 36px;
}

.photo-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.photo-add-btn {
  width: 72px;
  height: 56px;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #909399;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.photo-add-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.photo-empty {
  opacity: 0.4;
}

.photo-placeholder {
  width: 72px;
  height: 56px;
  background: #dbeffe;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #409eff;
}

.photo-box {
  position: relative;
}

.photo-thumb {
  width: 72px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
}

.upload-trigger {
  cursor: pointer;
}

.upload-input {
  display: none;
}

.remove-photo {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  line-height: 18px;
  cursor: pointer;
}

.photo-badge {
  position: absolute;
  bottom: 2px;
  left: 2px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 10px;
  line-height: 1;
  padding: 2px 4px;
  border-radius: 3px;
  pointer-events: none;
}

.no-task-banner {
  display: flex;
  align-items: center;
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 4px;
  padding: 10px 16px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #d46b08;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

/* 历史整改记录 */
.rectify-history {
  margin-top: 20px;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.rh-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.rh-item {
  background: #f9f9f9;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px 14px;
  margin-bottom: 10px;
}

.rh-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.rh-round {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
}

.rh-time {
  font-size: 12px;
  color: #909399;
}

.rh-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.5;
}

.rh-photos {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rh-pagination {
  margin-top: 10px;
  justify-content: center;
}

/* 右侧面板 */
.right-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.blue-panel {
  background: #4f89e8;
  padding: 14px;
  border-radius: 0;
}

.panel-label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.panel-label-light {
  color: #fff;
}

.panel-note {
  min-height: 110px;
  padding: 12px;
  background: #fff;
  color: #606266;
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 12px;
}

.panel-textarea {
  background: #dbeffe;
}

.pending-textarea {
  background: transparent;
}

.panel-textarea :deep(.el-textarea__inner) {
  background: #fff;
  border: none;
  border-radius: 0;
  resize: none;
  font-size: 13px;
  color: #333;
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
}

.pending-footer {
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  background-color: #1976d2;
  border-color: #1976d2;
}

.rectified-tag {
  font-size: 13px;
  color: #67c23a;
  background: #f0f9eb;
  border: 1px solid #b3e19d;
  padding: 4px 12px;
  border-radius: 4px;
}

@media (max-width: 1200px) {
  .body-layout {
    flex-direction: column;
  }

  .right-panel {
    width: 100%;
  }
}
</style>
