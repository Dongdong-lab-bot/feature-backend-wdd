<template>
  <div class="ledger-templates-page">
    <header class="page-header">
      <div class="header-title">电子台账模板管理</div>
      <el-button type="primary" @click="handleCreate">新建模板</el-button>
    </header>

    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索模板名称"
        clearable
        style="width: 260px"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="pagedRows"
      style="width: 100%; margin-top: 12px"
      :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
    >
      <el-table-column prop="id" label="ID" width="80" align="center" />
      <el-table-column prop="name" label="模板名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip>
        <template #default="scope">
          {{ scope.row.description || '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="90" align="center">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'" size="small">
            {{ scope.row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" align="center">
        <template #default="scope">
          {{ scope.row.created_at ? String(scope.row.created_at).replace('T', ' ').slice(0, 19) : '—' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center">
        <template #default="scope">
          <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <footer class="page-footer">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        :total="total"
        @size-change="loadList"
        @current-change="loadList"
      />
    </footer>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑模板' : '新建模板'"
      width="520px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入模板描述（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getLedgerTemplateList,
  createLedgerTemplate,
  updateLedgerTemplate,
  deleteLedgerTemplate
} from '@/api/canteen'

interface TemplateRow {
  id: number
  name: string
  description: string | null
  is_active: number
  created_at: string
}

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const allRows = ref<TemplateRow[]>([])

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', description: '' })
const rules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }]
}

const filteredRows = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return allRows.value
  return allRows.value.filter((item) => item.name.toLowerCase().includes(kw))
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const loadList = async () => {
  loading.value = true
  try {
    const res: any = await getLedgerTemplateList({ page: 1, size: 500 })
    allRows.value = (res?.data?.records || []).map((item: any) => ({
      id: Number(item.id),
      name: String(item.name || item.title || `模板${item.id}`),
      description: item.description ?? null,
      is_active: Number(item.is_active ?? 1),
      created_at: String(item.created_at || '')
    }))
    total.value = allRows.value.length
  } catch {
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  total.value = filteredRows.value.length
}

const handleCreate = () => {
  editingId.value = null
  dialogVisible.value = true
}

const handleEdit = (row: TemplateRow) => {
  editingId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  dialogVisible.value = true
}

const resetForm = () => {
  form.name = ''
  form.description = ''
  editingId.value = null
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = {
      name: form.name,
      title: form.name,
      description: form.description || undefined,
      schema: { version: '1.0', fields: [] }
    }
    if (editingId.value) {
      await updateLedgerTemplate(editingId.value, payload)
      ElMessage.success('模板已更新')
    } else {
      await createLedgerTemplate(payload)
      ElMessage.success('模板已创建')
    }
    dialogVisible.value = false
    await loadList()
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row: TemplateRow) => {
  try {
    await ElMessageBox.confirm(`确定删除模板「${row.name}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    await deleteLedgerTemplate(row.id)
    ElMessage.success('模板已删除')
    await loadList()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.ledger-templates-page {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 84px);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.search-bar {
  display: flex;
  gap: 8px;
  align-items: center;
}

.page-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
