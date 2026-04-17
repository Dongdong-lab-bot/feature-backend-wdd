<template>
  <div v-if="isCreateView" class="create-view">
    <div class="create-topbar">
      <div class="create-title">新建日管控检查表</div>
      <el-select v-model="createForm.approverRole" class="approver-top-select" placeholder="上级监管员">
        <el-option v-for="item in userOptions" :key="item.id" :label="item.name" :value="item.name" />
      </el-select>
      <el-button type="primary" class="save-btn" @click="handleSaveTemplate">保存</el-button>
    </div>

    <div class="create-card">
      <div class="form-grid">
        <div class="form-item">
          <label>检查表名称</label>
          <el-input v-model="createForm.name" />
        </div>
        <div class="form-item">
          <label>检查表执行人员</label>
          <el-select v-model="createForm.executorRole" placeholder="请选择执行人角色">
            <el-option v-for="item in userOptions" :key="`executor-${item.id}`" :label="item.name" :value="item.name" />
          </el-select>
        </div>
        <div class="form-item time-item">
          <label>开始提交时间</label>
          <div class="time-wrap">
            <el-time-picker v-model="createForm.startTime" value-format="HH:mm" format="HH:mm" />
            <span class="deadline-label">截止时间:</span>
            <el-time-picker v-model="createForm.endTime" value-format="HH:mm" format="HH:mm" />
          </div>
        </div>
        <div class="form-item">
          <label>检查表覆盖食堂</label>
          <el-select v-model="createForm.canteenIds" multiple collapse-tags placeholder="请选择食堂">
            <el-option v-for="item in canteenOptions" :key="`canteen-${item.id}`" :label="item.name" :value="String(item.id)" />
          </el-select>
        </div>
        <div class="form-item">
          <label>审批人员</label>
          <el-select v-model="createForm.approverRole" placeholder="请选择审批人角色">
            <el-option v-for="item in userOptions" :key="`approver-${item.id}`" :label="item.name" :value="item.name" />
          </el-select>
        </div>
      </div>

      <div class="item-header">
        <span>添加检查项</span>
        <el-button class="add-item-btn" @click="addCheckItem">新增检查项</el-button>
      </div>

      <div class="item-table">
        <div v-for="(item, index) in checkItems" :key="item.uid" class="item-row">
          <div class="index-cell">{{ index + 1 }}</div>
          <el-input v-model="item.content" class="content-cell" placeholder="请输入检查项内容" />
          <div class="mode-cell">
            <span class="mode-label">完成方式</span>
            <el-radio-group v-model="item.mode">
              <el-radio label="CONFIRM">仅确认</el-radio>
              <el-radio label="PHOTO">必须拍照</el-radio>
              <el-radio label="FILL">必须填报</el-radio>
            </el-radio-group>
          </div>
          <el-button link type="danger" @click="removeCheckItem(item.uid)">删除</el-button>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="isChecklistView" class="checklist-view">
    <div class="checklist-title">日管控模板</div>

    <div v-loading="templateLoading" class="template-list">
      <div v-for="item in templateCards" :key="item.id" class="template-card">
        <div class="card-left-accent"></div>
        <div class="card-main">
          <div class="card-name">{{ item.name }}</div>
          <div class="card-desc">需完成{{ item.taskCount }}项</div>
        </div>
        <div class="card-toggle-wrap">
          <span class="toggle-label">是否启用</span>
          <el-switch :model-value="item.enabled" @change="() => handleToggleEnable(item)" />
        </div>
        <div class="card-actions">
          <el-button class="outline-btn" @click="handleCoverUsers(item)">覆盖人员</el-button>
          <el-button class="outline-btn" @click="handleCoverCanteens(item)">覆盖食堂</el-button>
          <el-button type="primary" class="edit-btn" @click="handleEditTemplate(item)">编辑</el-button>
          <el-button type="danger" class="delete-btn" @click="handleDeleteTemplate(item)">删除</el-button>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="record-view">
    <header class="rv-header">
      <div class="title">日管理记录查看</div>
      <div class="controls">
        <div class="control-item">
          <span class="label">起止日期</span>
          <el-date-picker
            v-model="queryParams.dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </div>
        <div class="control-item">
          <span class="label">食堂</span>
          <el-select v-model="queryParams.canteenId" placeholder="全部食堂" style="width: 160px">
            <el-option label="全部食堂" value="" />
            <el-option v-for="item in canteenOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </div>
        <div class="control-item">
          <span class="label">状态</span>
          <el-select v-model="queryParams.status" placeholder="全部状态" style="width: 140px">
            <el-option label="全部状态" value="" />
            <el-option label="待提交" value="待提交" />
            <el-option label="待审核" value="待审核" />
            <el-option label="待整改" value="待整改" />
            <el-option label="已整改" value="已整改" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </div>
        <div class="control-item">
          <span class="label">搜索</span>
          <el-input v-model="queryParams.keyword" placeholder="搜索提交食堂/提交人/表格" style="width: 240px" clearable />
        </div>
      </div>
    </header>

    <div class="table-container">
      <el-table
        :data="pagedData"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
      >
        <el-table-column prop="canteen" label="提交食堂" min-width="170" show-overflow-tooltip />
        <el-table-column prop="submitter" label="提交人" min-width="120" />
        <el-table-column prop="form" label="提交表格" min-width="170" show-overflow-tooltip />
        <el-table-column prop="completed" label="日管理完成项" min-width="130" align="center" />
        <el-table-column prop="date" label="提交日期" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="90" align="center">
          <template #default="scope">
            <span :class="getStatusClass(scope.row.status)">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="130" align="center">
          <template #default="scope">
            <el-button link type="primary" @click="handleView(scope.row)">查看</el-button>
            <el-button link type="primary" @click="handleCancel(scope.row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <footer class="rv-footer">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </footer>
  </div>

  <!-- 日管控审核对话框 -->
  <el-dialog
    v-model="auditDialogVisible"
    :title="`日管控审核 — ${auditTaskInfo?.canteen || ''} #${auditTaskInfo?.taskId || ''}`"
    width="760px"
    align-center
    :close-on-click-modal="false"
  >
    <div v-if="auditTaskInfo" class="audit-task-meta">
      <span>食堂：{{ auditTaskInfo.canteen }}</span>
      <span>提交人：{{ auditTaskInfo.submitter }}</span>
      <span>提交时间：{{ auditTaskInfo.submissionDate }}</span>
      <el-tag :type="statusTagType(auditTaskInfo.status)" size="small">{{ auditTaskInfo.statusText }}</el-tag>
    </div>

    <div class="audit-items-wrap">
      <el-table :data="auditItems" size="small" style="width: 100%" max-height="320">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="content" label="检查内容" min-width="240" show-overflow-tooltip />
        <el-table-column label="现场照片" min-width="140" align="center">
          <template #default="scope">
            <div v-if="scope.row.photos && scope.row.photos.length" class="audit-photos">
              <el-image
                v-for="(photo, pi) in scope.row.photos.slice(0, 2)"
                :key="pi"
                :src="photo"
                class="audit-photo-thumb"
                fit="cover"
                :preview-src-list="scope.row.photos"
                :initial-index="pi"
                preview-teleported
              />
            </div>
            <span v-else class="audit-status-na">无</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-if="auditLogs.length" class="audit-log-wrap">
      <div class="audit-log-title">历史审核记录</div>

      <!-- 按轮次平铺展示 -->
      <div v-for="(round, ri) in auditRounds" :key="ri" class="round-row">
        <div class="round-row-left">
          <span class="round-index">第 {{ ri + 1 }} 轮</span>
          <el-tag type="danger" size="small">驳回</el-tag>
          <span class="round-time">{{ (round.reject.audited_at || round.reject.created_at || '').slice(0, 10) }}</span>
          <span v-if="round.reject.opinion" class="round-opinion">{{ round.reject.opinion }}</span>
          <template v-if="round.rectify">
            <el-divider direction="vertical" />
            <el-tag type="warning" size="small">已整改</el-tag>
            <span class="round-time">{{ (round.rectify.rectified_at || '').slice(0, 10) }}</span>
          </template>
          <template v-else>
            <el-divider direction="vertical" />
            <el-tag type="info" size="small">待整改</el-tag>
          </template>
        </div>
        <el-button size="small" link type="primary" @click="openRoundDetail(round)">查看详情</el-button>
      </div>

      <!-- 通过记录 -->
      <template v-for="(log, li) in passLogs" :key="'pass-' + li">
        <div class="audit-log-item">
          <el-tag type="success" size="small">通过</el-tag>
          <span class="log-date">{{ (log.audited_at || log.created_at || '').slice(0, 10) }}</span>
          <span v-if="log.opinion" class="log-opinion">{{ log.opinion }}</span>
        </div>
      </template>
    </div>

    <template v-if="canAuditCurrentTask">
      <div class="audit-opinion-wrap">
        <div class="audit-opinion-label">审核意见（驳回时必填）</div>
        <el-input
          v-model="auditOpinion"
          type="textarea"
          :rows="3"
          placeholder="请输入审核意见，驳回时将作为整改意见下发至食堂"
        />
      </div>
    </template>
    <template #footer>
      <template v-if="canAuditCurrentTask">
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="auditSubmitting" @click="handleAuditSubmit('REJECT')">驳回整改</el-button>
        <el-button type="primary" :loading="auditSubmitting" @click="handleAuditSubmit('PASS')">审核通过</el-button>
      </template>
      <template v-else>
        <el-button @click="auditDialogVisible = false">关闭</el-button>
      </template>
    </template>
  </el-dialog>

  <!-- 整改详情弹窗 -->
  <el-dialog
    v-model="rectifyDetailDialogVisible"
    title="整改详情"
    width="520px"
    append-to-body
    draggable
  >
    <template v-if="selectedRound">
      <!-- 驳回理由 -->
      <div class="rd-section">
        <div class="rd-section-label">驳回理由</div>
        <div class="rd-text">{{ selectedRound.reject.opinion || '无' }}</div>
      </div>

      <template v-if="selectedRound.rectify">
        <!-- 整改说明（只展示一条） -->
        <div class="rd-section">
          <div class="rd-section-label">整改说明</div>
          <div class="rd-text">{{ selectedRound.rectify.items?.map(i => i.description).filter(Boolean).find(Boolean) || '无' }}</div>
        </div>

        <!-- 按检查项分组展示照片 -->
        <div class="rd-section">
          <div class="rd-section-label">整改照片</div>
          <template v-if="selectedRound.rectify.items?.some(i => i.photos?.length)">
            <div
              v-for="(rItem, rIdx) in selectedRound.rectify.items.filter(i => i.photos?.length)"
              :key="rIdx"
              class="rd-item-block"
            >
              <div class="rd-item-title">
                <span class="rd-item-index">整改项 {{ rIdx + 1 }}</span>
                <span class="rd-item-content">{{ auditItems.find(a => a.resultId === rItem.result_id)?.content || '' }}</span>
              </div>
              <div class="rd-photos">
                <el-image
                  v-for="(p, pi) in rItem.photos"
                  :key="pi"
                  :src="p"
                  :preview-src-list="rItem.photos"
                  :initial-index="pi"
                  fit="cover"
                  class="rd-photo"
                  preview-teleported
                />
              </div>
            </div>
          </template>
          <div v-else class="rd-text">无整改照片</div>
        </div>
      </template>
      <div v-else class="rd-section rd-text" style="color:#909399">尚未整改</div>
    </template>
    <template #footer>
      <el-button @click="rectifyDetailDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { getUserList } from '@/api/user'
