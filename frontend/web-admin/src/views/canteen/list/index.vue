<template>
  <div class="ledger-page" v-loading="loading">
    <template v-if="isTemplateView">
      <div class="template-view">
        <div class="template-title">电子台账模板</div>
        <div class="template-list">
          <div v-for="item in templateCards" :key="item.id" class="template-row">
            <div class="template-name-col">
              <div class="template-name">{{ item.name }}</div>
              <div class="template-desc">{{ item.description }}</div>
            </div>
            <div class="template-enable-col">
              <span>是否启用</span>
              <el-switch v-model="item.enabled" />
            </div>
            <div class="template-btns">
              <el-button class="outline-btn" @click="handleCoverUsers(item)">覆盖人员</el-button>
              <el-button class="outline-btn" @click="handleCoverCanteens(item)">覆盖食堂</el-button>
              <el-button type="primary" class="edit-btn" @click="handleEditTemplate(item)">编辑</el-button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="record-view">
        <div class="ledger-toolbar">
          <div class="ledger-title">电子台账记录</div>
          <div class="toolbar-items">
            <div class="toolbar-item">
              <span class="label">起止日期</span>
              <el-date-picker
                v-model="query.dateRange"
                type="daterange"
                range-separator="-"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                class="date-picker"
              />
            </div>

            <div class="toolbar-item">
              <span class="label">食堂</span>
              <el-select v-model="query.canteenId" class="small-select" placeholder="全部食堂">
                <el-option label="全部" value="" />
                <el-option v-for="item in canteenOptions" :key="`ledger-canteen-${item.id}`" :label="item.name" :value="String(item.id)" />
              </el-select>
            </div>

            <div class="toolbar-item">
              <span class="label">台账</span>
              <el-select v-model="query.ledgerType" class="small-select" placeholder="全部台账">
                <el-option label="全部台账" value="" />
                <el-option v-for="item in ledgerTypeOptions" :key="`ledger-type-${item}`" :label="item" :value="item" />
              </el-select>
            </div>

            <div class="toolbar-item search-item">
              <span class="label">搜索</span>
              <el-input v-model="query.keyword" clearable class="search-input" />
            </div>
          </div>
        </div>

        <div class="ledger-table-wrap">
          <el-table
            :data="pagedRows"
            style="width: 100%"
            :header-cell-style="{ background: '#f5f5f5', color: '#303133', fontWeight: '600' }"
            :cell-style="{ padding: '10px 0' }"
          >
            <el-table-column prop="submitCanteen" label="提交食堂" min-width="220" show-overflow-tooltip />
            <el-table-column prop="submitter" label="提交人" min-width="90" />
            <el-table-column prop="ledgerName" label="提交电子台账" min-width="210" show-overflow-tooltip />
            <el-table-column prop="isSigned" label="是否签名" min-width="90" align="center" />
            <el-table-column prop="submitDate" label="提交日期" min-width="120" align="center" />
            <el-table-column prop="status" label="状态" min-width="100" align="center" />
            <el-table-column label="操作" min-width="130" align="center">
              <template #default="scope">
                <el-button link type="primary" @click="handlePrimary(scope.row)">{{ scope.row.primaryAction }}</el-button>
                <el-button link type="primary" @click="handleSecondary(scope.row)">{{ scope.row.secondaryAction }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <footer class="ledger-footer">
          <el-pagination
            v-model:current-page="page"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 30, 50]"
            layout="prev, pager, next"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </footer>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { getAllDepts, getLedgerInstanceList, getLedgerTemplateList, type AdminDeptRecord } from '@/api/canteen'

interface CanteenOption {
  id: number
  name: string
}

type LedgerStatus = '进行中' | '完整月'

interface LedgerRow {
  id: number
  canteenId: number
  submitCanteen: string
  submitter: string
  ledgerName: string
  isSigned: '是' | '否'
  submitDate: string
  status: LedgerStatus
  primaryAction: '查看' | '编辑'
  secondaryAction: '下载' | '取消'
}

interface LedgerTemplateCard {
  id: number
  name: string
  description: string
  enabled: boolean
}

const route = useRoute()
const router = useRouter()
const isMyRoute = computed(() =>
  route.name === 'LedgerRecords' || route.name === 'CanteenDevice' || route.name === 'LedgerTemplates'
)
const isTemplateView = computed(() => route.name === 'LedgerTemplates')

const loading = ref(false)
const rows = ref<LedgerRow[]>([])
const canteenOptions = ref<CanteenOption[]>([])
const templateCards = ref<LedgerTemplateCard[]>([])

