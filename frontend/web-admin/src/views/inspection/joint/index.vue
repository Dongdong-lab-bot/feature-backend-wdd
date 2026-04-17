<template>
  <div v-if="isCreateView" class="create-view">
    <div class="create-title">{{ isEditMode ? '编辑联合巡检检查表' : '新建联合巡检检查表' }}</div>

    <div class="create-card">
      <div class="create-row row-2">
        <label>检查表名称</label>
        <el-input v-model="createForm.name" />
      </div>

      <div class="create-row row-4">
        <label>检查表执行人员</label>
        <el-select v-model="createForm.executorRole" placeholder="请选择执行人员">
          <el-option v-for="item in createUserOptions" :key="`exec-${item.id}`" :label="item.name" :value="item.name" />
        </el-select>
        <label>审批人员</label>
        <el-select v-model="createForm.approverRole" placeholder="请选择审批人员">
          <el-option v-for="item in createUserOptions" :key="`approver-${item.id}`" :label="item.name" :value="item.name" />
        </el-select>
      </div>

      <div class="create-row row-4">
        <label>开始提交时间</label>
        <el-time-picker v-model="createForm.startTime" value-format="HH:mm" format="HH:mm" />
        <label>截止时间</label>
        <el-time-picker v-model="createForm.endTime" value-format="HH:mm" format="HH:mm" />
      </div>

      <div class="create-row row-2">
        <label>检查表覆盖食堂</label>
        <el-select v-model="createForm.canteenId" placeholder="请选择食堂">
          <el-option v-for="item in canteens" :key="`cover-${item.id}`" :label="item.name" :value="item.id" />
        </el-select>
      </div>

      <div class="create-row row-2">
        <label>表格类型</label>
        <el-select v-model="createForm.tableType" placeholder="请选择表格类型">
          <el-option label="打分表" value="SCORE" />
          <el-option label="选项表" value="OPTION" />
          <el-option label="选分表" value="SELECT_SCORE" />
        </el-select>
      </div>
    </div>

    <div class="items-grid">
      <div class="items-head">
        <div class="head-left">添加检查大项</div>
        <div class="head-right">添加检查小项</div>
      </div>

      <div v-for="section in createSections" :key="section.id" class="section-block">
        <div class="section-name">
          <span class="section-name-text">{{ section.name }}</span>
        </div>
        <div class="section-content">
          <div v-for="item in section.items" :key="item.id" class="item-row">
            <div class="item-text-wrap">
              <span class="item-text-label">{{ item.text }}</span>
            </div>
            <div class="item-inline">
              <span>问题类型:</span>
              <el-select v-model="item.issueType" class="mini-select">
                <el-option label="红线" value="红线" />
                <el-option label="黄线" value="黄线" />
                <el-option label="蓝线" value="蓝线" />
              </el-select>
              <template v-if="createForm.tableType === 'SELECT_SCORE'">
                <span>总分:</span>
                <el-input v-model="item.totalScore" class="mini-input" />
              </template>
              <template v-else-if="createForm.tableType === 'SCORE'">
                <span>总分:</span>
                <el-input v-model="item.totalScore" class="mini-input" placeholder="分值" @blur="validateItemScore(item)" />
              </template>
              <template v-else-if="createForm.tableType === 'OPTION'">
                <span>满分:</span>
                <el-input v-model="item.totalScore" class="mini-input" placeholder="分值" @blur="validateItemScore(item)" />
              </template>
            </div>
            <!-- 评分控件：始终占一个 grid 列 -->
            <div class="score-col">
              <el-button v-if="createForm.tableType === 'SELECT_SCORE'" class="score-btn" @click="handleSetupScore(section.id, item.id)">
                设置打分项{{ item.scoringOptions.length ? `(${item.scoringOptions.length}项)` : '' }}
              </el-button>
            </div>
            <div class="rectify-wrap">
              <span>是否整改</span>
              <el-radio-group v-model="item.needRectify" size="small">
                <el-radio :value="true">是</el-radio>
                <el-radio :value="false">否</el-radio>
              </el-radio-group>
            </div>
            <el-button link type="primary" @click="appendIssue(section.id)">向下新增一条</el-button>
            <el-button link type="danger" @click="deleteIssue(section.id, item.id)">删除</el-button>
          </div>
        </div>
      </div>

      <div class="actions-row">
        <div class="actions-left">
          <el-button class="add-major-btn" type="primary" @click="addMajorSection">+新增大项</el-button>
          <el-button class="del-major-btn" type="danger" plain @click="showDeleteMajorDialog">删除大项</el-button>
        </div>
        <el-button class="save-create-btn" type="primary" @click="saveCreateChecklist">保存</el-button>
      </div>
    </div>
  </div>

  <div v-else-if="isChecklistView" class="checklist-view">
    <div class="checklist-header">
      <div class="checklist-title">联合巡检检查表模板</div>
      <el-button type="primary" @click="router.push({ name: 'JointCreate' })">＋ 新建检查表</el-button>
    </div>

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
          <el-button class="delete-btn" @click="handleDeleteTemplate(item)">删除</el-button>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="isScoreView" class="score-view">
    <div class="score-toolbar">
      <div class="score-title">联合巡检表分数统计</div>
      <div class="score-controls">
        <div class="score-control-item">
          <span class="label">起止日期</span>
          <el-date-picker
            v-model="scoreQuery.dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="score-date"
          />
        </div>
        <div class="score-control-item">
          <span class="label">食堂筛选</span>
          <el-select v-model="scoreQuery.canteenId" class="score-select" placeholder="全部食堂">
            <el-option label="全部食堂" value="" />
            <el-option v-for="item in canteens" :key="`joint-score-canteen-${item.id}`" :label="item.name" :value="String(item.id)" />
          </el-select>
        </div>
        <div class="score-control-item">
          <span class="label">表格筛选</span>
          <el-select v-model="scoreQuery.formName" class="score-select" placeholder="全部表格">
            <el-option label="全部表格" value="" />
            <el-option v-for="name in scoreFormOptions" :key="`joint-score-form-${name}`" :label="name" :value="name" />
          </el-select>
        </div>
        <div class="score-control-item score-search-item">
          <span class="label">搜索</span>
          <el-input v-model="scoreQuery.keyword" placeholder="请输入关键字" class="score-search" clearable @keyup.enter="handleScoreSearch" />
        </div>
      </div>
    </div>

    <div class="score-table-wrap">
      <el-table
        :data="scorePagedRows"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ background: '#f5f5f5', color: '#606266', fontWeight: 'bold' }"
      >
        <el-table-column prop="canteen" label="食堂名称" min-width="170" show-overflow-tooltip />
        <el-table-column prop="form" label="检查表" min-width="170" show-overflow-tooltip />
        <el-table-column prop="score" label="分数" min-width="90" align="center" />
        <el-table-column prop="redline" label="红线问题数" min-width="110" align="center" />
        <el-table-column prop="yellowline" label="黄线问题数" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="90" align="center">
          <template #default="scope">
            <span :class="scoreStatusClass(scope.row.status)">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="130" align="center">
          <template #default="scope">
            <el-button link type="primary" @click="handleScoreEdit(scope.row)">编辑</el-button>
            <el-button link type="primary" @click="handleScoreCancel(scope.row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <footer class="score-footer">
      <el-button class="download-btn" type="primary" @click="handleScoreDownload">下载Excel文件分数统计表</el-button>
      <el-pagination
        v-model:current-page="scorePage"
        v-model:page-size="scorePageSize"
        :page-sizes="[10, 20, 30, 50]"
        layout="prev, pager, next"
        :total="scoreTotal"
        @size-change="handleScoreSizeChange"
        @current-change="handleScorePageChange"
      />
    </footer>
  </div>

  <div v-else-if="isDetailView" class="detail-view">
    <div class="detail-headline">{{ detailRecordTitle }}</div>
    <div class="detail-meta">时间：{{ detailDate }}&nbsp;&nbsp;&nbsp;&nbsp;提交人：{{ detailSubmitter }}</div>

    <div class="detail-grid">
      <div class="detail-left-col">
        <div class="col-header">表格问题大项</div>
        <div
          v-for="section in detailSections"
          :key="section.id"
          class="section-item"
          :class="{ active: selectedSectionId === section.id }"
          @click="selectedSectionId = section.id"
        >
          {{ section.name }}
        </div>
      </div>

      <div class="detail-main-col">
        <div class="main-head-row">
          <div class="main-head-item">问题小项</div>
          <div class="main-head-item">整改反馈情况</div>
          <div class="main-head-item action-head"></div>
        </div>

        <div v-for="issue in currentSectionIssues" :key="issue.id" class="issue-row">
          <div class="issue-cell issue-problem">
            <div class="issue-title-line">
              <span class="issue-tag" :style="{ backgroundColor: issue.tagColor }"></span>
              <span>{{ issue.title }}</span>
              <span class="full-score">满分：{{ issue.fullScore }}分</span>
            </div>
            <div class="issue-score">得分：{{ issue.score }}分</div>
            <div class="issue-desc">描述：{{ issue.description }}</div>
            <div class="photo-list">
              <div class="photo-box">图片</div>
              <div class="photo-box">图片</div>
            </div>
          </div>

          <div class="issue-cell issue-feedback">
            <div class="feedback-desc">整改描述：{{ issue.rectifyDesc }}</div>
            <div class="photo-list">
              <div class="photo-box">图片</div>
              <div class="photo-box">图片</div>
            </div>
          </div>

          <div class="issue-cell issue-action">
            <div class="action-btns">
              <el-button class="pass-btn" :class="{ active: issue.decision === 'pass' }" @click="issue.decision = 'pass'">通过</el-button>
              <el-button class="reject-btn" :class="{ active: issue.decision === 'reject' }" @click="issue.decision = 'reject'">驳回</el-button>
            </div>
            <el-input v-model="issue.rejectReason" type="textarea" :rows="3" placeholder="驳回描述" class="reject-input" />
          </div>
        </div>
      </div>
    </div>

    <div class="detail-submit-wrap">
      <el-button type="primary" class="detail-submit-btn" @click="handleDetailSubmit">提交</el-button>
    </div>
  </div>

  <div v-else class="record-view">
    <header class="rv-header">
      <div class="title">联合巡检记录</div>
      <div class="controls">
        <div class="control-item">
          <span class="label">起止日期</span>
          <el-date-picker
            v-model="query.dateRange"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </div>
        <div class="control-item">
          <span class="label">状态</span>
          <el-select v-model="query.status" placeholder="全部状态" style="width: 140px">
            <el-option label="全部状态" value="" />
            <el-option label="待整改" value="待整改" />
            <el-option label="已改待审" value="已改待审" />
            <el-option label="整改成功" value="整改成功" />
          </el-select>
        </div>
        <div class="control-item">
          <span class="label">搜索</span>
          <el-input v-model="query.keyword" style="width: 240px" clearable />
        </div>
      </div>
    </header>

    <div class="table-container">
      <el-table
        :data="pagedRows"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
      >
        <el-table-column prop="submitCanteen" label="提交食堂" min-width="190" show-overflow-tooltip />
        <el-table-column prop="submitter" label="提交人" min-width="85" />
        <el-table-column prop="submitForm" label="提交表格" min-width="180" show-overflow-tooltip />
        <el-table-column prop="score" label="检查分数" min-width="95" align="center" />
        <el-table-column prop="redline" label="红线问题" min-width="95" align="center" />
        <el-table-column prop="submitDate" label="提交日期" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="95" align="center">
          <template #default="scope">
            <span :class="getStatusClass(scope.row.status)">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="140" align="center">
          <template #default="scope">
            <el-button link type="primary" @click="handlePrimary(scope.row)">{{ scope.row.primaryAction }}</el-button>
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
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { getAllDepts, getJointTaskDetail, getJointTaskList, getJointTemplateList, getJointTemplateDetail, createJointTemplate, updateJointTemplate, deleteJointTemplate } from '@/api/canteen'
import { getUserList } from '@/api/user'
import { auditJointTask, buildIdempotencyKey, type InspectionSubmitItem } from '@/api/inspection'