import {
  createDailyTemplate,
  deleteDailyTemplate,
  getDailyTaskDetail,
  getDailyTaskList,
  getDailyTemplateDetail,
  getDailyTemplateList,
  getAllDepts,
  toggleDailyTemplateStatus,
  updateDailyTemplate
} from '@/api/canteen'
import { auditDailyTask, buildIdempotencyKey } from '@/api/inspection'

interface CanteenOption {
  id: number
  name: string
}

interface DailyRecord {
  id: number
  canteen: string
  submitter: string
  form: string
  completed: string
  date: string
  status: '待提交' | '待审核' | '待整改' | '已整改' | '已完成'
  rawStatus: string
}

interface TemplateCard {
  id: number
  name: string
  taskCount: number
  enabled: boolean
}

interface UserOption {
  id: number
  name: string
}

interface CheckItem {
  uid: number
  content: string
  mode: 'CONFIRM' | 'PHOTO' | 'FILL'
}

interface AuditTaskInfo {
  taskId: number
  canteen: string
  submitter: string
  submissionDate: string
  status: string
  statusText: string
}

interface AuditItem {
  itemId: number
  resultId: number
  content: string
  isQualified: boolean | null
  description: string
  photos: string[]
}

interface AuditLog {
  action: string
  opinion?: string
  created_at?: string
  audited_at?: string
  auditor_id?: string
  rectifier_id?: string
  rectified_at?: string
  items?: { result_id: number; description: string; photos: string[] }[]
}

