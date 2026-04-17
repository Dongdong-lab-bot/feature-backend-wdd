<template>
  <div class="app-container">
    <div class="page-header">
      <span class="page-title">电子台账模板</span>
    </div>

    <div v-if="loading" style="text-align:center;padding:40px;">
      <el-icon class="is-loading" :size="32"><i class="el-icon-loading" /></el-icon>
      <p style="color:#999;margin-top:8px;">加载中...</p>
    </div>

    <el-empty v-else-if="!templates.length" description="暂无待填写的台账任务" />

    <el-row v-else :gutter="20" class="template-list">
      <el-col
        v-for="item in templates"
        :key="item.id"
        :xs="24"
        :sm="24"
        :md="12"
        :lg="12"
        :xl="12"
      >
        <div class="template-card">
          <div class="card-left">
            <h3 class="template-name">{{ item.name }}</h3>
            <p class="template-desc">{{ item.requirement }}</p>
          </div>
          <div class="card-right">
            <el-button type="primary" class="fill-btn" @click="handleFill(item)">
              填写
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 填写弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="'填写 - ' + currentTemplate?.name"
      width="600px"
      destroy-on-close
    >
      <el-form :model="formData" label-width="120px" class="template-form">
        <!-- 动态表单渲染 -->
        <template v-if="currentTemplate?.schema_snapshot?.fields">
          <el-form-item 
            v-for="field in currentTemplate.schema_snapshot.fields" 
            :key="field.field_id" 
            :label="field.label || field.field_id"
            :required="field.required"
          >
            <!-- 字符串/数字输入 -->
            <el-input 
              v-if="['string', 'number'].includes(field.type) && !field.enum" 
              v-model="formData[field.field_id]" 
              :type="field.type === 'number' ? 'number' : 'text'"
              :placeholder="`请输入${field.label || field.field_id}`"
            />
            <!-- 枚举选择 -->
            <el-select 
              v-else-if="field.enum" 
              v-model="formData[field.field_id]" 
              :placeholder="`请选择${field.label || field.field_id}`"
            >
              <el-option v-for="opt in field.enum" :key="opt" :label="opt" :value="opt" />
            </el-select>
          </el-form-item>
        </template>

        <!-- 兼容旧的假数据渲染 -->
        <template v-else>
          <el-form-item label="记录日期">
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="formData.operator" placeholder="请输入操作人姓名" />
        </el-form-item>
        
        <template v-if="currentTemplate?.name.includes('留样')">
          <el-form-item label="留样餐次">
            <el-select v-model="formData.mealType" placeholder="请选择">
              <el-option label="早餐" value="早餐" />
              <el-option label="午餐" value="午餐" />
              <el-option label="晚餐" value="晚餐" />
            </el-select>
          </el-form-item>
          <el-form-item label="留样品种">
            <el-input v-model="formData.foodName" placeholder="请输入食品名称" />
          </el-form-item>
        </template>

        <template v-if="currentTemplate?.name.includes('消毒')">
             <el-form-item label="消毒对象">
            <el-input v-model="formData.target" placeholder="例如：餐具、环境" />
          </el-form-item>
          <el-form-item label="消毒方法">
            <el-select v-model="formData.method" placeholder="请选择">
              <el-option label="热力消毒" value="热力" />
              <el-option label="化学消毒" value="化学" />
              <el-option label="紫外线" value="紫外线" />
            </el-select>
          </el-form-item>
        </template>
        
        <el-form-item label="备注">
            <el-input
              v-model="formData.remark"
              type="textarea"
              rows="3"
              placeholder="请输入备注信息"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">提交</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getLedgerInstances, saveLedgerInstanceDraft, submitLedgerInstance } from '@/api/ledger'

export interface Template {
  id: number
  name: string
  requirement: string
  schema_snapshot?: any
  content?: any
}

const dialogVisible = ref(false)
const currentTemplate = ref<Template | null>(null)
const submitting = ref(false)
const loading = ref(false)

const templates = ref<Template[]>([])

const loadTemplatesByInstances = async () => {
  loading.value = true
  try {
    const data = await getLedgerInstances({ page: 1, size: 50, status: 'PENDING' })
    const records = Array.isArray(data?.records) ? data.records : []
    templates.value = records.map((item) => ({
      id: item.id,
      name: item.template_title || '台账任务',
      requirement: `创建时间：${(item.created_at || '').slice(0, 19).replace('T', ' ') || '—'}`,
      schema_snapshot: item.schema_snapshot,
      content: item.content
    }))
  } catch {
    ElMessage.error('获取台账任务失败，请刷新重试')
    templates.value = []
  } finally {
    loading.value = false
  }
}

const formData = ref<Record<string, any>>({
  date: new Date().toISOString().split('T')[0],
  operator: '张三',
  remark: '',
  mealType: '',
  foodName: '',
  target: '',
  method: ''
})

const handleFill = async (item: Template) => {
  currentTemplate.value = item
  
  // 初始化动态表单数据
  const initialData: Record<string, any> = {}
  
  // 如果列表中没有携带 schema_snapshot，我们使用兜底结构
  if (item.schema_snapshot?.fields) {
    item.schema_snapshot.fields.forEach((field: any) => {
      initialData[field.field_id] = item.content?.[field.field_id] ?? ''
    })
  } else {
    // 兼容旧结构或假数据
    Object.assign(initialData, {
      date: new Date().toISOString().split('T')[0],
      operator: '张三',
      remark: '',
      mealType: '',
      foodName: '',
      target: '',
      method: ''
    })
  }
  formData.value = initialData
  dialogVisible.value = true
}

const submitForm = () => {
  if (!currentTemplate.value) {
    dialogVisible.value = false
    return
  }

  submitting.value = true
  const content = {
    date: formData.value.date,
    operator: formData.value.operator,
    remark: formData.value.remark,
    meal_type: formData.value.mealType,
    food_name: formData.value.foodName,
    target: formData.value.target,
    method: formData.value.method
  }

  saveLedgerInstanceDraft(currentTemplate.value.id, content)
    .then(() => submitLedgerInstance(currentTemplate.value!.id, content))
    .then(() => {
      ElMessage.success(`${currentTemplate.value?.name} 提交成功`)
      dialogVisible.value = false
    })
    .finally(() => {
      submitting.value = false
    })
}

onMounted(() => {
  loadTemplatesByInstances()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  background-color: #f5f7fa; /* Light grey background */
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
  background-color: #fff;
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: normal;
  color: #333;
}

.template-list {
  /* No special styles needed here */
}

.template-card {
  background-color: #fff;
  margin-bottom: 20px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 4px solid #409EFF; /* Blue accent border */
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  position: relative;
  transition: all 0.3s;
}

.template-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.1);
}

.card-left {
  flex: 1;
}

.template-name {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.template-desc {
  margin: 0;
  font-size: 13px;
  color: #999;
}

.card-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fill-btn {
  padding: 8px 25px;
  font-size: 14px;
  border-radius: 4px;
}

/* Specific styling to match image for the selected state if needed, 
   but for now we stick to hover or just the left border */
</style>