interface JointRow {
  id: number
  canteenId: number
  submitCanteen: string
  submitter: string
  submitForm: string
  score: number
  redline: number
  submitDate: string
  status: '待整改' | '已改待审' | '整改成功'
  primaryAction: '查看' | '编辑'
}

interface CanteenOption {
  id: number
  name: string
}

interface JointDetailIssue {
  id: number
  title: string
  fullScore: number
  score: number
  description: string
  rectifyDesc: string
  tagColor: string
  decision: '' | 'pass' | 'reject'
  rejectReason: string
}

interface JointDetailSection {
  id: string
  name: string
  issues: JointDetailIssue[]
}

type JointScoreStatus = '待整改' | '已整改'

interface JointScoreRow {
  id: number
  canteenId: number
  canteen: string
  form: string
  score: number
  redline: number
  yellowline: number
  status: JointScoreStatus
  submitDate: string
}

interface JointTemplateCard {
  id: number
  name: string
  taskCount: number
  enabled: boolean
}

interface CreateUserOption {
  id: string
  name: string
}

interface CreateIssueItem {
  id: string
  text: string
  issueType: '红线' | '黄线' | '蓝线'
  totalScore: string
  scoringOptions: number[]
  needRectify: boolean
}

interface CreateSection {
  id: string
  name: string
  items: CreateIssueItem[]
}