const route = useRoute()
const router = useRouter()
const isCreateView = computed(() => route.name === 'DailyCreate')
const isChecklistView = computed(() => route.name === 'DailyChecklist')
const editingTemplateId = ref<number | null>(null)

const userOptions = ref<UserOption[]>([])

const createForm = reactive({
  name: '',
  executorRole: '',
  startTime: '09:00',
  endTime: '20:00',
  canteenIds: [] as string[],
  approverRole: ''
})

const checkItems = ref<CheckItem[]>([
  { uid: 1, content: '完成食堂员工晨检检查，晨检人数与到岗人数需一致', mode: 'CONFIRM' },
  { uid: 2, content: '检查后厨设备运行状态，确认温控及消杀记录完整', mode: 'PHOTO' }
])

// 审核对话框状态
const auditDialogVisible = ref(false)
const auditTaskInfo = ref<AuditTaskInfo | null>(null)
const auditItems = ref<AuditItem[]>([])
const auditLogs = ref<AuditLog[]>([])
const auditOpinion = ref('')
const auditSubmitting = ref(false)
const expandedRounds = ref<number[]>([])
const rectifyDetailDialogVisible = ref(false)
const selectedRound = ref<{ reject: AuditLog; rectify: AuditLog | null } | null>(null)

function openRoundDetail(round: { reject: AuditLog; rectify: AuditLog | null }) {
  selectedRound.value = round
  rectifyDetailDialogVisible.value = true
}

