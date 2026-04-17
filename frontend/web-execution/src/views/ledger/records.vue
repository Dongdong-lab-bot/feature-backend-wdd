<template>
  <div class="app-container">
    <div class="header-container">
      <div class="page-title">电子台账记录</div>
      <div class="filter-container">
        <div class="filter-item">
          <span class="filter-label">起止日期</span>
          <el-date-picker
            v-model="startDate"
            type="date"
            placeholder="开始日期"
            style="width: 140px"
            value-format="YYYY-MM-DD"
          />
          <span class="separator">-</span>
          <el-date-picker
            v-model="endDate"
            type="date"
            placeholder="结束日期"
            style="width: 140px"
            value-format="YYYY-MM-DD"
          />
        </div>
        
        <div class="filter-item">
          <span class="filter-label">食堂</span>
          <el-select v-model="selectedCanteen" placeholder="请选择食堂" style="width: 140px">
            <el-option label="武岗一中一食堂" value="武岗一中一食堂" />
            <el-option label="武岗一中二食堂" value="武岗一中二食堂" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">台账</span>
          <el-select v-model="selectedLedger" placeholder="请选择台账" style="width: 140px">
            <el-option label="留样台账" value="留样台账" />
            <el-option label="紫外线消毒记录" value="紫外线消毒记录" />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">搜索</span>
          <el-input
            v-model="searchText"
            placeholder=""
            style="width: 200px"
          />
        </div>
      </div>
    </div>

    <div class="table-container">
      <el-table :data="paginatedData" v-loading="loading" style="width: 100%" :header-cell-style="{ background: '#f5f7fa', color: '#606266' }">
        <el-table-column prop="canteen" label="提交食堂" min-width="160" />
        <el-table-column prop="submitter" label="提交人" min-width="100" />
        <el-table-column prop="ledgerName" label="提交电子台账" min-width="160" />
        <el-table-column prop="signed" label="是否签名" min-width="100">
          <template #default="scope">
            {{ scope.row.signed ? '是' : '否' }}
          </template>
        </el-table-column>
        <el-table-column prop="date" label="提交日期" min-width="120" />
        <el-table-column prop="status" label="状态" min-width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <template v-if="scope.row.status === '进行中' && scope.row.id <= 2">
              <el-button link type="primary" size="small" @click="handleView(scope.row)">查看</el-button>
              <el-button link type="primary" size="small" @click="handleDownload(scope.row)">下载</el-button>
            </template>
            <template v-else>
              <el-button link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="handleCancel(scope.row)">取消</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        background
        prev-text="上一项"
        next-text="下一项"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
import { getLedgerInstances, verifyLedgerInstance } from '@/api/ledger'

// Filters
const startDate = ref('2026.1.12')
const endDate = ref('2026.2.23')
const selectedCanteen = ref('武岗一中一食堂')
const selectedLedger = ref('留样台账')
const searchText = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)

// Mock Data
interface Record {
  id: number
  canteen: string
  submitter: string
  ledgerName: string
  signed: boolean
  date: string
  status: string
}

const tableData = ref<Record[]>([])
const fallbackData: Record[] = [
  { id: 1, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', signed: true, date: '2020-05-24', status: '进行中' },
  { id: 2, canteen: '武岗一中一食堂', submitter: '李四', ledgerName: '留样台账记录', signed: true, date: '2020-05-24', status: '进行中' },
  { id: 3, canteen: '武岗一中一食堂', submitter: '王五', ledgerName: '紫外线消毒记录', signed: true, date: '2020-05-24', status: '进行中' },
  { id: 4, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', signed: true, date: '2020-05-24', status: '完整月' },
  { id: 5, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', signed: true, date: '2020-05-24', status: '完整月' },
  { id: 6, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', signed: true, date: '2020-04-15', status: '完整月' },
  { id: 7, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', signed: true, date: '2020-04-24', status: '完整月' },
  { id: 8, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', signed: true, date: '2020-04-24', status: '完整月' },
  { id: 9, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '留样台账记录', signed: true, date: '2020-04-24', status: '完整月' },
  { id: 10, canteen: '武岗一中一食堂', submitter: '张三', ledgerName: '紫外线消毒记录', signed: true, date: '2020-04-24', status: '完整月' }
]

const apiToStatus: Record<string, string> = {
  PENDING: '进行中',
  FILLING: '进行中',
  SIGNED: '完整月',
  ARCHIVED: '完整月'
}

const statusToSigned: Record<string, boolean> = {
  PENDING: false,
  FILLING: false,
  SIGNED: true,
  ARCHIVED: true
}

const loadLedgerRecords = async () => {
  loading.value = true
  try {
    const result = await getLedgerInstances({ page: 1, size: 200 })
    const records = Array.isArray(result?.records) ? result.records : []
    tableData.value = records.map((item) => ({
      id: item.id,
      canteen: `食堂${item.canteen_id || '-'}`,
      submitter: '系统提交',
      ledgerName: item.id % 2 === 0 ? '留样台账记录' : '紫外线消毒记录',
      signed: statusToSigned[item.status] ?? true,
      date: (item.created_at || '').slice(0, 10) || '-',
      status: apiToStatus[item.status] || '进行中'
    }))
  } catch {
    tableData.value = fallbackData
    ElMessage.warning('电子台账记录接口不可用，已展示示例数据')
  } finally {
    loading.value = false
  }
}

const filteredData = computed(() => {
  return tableData.value.filter(item => {
    // Simple filter logic for demo purposes
    // In a real app, this would likely be handled by the backend or more robust frontend logic
    const matchCanteen = !selectedCanteen.value || item.canteen.includes(selectedCanteen.value)
    const matchLedger = !selectedLedger.value || item.ledgerName.includes(selectedLedger.value.replace('台账', ''))
    const matchSearch = !searchText.value || 
      item.canteen.includes(searchText.value) || 
      item.submitter.includes(searchText.value)
    
    return matchCanteen && matchLedger && matchSearch
  })
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const total = computed(() => filteredData.value.length)

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handleView = (row: Record) => {
  verifyLedgerInstance(row.id)
    .then((res) => {
      ElMessage.success(res?.is_valid ? '台账验签通过' : '台账验签未通过')
    })
    .catch(() => {
      ElMessage.error('台账验签失败')
    })
}

const handleDownload = (row: Record) => {
  ElMessage.success(`开始下载 ${row.ledgerName}`)
}

const handleEdit = (row: Record) => {
  ElMessage.info(`编辑 ${row.id}`)
}

const handleCancel = (row: Record) => {
  ElMessage.warning(`取消 ${row.id}`)
}

loadLedgerRecords()
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #fff;
  min-height: calc(100vh - 40px);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.page-title {
  font-size: 18px;
  color: #333;
}

.filter-container {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.separator {
  color: #606266;
  margin: 0 4px;
}

.table-container {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* Customizing Element Plus Pagination to match image style somewhat */
:deep(.el-pagination.is-background .el-pager li:not(.is-disabled).is-active) {
  background-color: #409eff;
  color: #fff;
}

:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) {
  padding: 0 10px;
}
</style>