const route = useRoute()
const router = useRouter()
const isDetailView = computed(() => route.name === 'JointDetail')
const isChecklistView = computed(() => route.name === 'JointChecklist')
const isCreateView = computed(() => route.name === 'JointCreate')
const isScoreView = computed(() => route.name === 'JointScore')
const isEditMode = computed(() => isCreateView.value && !!route.query.templateId)

const loading = ref(false)
const canteens = ref<CanteenOption[]>([])
const allRows = ref<JointRow[]>([])
const templateLoading = ref(false)
const templateCards = ref<JointTemplateCard[]>([])

const createUserOptions = ref<CreateUserOption[]>([])

const createForm = reactive({
  name: '',
  executorRole: '',
  approverRole: '',
  startTime: '',
  endTime: '20:00',
  canteenId: 0,
  tableType: 'SELECT_SCORE'
})

const createSections = ref<CreateSection[]>([])

const query = reactive({
  dateRange: ['2026-01-12', '2026-02-23'] as string[],
  status: '待整改',
  keyword: ''
})

const scoreQuery = reactive({
  dateRange: ['2026-01-12', '2026-02-23'] as string[],
  canteenId: '',
  formName: '',
  keyword: ''
})

const page = ref(1)
const pageSize = ref(10)
const scorePage = ref(2)
const scorePageSize = ref(10)

const detailRecordTitle = ref('武岗一中一食堂联合巡检记录')
const detailDate = ref('2026.1.6')
const detailSubmitter = ref('张三')
const detailSections = ref<JointDetailSection[]>([])
const selectedSectionId = ref<string>('food')
const selectedTaskId = ref<number | null>(null)

const statusMap: Record<string, JointRow['status']> = {
  PENDING: '待整改',
  SUBMITTED: '已改待审',
  REJECTED: '待整改',
  RECTIFIED: '已改待审',
  COMPLETED: '整改成功'
}

const submitterPool = ['张三', '李四', '王五']
const formPool = ['3月五部委联合巡检检查表', '5月教育市监联合检查', '6月食安总监交叉巡检']

const inRange = (date: string, start: string, end: string) => {
  if (!start || !end) return true
  return date >= start && date <= end
}

const filteredRows = computed(() => {
  const [startDate, endDate] = query.dateRange || []
  const keyword = query.keyword.trim().toLowerCase()
  return allRows.value.filter((item) => {
    const matchStatus = !query.status || item.status === query.status
    const matchDate = !startDate || !endDate || inRange(item.submitDate, startDate, endDate)
    const matchKeyword = !keyword || `${item.submitCanteen} ${item.submitter} ${item.submitForm}`.toLowerCase().includes(keyword)
    return matchStatus && matchDate && matchKeyword
  })
})

const total = computed(() => filteredRows.value.length)

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const scoreRows = computed<JointScoreRow[]>(() => {
  return allRows.value.map((item) => {
    const scoreStatus: JointScoreStatus = item.status === '待整改' ? '待整改' : '已整改'
    return {
      id: item.id,
      canteenId: item.canteenId,
      canteen: item.submitCanteen,
      form: item.submitForm,
      score: item.score,
      redline: item.redline,
      yellowline: 20,
      status: scoreStatus,
      submitDate: item.submitDate
    }
  })
})

const scoreFormOptions = computed(() => {
  const set = new Set<string>()
  scoreRows.value.forEach((item) => set.add(item.form))
  return Array.from(set)
})

const filteredScoreRows = computed(() => {
  const [startDate, endDate] = scoreQuery.dateRange || []
  const keyword = scoreQuery.keyword.trim().toLowerCase()
  return scoreRows.value.filter((item) => {
    const matchCanteen = !scoreQuery.canteenId || String(item.canteenId) === scoreQuery.canteenId
    const matchForm = !scoreQuery.formName || item.form === scoreQuery.formName
    const matchDate = !startDate || !endDate || inRange(item.submitDate, startDate, endDate)
    const matchKeyword = !keyword || `${item.canteen} ${item.form}`.toLowerCase().includes(keyword)
    return matchCanteen && matchForm && matchDate && matchKeyword
  })
})

const scoreTotal = computed(() => filteredScoreRows.value.length)