// 将 audit_logs 按 REJECT→RECTIFY 配对分组
const auditRounds = computed(() => {
  const rounds: { reject: AuditLog; rectify: AuditLog | null }[] = []
  const logs = auditLogs.value
  for (let i = 0; i < logs.length; i++) {
    const log = logs[i]
    if (log.action === 'REJECT' || log.action === 'REJECTED') {
      const next = logs[i + 1]
      const rectify = next?.action === 'RECTIFY' ? next : null
      if (rectify) i++
      rounds.push({ reject: log, rectify })
    }
  }
  return rounds
})

const passLogs = computed(() =>
  auditLogs.value.filter(l => l.action === 'PASS')
)

const canAuditCurrentTask = computed(() =>
  ['SUBMITTED', 'RECTIFIED'].includes(auditTaskInfo.value?.status || '')
)

const templateLoading = ref(false)
const templateCards = ref<TemplateCard[]>([])

const loading = ref(false)
const canteenOptions = ref<CanteenOption[]>([])
const rows = ref<DailyRecord[]>([])

const queryParams = reactive({
  dateRange: [] as string[],
  canteenId: '',
  status: '',
  keyword: ''
})

const page = ref(1)
const pageSize = ref(10)

const statusMap: Record<string, DailyRecord['status']> = {
  pending: '待提交',
  submitted: '待审核',
  rejected: '待整改',
  rectified: '已整改',
  completed: '已完成',
  signed: '已完成',
  archived: '已完成',
  filling: '待提交'
}

const inRange = (date: string, start: string, end: string) => {
  if (!date || !start || !end) return true
  return date >= start && date <= end
}

const filtered = computed(() => {
  const [startDate, endDate] = queryParams.dateRange || []
  const kw = queryParams.keyword.trim().toLowerCase()
  return rows.value.filter((row) => {
    const matchCanteen = !queryParams.canteenId || row.canteen.includes(resolveCanteenName(Number(queryParams.canteenId)))
    const matchStatus = !queryParams.status || row.status === queryParams.status
    const matchDate = !startDate || !endDate || inRange(row.date, startDate, endDate)
    const matchKeyword = !kw || `${row.canteen} ${row.submitter} ${row.form}`.toLowerCase().includes(kw)
    return matchCanteen && matchStatus && matchDate && matchKeyword
  })
})

const total = computed(() => filtered.value.length)

const pagedData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

const resolveCanteenName = (id: number) => {
  return canteenOptions.value.find((item) => item.id === id)?.name || `食堂${id || '-'}`
}

const loadCanteens = async () => {
  try {
    const res: any = await getAllDepts()
    const records = res?.data?.records || []
    canteenOptions.value = records
      .filter((item: any) => item.org_type === 'CANTEEN')
      .map((item: any) => ({ id: item.id, name: item.name }))
  } catch {
    canteenOptions.value = []
  }
}