const ledgerTypePool = ['留样台账记录', '紫外线消毒记录', '晨检台账记录']
const submitterPool = ['张三', '李四', '王五']

const query = reactive({
  dateRange: ['2026-01-12', '2026-02-23'] as string[],
  canteenId: '',
  ledgerType: '留样台账记录',
  keyword: ''
})

const page = ref(2)
const pageSize = ref(10)

const ledgerTypeOptions = computed(() => {
  const set = new Set<string>(ledgerTypePool)
  rows.value.forEach((item) => set.add(item.ledgerName))
  return Array.from(set)
})

const inRange = (date: string, start: string, end: string) => {
  if (!start || !end) return true
  return date >= start && date <= end
}

const filteredRows = computed(() => {
  const [startDate, endDate] = query.dateRange || []
  const keyword = query.keyword.trim().toLowerCase()

  return rows.value.filter((item) => {
    const matchCanteen = !query.canteenId || String(item.canteenId) === query.canteenId
    const matchLedger = !query.ledgerType || item.ledgerName === query.ledgerType
    const matchDate = !startDate || !endDate || inRange(item.submitDate, startDate, endDate)
    const matchKeyword =
      !keyword ||
      `${item.submitCanteen} ${item.submitter} ${item.ledgerName} ${item.submitDate}`.toLowerCase().includes(keyword)

    return matchCanteen && matchLedger && matchDate && matchKeyword
  })
})