const scorePagedRows = computed(() => {
  const start = (scorePage.value - 1) * scorePageSize.value
  return filteredScoreRows.value.slice(start, start + scorePageSize.value)
})

const currentSectionIssues = computed(() => {
  const section = detailSections.value.find((item) => item.id === selectedSectionId.value)
  return section?.issues || []
})

const makeCreateItem = (id: string, text: string): CreateIssueItem => ({
  id,
  text,
  issueType: '红线',
  totalScore: '--',
  scoringOptions: [],
  needRectify: true
})

const makeDefaultCreateSections = (): CreateSection[] => [
  { id: 'food', name: '食材问题排查', items: [makeCreateItem('food-1', '1、食堂无三无、腐烂、过期食材')] },
  { id: 'env', name: '环境问题排查', items: [makeCreateItem('env-1', '1、后厨环境卫生整洁')] },
  { id: 'dine', name: '就餐问题排查', items: [makeCreateItem('dine-1', '1、前厅餐后桌面卫生整洁')] },
  { id: 'fire', name: '消防问题排查', items: [makeCreateItem('fire-1', '1、灭火器均在使用期限内')] }
]

const loadCreateUsers = async () => {
  try {
    const res: any = await getUserList({ page: 1, size: 200 })
    const records = res?.data?.records || res?.data?.list || []
    createUserOptions.value = records.map((u: any) => ({
      id: String(u.id),
      name: String(u.name || u.username || u.real_name || '')
    }))
  } catch {
    createUserOptions.value = []
  }
}

const initCreateView = async () => {
  await loadCreateUsers()
  const templateId = Number(route.query.templateId || 0)
  if (!templateId) {
    createForm.name = ''
    createForm.executorRole = ''
    createForm.approverRole = ''
    createForm.startTime = ''
    createForm.endTime = '20:00'
    createForm.canteenId = canteens.value[0]?.id || 0
    createForm.tableType = 'SELECT_SCORE'
    createSections.value = []
    return
  }
  try {
    const res: any = await getJointTemplateDetail(templateId)
    const tpl = res?.data || res
    createForm.name = tpl.template_name || tpl.name || ''
    createForm.executorRole = String(tpl.executor_role || '')
    createForm.approverRole = String(tpl.approver_role || '')
    createForm.tableType = String(tpl.form_type || 'SELECT_SCORE')
    createForm.startTime = String(tpl.start_time || '')
    createForm.endTime = String(tpl.end_time || '20:00')
    const nodeIds: number[] = Array.isArray(tpl.target_node_ids) ? tpl.target_node_ids.map(Number) : []
    createForm.canteenId = nodeIds[0] || canteens.value[0]?.id || 0
    if (Array.isArray(tpl.major_items) && tpl.major_items.length) {
      createSections.value = tpl.major_items.map((maj: any) => ({
        id: `major-${maj.sort_order || maj.id || maj.order}`,
        name: maj.title || maj.name || '',
        items: (maj.minor_items || []).map((min: any, mi: number) => ({
          ...makeCreateItem(`minor-${min.item_id || min.id || mi}`, min.content || min.name || ''),
          issueType: (min.issue_type as CreateIssueItem['issueType']) || '红线',
          totalScore: min.total_score != null ? String(min.total_score) : '--',
          scoringOptions: Array.isArray(min.scoring_options) ? min.scoring_options.map(Number) : []
        }))
      }))
    } else {
      createSections.value = []
    }
  } catch {
    createSections.value = []
  }
}

const loadCanteens = async () => {
  try {
    const res: any = await getAllDepts()
    const rows = res?.data?.records || []
    canteens.value = rows
      .filter((item: any) => item.org_type === 'CANTEEN' || item.org_type === 'AREA')
      .map((item: any) => ({ id: Number(item.id), name: String(item.name) }))
  } catch {
    canteens.value = []
  }
}

const fallbackRows = (): JointRow[] => [
  { id: 1, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '3月五部委联合巡检检查表', score: 88, redline: 1, submitDate: '2026-02-23', status: '待整改', primaryAction: '编辑' },
  { id: 2, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '3月五部委联合巡检检查表', score: 86, redline: 1, submitDate: '2026-02-22', status: '待整改', primaryAction: '编辑' },
  { id: 3, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '3月五部委联合巡检检查表', score: 84, redline: 1, submitDate: '2026-02-21', status: '待整改', primaryAction: '编辑' },
  { id: 4, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '3月五部委联合巡检检查表', score: 89, redline: 0, submitDate: '2026-02-20', status: '待整改', primaryAction: '编辑' },
  { id: 5, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '3月五部委联合巡检检查表', score: 91, redline: 0, submitDate: '2026-02-19', status: '待整改', primaryAction: '编辑' },
  { id: 6, canteenId: 102, submitCanteen: '武岗初级中学', submitter: '李四', submitForm: '3月五部委联合巡检检查表', score: 95, redline: 0, submitDate: '2026-02-18', status: '整改成功', primaryAction: '编辑' },
  { id: 7, canteenId: 102, submitCanteen: '武岗初级中学', submitter: '李四', submitForm: '3月五部委联合巡检检查表', score: 92, redline: 0, submitDate: '2026-02-17', status: '整改成功', primaryAction: '编辑' },
  { id: 8, canteenId: 102, submitCanteen: '武岗初级中学', submitter: '李四', submitForm: '3月五部委联合巡检检查表', score: 89, redline: 0, submitDate: '2026-02-16', status: '整改成功', primaryAction: '编辑' },
  { id: 9, canteenId: 102, submitCanteen: '武岗初级中学', submitter: '李四', submitForm: '3月五部委联合巡检检查表', score: 88, redline: 1, submitDate: '2026-02-15', status: '整改成功', primaryAction: '编辑' },
  { id: 10, canteenId: 102, submitCanteen: '武岗初级中学', submitter: '李四', submitForm: '3月五部委联合巡检检查表', score: 93, redline: 0, submitDate: '2026-02-14', status: '整改成功', primaryAction: '编辑' }
]