const loadUsers = async () => {
  try {
    const res: any = await getUserList({ page: 1, size: 200 })
    const records = res?.data?.records || []
    userOptions.value = records.map((item: any) => ({
      id: item.id,
      name: item.real_name || item.username || `用户${item.id}`
    }))
  } catch {
    userOptions.value = []
  }
}

const loadRecords = async () => {
  loading.value = true
  try {
    const res: any = await getDailyTaskList({ page: 1, page_size: 500 })
    const records = (res?.data?.list || []) as any[]
    rows.value = records.map((item: any) => {
      const rawStatus = String(item.status || '').toLowerCase()
      return {
        id: item.task_id || item.id,
        canteen: String(item.canteen_name || item.canteen_name_snapshot || '-'),
        submitter: String(item.submitter_name || item.executor_name_snapshot || '系统生成'),
        form: String(item.template_name || '日管理检查表'),
        completed: String(item.completion_progress || '-'),
        date: String(item.submission_date || item.business_date || item.created_at || '').slice(0, 10) || '-',
        status: statusMap[rawStatus] || '待提交',
        rawStatus
      } as DailyRecord
    })
  } catch {
    rows.value = []
    ElMessage.warning('日管理记录接口暂不可用')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (value: number) => {
  page.value = value
}

const handleSizeChange = (value: number) => {
  pageSize.value = value
  page.value = 1
}

const statusTagType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    PENDING: 'info',
    SUBMITTED: 'warning',
    REJECTED: 'danger',
    RECTIFIED: 'warning',
    COMPLETED: 'success'
  }
  return map[status] || 'info'
}

const handleView = async (row: DailyRecord) => {
  try {
    const res: any = await getDailyTaskDetail(row.id)
    const data = res?.data
    const info = data?.task_info
    if (!info) {
      ElMessage.warning('无法获取任务详情')
      return
    }
    auditTaskInfo.value = {
      taskId: row.id,
      canteen: String(info.canteen_name || row.canteen),
      submitter: String(info.inspector_name || row.submitter),
      submissionDate: info.submission_date ? String(info.submission_date).slice(0, 10) : '未提交',
      status: String(info.status || ''),
      statusText: statusMap[String(info.status || '').toLowerCase()] || String(info.status_text || info.status || '-')
    }
    const snapshot: any[] = Array.isArray(data?.form_snapshot) ? data.form_snapshot : []
    auditItems.value = snapshot.map((item: any, idx: number) => ({
      itemId: Number(item.item_id ?? idx),
      resultId: Number(item.result_id ?? 0),
      content: String(item.content || `检查项${idx + 1}`),
      isQualified: item.is_qualified != null ? Boolean(item.is_qualified) : null,
      description: String(item.description || ''),
      photos: Array.isArray(item.photos) ? (item.photos as string[]) : []
    }))
    auditLogs.value = Array.isArray(data?.audit_logs) ? data.audit_logs : []
    auditOpinion.value = ''
    // 默认展开最后一轮（最新驳回）
    const rejectCount = auditLogs.value.filter(l => l.action === 'REJECT' || l.action === 'REJECTED').length
    expandedRounds.value = rejectCount > 0 ? [rejectCount - 1] : []
    auditDialogVisible.value = true
  } catch {
    ElMessage.error('获取任务详情失败')
  }
}

const handleAuditSubmit = async (action: 'PASS' | 'REJECT') => {
  if (action === 'REJECT' && !auditOpinion.value.trim()) {
    ElMessage.warning('驳回时请填写审核意见')
    return
  }
  auditSubmitting.value = true
  try {
    const userStore = (await import('@/store/user')).useUserStore()
    const auditorId = String(userStore.userInfo?.id || '')
    await auditDailyTask(
      auditTaskInfo.value!.taskId,
      { auditor_id: auditorId, action, opinion: auditOpinion.value.trim() || undefined },
      buildIdempotencyKey()
    )
    ElMessage.success(action === 'PASS' ? '审核通过' : '已驳回，整改意见已下发至食堂')
    auditDialogVisible.value = false
    await loadRecords()
  } catch {
    ElMessage.error('审核操作失败，请稍后重试')
  } finally {
    auditSubmitting.value = false
  }
}

const handleCancel = (row: DailyRecord) => {
  ElMessage.info(`已取消记录 #${row.id}`)
}

const getStatusClass = (status: DailyRecord['status']) => {
  if (status === '待提交') return 'status-draft'
  if (status === '待审核') return 'status-pending'
  if (status === '待整改') return 'status-review'
  if (status === '已整改') return 'status-fixed'
  if (status === '已完成') return 'status-done'
  return 'status-draft'
}

