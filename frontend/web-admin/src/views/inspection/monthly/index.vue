<template>
  <div class="monthly-page">
    <header v-if="isRecordsView" class="page-header">
      <div class="page-title">{{ pageTitle }}</div>
    </header>

    <section v-if="isRecordsView" class="records-view">
      <div class="record-search-row">
        <el-select v-model="recordQuery.type" class="record-search-type">
          <el-option label="全查询" value="all" />
          <el-option label="按流水号(#)查询" value="serialNo" />
          <el-option label="按报告名称查询" value="reportName" />
          <el-option label="按提报人查询" value="owner" />
        </el-select>
        <el-input
          v-model="recordQuery.keyword"
          :placeholder="recordQuery.type === 'all' ? '显示全部记录，无需输入' : recordQuery.type === 'serialNo' ? '请输入流水号（如：18）' : recordQuery.type === 'reportName' ? '请输入报告名称关键词' : '请输入提报人姓名'"
          :disabled="recordQuery.type === 'all'"
          clearable
          class="record-search-input"
          @keyup.enter="handleRecordSearch"
        />
        <el-button type="primary" class="exact-btn" @click="handleRecordSearch">查询</el-button>
      </div>

      <div class="table-wrap">
        <el-table :data="recordFilteredRows" style="width: 100%" :header-cell-style="{ background: '#f5f5f5', color: '#303133', fontWeight: 'bold' }">
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column prop="id" label="#" min-width="70" align="center" />
          <el-table-column prop="reportName" label="报告名称" min-width="220" show-overflow-tooltip />
          <el-table-column prop="owner" label="提报人" min-width="100" align="center" />
          <el-table-column label="系统报告" min-width="120" align="center">
            <template #default="scope">
              <el-button link type="primary" @click="handleViewSystemReport(scope.row)">查看</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="reportTime" label="报告时间" min-width="170" align="center" />
          <el-table-column label="线下报告" min-width="120" align="center">
            <template #default="scope">
              <el-button link type="primary" @click="handleViewOfflineReport(scope.row)">查看</el-button>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="220" align="center">
            <template #default="scope">
              <el-button link type="primary" @click="handleUploadOffline(scope.row)">上传线下报告</el-button>
              <el-button link type="primary" @click="handleDeleteRecord(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <section v-else class="export-view">
      <div class="export-top">
        <div class="export-title">月调度报告生成</div>
        <el-button class="back-btn" @click="goBack">返回</el-button>
      </div>

      <div class="segment-title">报告主要内容</div>
      <div class="segment-body">
        <div class="form-grid-3">
          <div class="field-block span-2">
            <div class="field-label">标题</div>
            <el-input v-model="exportForm.title" />
          </div>
          <div class="field-block">
            <div class="field-label">报告人</div>
            <el-select v-model="exportForm.reporter" class="full-width">
              <el-option v-for="item in reporterOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </div>
          <div class="field-block">
            <div class="field-label">报告时间日期</div>
            <el-date-picker v-model="exportForm.reportDate" type="date" value-format="YYYY-MM-DD" placeholder="yyyy/mm/日" class="full-width" />
          </div>
        </div>
        <div class="field-block mt8">
          <div class="field-label">月调度参会人员</div>
          <el-input v-model="exportForm.attendees" placeholder="请输入参会人员（可逗号分隔）" />
        </div>
      </div>

      <div class="segment-title">月调度报告内容提取</div>
      <div class="segment-body">
        <div class="data-row-title">日管控数据</div>
        <div class="form-grid-3">
          <div class="field-block">
            <div class="field-label">时间范围</div>
            <el-date-picker v-model="exportForm.dailyDate" type="daterange" value-format="YYYY-MM-DD" range-separator="-" start-placeholder="开始日期" end-placeholder="结束日期" class="full-width" />
          </div>
          <div class="field-block">
            <div class="field-label">检查表</div>
            <el-select v-model="exportForm.dailyChecklistId" class="full-width">
              <el-option v-for="item in checklistOptions" :key="`daily-${item.id}`" :label="item.name" :value="item.id" />
            </el-select>
          </div>
          <div class="field-block">
            <div class="field-label">包含食堂</div>
            <el-select v-model="exportForm.dailyCanteenId" class="full-width">
              <el-option v-for="item in canteenOptions" :key="`daily-canteen-${item.id}`" :label="item.name" :value="item.id" />
            </el-select>
          </div>
        </div>

        <div class="data-row-title mt8">周排查数据</div>
        <div class="form-grid-3">
          <div class="field-block">
            <div class="field-label">时间范围</div>
            <el-date-picker v-model="exportForm.weeklyDate" type="daterange" value-format="YYYY-MM-DD" range-separator="-" start-placeholder="开始日期" end-placeholder="结束日期" class="full-width" />
          </div>
          <div class="field-block">
            <div class="field-label">检查表</div>
            <el-select v-model="exportForm.weeklyChecklistId" class="full-width">
              <el-option v-for="item in weeklyChecklistOptions" :key="`weekly-${item.id}`" :label="item.name" :value="item.id" />
            </el-select>
          </div>
          <div class="field-block">
            <div class="field-label">包含食堂</div>
            <el-select v-model="exportForm.weeklyCanteenId" class="full-width">
              <el-option v-for="item in canteenOptions" :key="`weekly-canteen-${item.id}`" :label="item.name" :value="item.id" />
            </el-select>
          </div>
        </div>
      </div>

      <div class="segment-title">报告预览</div>
      <div class="segment-body preview-wrap">
        <h3>一、总体概述</h3>
        <p>
          本月，学校、食堂与一食堂整体运行平稳，食品安全和卫生管理基本符合《学校食品安全与营养健康管理规定》及本校食堂管理制度要求。
          两个食堂均严格执行“日管控、周排查、月调度”工作机制，未发生食品安全事故。通过日常巡查与专项检查相结合，及时发现并整改部分操作不规范、设备老化等问题，保障了师生饮食安全。
        </p>

        <h3>二、一食堂日管控执行情况</h3>
        <ul>
          <li>执行率：全月31天，日管控记录完整，执行率达100%。</li>
          <li>主要管控内容：晨检记录、食材留样、环境消杀、设备巡检与台账回填。</li>
          <li>问题闭环：发现问题后当日整改率为96.8%，超期问题均已复核通过。</li>
        </ul>

        <h3>三、二食堂日管控执行情况</h3>
        <ul>
          <li>执行率：全月31天，日管控记录完整，执行率达100%。</li>
          <li>主要管控内容：员工晨检与着装规范、食材存储温控、加工过程留样、餐具消毒记录。</li>
          <li>问题闭环：个别台账填写不及时问题已完成补录并复核通过。</li>
        </ul>

        <div class="preview-actions">
          <el-button type="primary" class="download-btn" @click="handleExport">保存并下载</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { deleteMonthlyReport, exportMonthlyReport, getAllDepts, getDailyTemplateList, getWeeklyTemplateList, listMonthlyReports, uploadOfflineMonthlyReport } from '@/api/canteen'