const extractList = (payload: unknown): Array<Record<string, unknown>> => {
  if (Array.isArray(payload)) return payload as Array<Record<string, unknown>>
  if (!payload || typeof payload !== 'object') return []

  const data = payload as Record<string, unknown>
  if (Array.isArray(data.list)) return data.list as Array<Record<string, unknown>>
  if (Array.isArray(data.records)) return data.records as Array<Record<string, unknown>>
  if (Array.isArray(data.items)) return data.items as Array<Record<string, unknown>>
  if (Array.isArray(data.data)) return data.data as Array<Record<string, unknown>>

  return []
}

const loadRows = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = query.dateRange || []
    const res: any = await getJointTaskList({
      page: 1,
      page_size: 100,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      status: query.status || undefined,
      keyword: query.keyword || undefined
    })
    const records = Array.isArray(res?.data?.list) ? res.data.list : []
    allRows.value = records.map((item: any, index: number) => {
      const canteenId = Number(item.canteen_id || 0)
      const rawStatus = String(item.status || '').toUpperCase()
      const submitDate = String(item.submission_date || item.business_date || '').slice(0, 10) || '2026-02-23'
      return {
        id: Number(item.id),
        canteenId: canteenId || 0,
        submitCanteen: String(item.canteen_name || canteens.value.find((c) => c.id === canteenId)?.name || `食堂${canteenId || 1}`),
        submitter: String(item.executor_name || submitterPool[index % submitterPool.length]),
        submitForm: String(item.template_name || formPool[index % formPool.length]),
        score: Number(item.total_score || 84 + ((index + 3) % 12)),
        redline: Number(item.red_line_issues || index % 2),
        submitDate,
        status: statusMap[rawStatus] || '待整改',
        primaryAction: '编辑'
      } as JointRow
    })
    if (!allRows.value.length) {
      allRows.value = fallbackRows()
    }
  } catch {
    allRows.value = fallbackRows()
    ElMessage.warning('联合巡检记录接口暂不可用，当前展示示例数据')
  } finally {
    loading.value = false
  }
}

const loadTemplateCards = async () => {
  templateLoading.value = true
  try {
    const res: any = await getJointTemplateList({ page: 1, page_size: 100 })
    const records = Array.isArray(res?.data?.list) ? res.data.list : []
    templateCards.value = records.map((item: any) => ({
      id: Number(item.id),
      name: String(item.template_name || item.name || ''),
      taskCount: 0,
      enabled: Boolean(item.is_active)
    }))
  } catch {
    templateCards.value = []
  } finally {
    templateLoading.value = false
  }
}

const createIssue = (idBase: number, title: string, score: number, color: string): JointDetailIssue => ({
  id: idBase,
  title,
  fullScore: 6,
  score,
  description: '发现卫生或流程细节需整改的问题',
  rectifyDesc: '已完成现场整改并补充整改记录',
  tagColor: color,
  decision: '',
  rejectReason: ''
})

const buildDetailSections = (): JointDetailSection[] => [
  {
    id: 'food',
    name: '食材问题排查',
    issues: [
      createIssue(1, '1、食堂无三无、腐烂、过期食材', 3, '#f5222d'),
      createIssue(2, '2、食堂地面无明显积水，清洁到位', 3, '#d4d600'),
      createIssue(3, '3、前厅餐后桌面卫生整洁', 3, '#409eff')
    ]
  },
  { id: 'people', name: '人员问题排查', issues: [createIssue(4, '1、工作人员证照齐全并在有效期内', 4, '#409eff')] },
  { id: 'environment', name: '环境问题排查', issues: [createIssue(5, '1、后厨通风与照明符合标准', 4, '#409eff')] },
  { id: 'device', name: '设备问题排查', issues: [createIssue(6, '1、设备巡检记录齐全', 4, '#409eff')] },
  { id: 'risk', name: '消费风险排查', issues: [createIssue(7, '1、风险预警机制运行正常', 4, '#409eff')] }
]

const toDetailIssue = (item: InspectionSubmitItem, index: number): JointDetailIssue => {
  const tagColor = item.result ? '#409eff' : (index % 2 === 0 ? '#f5222d' : '#d4d600')
  return {
    id: index + 1,
    title: item.item_id,
    fullScore: 6,
    score: item.result ? 6 : 3,
    description: item.issue_desc || '暂无问题描述',
    rectifyDesc: '',
    tagColor,
    decision: '',
    rejectReason: ''
  }
}

const initDetailByRoute = async () => {
  const id = Number(route.query.id || 0)
  selectedTaskId.value = id || null
  const matched = allRows.value.find((item) => item.id === id)
  if (matched) {
    detailRecordTitle.value = `${matched.submitCanteen}联合巡检记录`
    detailDate.value = matched.submitDate.replace(/-/g, '.')
    detailSubmitter.value = matched.submitter
  }

  try {
    if (!id) {
      detailSections.value = buildDetailSections()
    } else {
      const res = await getJointTaskDetail(id)
      const taskData = res?.data
      const majorItems = Array.isArray(taskData?.form_snapshot?.major_items) ? taskData.form_snapshot.major_items as InspectionSubmitItem[] : []
      detailSections.value = [
        {
          id: 'inspection-items',
          name: '巡检问题项',
          issues: majorItems.length ? majorItems.map((item, index) => toDetailIssue(item, index)) : buildDetailSections()[0].issues
        }
      ]
    }
  } catch {
    detailSections.value = buildDetailSections()
  }

  selectedSectionId.value = detailSections.value[0]?.id || 'food'
}

const handlePrimary = (row: JointRow) => {
  router.push({ name: 'JointDetail', query: { id: String(row.id) } })
}

const handleCancel = (row: JointRow) => {
  ElMessage.info(`取消记录 #${row.id}`)
}

const handlePageChange = (value: number) => {
  page.value = value
}