const fallbackTemplates: TemplateCard[] = [
  { id: 1, name: '高中日管控检查表', taskCount: 25, enabled: true },
  { id: 2, name: '初中日管控检查表', taskCount: 25, enabled: true },
  { id: 3, name: '幼儿园日管控检查表', taskCount: 25, enabled: true }
]

const loadTemplateCards = async () => {
  templateLoading.value = true
  try {
    const res: any = await getDailyTemplateList({ page: 1, page_size: 100 })
    const records = res?.data?.list || []
    if (!records.length) {
      templateCards.value = fallbackTemplates
      return
    }
    templateCards.value = records.map((item: any) => ({
      id: item.id,
      name: item.template_name || `模板${item.id}`,
      taskCount: 25,
      enabled: Boolean(item.is_active)
    }))
  } catch {
    templateCards.value = fallbackTemplates
    ElMessage.warning('模板接口暂不可用，当前展示示例模板')
  } finally {
    templateLoading.value = false
  }
}

const handleToggleEnable = async (item: TemplateCard) => {
  const newState = !item.enabled
  try {
    await toggleDailyTemplateStatus(item.id, newState)
    item.enabled = newState
    ElMessage.success(newState ? '模板已启用' : '模板已停用')
  } catch {
    ElMessage.error('状态更新失败，请稍后重试')
  }
}

const handleCoverUsers = (item: TemplateCard) => {
  ElMessage.info(`模板 #${item.id} 覆盖人员功能待后端接口支持`)
}

const handleCoverCanteens = (item: TemplateCard) => {
  ElMessage.info(`模板 #${item.id} 覆盖食堂功能待后端接口支持`)
}

const handleEditTemplate = (item: TemplateCard) => {
  router.push({ name: 'DailyCreate', query: { templateId: String(item.id) } })
}

const handleDeleteTemplate = async (item: TemplateCard) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板「${item.name}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteDailyTemplate(item.id)
    ElMessage.success('模板已删除')
    templateCards.value = templateCards.value.filter((t) => t.id !== item.id)
  } catch {
    ElMessage.error('删除失败，请稍后重试')
  }
}

const addCheckItem = () => {
  const nextUid = checkItems.value.length ? Math.max(...checkItems.value.map((item) => item.uid)) + 1 : 1
  checkItems.value.push({ uid: nextUid, content: '', mode: 'CONFIRM' })
}

const removeCheckItem = (uid: number) => {
  if (checkItems.value.length <= 1) {
    ElMessage.warning('至少保留一个检查项')
    return
  }
  checkItems.value = checkItems.value.filter((item) => item.uid !== uid)
}

const modeToCompletionMethod: Record<CheckItem['mode'], 'CONFIRM_ONLY' | 'PHOTO_REQUIRED' | 'INPUT_REQUIRED'> = {
  CONFIRM: 'CONFIRM_ONLY',
  PHOTO: 'PHOTO_REQUIRED',
  FILL: 'INPUT_REQUIRED'
}

const resetCreateForm = () => {
  editingTemplateId.value = null
  createForm.name = ''
  createForm.executorRole = ''
  createForm.startTime = '09:00'
  createForm.endTime = '20:00'
  createForm.canteenIds = []
  createForm.approverRole = ''
  checkItems.value = [{ uid: 1, content: '', mode: 'CONFIRM' }]
}

const buildDailyTemplateItems = () => {
  return checkItems.value.map((item, index) => {
    return {
      sort_order: index + 1,
      content: item.content.trim(),
      completion_method: modeToCompletionMethod[item.mode]
    }
  })
}

