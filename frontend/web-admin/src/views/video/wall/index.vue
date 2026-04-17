<template>
  <div class="video-page" v-loading="loading">
    <template v-if="isInspectionView">
      <div class="inspect-head">
        <div class="inspect-title">视频巡检</div>
        <div class="inspect-control">
          <span>食堂选择</span>
          <el-select v-model="inspectionFilters.canteenId" class="head-select" @change="handleInspectCanteenChange">
            <el-option v-for="item in canteenOptions" :key="`inspect-canteen-${item.id}`" :label="item.name" :value="item.id" />
          </el-select>
        </div>
        <div class="inspect-control">
          <span>画面区域</span>
          <el-select v-model="inspectionFilters.cameraId" class="head-select" @change="handleInspectCameraChange">
            <el-option v-for="item in selectedCanteenCameras" :key="`inspect-camera-${item.id}`" :label="item.label" :value="item.id" />
          </el-select>
        </div>
      </div>

      <div class="inspect-layout">
        <section class="inspect-video-area">
          <div class="grid-frame">
            <div v-for="item in visibleVideoCards" :key="item.id" class="video-card">
              <img :src="placeholderImage" alt="video" class="video-img" />
              <div class="video-name">{{ item.name }}</div>
            </div>
          </div>
          <div class="toolbar">
            <el-button link type="primary" @click="switchSplitScreen">分屏选择</el-button>
            <el-button link type="primary" @click="viewPlayback">录像回看</el-button>
            <el-button link type="primary" @click="toggleFullscreen">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </div>
        </section>

        <aside class="inspect-panel">
          <div v-for="item in inspectItems" :key="item.id" class="inspect-item">
            <div class="item-header">
              <div class="item-title-wrap">
                <span class="color-tag" :style="{ background: item.color }"></span>
                <span>{{ item.title }}</span>
              </div>
              <span>满分：6分</span>
            </div>
            <div class="item-score-row">
              <el-radio-group v-model="item.score" class="score-radio-group">
                <el-radio :value="3">3分</el-radio>
                <el-radio :value="4">4分</el-radio>
                <el-radio :value="6">6分</el-radio>
              </el-radio-group>
            </div>
            <div class="item-desc">描述：{{ item.desc }}</div>
            <div class="item-media-row">
              <img :src="placeholderImage" alt="snapshot" class="shot-thumb" />
              <img :src="placeholderImage" alt="snapshot" class="shot-thumb" />
              <el-button class="shot-btn" @click="captureShot(item.id)">点击抓拍</el-button>
            </div>
          </div>
          <div class="inspect-submit-wrap">
            <el-button type="primary" class="inspect-submit-btn" @click="submitInspect">提交</el-button>
          </div>
        </aside>
      </div>
    </template>

    <template v-else-if="isRecordsView">
      <div class="record-view">
        <header class="rv-header">
          <div class="title">视频巡检记录</div>
          <div class="controls">
            <div class="control-item">
              <span class="label">起止日期</span>
              <el-date-picker
                v-model="recordQuery.dateRange"
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
              <el-select v-model="recordQuery.status" placeholder="全部状态" style="width: 140px">
                <el-option label="全部状态" value="" />
                <el-option label="待整改" value="待整改" />
                <el-option label="已改待审" value="已改待审" />
                <el-option label="整改成功" value="整改成功" />
              </el-select>
            </div>
            <div class="control-item">
              <span class="label">搜索</span>
              <el-input v-model="recordQuery.keyword" clearable style="width: 240px" />
            </div>
          </div>
        </header>

        <div class="table-container">
          <el-table
            :data="recordPagedRows"
            v-loading="recordLoading"
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
          >
            <el-table-column prop="submitCanteen" label="提交食堂" min-width="180" show-overflow-tooltip />
            <el-table-column prop="submitter" label="提交人" min-width="80" />
            <el-table-column prop="submitForm" label="提交表格" min-width="170" show-overflow-tooltip />
            <el-table-column prop="score" label="检查分数" min-width="95" align="center" />
            <el-table-column prop="redline" label="红线问题" min-width="95" align="center" />
            <el-table-column prop="submitDate" label="提交日期" min-width="120" align="center" />
            <el-table-column prop="status" label="状态" min-width="95" align="center">
              <template #default="scope">
                <span :class="recordStatusClass(scope.row.status)">{{ scope.row.status }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="120" align="center">
              <template #default="scope">
                <el-button link type="primary" @click="handleRecordPrimary(scope.row)">{{ scope.row.primaryAction }}</el-button>
                <el-button link type="primary" @click="handleRecordCancel(scope.row)">取消</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <footer class="rv-footer">
          <el-pagination
            v-model:current-page="recordPage"
            v-model:page-size="recordPageSize"
            :page-sizes="[10, 20, 30, 50]"
            layout="prev, pager, next"
            :total="recordTotal"
            @size-change="handleRecordSizeChange"
            @current-change="handleRecordPageChange"
          />
        </footer>
      </div>
    </template>

    <template v-else-if="isScoreView">
      <div class="score-view">
        <div class="score-toolbar">
          <div class="score-title">视频巡检表分数统计</div>
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
                <el-option v-for="item in canteenOptions" :key="`video-score-canteen-${item.id}`" :label="item.name" :value="String(item.id)" />
              </el-select>
            </div>
            <div class="score-control-item">
              <span class="label">表格筛选</span>
              <el-select v-model="scoreQuery.formName" class="score-select" placeholder="全部表格">
                <el-option label="全部表格" value="" />
                <el-option v-for="name in scoreFormOptions" :key="`video-score-form-${name}`" :label="name" :value="name" />
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
            v-loading="recordLoading"
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
    </template>

    <template v-else-if="isChecklistView">
      <div class="checklist-view">
        <template v-if="!checklistEditing">
          <div class="checklist-title">视频巡检检查表模板</div>
          <div class="checklist-list">
            <div v-for="item in checklistTemplates" :key="item.id" class="template-row">
              <div class="template-name-col">
                <div class="template-name">{{ item.name }}</div>
                <div class="template-desc">需完成{{ item.itemCount }}项</div>
              </div>
              <div class="template-enable-col">
                <span>是否启用</span>
                <el-switch v-model="item.enabled" />
              </div>
              <div class="template-btns">
                <el-button class="ghost-btn" @click="handleTemplatePeople(item)">覆盖人员</el-button>
                <el-button class="ghost-btn" @click="handleTemplateCanteen(item)">覆盖食堂</el-button>
                <el-button type="primary" class="edit-btn" @click="handleTemplateEdit(item)">编辑</el-button>
              </div>
            </div>
          </div>
          <div class="checklist-create-wrap">
            <el-button type="primary" @click="handleCreateTemplate">+新建巡检检查表</el-button>
          </div>
        </template>

        <template v-else>
          <div class="checklist-edit-title">新建视频巡检检查表</div>
          <div class="checklist-edit-grid">
            <div class="eg-label">检查表名称</div>
            <div class="eg-cell span-3"><el-input v-model="checklistForm.name" /></div>

            <div class="eg-label">检查表执行人员</div>
            <div class="eg-cell">
              <el-select v-model="checklistForm.executor" style="width: 100%">
                <el-option v-for="item in checklistPeopleOptions" :key="`executor-${item}`" :label="item" :value="item" />
              </el-select>
            </div>
            <div class="eg-label">审批人员</div>
            <div class="eg-cell">
              <el-select v-model="checklistForm.auditor" style="width: 100%">
                <el-option v-for="item in checklistPeopleOptions" :key="`auditor-${item}`" :label="item" :value="item" />
              </el-select>
            </div>

            <div class="eg-label">开始提交时间</div>
            <div class="eg-cell">
              <el-time-picker v-model="checklistForm.startTime" format="HH:mm" value-format="HH:mm" style="width: 100%" placeholder="--:--" />
            </div>
            <div class="eg-label">截止时间</div>
            <div class="eg-cell">
              <el-time-picker v-model="checklistForm.endTime" format="HH:mm" value-format="HH:mm" style="width: 100%" />
            </div>

            <div class="eg-label">检查表覆盖食堂</div>
            <div class="eg-cell span-3">
              <el-select v-model="checklistForm.canteenId" style="width: 100%">
                <el-option v-for="item in checklistCanteenOptions" :key="`canteen-${item.id}`" :label="item.name" :value="item.id" />
              </el-select>
            </div>

            <div class="eg-label">表格类型</div>
            <div class="eg-cell span-3">
              <el-select v-model="checklistForm.formType" style="width: 100%">
                <el-option label="选分表" value="选分表" />
                <el-option label="填空表" value="填空表" />
              </el-select>
            </div>

            <div class="eg-label">添加检查大项</div>
            <div class="eg-cell span-3 add-tools">
              <el-button link type="primary" @click="handleAddMajorSection">添加检查小项</el-button>
            </div>
          </div>

          <div class="check-item-table">
            <div v-for="section in checklistForm.sections" :key="section.id" class="major-row">
              <div class="major-name">{{ section.name }}</div>
              <div class="minor-list">
                <div v-for="(minor, index) in section.items" :key="minor.id" class="minor-row">
                  <div class="minor-title">
                    <span>{{ index + 1 }}、{{ minor.title }}</span>
                  </div>
                  <div class="minor-type">
                    <span>问题类型：</span>
                    <el-select v-model="minor.riskType" style="width: 88px">
                      <el-option label="红线" value="红线" />
                      <el-option label="黄线" value="黄线" />
                      <el-option label="蓝线" value="蓝线" />
                    </el-select>
                  </div>
                  <div class="minor-score">
                    <span>总分：</span>
                    <el-input v-model.number="minor.fullScore" style="width: 72px" />
                    <el-icon><Clock /></el-icon>
                  </div>
                  <el-button type="primary" class="minor-btn">设置打分项</el-button>
                  <el-button type="primary" class="minor-btn">关联摄像头</el-button>
                  <div class="minor-rectify">
                    <span>是否整改</span>
                    <el-radio-group v-model="minor.needRectify">
                      <el-radio :value="true">是</el-radio>
                      <el-radio :value="false">否</el-radio>
                    </el-radio-group>
                  </div>
                  <el-button link type="primary" @click="handleAddMinor(section.id)">向下新增一条</el-button>
                </div>
              </div>
            </div>
          </div>

          <div class="checklist-edit-actions">
            <el-button type="primary" @click="handleSaveChecklist">保存</el-button>
          </div>
        </template>
      </div>
    </template>

    <template v-else-if="isDetailView">
      <div class="detail-view">
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
                  <img :src="placeholderImage" alt="issue" class="detail-thumb" />
                  <img :src="placeholderImage" alt="issue" class="detail-thumb" />
                </div>
              </div>

              <div class="issue-cell issue-feedback">
                <div class="feedback-desc">整改描述：{{ issue.rectifyDesc }}</div>
                <div class="photo-list">
                  <img :src="placeholderImage" alt="feedback" class="detail-thumb" />
                  <img :src="placeholderImage" alt="feedback" class="detail-thumb" />
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
    </template>

    <template v-else>
      <div class="page-title">视频食堂选择</div>
      <div class="layout-wrap">
        <aside class="left-panes">
          <div class="tree-pane">
            <el-tree
              :data="orgTreeData"
              node-key="id"
              :props="treeProps"
              default-expand-all
              highlight-current
              @node-click="handleOrgNodeClick"
            />
          </div>
          <div class="tree-pane second-pane">
            <el-tree
              :data="cameraTreeData"
              node-key="id"
              :props="treeProps"
              default-expand-all
              highlight-current
              @node-click="handleCameraNodeClick"
            />
          </div>
        </aside>

        <section class="right-grid-area">
          <div class="grid-frame">
            <div v-for="item in visibleVideoCards" :key="item.id" class="video-card">
              <img :src="placeholderImage" alt="video" class="video-img" />
              <div class="video-name">{{ item.name }}</div>
            </div>
          </div>
          <div class="toolbar">
            <el-button link type="primary" @click="switchSplitScreen">分屏选择</el-button>
            <el-button link type="primary" @click="viewPlayback">录像回看</el-button>
            <el-button link type="primary" @click="toggleFullscreen">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, FullScreen } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getAllDepts, getOrgTree, getLedgerInstanceList, type AdminDeptRecord, type OrgTreeNode } from '@/api/canteen'