interface MonthlyRecordRow {
  id: number
  serialNo: string
  docNo: string
  reportName: string
  owner: string
  reportTime: string
  canteenId: number
  fileUrl?: string
  sourceType?: 'system' | 'offline'
}

interface CanteenOption {
  id: number
  name: string
}

interface TemplateOption {
  id: number
  name: string
}

const route = useRoute()
const router = useRouter()
const isRecordsView = computed(() => route.name === 'MonthlyReportRecords')
const pageTitle = computed(() => (isRecordsView.value ? '月调度报告记录' : '月调度报告导出'))

const canteens = ref<CanteenOption[]>([])
const dailyTemplateOptions = ref<TemplateOption[]>([])
const weeklyTemplateListRef = ref<TemplateOption[]>([])
const templateOptions = ref<TemplateOption[]>([])

const canteenOptions = computed(() => canteens.value)
const reporterOptions = ['食安总监', '食品安全员', '后勤主任']
const checklistOptions = computed(() => dailyTemplateOptions.value.length ? dailyTemplateOptions.value : templateOptions.value)
const weeklyChecklistOptions = computed(() => weeklyTemplateListRef.value.length ? weeklyTemplateListRef.value : templateOptions.value)

const allRecords = ref<MonthlyRecordRow[]>([])

const recordQuery = reactive({
  keyword: '',
  type: 'all' as 'all' | 'serialNo' | 'reportName' | 'owner'
})