const handleSaveTemplate = async () => {
  const name = createForm.name.trim()
  if (!name) {
    ElMessage.warning('请输入检查表名称')
    return
  }

  const invalidItem = checkItems.value.find((item) => !item.content.trim())
  if (invalidItem) {
    ElMessage.warning('请填写完整的检查项内容')
    return
  }

  if (!createForm.canteenIds.length) {
    ElMessage.warning('请选择检查表覆盖食堂')
    return
  }

  const templateItems = buildDailyTemplateItems()
  const targetNodeIds = createForm.canteenIds
    .map((id) => Number(id))
    .filter((id) => !Number.isNaN(id))

  try {
    const payload = {
      template_name: name,
      executor_role: createForm.executorRole || undefined,
      approver_role: createForm.approverRole || undefined,
      target_node_ids: targetNodeIds,
      start_time: createForm.startTime || undefined,
      end_time: createForm.endTime || undefined,
      items: templateItems
    }

    // 未通过编辑入口进来时，检查是否已存在同名模板，如有则覆盖
    let resolvedId = editingTemplateId.value
    if (!resolvedId) {
      const listRes: any = await getDailyTemplateList({ page: 1, page_size: 100 })
      const sameNameItem = (listRes?.data?.list || []).find(
        (t: any) => String(t.template_name || '').trim() === name
      )
      if (sameNameItem) {
        resolvedId = Number(sameNameItem.id)
      }
    }

    if (resolvedId) {
      await updateDailyTemplate(resolvedId, payload)
      ElMessage.success('模板已更新')
    } else {
      await createDailyTemplate(payload)
      ElMessage.success('模板已创建')
    }
    router.push({ name: 'DailyChecklist' })
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  }
}

const completionMethodToMode: Record<string, CheckItem['mode']> = {
  CONFIRM_ONLY: 'CONFIRM',
  PHOTO_REQUIRED: 'PHOTO',
  INPUT_REQUIRED: 'FILL'
}

const loadTemplateForEdit = async (templateId: number) => {
  try {
    const res: any = await getDailyTemplateDetail(templateId)
    const detail = res?.data
    if (!detail) {
      ElMessage.warning('模板详情为空，无法编辑')
      return
    }

    editingTemplateId.value = Number(detail.id)
    createForm.name = String(detail.template_name || '')
    createForm.executorRole = String(detail.executor_role || '')
    createForm.approverRole = String(detail.approver_role || '')
    createForm.startTime = String(detail.start_time || '09:00')
    createForm.endTime = String(detail.end_time || '20:00')
    createForm.canteenIds = Array.isArray(detail.target_node_ids)
      ? detail.target_node_ids.map((id: number) => String(id))
      : []

    const items = Array.isArray(detail.items) ? detail.items : []
    if (items.length) {
      checkItems.value = items.map((item: any, index: number) => ({
        uid: Number(item.item_id || index + 1),
        content: String(item.content || ''),
        mode: completionMethodToMode[String(item.completion_method || '')] || 'CONFIRM'
      }))
    }
  } catch {
    ElMessage.error('加载模板详情失败，请检查权限或稍后重试')
  }
}

onMounted(async () => {
  await loadCanteens()

  if (isCreateView.value) {
    await loadUsers()
    const templateId = Number(route.query.templateId || 0)
    if (templateId) {
      await loadTemplateForEdit(templateId)
    }
    return
  }

  if (isChecklistView.value) {
    await loadTemplateCards()
    return
  }
  await loadRecords()
})

watch(
  () => route.name,
  async (name) => {
    if (name === 'DailyChecklist') {
      await loadTemplateCards()
    } else if (name === 'DailyCreate') {
      resetCreateForm()
      await loadCanteens()
      await loadUsers()
      const templateId = Number(route.query.templateId || 0)
      if (templateId) {
        await loadTemplateForEdit(templateId)
      }
    } else if (name === 'DailyRecords') {
      await loadRecords()
    }
  }
)
</script>

<style scoped>
.create-view {
  padding: 16px;
  background: #f1f2f7;
  min-height: calc(100vh - 84px);
}