const handleSizeChange = (value: number) => {
  pageSize.value = value
  page.value = 1
}

const handleScorePageChange = (value: number) => {
  scorePage.value = value
}

const handleScoreSizeChange = (value: number) => {
  scorePageSize.value = value
  scorePage.value = 1
}

const handleScoreSearch = () => {
  scorePage.value = 1
}

const handleScoreEdit = (row: JointScoreRow) => {
  router.push({ name: 'JointDetail', query: { id: String(row.id) } })
}

const handleScoreCancel = (row: JointScoreRow) => {
  ElMessage.info(`取消记录 #${row.id}`)
}

const handleScoreDownload = () => {
  const headers = '食堂名称,检查表,分数,红线问题数,黄线问题数,状态\n'
  const body = filteredScoreRows.value
    .map((item) => `${item.canteen},${item.form},${item.score},${item.redline},${item.yellowline},${item.status}`)
    .join('\n')
  const blob = new Blob([headers + body], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '联合巡检分数统计.csv'
  a.click()
  URL.revokeObjectURL(url)
}

const handleDetailSubmit = async () => {
  if (!selectedTaskId.value) {
    ElMessage.warning('缺少任务ID，无法提交审核')
    return
  }

  const hasReject = currentSectionIssues.value.some((issue) => issue.decision === 'reject')
  const opinion = currentSectionIssues.value
    .filter((issue) => issue.decision === 'reject' && issue.rejectReason.trim())
    .map((issue) => `${issue.title}：${issue.rejectReason.trim()}`)
    .join('\n')

  try {
    const userStore = (await import('@/store/user')).useUserStore()
    const auditorId = String(userStore.userInfo?.id || '')
    await auditJointTask(
      selectedTaskId.value,
      { auditor_id: auditorId, action: hasReject ? 'REJECT' : 'PASS', opinion: opinion || undefined },
      buildIdempotencyKey()
    )
    ElMessage.success('联合巡检审核提交成功')
    router.push({ name: 'JointRecords' })
  } catch {
    ElMessage.error('联合巡检审核提交失败，请稍后重试')
  }
}

const handleToggleEnable = (item: JointTemplateCard) => {
  item.enabled = !item.enabled
  ElMessage.info('后端暂未提供模板启停轻量接口，当前仅本地切换展示')
}

const handleCoverUsers = (item: JointTemplateCard) => {
  ElMessage.info(`模板 #${item.id} 覆盖人员功能待后端接口支持`)
}

const handleCoverCanteens = (item: JointTemplateCard) => {
  ElMessage.info(`模板 #${item.id} 覆盖食堂功能待后端接口支持`)
}

const handleEditTemplate = (item: JointTemplateCard) => {
  router.push({ name: 'JointCreate', query: { templateId: String(item.id) } })
}

const handleDeleteTemplate = async (item: JointTemplateCard) => {
  try {
    await ElMessageBox.confirm(`确定删除模板「${item.name}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    await deleteJointTemplate(item.id)
    templateCards.value = templateCards.value.filter((t) => t.id !== item.id)
    ElMessage.success('已删除')
  } catch {
    // cancelled or error
  }
}

const deleteIssue = (sectionId: string, itemId: string) => {
  const section = createSections.value.find((s) => s.id === sectionId)
  if (!section) return
  if (section.items.length <= 1) {
    ElMessage.warning('每个大项至少保留一条检查小项')
    return
  }
  section.items = section.items.filter((item) => item.id !== itemId)
}

const deleteMajorSection = async (sectionId: string) => {
  const section = createSections.value.find((s) => s.id === sectionId)
  if (!section) return
  try {
    await ElMessageBox.confirm(`确定删除大项「${section.name}」及其所有小项吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    createSections.value = createSections.value.filter((s) => s.id !== sectionId)
  } catch {
    // cancelled
  }
}

const showDeleteMajorDialog = async () => {
  if (!createSections.value.length) {
    ElMessage.warning('当前没有可删除的大项')
    return
  }
  const options = createSections.value.map((s) => `<option value="${s.id}">${s.name}</option>`).join('')
  const selectHtml = `<select id="delete-major-select" style="width:100%;margin-top:8px;padding:6px 8px;border:1px solid #dcdfe6;border-radius:4px;font-size:14px;">${options}</select>`

  // 第一步：选择要删除的大项
  let selectedId: string | null = null
  try {
    await ElMessageBox({
      title: '删除大项',
      message: `<div>请选择要删除的检查大项：${selectHtml}</div>`,
      dangerouslyUseHTMLString: true,
      showCancelButton: true,
      confirmButtonText: '下一步',
      cancelButtonText: '取消',
      type: 'warning',
      beforeClose: (action, _instance, done) => {
        if (action !== 'confirm') { done(); return }
        const sel = document.getElementById('delete-major-select') as HTMLSelectElement | null
        selectedId = sel?.value || null
        if (!selectedId) { ElMessage.warning('请选择要删除的大项'); return }
        done()
      }
    })
  } catch {
    return
  }

  if (!selectedId) return
  const section = createSections.value.find((s) => s.id === selectedId)
  if (!section) return

  // 第二步：二次确认
  try {
    await ElMessageBox.confirm(
      `确定删除大项「${section.name}」及其所有检查小项吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    createSections.value = createSections.value.filter((s) => s.id !== selectedId)
    ElMessage.success(`大项「${section.name}」已删除`)
  } catch {
    // 取消
  }
}

const promptText = async (title: string, placeholder: string, defaultValue = ''): Promise<string | null> => {
  try {
    const result = await ElMessageBox.prompt('请输入内容', title, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: defaultValue,
      inputPlaceholder: placeholder,
      inputValidator: (val: string) => !!val.trim() || '内容不能为空'
    })
    const maybeValue = (result as any)?.value
    return String(maybeValue || '').trim()
  } catch {
    return null
  }
}

const appendIssue = async (sectionId: string) => {
  const section = createSections.value.find((item) => item.id === sectionId)
  if (!section) return
  const nextIndex = section.items.length + 1
  const input = await promptText('新增检查小项', `例如：${nextIndex}、请输入检查小项`, `${nextIndex}、新增检查小项`)
  if (!input) return
  section.items.push(makeCreateItem(`${sectionId}-${Date.now()}`, input))
}

const addMajorSection = async () => {
  const next = createSections.value.length + 1
  const sectionName = await promptText('新增检查大项', `例如：新增大项${next}`, `新增大项${next}`)
  if (!sectionName) return
  const firstItem = await promptText('新增检查小项', '请输入该大项下第一条检查小项', '1、新增检查小项')
  if (!firstItem) return
  createSections.value.push({
    id: `major-${Date.now()}`,
    name: sectionName,
    items: [makeCreateItem(`major-${next}-1`, firstItem)]
  })
}

const validateItemScore = (item: CreateIssueItem) => {
  const val = item.totalScore.trim()
  if (val === '--' || val === '') return
  if (!/^\d+(\.\d{0,1})?$/.test(val)) {
    item.totalScore = '--'
    ElMessage.warning('分值格式不正确，已重置，请输入数字（最多一位小数）')
  }
}

const handleSetupScore = async (sectionId: string, itemId: string) => {
  const section = createSections.value.find((s) => s.id === sectionId)
  const item = section?.items.find((i) => i.id === itemId)
  if (!item) return
  const currentOptions = item.scoringOptions.join(', ')
  try {
    const result = await ElMessageBox.prompt(
      '请输入打分项分值，用逗号分隔（例如: 0, 3, 5, 6）',
      '设置打分项',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: currentOptions,
        inputValidator: (val: string) => {
          if (!val.trim()) return '请输入至少一个分值'
          const nums = val.split(',').map((s) => s.trim()).filter(Boolean)
          return nums.every((n) => /^\d+(\.\d+)?$/.test(n)) || '请输入有效数字'
        }
      }
    )
    const maybeValue = (result as any)?.value
    const nums = String(maybeValue || '').split(',').map((s) => Number(s.trim())).filter((n) => !isNaN(n))
    item.scoringOptions = nums
    if (nums.length) {
      if (item.totalScore === '--' || item.totalScore === '') {
        item.totalScore = String(Math.max(...nums))
      }
    }
  } catch {
    // cancelled
  }
}

const saveCreateChecklist = async () => {
  if (!createForm.name.trim()) {
    ElMessage.warning('请填写检查表名称')
    return
  }
  if (!createSections.value.length) {
    ElMessage.warning('请至少添加一个大项')
    return
  }
  for (const section of createSections.value) {
    if (!section.name.trim()) {
      ElMessage.warning('大项名称不能为空')
      return
    }
    const emptyItem = section.items.find((item) => !item.text.trim())
    if (emptyItem) {
      ElMessage.warning(`“${section.name}” 中存在未填写内容的小项`)
      return
    }
  }
  if (!createForm.canteenId) {
    ElMessage.warning('请选择检查表覆盖食堂')
    return
  }

  if (createForm.tableType === 'SELECT_SCORE') {
    for (const section of createSections.value) {
      for (const item of section.items) {
        if (!item.scoringOptions.length) {
          ElMessage.warning(`「${item.text}」未设置打分项，请点击“设置打分项”进行设置`)
          return
        }
      }
    }
  }

  const majorItems = createSections.value.map((section, i) => ({
    sort_order: i + 1,
    title: section.name,
    minor_items: section.items.map((item, j) => ({
      sort_order: j + 1,
      content: item.text,
      issue_type: item.issueType,
      total_score: item.totalScore && item.totalScore !== '--' ? Number(item.totalScore) : undefined,
      scoring_options: createForm.tableType === 'SELECT_SCORE' && item.scoringOptions.length ? item.scoringOptions : undefined
    }))
  }))
  const targetNodeIds = createForm.canteenId ? [Number(createForm.canteenId)] : []
  const templateId = Number(route.query.templateId || 0)
  const payload = {
    template_name: createForm.name.trim(),
    executor_role: createForm.executorRole || undefined,
    approver_role: createForm.approverRole || undefined,
    target_node_ids: targetNodeIds,
    start_time: createForm.startTime || undefined,
    end_time: createForm.endTime || undefined,
    form_type: createForm.tableType,
    major_items: majorItems
  }
  try {
    if (templateId) {
      await updateJointTemplate(templateId, payload)
    } else {
      await createJointTemplate(payload)
    }
    ElMessage.success('联合巡检检查表保存成功')
    router.push({ name: 'JointChecklist' })
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  }
}

const getStatusClass = (status: JointRow['status']) => {
  if (status === '待整改') return 'status-pending'
  if (status === '已改待审') return 'status-review'
  return 'status-success'
}

const scoreStatusClass = (status: JointScoreStatus) => {
  return status === '已整改' ? 'status-success' : 'status-pending'
}

onMounted(async () => {
  await loadCanteens()
  if (isChecklistView.value) {
    await loadTemplateCards()
    return
  }
  if (isCreateView.value) {
    await initCreateView()
    return
  }
  if (isDetailView.value) {
    await initDetailByRoute()
    return
  }
  await loadRows()
})

watch(
  () => [route.name, route.query.id],
  async () => {
    if (isChecklistView.value) {
      await loadTemplateCards()
      return
    }
    if (isCreateView.value) {
      await initCreateView()
      return
    }
    if (isDetailView.value) {
      await initDetailByRoute()
      return
    }
    if (!allRows.value.length) {
      await loadRows()
    }
  }
)
</script>

<style scoped>
.record-view {
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  padding: 20px;
  background: #fff;
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

.status-pending {
  color: #e6a23c;
}

.status-review {
  color: #409eff;
}

.status-success {
  color: #67c23a;
}

.score-view {
  padding: 12px 12px 10px;
  background: #fff;
  min-height: calc(100vh - 84px);
}

.score-toolbar {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.score-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.score-controls {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}

.score-control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-control-item .label {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
}

.score-date {
  width: 270px;
}

.score-select {
  width: 130px;
}

.score-search-item {
  margin-left: 8px;
}

.score-search {
  width: 230px;
}

.score-table-wrap {
  border: 1px solid #ebeef5;
  background: #fff;
}

.score-footer {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.download-btn {
  background: #4a8ded;
  border-color: #4a8ded;
  height: 32px;
  padding: 0 16px;
}

.create-view {
  background: #fff;
  min-height: calc(100vh - 84px);
  padding: 12px;
}

.create-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.create-card {
  border: 1px solid #dcdfe6;
  background: #fff;
  padding: 10px;
  margin-bottom: 0;
}

.create-row {
  display: grid;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.create-row label {
  font-size: 14px;
  color: #303133;
}

.row-2 {
  grid-template-columns: 100px 300px;
}

.row-4 {
  grid-template-columns: 100px 300px 100px 300px;
}

.items-grid {
  margin-top: 8px;
  border: 1px solid #dcdfe6;
  background: #fff;
}

.items-head {
  display: grid;
  grid-template-columns: 120px 1fr;
  min-height: 36px;
  border-bottom: 1px solid #dcdfe6;
}

.head-left,
.head-right {
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 14px;
  color: #303133;
}

.head-left {
  border-right: 1px solid #dcdfe6;
}

.section-block {
  display: grid;
  grid-template-columns: 120px 1fr;
  border-bottom: 1px solid #dcdfe6;
}

.section-name {
  padding: 8px;
  border-right: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
}

.section-content {
  padding: 8px;
}

.item-row {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) 360px 160px 200px 120px 60px;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  border-bottom: 1px solid #e5e7eb;
}

.item-row:last-child {
  border-bottom: none;
}

.item-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-select {
  width: 90px;
}

.mini-input {
  width: 80px;
}

.score-btn {
  background: #4a8ded;
  border-color: #4a8ded;
  color: #fff;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-col {
  display: flex;
  align-items: center;
  overflow: hidden;
}

.rectify-wrap {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
  gap: 8px;
}

.actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0 0;
}

.actions-left {
  display: flex;
  gap: 10px;
  align-items: center;
}

.add-major-btn,
.del-major-btn,
.save-create-btn {
  min-width: 100px;
  height: 30px;
}

.checklist-view {
  padding: 0;
  background: #eef0f8;
  min-height: calc(100vh - 84px);
}

.checklist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: #f7f7f7;
  border-bottom: 1px solid #e5e7ef;
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
  grid-template-columns: 4px 1fr 260px 420px;
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

.card-actions {
  display: flex;
  justify-content: center;
  gap: 22px;
}

.outline-btn {
  width: 88px;
  height: 36px;
  border-color: #4a8ded;
  color: #4a8ded;
  font-size: 14px;
}

.edit-btn {
  width: 88px;
  height: 36px;
  font-size: 14px;
  background: #4a8ded;
  border-color: #4a8ded;
}

.delete-btn {
  width: 88px;
  height: 36px;
  font-size: 14px;
  background: #f56c6c;
  border-color: #f56c6c;
  color: #fff;
}

.detail-view {
  background: #fff;
  min-height: calc(100vh - 84px);
  padding: 16px 12px;
}

.detail-headline {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.detail-meta {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 170px 1fr;
  gap: 8px;
}

.detail-left-col,
.detail-main-col {
  border: 1px solid #6f7787;
  background: #aeb9d8;
}

.col-header {
  height: 36px;
  line-height: 36px;
  padding: 0 8px;
  border-bottom: 1px solid #6f7787;
  font-size: 14px;
  color: #303133;
}

.section-item {
  height: 42px;
  line-height: 42px;
  padding: 0 10px;
  border-bottom: 1px solid #6f7787;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
}

.section-item.active {
  background: rgba(255, 255, 255, 0.36);
  font-weight: 600;
}

.main-head-row,
.issue-row {
  display: grid;
  grid-template-columns: 53% 33% 14%;
}

.main-head-row {
  height: 36px;
  border-bottom: 1px solid #6f7787;
}

.main-head-item {
  line-height: 36px;
  padding: 0 8px;
  font-size: 14px;
  color: #303133;
  border-right: 1px solid #6f7787;
}

.main-head-item:last-child,
.issue-cell:last-child {
  border-right: none;
}

.issue-row {
  min-height: 120px;
  border-bottom: 1px solid #dbe3f5;
}

.issue-cell {
  padding: 8px;
  border-right: 1px solid #dbe3f5;
}

.issue-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
}

.issue-tag {
  width: 26px;
  height: 18px;
  display: inline-block;
}

.full-score {
  margin-left: auto;
  font-size: 14px;
}

.issue-score,
.issue-desc,
.feedback-desc {
  font-size: 14px;
  color: #303133;
  margin-top: 2px;
}

.photo-list {
  margin-top: 6px;
  display: flex;
  gap: 8px;
}

.photo-box {
  width: 78px;
  height: 58px;
  border: 3px solid #d7dce5;
  background: #4da7d6;
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btns {
  display: flex;
  gap: 8px;
}

.pass-btn,
.reject-btn {
  width: 100%;
  height: 34px;
  margin: 0;
}

.pass-btn {
  background: #4a8ded;
  color: #fff;
  border: 1px solid #4a8ded;
}

.pass-btn.active {
  background: #2f72d6;
  border-color: #2f72d6;
}

.reject-btn {
  background: #ef1010;
  color: #fff;
  border: 1px solid #ef1010;
}

.reject-btn.active {
  background: #cf0a0a;
  border-color: #cf0a0a;
}

.reject-input {
  margin-top: 8px;
}

.detail-submit-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.detail-submit-btn {
  width: 260px;
  background: #4a8ded;
  border-color: #4a8ded;
}
</style>