const total = computed(() => filteredRows.value.length)

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const fallbackRows = (): LedgerRow[] => [
  { id: 1, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', isSigned: '是', submitDate: '2020-05-24', status: '进行中', primaryAction: '查看', secondaryAction: '下载' },
  { id: 2, canteenId: 201, submitCanteen: '武岗实验中学一食堂', submitter: '李四', ledgerName: '留样台账记录', isSigned: '是', submitDate: '2020-05-24', status: '进行中', primaryAction: '查看', secondaryAction: '下载' },
  { id: 3, canteenId: 301, submitCanteen: '城东机关幼儿园食堂', submitter: '王五', ledgerName: '紫外线消毒记录', isSigned: '是', submitDate: '2020-05-24', status: '进行中', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 4, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', isSigned: '是', submitDate: '2020-05-24', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 5, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', isSigned: '是', submitDate: '2020-05-24', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 6, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', isSigned: '是', submitDate: '2020-04-15', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 7, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', isSigned: '是', submitDate: '2020-04-24', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 8, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', isSigned: '是', submitDate: '2020-04-24', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 9, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', isSigned: '是', submitDate: '2020-04-24', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' },
  { id: 10, canteenId: 101, submitCanteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', isSigned: '是', submitDate: '2020-04-24', status: '完整月', primaryAction: '编辑', secondaryAction: '取消' }
]

const fallbackTemplates = (): LedgerTemplateCard[] => [
  { id: 1, name: '留样记录表', description: '外出申请(2020-10-07 00:30:49)', enabled: true },
  { id: 2, name: '消杀记录表', description: '出差申请(2020-10-07 00:30:49)', enabled: true },
  { id: 3, name: '晨检记录表', description: '请假申请(2020-10-07 00:30:49)', enabled: true }
]

const loadCanteens = async () => {
  try {
    const deptRes: any = await getAllDepts()
    const records = (deptRes?.data?.records || []) as AdminDeptRecord[]
    canteenOptions.value = records
      .filter((item) => item.org_type === 'CANTEEN')
      .map((item) => ({ id: Number(item.id), name: item.name }))
  } catch {
    canteenOptions.value = [
      { id: 101, name: '武岗一中一食堂' },
      { id: 201, name: '武岗实验中学一食堂' },
      { id: 301, name: '城东机关幼儿园食堂' }
    ]
  }
}

const mapStatusToLedgerStatus = (status?: string): LedgerStatus => {
  const raw = String(status || '').toLowerCase()
  if (raw === 'archived') return '完整月'
  return '进行中'
}

const loadRows = async () => {
  loading.value = true
  try {
    const res: any = await getLedgerInstanceList({ page: 1, size: 200 })
    const records = res?.data?.records || []

    rows.value = records.map((item: any, index: number) => {
      const canteenId = Number(item.canteen_id || 0)
      const status = mapStatusToLedgerStatus(item.status)
      return {
        id: Number(item.id),
        canteenId,
        submitCanteen: canteenOptions.value.find((c) => c.id === canteenId)?.name || `食堂${canteenId || 1}`,
        submitter: submitterPool[index % submitterPool.length],
        ledgerName: ledgerTypePool[index % ledgerTypePool.length],
        isSigned: '是',
        submitDate: String(item.created_at || '').slice(0, 10) || '2020-05-24',
        status,
        primaryAction: index < 2 ? '查看' : '编辑',
        secondaryAction: index < 2 ? '下载' : '取消'
      } as LedgerRow
    })

    if (!rows.value.length) {
      rows.value = fallbackRows()
    }
  } catch {
    rows.value = fallbackRows()
    ElMessage.warning('电子台账记录接口暂不可用，当前展示示例数据')
  } finally {
    loading.value = false
  }
}

const loadTemplateCards = async () => {
  loading.value = true
  try {
    const res: any = await getLedgerTemplateList({ page: 1, size: 100 })
    const records = res?.data?.records || []
    templateCards.value = records.map((item: any, index: number) => ({
      id: Number(item.id),
      name: String(item.name || `台账模板${index + 1}`),
      description: String(item.description || fallbackTemplates()[index % 3].description),
      enabled: Number(item.is_active || 0) === 1
    }))

    if (!templateCards.value.length) {
      templateCards.value = fallbackTemplates()
    }
  } catch {
    templateCards.value = fallbackTemplates()
    ElMessage.warning('电子台账模板接口暂不可用，当前展示示例数据')
  } finally {
    loading.value = false
  }
}

const loadByRoute = async () => {
  if (isTemplateView.value) {
    await loadTemplateCards()
    return
  }
  await loadRows()
}

const handlePrimary = (row: LedgerRow) => {
  ElMessage.info(`${row.primaryAction}记录 #${row.id}`)
}

const handleSecondary = (row: LedgerRow) => {
  if (row.secondaryAction === '下载') {
    ElMessage.success(`开始下载台账 #${row.id}`)
    return
  }
  ElMessage.info(`取消记录 #${row.id}`)
}

const handleCoverUsers = (item: LedgerTemplateCard) => {
  ElMessage.info(`模板 ${item.name} 覆盖人员功能开发中`)
}

const handleCoverCanteens = (item: LedgerTemplateCard) => {
  ElMessage.info(`模板 ${item.name} 覆盖食堂功能开发中`)
}

const handleEditTemplate = (item: LedgerTemplateCard) => {
  router.push({
    name: 'LedgerDesigner',
    query: {
      templateId: String(item.id),
      name: item.name
    }
  })
}

const handlePageChange = (value: number) => {
  page.value = value
}

const handleSizeChange = (value: number) => {
  pageSize.value = value
  page.value = 1
}

onMounted(async () => {
  await loadCanteens()
  await loadByRoute()
})

watch(
  () => route.name,
  async () => {
    if (!isMyRoute.value) return
    await loadByRoute()
  }
)
</script>

<style scoped>
.ledger-page {
  min-height: calc(100vh - 84px);
  background: #fff;
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #303133;
}

.record-view {
  padding: 20px;
}

.ledger-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.ledger-title {
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.toolbar-items {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
}

.toolbar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.date-picker {
  width: 270px;
}

.small-select {
  width: 130px;
}

.search-item {
  margin-left: 8px;
}

.search-input {
  width: 230px;
}

.ledger-table-wrap {
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.ledger-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.template-view {
  background: #eef0f8;
  min-height: calc(100vh - 84px);
  padding: 0;
}

.template-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  padding: 18px 10px;
  background: #f7f7f7;
  border-bottom: 1px solid #e5e7ef;
}

.template-list {
  padding: 20px 10px;
}

.template-row {
  background: #f5f5f5;
  border-left: 4px solid #4a8ded;
  display: grid;
  grid-template-columns: 1fr 260px 420px;
  align-items: center;
  min-height: 101px;
  margin-bottom: 20px;
  padding: 0 0 0 22px;
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
  justify-content: center;
  gap: 22px;
}

.outline-btn {
  width: 100px;
  height: 43px;
  border-color: #4a8ded;
  color: #4a8ded;
  background: #fff;
}

.edit-btn {
  width: 80px;
  height: 30px;
  font-size: 12px;
  background: #4a8ded;
  border-color: #4a8ded;
}

@media (max-width: 900px) {
  .ledger-title {
    font-size: 18px;
  }

  .date-picker {
    width: 250px;
  }

  .search-input {
    width: 180px;
  }

  .template-title {
    font-size: 24px;
  }

  .template-row {
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 14px;
  }

  .template-name {
    font-size: 20px;
  }

  .template-desc {
    font-size: 16px;
    margin-top: 6px;
  }

  .template-enable-col {
    justify-content: flex-start;
    font-size: 14px;
  }

  .template-btns {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .outline-btn,
  .edit-btn {
    font-size: 14px;
  }
}
</style>