// 已提交的搜索条件，点击查询后才生效
const submittedQuery = reactive({
  keyword: '',
  type: 'all' as 'all' | 'serialNo' | 'reportName' | 'owner'
})

const recordFilteredRows = computed(() => {
  if (submittedQuery.type === 'all') return allRecords.value
  const keyword = submittedQuery.keyword.trim()
  if (!keyword) return allRecords.value
  const kLower = keyword.toLowerCase()
  if (submittedQuery.type === 'serialNo') {
    // 流水号：匹配 # 列（id），支持模糊包含
    return allRecords.value.filter((item) => String(item.id).includes(keyword.trim()))
  } else if (submittedQuery.type === 'reportName') {
    // 报告名称：模糊匹配
    return allRecords.value.filter((item) => item.reportName.toLowerCase().includes(kLower))
  } else {
    // 提报人：模糊匹配
    return allRecords.value.filter((item) => item.owner.toLowerCase().includes(kLower))
  }
})

const exportForm = reactive({
  title: '2026年1月武岗一中月调度报告',
  reporter: '食安总监',
  reportDate: '',
  attendees: '',
  dailyDate: [] as string[],
  dailyChecklistId: 0,
  dailyCanteenId: 0,
  weeklyDate: [] as string[],
  weeklyChecklistId: 0,
  weeklyCanteenId: 0
})

const fallbackRecords = (): MonthlyRecordRow[] => [
  { id: 20, serialNo: 'LS-2026-01-20', docNo: 'WG-01', reportName: '2026年1月武岗一中月调度报告', owner: '食安总监', reportTime: '2020-08-20 14:20:02', canteenId: 0 },
  { id: 19, serialNo: 'LS-2026-02-19', docNo: 'WG-02', reportName: '2026年2月武岗一中月调度报告', owner: '食安总监', reportTime: '2020-08-20 14:20:02', canteenId: 0 },
  { id: 18, serialNo: 'LS-2026-03-18', docNo: 'WG-03', reportName: '2026年3月武岗一中月调度报告', owner: '食安总监', reportTime: '2020-08-20 14:20:02', canteenId: 0 }
]

const resolveCanteenName = (id: number) => canteens.value.find((item) => item.id === id)?.name || `食堂${id || '-'}`

const formatMonthLabel = (dateText: string, index: number) => {
  if (!dateText) return `${index + 1}月`
  const month = String(dateText).slice(5, 7)
  return `${Number(month)}月`
}

const loadCanteens = async () => {
  try {
    const res: any = await getAllDepts()
    const rows = res?.data?.records || []
    canteens.value = rows
      .filter((item: any) => item.org_type === 'CANTEEN')
      .map((item: any) => ({ id: item.id, name: item.name }))

    if (!exportForm.dailyCanteenId && canteens.value.length) {
      exportForm.dailyCanteenId = canteens.value[0].id
      exportForm.weeklyCanteenId = canteens.value[0].id
    }
  } catch {
    canteens.value = []
  }
}

const FALLBACK_DAILY_TEMPLATES: TemplateOption[] = [
  { id: 1, name: '日管控检查表（默认）' }
]
const FALLBACK_WEEKLY_TEMPLATES: TemplateOption[] = [
  { id: 1, name: '周排查检查表（默认）' }
]

const loadTemplateOptions = async () => {
  try {
    const [dailyRes, weeklyRes]: [any, any] = await Promise.all([
      getDailyTemplateList({ page: 1, page_size: 100 }),
      getWeeklyTemplateList({ page: 1, page_size: 100 })
    ])
    const dailyList = (dailyRes?.data?.list || []).map((item: any) => ({
      id: Number(item.id),
      name: String(item.template_name || item.name || `日管控模板${item.id}`)
    }))
    const weeklyList = (weeklyRes?.data?.list || []).map((item: any) => ({
      id: Number(item.id),
      name: String(item.template_name || item.name || `周排查模板${item.id}`)
    }))
    dailyTemplateOptions.value = dailyList.length ? dailyList : FALLBACK_DAILY_TEMPLATES
    weeklyTemplateListRef.value = weeklyList.length ? weeklyList : FALLBACK_WEEKLY_TEMPLATES
    if (!exportForm.dailyChecklistId) exportForm.dailyChecklistId = dailyTemplateOptions.value[0].id
    if (!exportForm.weeklyChecklistId) exportForm.weeklyChecklistId = weeklyTemplateListRef.value[0].id
  } catch {
    dailyTemplateOptions.value = FALLBACK_DAILY_TEMPLATES
    weeklyTemplateListRef.value = FALLBACK_WEEKLY_TEMPLATES
    if (!exportForm.dailyChecklistId) exportForm.dailyChecklistId = FALLBACK_DAILY_TEMPLATES[0].id
    if (!exportForm.weeklyChecklistId) exportForm.weeklyChecklistId = FALLBACK_WEEKLY_TEMPLATES[0].id
  }
}