.create-topbar {
  display: grid;
  grid-template-columns: 1fr 180px 90px;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.create-title {
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.approver-top-select {
  justify-self: end;
}

.save-btn {
  width: 80px;
  height: 34px;
  justify-self: end;
}

.create-card {
  background: #fff;
  border: 1px solid #ebeef5;
  padding: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 14px;
}

.form-item {
  display: grid;
  grid-template-columns: 140px 1fr;
  align-items: center;
  gap: 10px;
}

.form-item > label {
  color: #606266;
  font-size: 14px;
}

.time-item .time-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.deadline-label {
  color: #606266;
  font-size: 14px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f2f2f2;
  padding-top: 14px;
  margin-top: 8px;
  color: #303133;
  font-size: 14px;
}

.add-item-btn {
  border-color: #4a8ded;
  color: #4a8ded;
}

.item-table {
  margin-top: 12px;
}

.item-row {
  display: grid;
  grid-template-columns: 50px 1fr auto 70px;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  border-bottom: 1px solid #f2f2f2;
  padding: 8px 0;
}

.index-cell {
  text-align: center;
  color: #606266;
}

.content-cell {
  width: 100%;
}

.mode-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-label {
  color: #606266;
  font-size: 13px;
}

.checklist-view {
  padding: 0;
  background: #eef0f8;
  min-height: calc(100vh - 84px);
}

.checklist-title {
  font-size: 18px;
  color: #303133;
  font-weight: 600;
  padding: 18px 10px;
  background: #f7f7f7;
  border-bottom: 1px solid #e5e7ef;
}

.template-list {
  padding: 20px 10px;
}

.template-card {
  display: grid;
  grid-template-columns: 4px 1fr 260px 520px;
  align-items: center;
  background: #f5f5f5;
  margin-bottom: 20px;
  min-height: 101px;
}

.card-left-accent {
  width: 4px;
  height: 100%;
  background: #4a8ded;
}

.card-main {
  padding-left: 24px;
}

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-desc {
  font-size: 16px;
  color: #9aa3b2;
  margin-top: 10px;
}

.card-toggle-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.toggle-label {
  font-size: 14px;
  color: #303133;
}

.card-toggle-wrap :deep(.el-switch) {
  --el-switch-on-color: #2196d3;
  --el-switch-off-color: #cfd7e6;
  transform: scale(1);
}

.card-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
}

.outline-btn {
  width: 100px;
  height: 43px;
  border-color: #4a8ded;
  color: #4a8ded;
  font-size: 14px;
}

.edit-btn {
  width: 80px;
  height: 43px;
  font-size: 14px;
  background: #4a8ded;
  border-color: #4a8ded;
}

.delete-btn {
  width: 80px;
  height: 43px;
  font-size: 14px;
}

.record-view {
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  padding: 20px;
  background-color: #fff;
  min-height: calc(100vh - 84px);
}

.rv-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.rv-header .title {
  font-size: 18px;
  font-weight: 600;
  margin-right: 20px;
  white-space: nowrap;
}

.controls {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-item .label {
  font-size: 14px;
  color: #606266;
}

.table-container {
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.rv-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.status-draft {
  color: #909399;
}

.status-pending {
  color: #e6a23c;
}

.status-review {
  color: #f56c6c;
}

.status-fixed {
  color: #409eff;
}

.status-done {
  color: #67c23a;
}

.status-archived {
  color: #909399;
}

.audit-task-meta {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #606266;
  flex-wrap: wrap;
}

.audit-items-wrap {
  margin-bottom: 16px;
}

.audit-status-ok {
  color: #67c23a;
  font-weight: 500;
}

.audit-status-fail {
  color: #f56c6c;
  font-weight: 500;
}

.audit-status-na {
  color: #909399;
}

.audit-photos {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: wrap;
}

.audit-photo-thumb {
  width: 56px;
  height: 44px;
  object-fit: cover;
  border-radius: 3px;
  border: 1px solid #e4e7ed;
  cursor: zoom-in;
}

.audit-log-wrap {
  margin: 16px 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.audit-log-title {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.audit-log-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
}

.audit-log-item:last-child {
  border-bottom: none;
}

.log-date {
  color: #909399;
}

.log-opinion {
  color: #606266;
  flex: 1;
}

/* 分轮平铺行 */
.round-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px;
  border-bottom: 1px solid #ebeef5;
}

.round-row:last-of-type {
  border-bottom: none;
}

.round-row-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.rd-section {
  padding: 10px 0;
  border-bottom: 1px dashed #ebeef5;
}

.rd-section:last-child {
  border-bottom: none;
}

.round-index {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-right: 4px;
}

.round-time {
  font-size: 12px;
  color: #909399;
}

.round-opinion {
  font-size: 12px;
  color: #f56c6c;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.round-detail {
  padding: 6px 0 6px 4px;
  border-bottom: 1px dashed #ebeef5;
}

.round-detail:last-child {
  border-bottom: none;
}

.rd-section-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.rd-item-block {
  background: #f9fafe;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.rd-item-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rd-item-index {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  background: #ecf5ff;
  border-radius: 3px;
  padding: 1px 6px;
  flex-shrink: 0;
}

.rd-item-content {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.rd-item-row {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-top: 4px;
}

.rd-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.rd-photos {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.rd-photo {
  width: 72px;
  height: 56px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  cursor: zoom-in;
  display: block;
}

.audit-opinion-wrap {
  margin-top: 16px;
}

.audit-opinion-label {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
}
</style>