interface TreeNode {
  id: string
  label: string
  children?: TreeNode[]
  canteenId?: number
  isCamera?: boolean
}

interface VideoCard {
  id: string
  name: string
}

interface InspectItem {
  id: string
  color: string
  title: string
  score: number
  desc: string
}

interface CanteenOption {
  id: number
  name: string
}

interface CameraOption {
  id: string
  label: string
}

type VideoRecordStatus = '待整改' | '已改待审' | '整改成功'

interface VideoRecordRow {
  id: number
  submitCanteen: string
  submitter: string
  submitForm: string
  score: number
  redline: number
  submitDate: string
  status: VideoRecordStatus
  primaryAction: '查看' | '编辑'
}

interface VideoDetailIssue {
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

interface VideoDetailSection {
  id: string
  name: string
  issues: VideoDetailIssue[]
}

type VideoScoreStatus = '待整改' | '已整改'

interface VideoScoreRow {
  id: number
  canteenId: number
  canteen: string
  form: string
  score: number
  redline: number
  yellowline: number
  status: VideoScoreStatus
  submitDate: string
}

interface ChecklistTemplate {
  id: number
  name: string
  itemCount: number
  enabled: boolean
}

interface ChecklistMinorItem {
  id: number
  title: string
  riskType: '红线' | '黄线' | '蓝线'
  fullScore: number
  needRectify: boolean
}

interface ChecklistMajorSection {
  id: number
  name: string
  items: ChecklistMinorItem[]
}

const route = useRoute()
const router = useRouter()
const isInspectionView = computed(() => route.name === 'VideoInspection')
const isRecordsView = computed(() => route.name === 'VideoRecords')
const isDetailView = computed(() => route.name === 'VideoDetail')
const isChecklistView = computed(() => route.name === 'VideoChecklist')
const isScoreView = computed(() => route.name === 'VideoScore')

const loading = ref(false)
const orgTreeData = ref<TreeNode[]>([])
const cameraTreeData = ref<TreeNode[]>([])
const canteenOptions = ref<CanteenOption[]>([])
const selectedCanteenId = ref<number | null>(null)
const videoCards = ref<VideoCard[]>([])
const recordRows = ref<VideoRecordRow[]>([])
const recordLoading = ref(false)
const detailRecordTitle = ref('武岗一中一食堂视频巡检记录')
const detailDate = ref('2026.1.6')
const detailSubmitter = ref('张三')
const detailSections = ref<VideoDetailSection[]>([])
const selectedSectionId = ref<string>('food')
const checklistEditing = ref(false)
const checklistTemplates = ref<ChecklistTemplate[]>([
  { id: 1, name: '高中视频巡检表', itemCount: 25, enabled: true },
  { id: 2, name: '小学视频巡检检查表', itemCount: 25, enabled: true },
  { id: 3, name: '中央厨房视频巡检检查表', itemCount: 25, enabled: true }
])
const activeTemplateId = ref<number | null>(null)
const checklistPeopleOptions = ['食安总监', '食堂经理', '校区管理员']

const checklistForm = reactive({
  name: '',
  executor: '食安总监',
  auditor: '食安总监',
  startTime: '',
  endTime: '20:00',
  canteenId: 0,
  formType: '选分表',
  sections: [] as ChecklistMajorSection[]
})

const inspectionFilters = reactive({
  canteenId: 0,
  cameraId: ''
})

const recordQuery = reactive({
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

const recordPage = ref(2)
const recordPageSize = ref(10)
const scorePage = ref(2)
const scorePageSize = ref(10)

const checklistCanteenOptions = computed(() => {
  return canteenOptions.value.length ? canteenOptions.value : [{ id: 1, name: '城东食堂' }]
})

const inspectItems = ref<InspectItem[]>([
  {
    id: 'i1',
    color: '#ef1010',
    title: '1、食堂无三无、腐烂、过期食材',
    score: 3,
    desc: '发现生鲜食材关于土豆有发芽情况'
  },
  {
    id: 'i2',
    color: '#d4d600',
    title: '2、食堂地面无明显积水，清洁到位',
    score: 4,
    desc: '烹饪间有积水明显，需要处理下水道排水问题'
  },
  {
    id: 'i3',
    color: '#4a8ded',
    title: '1、前厅餐后桌面卫生整洁',
    score: 3,
    desc: '桌面卫生一般，需要加强及时清扫'
  }
])

const treeProps = {
  label: 'label',
  children: 'children'
}

const placeholderImage =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180"><rect width="320" height="180" fill="#efefef"/><circle cx="190" cy="36" r="13" fill="#bbb"/><path d="M4 120 L82 80 L155 120 L216 72 L316 148 L316 176 L4 176 Z" fill="#2398ca"/></svg>'
  )

const visibleVideoCards = computed(() => {
  if (!videoCards.value.length) {
    return Array.from({ length: 9 }).map((_, idx) => ({
      id: `placeholder-${idx + 1}`,
      name: `摄像头${idx + 1}`
    }))
  }
  return videoCards.value.slice(0, 9)
})

const mapOrgTree = (nodes: OrgTreeNode[]): TreeNode[] => {
  return nodes.map((node) => ({
    id: `org-${node.id}`,
    label: node.name,
    canteenId: node.type === 'CANTEEN' ? Number(node.id) : undefined,
    children: node.children ? mapOrgTree(node.children) : []
  }))
}

const buildCameraTreeByDept = (depts: AdminDeptRecord[]) => {
  const canteens = depts.filter((item) => item.org_type === 'CANTEEN')
  return canteens.map((canteen) => ({
    id: `cam-root-${canteen.id}`,
    label: canteen.name,
    canteenId: canteen.id,
    children: [1, 2, 3, 4, 5, 6].map((idx) => ({
      id: `cam-${canteen.id}-${idx}`,
      label: `${idx}号摄像头`,
      canteenId: canteen.id,
      isCamera: true
    }))
  }))
}

const buildCameraOptionsByCanteen = (canteenId: number): CameraOption[] => {
  return [1, 2, 3, 4, 5, 6].map((idx) => ({
    id: `cam-${canteenId}-${idx}`,
    label: `${idx}号摄像头`
  }))
}

const selectedCanteenCameras = computed<CameraOption[]>(() => {
  const id = inspectionFilters.canteenId || selectedCanteenId.value
  if (!id) return []
  return buildCameraOptionsByCanteen(id)
})

const inRange = (date: string, start: string, end: string) => {
  if (!start || !end) return true
  return date >= start && date <= end
}

const recordFilteredRows = computed(() => {
  const [startDate, endDate] = recordQuery.dateRange || []
  const keyword = recordQuery.keyword.trim().toLowerCase()
  return recordRows.value.filter((item) => {
    const matchStatus = !recordQuery.status || item.status === recordQuery.status
    const matchDate = !startDate || !endDate || inRange(item.submitDate, startDate, endDate)
    const matchKeyword = !keyword || `${item.submitCanteen} ${item.submitter} ${item.submitForm}`.toLowerCase().includes(keyword)
    return matchStatus && matchDate && matchKeyword
  })
})

const recordTotal = computed(() => recordFilteredRows.value.length)

const recordPagedRows = computed(() => {
  const start = (recordPage.value - 1) * recordPageSize.value
  return recordFilteredRows.value.slice(start, start + recordPageSize.value)
})

const scoreRows = computed<VideoScoreRow[]>(() => {
  return recordRows.value.map((item) => ({
    id: item.id,
    canteenId: canteenOptions.value.find((c) => c.name === item.submitCanteen)?.id || 0,
    canteen: item.submitCanteen,
    form: item.submitForm,
    score: item.score,
    redline: item.redline,
    yellowline: 20,
    status: item.status === '待整改' ? '待整改' : '已整改',
    submitDate: item.submitDate
  }))
})

const scoreFormOptions = computed(() => {
  const formSet = new Set<string>()
  scoreRows.value.forEach((item) => formSet.add(item.form))
  return Array.from(formSet)
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

const statusMap: Record<string, VideoRecordStatus> = {
  filling: '待整改',
  pending: '待整改',
  signed: '已改待审',
  archived: '整改成功'
}

const submitterPool = ['张三', '李四', '王五']
const formPool = ['高中视频巡检检查表', '初中视频巡检检查表', '幼儿园视频巡检检查表']

const createDetailIssue = (idBase: number, title: string, score: number, color: string): VideoDetailIssue => ({
  id: idBase,
  title,
  fullScore: 6,
  score,
  description: '发现生鲜食材关于土豆有发芽情况',
  rectifyDesc: '发现生鲜食材关于土豆有发芽情况',
  tagColor: color,
  decision: '',
  rejectReason: ''
})

const createChecklistMinor = (idBase: number, title = '食堂无三无、腐烂、过期食材'): ChecklistMinorItem => ({
  id: idBase,
  title,
  riskType: '红线',
  fullScore: 6,
  needRectify: true
})

const createChecklistSections = (): ChecklistMajorSection[] => [
  {
    id: 1,
    name: '食材问题排查',
    items: [createChecklistMinor(11), createChecklistMinor(12), createChecklistMinor(13)]
  },
  {
    id: 2,
    name: '环境问题排查',
    items: [createChecklistMinor(21, '食堂地面无明显积水，清洁到位')]
  },
  {
    id: 3,
    name: '就餐问题排查',
    items: [createChecklistMinor(31, '前厅餐后桌面卫生整洁')]
  },
  {
    id: 4,
    name: '消防问题排查',
    items: [createChecklistMinor(41, '灭火器均在使用期限内')]
  }
]

const buildDetailSections = (): VideoDetailSection[] => [
  {
    id: 'food',
    name: '食材问题排查',
    issues: [
      createDetailIssue(1, '1、食堂无三无、腐烂、过期食材', 3, '#ef1010'),
      createDetailIssue(2, '2、食堂地面无明显积水，清洁到位', 3, '#d4d600'),
      createDetailIssue(3, '1、前厅餐后桌面卫生整洁', 3, '#4a8ded')
    ]
  },
  { id: 'people', name: '人员问题排查', issues: [createDetailIssue(4, '1、工作人员证照齐全并在有效期内', 4, '#4a8ded')] },
  { id: 'environment', name: '环境问题排查', issues: [createDetailIssue(5, '1、后厨通风与照明符合标准', 4, '#4a8ded')] },
  { id: 'device', name: '设备问题排查', issues: [createDetailIssue(6, '1、设备巡检记录齐全', 4, '#4a8ded')] },
  { id: 'risk', name: '消费风险排查', issues: [createDetailIssue(7, '1、风险预警机制运行正常', 4, '#4a8ded')] }
]

const buildVideoCards = (canteenId: number | null, cameraName?: string) => {
  const base = canteenId ? `食堂${canteenId}` : '当前食堂'
  if (cameraName) {
    videoCards.value = [{ id: `single-${Date.now()}`, name: `${base}-${cameraName}` }]
    return
  }
  videoCards.value = Array.from({ length: 9 }).map((_, idx) => ({
    id: `${base}-${idx + 1}`,
    name: `${base}-${idx + 1}号摄像头`
  }))
}

const loadPageData = async () => {
  loading.value = true
  try {
    const [orgRes, deptRes]: any = await Promise.all([getOrgTree(), getAllDepts()])
    const tree = orgRes?.data?.tree || []
    const depts = deptRes?.data?.records || []

    orgTreeData.value = mapOrgTree(tree)
    cameraTreeData.value = buildCameraTreeByDept(depts)
    canteenOptions.value = depts
      .filter((item: AdminDeptRecord) => item.org_type === 'CANTEEN')
      .map((item: AdminDeptRecord) => ({ id: Number(item.id), name: item.name }))

    const firstCanteen = depts.find((item: AdminDeptRecord) => item.org_type === 'CANTEEN')
    selectedCanteenId.value = firstCanteen?.id ?? null
    inspectionFilters.canteenId = firstCanteen?.id ?? 0
    const firstCamera = firstCanteen ? `cam-${firstCanteen.id}-1` : ''
    inspectionFilters.cameraId = firstCamera
    buildVideoCards(selectedCanteenId.value)
  } catch {
    orgTreeData.value = []
    cameraTreeData.value = []
    canteenOptions.value = []
    inspectionFilters.canteenId = 0
    inspectionFilters.cameraId = ''
    buildVideoCards(null)
    ElMessage.warning('视频组织数据加载失败，当前展示默认画面')
  } finally {
    loading.value = false
  }
}

const loadRecordRows = async () => {
  recordLoading.value = true
  try {
    const res: any = await getLedgerInstanceList({ page: 1, size: 200 })
    const records = res?.data?.records || []
    recordRows.value = records.map((item: any, index: number) => {
      const canteenId = Number(item.canteen_id || 0)
      const rawStatus = String(item.status || '').toLowerCase()
      return {
        id: Number(item.id),
        submitCanteen: canteenOptions.value.find((c) => c.id === canteenId)?.name || `食堂${canteenId || 1}`,
        submitter: submitterPool[index % submitterPool.length],
        submitForm: formPool[index % formPool.length],
        score: 69 + ((index + 4) % 27),
        redline: (index + 2) % 3,
        submitDate: String(item.created_at || '').slice(0, 10) || '2020-05-24',
        status: statusMap[rawStatus] || '待整改',
        primaryAction: index < 2 ? '查看' : '编辑'
      } as VideoRecordRow
    })

    if (!recordRows.value.length) {
      recordRows.value = [
        { id: 1, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '高中视频巡检检查表', score: 85, redline: 0, submitDate: '2020-05-24', status: '待整改', primaryAction: '查看' },
        { id: 2, submitCanteen: '武岗实验中学一食堂', submitter: '李四', submitForm: '初中视频巡检检查表', score: 89, redline: 0, submitDate: '2020-05-24', status: '已改待审', primaryAction: '查看' },
        { id: 3, submitCanteen: '城东机关幼儿园食堂', submitter: '王五', submitForm: '幼儿园视频巡检检查表', score: 73, redline: 1, submitDate: '2020-05-24', status: '整改成功', primaryAction: '编辑' }
      ]
    }
  } catch {
    recordRows.value = [
      { id: 1, submitCanteen: '武岗一中一食堂', submitter: '张三', submitForm: '高中视频巡检检查表', score: 85, redline: 0, submitDate: '2020-05-24', status: '待整改', primaryAction: '查看' },
      { id: 2, submitCanteen: '武岗实验中学一食堂', submitter: '李四', submitForm: '初中视频巡检检查表', score: 89, redline: 0, submitDate: '2020-05-24', status: '已改待审', primaryAction: '查看' },
      { id: 3, submitCanteen: '城东机关幼儿园食堂', submitter: '王五', submitForm: '幼儿园视频巡检检查表', score: 73, redline: 1, submitDate: '2020-05-24', status: '整改成功', primaryAction: '编辑' }
    ]
    ElMessage.warning('视频巡检记录接口暂不可用，当前展示示例数据')
  } finally {
    recordLoading.value = false
  }
}

const initDetailByRoute = () => {
  const id = Number(route.query.id || 0)
  const matched = recordRows.value.find((item) => item.id === id)
  if (matched) {
    detailRecordTitle.value = `${matched.submitCanteen}视频巡检记录`
    detailDate.value = matched.submitDate.replace(/-/g, '.')
    detailSubmitter.value = matched.submitter
  }
  detailSections.value = buildDetailSections()
  selectedSectionId.value = detailSections.value[0]?.id || 'food'
}

const handleOrgNodeClick = (node: TreeNode) => {
  if (node.canteenId) {
    selectedCanteenId.value = node.canteenId
    inspectionFilters.canteenId = node.canteenId
    inspectionFilters.cameraId = `cam-${node.canteenId}-1`
    buildVideoCards(selectedCanteenId.value)
  }
}

const handleCameraNodeClick = (node: TreeNode) => {
  if (!node.canteenId) return
  selectedCanteenId.value = node.canteenId
  inspectionFilters.canteenId = node.canteenId
  if (node.isCamera) {
    inspectionFilters.cameraId = node.id
    buildVideoCards(node.canteenId, node.label)
  } else {
    inspectionFilters.cameraId = `cam-${node.canteenId}-1`
    buildVideoCards(node.canteenId)
  }
}

const handleInspectCanteenChange = (value: number) => {
  selectedCanteenId.value = value
  inspectionFilters.cameraId = `cam-${value}-1`
  buildVideoCards(value)
}

const handleInspectCameraChange = (value: string) => {
  const selected = selectedCanteenCameras.value.find((item) => item.id === value)
  if (!selected || !inspectionFilters.canteenId) return
  buildVideoCards(inspectionFilters.canteenId, selected.label)
}

const captureShot = (itemId: string) => {
  ElMessage.success(`检查项 ${itemId} 抓拍成功`)
}

const submitInspect = () => {
  ElMessage.success('视频巡检提交成功')
}

const handleDetailSubmit = () => {
  ElMessage.success('视频巡检详情提交成功')
}

const resetChecklistForm = () => {
  checklistForm.name = ''
  checklistForm.executor = '食安总监'
  checklistForm.auditor = '食安总监'
  checklistForm.startTime = ''
  checklistForm.endTime = '20:00'
  checklistForm.canteenId = checklistCanteenOptions.value[0]?.id || 0
  checklistForm.formType = '选分表'
  checklistForm.sections = createChecklistSections()
}

const handleTemplatePeople = (item: ChecklistTemplate) => {
  ElMessage.info(`模板 ${item.name} 人员覆盖功能开发中`)
}

const handleTemplateCanteen = (item: ChecklistTemplate) => {
  ElMessage.info(`模板 ${item.name} 食堂覆盖功能开发中`)
}

const handleTemplateEdit = (item: ChecklistTemplate) => {
  activeTemplateId.value = item.id
  checklistEditing.value = true
  resetChecklistForm()
  checklistForm.name = item.name
}

const handleCreateTemplate = () => {
  activeTemplateId.value = null
  checklistEditing.value = true
  resetChecklistForm()
}

const handleAddMajorSection = () => {
  const nextId = checklistForm.sections.length + 1
  checklistForm.sections.push({
    id: nextId,
    name: `新增问题排查${nextId}`,
    items: [createChecklistMinor(nextId * 10 + 1)]
  })
}

const handleAddMinor = (sectionId: number) => {
  const target = checklistForm.sections.find((item) => item.id === sectionId)
  if (!target) return
  const nextId = target.items.length ? target.items[target.items.length - 1].id + 1 : sectionId * 10 + 1
  target.items.push(createChecklistMinor(nextId))
}

const handleSaveChecklist = () => {
  if (!checklistForm.name.trim()) {
    ElMessage.warning('请填写检查表名称')
    return
  }

  const payloadName = checklistForm.name.trim()
  if (activeTemplateId.value) {
    const target = checklistTemplates.value.find((item) => item.id === activeTemplateId.value)
    if (target) {
      target.name = payloadName
      target.itemCount = checklistForm.sections.reduce((acc, section) => acc + section.items.length, 0)
    }
  } else {
    checklistTemplates.value.unshift({
      id: Date.now(),
      name: payloadName,
      itemCount: checklistForm.sections.reduce((acc, section) => acc + section.items.length, 0),
      enabled: true
    })
  }

  checklistEditing.value = false
  ElMessage.success('视频巡检检查表保存成功')
}

const handleRecordPrimary = (row: VideoRecordRow) => {
  if (row.primaryAction === '查看') {
    router.push({ name: 'VideoDetail', query: { id: String(row.id) } })
    return
  }
  router.push({ name: 'VideoInspection', query: { id: String(row.id) } })
}

const handleRecordCancel = (row: VideoRecordRow) => {
  ElMessage.info(`取消记录 #${row.id}`)
}

const handleRecordPageChange = (value: number) => {
  recordPage.value = value
}

const handleRecordSizeChange = (value: number) => {
  recordPageSize.value = value
  recordPage.value = 1
}

const handleScoreSearch = () => {
  scorePage.value = 1
}

const handleScorePageChange = (value: number) => {
  scorePage.value = value
}

const handleScoreSizeChange = (value: number) => {
  scorePageSize.value = value
  scorePage.value = 1
}

const handleScoreEdit = (row: VideoScoreRow) => {
  router.push({ name: 'VideoInspection', query: { id: String(row.id) } })
}

const handleScoreCancel = (row: VideoScoreRow) => {
  ElMessage.info(`取消统计记录 #${row.id}`)
}

const handleScoreDownload = () => {
  ElMessage.success('视频巡检分数统计导出成功')
}

const scoreStatusClass = (status: VideoScoreStatus) => {
  return status === '待整改' ? 'status-pending' : 'status-success'
}

const recordStatusClass = (status: VideoRecordStatus) => {
  if (status === '整改成功') return 'status-success'
  if (status === '已改待审') return 'status-review'
  return 'status-pending'
}

const switchSplitScreen = () => {
  buildVideoCards(selectedCanteenId.value)
}

const viewPlayback = () => {
  ElMessage.info('录像回看功能开发中')
}

const toggleFullscreen = async () => {
  const target = document.documentElement
  if (!document.fullscreenElement) {
    await target.requestFullscreen()
  } else {
    await document.exitFullscreen()
  }
}

onMounted(async () => {
  await loadPageData()
  if (isRecordsView.value || isDetailView.value || isScoreView.value) {
    await loadRecordRows()
  }
  if (isChecklistView.value) {
    resetChecklistForm()
    checklistEditing.value = route.query.mode === 'edit'
  }
  if (isDetailView.value) {
    initDetailByRoute()
  }
})

watch(
  () => [route.name, route.query.id],
  async () => {
    if ((isRecordsView.value || isDetailView.value || isScoreView.value) && !recordRows.value.length) {
      await loadRecordRows()
    }
    if (isChecklistView.value) {
      if (!checklistForm.sections.length) {
        resetChecklistForm()
      }
      checklistEditing.value = route.query.mode === 'edit' || checklistEditing.value
    } else {
      checklistEditing.value = false
    }
    if (isDetailView.value) {
      initDetailByRoute()
    }
  }
)
</script>

<style scoped>
.video-page {
  background: #efefef;
  min-height: calc(100vh - 84px);
  padding: 14px 18px;
}

.inspect-head {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 10px;
}

.inspect-title {
  font-size: 28px;
  color: #303133;
}

.inspect-control {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
  font-size: 14px;
}

.head-select {
  width: 260px;
}

.inspect-layout {
  display: grid;
  grid-template-columns: 1fr 390px;
  gap: 16px;
}

.inspect-video-area {
  min-width: 0;
}

.inspect-panel {
  padding-top: 4px;
}

.inspect-item {
  margin-bottom: 20px;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: #303133;
}

.item-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-tag {
  width: 26px;
  height: 16px;
  display: inline-block;
}

.item-score-row {
  margin-top: 3px;
}

.score-radio-group :deep(.el-radio) {
  margin-right: 12px;
  color: #303133;
}

.item-desc {
  margin-top: 2px;
  font-size: 14px;
  color: #303133;
}

.item-media-row {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.shot-thumb {
  width: 76px;
  height: 58px;
  border: 4px solid #bfbfbf;
}

.shot-btn {
  height: 58px;
  width: 120px;
  font-size: 14px;
}

.inspect-submit-wrap {
  margin-top: 50px;
  display: flex;
  justify-content: flex-end;
}

.inspect-submit-btn {
  width: 100%;
  height: 42px;
  background: #4a8ded;
  border-color: #4a8ded;
  font-size: 14px;
}

.record-view {
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  background: #fff;
  min-height: calc(100vh - 84px);
  padding: 20px;
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
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
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

.checklist-view {
  background: #fff;
  min-height: calc(100vh - 84px);
  padding: 0;
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.checklist-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  padding: 18px 10px;
  background: #fff;
  border-bottom: 1px solid #e5e7ef;
}

.checklist-list {
  padding: 20px 10px;
}

.template-row {
  background: #fff;
  border-left: 4px solid #4a8ded;
  display: grid;
  grid-template-columns: 1fr 260px 420px;
  align-items: center;
  min-height: 101px;
  margin-bottom: 20px;
  padding: 0 22px;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.template-desc {
  margin-top: 10px;
  font-size: 16px;
  color: #9aa3b2;
}

.template-enable-col {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  font-size: 14px;
  color: #303133;
}

.template-btns {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

.ghost-btn,
.edit-btn {
  height: 32px;
}

.ghost-btn {
  width: 100px;
  border-color: #4a8ded;
  color: #4a8ded;
  background: #fff;
}

.edit-btn {
  width: 80px;
  font-size: 12px;
  background: #4a8ded;
  border-color: #4a8ded;
}

.checklist-create-wrap {
  padding: 0 16px 18px;
}

.checklist-create-wrap :deep(.el-button) {
  height: 36px;
  min-width: 132px;
  background: #4a8ded;
  border-color: #4a8ded;
}

.checklist-edit-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  padding: 18px 10px;
  background: #fff;
  border-bottom: 1px solid #e5e7ef;
}

.checklist-edit-grid {
  display: grid;
  grid-template-columns: 100px 300px 100px 300px;
  border-top: 1px solid #e6e9ef;
  border-left: 1px solid #e6e9ef;
  margin: 10px 10px 0;
  background: #fff;
}

.eg-label,
.eg-cell {
  min-height: 52px;
  display: flex;
  align-items: center;
  border-right: 1px solid #e6e9ef;
  border-bottom: 1px solid #e6e9ef;
  padding: 6px 10px;
  background: #fff;
}

.eg-label {
  color: #303133;
  font-size: 14px;
}

.eg-cell {
  background: #fff;
}

.span-3 {
  grid-column: span 3;
}

.add-tools :deep(.el-button) {
  font-size: 16px;
}

.check-item-table {
  margin: 0 10px;
  border-left: 1px solid #e6e9ef;
  border-right: 1px solid #e6e9ef;
  border-bottom: 1px solid #e6e9ef;
  background: #fff;
}

.major-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  border-bottom: 1px solid #e6e9ef;
}

.major-name {
  padding: 14px 10px;
  border-right: 1px solid #e6e9ef;
  background: #fff;
  font-size: 14px;
  color: #303133;
}

.minor-list {
  background: #fff;
}

.minor-row {
  min-height: 38px;
  display: grid;
  grid-template-columns: minmax(260px, 1fr) 180px 170px 110px 110px 220px 120px;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid #eceff5;
}

.minor-row:last-child {
  border-bottom: none;
}

.minor-title,
.minor-type,
.minor-score,
.minor-rectify {
  font-size: 14px;
  color: #303133;
}

.minor-type,
.minor-score,
.minor-rectify {
  display: flex;
  align-items: center;
  gap: 6px;
}

.minor-btn {
  width: 102px;
  height: 30px;
  background: #4a8ded;
  border-color: #4a8ded;
  font-size: 12px;
}

.checklist-edit-actions {
  display: flex;
  justify-content: flex-end;
  padding: 20px 16px;
}

.checklist-edit-actions :deep(.el-button) {
  width: 110px;
  height: 42px;
  background: #4a8ded;
  border-color: #4a8ded;
}

.detail-view {
  background: #efefef;
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

.detail-left-col {
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

.detail-main-col {
  border: 1px solid #6f7787;
  background: #aeb9d8;
}

.main-head-row {
  display: grid;
  grid-template-columns: 53% 33% 14%;
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

.main-head-item:last-child {
  border-right: none;
}

.action-head {
  background: transparent;
}

.issue-row {
  display: grid;
  grid-template-columns: 53% 33% 14%;
  min-height: 120px;
  border-bottom: 1px solid #dbe3f5;
}

.issue-cell {
  padding: 8px;
  border-right: 1px solid #dbe3f5;
}

.issue-cell:last-child {
  border-right: none;
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

.detail-thumb {
  width: 78px;
  height: 58px;
  border: 3px solid #d7dce5;
}

.issue-action {
  padding: 8px;
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

.page-title {
  font-size: 20px;
  color: #303133;
  margin-bottom: 12px;
}

.layout-wrap {
  display: flex;
  gap: 16px;
}

.left-panes {
  width: 300px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.tree-pane {
  background: #5a91eb;
  color: #fff;
  min-height: 520px;
  padding: 8px 6px;
}

.second-pane {
  background: #6e9de6;
}

.tree-pane :deep(.el-tree) {
  background: transparent;
  color: #fff;
}

.tree-pane :deep(.el-tree-node__content) {
  height: 26px;
  color: #fff;
}

.tree-pane :deep(.el-tree-node__content:hover),
.tree-pane :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: rgba(255, 255, 255, 0.15);
}

.tree-pane :deep(.el-tree-node__expand-icon) {
  color: #fff;
}

.right-grid-area {
  flex: 1;
}

.grid-frame {
  background: #bfbfbf;
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 12px;
}

.video-card {
  background: #fff;
  border: 4px solid #d6d6d6;
  aspect-ratio: 16 / 9;
  position: relative;
  overflow: hidden;
}

.video-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-name {
  position: absolute;
  left: 8px;
  bottom: 6px;
  font-size: 12px;
  color: #fff;
  background: rgba(0, 0, 0, 0.35);
  padding: 2px 6px;
  border-radius: 3px;
}

.toolbar {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
}

.toolbar :deep(.el-button) {
  font-size: 24px;
  color: #4a8ded;
}

@media (max-width: 1200px) {
  .inspect-layout {
    grid-template-columns: 1fr;
  }

  .layout-wrap {
    flex-direction: column;
  }

  .left-panes {
    width: 100%;
  }

  .grid-frame {
    grid-template-columns: repeat(2, minmax(220px, 1fr));
  }
}

@media (max-width: 768px) {
  .inspect-head {
    flex-wrap: wrap;
    gap: 10px;
  }

  .head-select {
    width: 200px;
  }

  .grid-frame {
    grid-template-columns: 1fr;
  }

  .template-row {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 16px;
  }

  .template-name {
    font-size: 22px;
  }

  .template-desc {
    margin-top: 8px;
    font-size: 18px;
  }

  .template-enable-col {
    font-size: 16px;
  }

  .template-btns {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .checklist-edit-grid {
    grid-template-columns: 120px 1fr;
  }

  .span-3 {
    grid-column: span 1;
  }

  .major-row {
    grid-template-columns: 1fr;
  }

  .major-name {
    border-right: none;
    border-bottom: 1px solid #e6e9ef;
  }

  .minor-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
</style>