const loadRecordRows = async () => {
  try {
    const res: any = await listMonthlyReports({ page: 1, page_size: 100 })
    const records = res?.data?.records || []
    if (records.length) {
      allRecords.value = records.map((item: any, index: number) => ({
        id: item.id,
        serialNo: item.serial_no || `LS-${item.id}`,
        docNo: item.doc_no || `WG-${String(index + 1).padStart(2, '0')}`,
        reportName: item.title || item.report_name || `月调度报告#${item.id}`,
        owner: item.reporter_name || item.reporter_name_snapshot || item.owner || '食安总监',
        reportTime: (item.report_time || item.created_at) ? String(item.report_time || item.created_at).replace('T', ' ').slice(0, 19) : '',
        canteenId: item.canteen_id || 0,
        fileUrl: item.offline_report_url || undefined,
        sourceType: item.source_type || (item.offline_report_url ? 'offline' : 'system')
      }))
    } else {
      allRecords.value = fallbackRecords()
    }
  } catch {
    allRecords.value = fallbackRecords()
  }
}

const handleRecordSearch = () => {
  if (recordQuery.type !== 'all' && !recordQuery.keyword.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }
  submittedQuery.keyword = recordQuery.keyword
  submittedQuery.type = recordQuery.type
}

const handleViewSystemReport = (row: MonthlyRecordRow) => {
  // 导航到报告导出页，携带报告ID以便查看/重新导出
  router.push({ name: 'MonthlyReportExport', query: { reportId: String(row.id) } })
}

const handleViewOfflineReport = (row: MonthlyRecordRow) => {
  if (row.fileUrl) {
    window.open(row.fileUrl, '_blank')
  } else {
    ElMessage.info('该记录暂无线下报告文件，请先上传')
  }
}

const handleUploadOffline = async (row: MonthlyRecordRow) => {
  if (!row.canteenId) {
    ElMessage.warning('该记录无关联食堂，无法上传')
    return
  }
  try {
    await ElMessageBox.confirm(`确定上传「${row.reportName}」的线下报告？`, '上传确认', {
      confirmButtonText: '确定上传',
      cancelButtonText: '取消',
      type: 'info'
    })
    await uploadOfflineMonthlyReport({
      title: row.reportName,
      canteen_id: row.canteenId
    })
    ElMessage.success('线下报告上传成功')
    await loadRecordRows()
  } catch {
    // 取消或失败
  }
}

const handleDeleteRecord = async (row: MonthlyRecordRow) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除报告「${row.reportName}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await deleteMonthlyReport(row.id)
    ElMessage.success('报告已删除')
    await loadRecordRows()
  } catch {
    ElMessage.error('删除失败，请稍后重试')
  }
}

const downloadBlobFile = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

const handleExport = async () => {
  const startDate = Array.isArray(exportForm.dailyDate) ? exportForm.dailyDate[0] : exportForm.dailyDate
  const endDate = Array.isArray(exportForm.dailyDate) ? exportForm.dailyDate[1] : ''
  // 优先用周排查日期范围
  const weeklyStart = Array.isArray(exportForm.weeklyDate) ? exportForm.weeklyDate[0] : ''
  const weeklyEnd = Array.isArray(exportForm.weeklyDate) ? exportForm.weeklyDate[1] : ''
  const finalStart = weeklyStart || startDate || exportForm.reportDate || new Date().toISOString().slice(0, 10)
  const finalEnd = weeklyEnd || endDate || finalStart

  // data_sources: 所选模板 ID 列表
  const sources = [
    exportForm.dailyChecklistId,
    exportForm.weeklyChecklistId
  ].filter(Boolean) as number[]

  if (!sources.length) {
    ElMessage.warning('请先选择检查表')
    return
  }

  try {
    const response: any = await exportMonthlyReport({
      start_date: finalStart,
      end_date: finalEnd,
      data_sources: sources,
      export_format: 'docx'
    })
    const blob: Blob = response?.data instanceof Blob ? response.data : new Blob([response?.data ?? ''])
    const filename = `${exportForm.title || '月调度报告'}.docx`
    downloadBlobFile(blob, filename)
    ElMessage.success('报告导出成功')
  } catch {
    ElMessage.error('报告导出失败，请稍后重试')
  }
}

const goBack = () => {
  router.back()
}

const initPageData = async () => {
  await loadCanteens()
  if (isRecordsView.value) {
    await loadRecordRows()
  } else {
    await loadTemplateOptions()
  }
}

onMounted(async () => {
  await initPageData()
})

watch(
  () => route.name,
  async () => {
    if (isRecordsView.value && !allRecords.value.length) {
      await loadRecordRows()
    }
  }
)
</script>

<style scoped>
.monthly-page {
  background: #fff;
  min-height: calc(100vh - 84px);
  padding: 12px;
}

.page-header {
  margin-bottom: 10px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.records-view,
.export-view {
  border: 1px solid #ebeef5;
  background: #fff;
  padding: 12px;
}

.export-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.export-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.back-btn {
  min-width: 84px;
}

.segment-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  background: #e8eef7;
  border-top: 1px dashed #7db0f6;
  padding: 10px 12px;
  margin-top: 10px;
}

.segment-body {
  padding: 10px 8px 12px;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 12px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.span-2 {
  grid-column: span 2;
}

.field-label {
  font-size: 14px;
  color: #303133;
}

.full-width {
  width: 100%;
}

.data-row-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.mt8 {
  margin-top: 8px;
}

.preview-wrap h3 {
  font-size: 24px;
  line-height: 1.5;
  color: #0f172a;
  margin: 10px 0;
}

.preview-wrap p,
.preview-wrap li {
  font-size: 14px;
  line-height: 1.9;
  color: #0f172a;
}

.preview-wrap ul {
  margin: 6px 0 0;
  padding-left: 22px;
}

.preview-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.download-btn {
  min-width: 160px;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.toolbar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-search-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.record-search-type {
  width: 160px;
  flex-shrink: 0;
}

.record-search-input {
  width: 280px;
}

.exact-btn {
  min-width: 86px;
}

.search-item {
  margin-left: auto;
}

.label {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
}

.field {
  width: 150px;
}

.field-small {
  width: 120px;
}

.field-wide {
  width: 260px;
}

.table-wrap {
  border: 1px solid #ebeef5;
}

.footer-row {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-success {
  color: #67c23a;
  font-weight: 600;
}

.status-pending {
  color: #e6a23c;
  font-weight: 600;
}

.export-card,
.history-card {
  border: 1px solid #ebeef5;
  background: #fff;
  padding: 12px;
}

.history-card {
  margin-top: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 10px 12px;
}

.card-actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}

@media (max-width: 1200px) {
  .search-item {
    margin-left: 0;
  }

  .form-grid-3 {
    grid-template-columns: repeat(2, minmax(220px, 1fr));
  }

  .span-2 {
    grid-column: span 2;
  }

  .preview-wrap h3 {
    font-size: 20px;
  }

  .preview-wrap p,
  .preview-wrap li {
    font-size: 14px;
  }

  .module-grid {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }
}

@media (max-width: 768px) {
  .field,
  .field-small,
  .field-wide {
    width: 100%;
  }

  .record-search-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .record-search-input {
    width: 100%;
  }

  .toolbar-item {
    width: 100%;
  }

  .form-grid-3 {
    grid-template-columns: 1fr;
  }

  .span-2 {
    grid-column: auto;
  }

  .preview-wrap h3 {
    font-size: 18px;
  }

  .preview-wrap p,
  .preview-wrap li {
    font-size: 13px;
  }

  .module-grid {
    grid-template-columns: 1fr;
  }

  .footer-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
