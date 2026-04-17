<template>
  <div class="template-scope-container">
    <el-card class="scope-card">
      <template #header>
        <div class="card-header">
          <span>覆盖范围设置</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="scopeForm"
        label-width="100px"
        v-loading="loading"
      >
        <el-form-item label="覆盖人员">
          <el-select
            v-model="scopeForm.users"
            multiple
            filterable
            placeholder="请选择覆盖人员"
            style="width: 100%"
            @change="handleUsersChange"
          >
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            >
              <span>{{ user.real_name }}</span>
              <span style="color: #999; font-size: 12px; margin-left: 8px">
                {{ user.username }}
              </span>
            </el-option>
          </el-select>
          <div class="form-tip">选择需要填写此模板的人员，支持多选</div>
        </el-form-item>

        <el-form-item label="覆盖食堂">
          <el-select
            v-model="scopeForm.canteens"
            multiple
            filterable
            placeholder="请选择覆盖食堂"
            style="width: 100%"
            @change="handleCanteensChange"
          >
            <el-option
              v-for="canteen in availableCanteens"
              :key="canteen.id"
              :label="canteen.name"
              :value="canteen.id"
            >
              <span>{{ canteen.name }}</span>
            </el-option>
          </el-select>
          <div class="form-tip">选择需要填写此模板的食堂，支持多选</div>
        </el-form-item>

        <el-form-item label="扩展配置">
          <el-input
            v-model="scopeForm.extraConfig"
            type="textarea"
            :rows="3"
            placeholder="请输入扩展配置（JSON格式）"
            style="width: 100%"
          />
          <div class="form-tip">可选，用于模板的额外配置信息</div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSave"
            :loading="saveLoading"
          >
            保存设置
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="scope-info-card" v-if="scopeInfo">
      <template #header>
        <div class="card-header">
          <span>当前覆盖范围</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="覆盖人员数量">
          {{ scopeInfo.users?.length || 0 }} 人
        </el-descriptions-item>
        <el-descriptions-item label="覆盖食堂数量">
          {{ scopeInfo.canteens?.length || 0 }} 家
        </el-descriptions-item>
        <el-descriptions-item label="模板描述" :span="2">
          {{ scopeInfo.description || '暂无描述' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getTemplateScope,
  updateTemplateFull,
  batchUpdateScopeUsers,
  batchUpdateScopeCanteens,
  type TemplateScopeResponse,
} from '@/api/ledger/template'

interface UserItem {
  id: number
  real_name: string
  username: string
}

interface CanteenItem {
  id: number
  name: string
}

const props = defineProps<{
  templateId: number
}>()

const loading = ref(false)
const saveLoading = ref(false)
const formRef = ref()
const scopeInfo = ref<TemplateScopeResponse | null>(null)

const scopeForm = reactive({
  users: [] as number[],
  canteens: [] as number[],
  extraConfig: '',
})

const availableUsers = ref<UserItem[]>([])
const availableCanteens = ref<CanteenItem[]>([])

const fetchScopeInfo = async () => {
  if (!props.templateId) return

  loading.value = true
  try {
    const res = await getTemplateScope(props.templateId)
    if (res.code === 20000) {
      scopeInfo.value = res.data
      scopeForm.users = res.data.users || []
      scopeForm.canteens = res.data.canteens || []
    } else {
      ElMessage.error(res.msg || '获取覆盖范围失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取覆盖范围失败')
  } finally {
    loading.value = false
  }
}

const handleUsersChange = async (userIds: number[]) => {
  if (!props.templateId) return

  saveLoading.value = true
  try {
    const res = await batchUpdateScopeUsers(props.templateId, userIds)
    if (res.code === 20000) {
      ElMessage.success('人员覆盖范围更新成功')
      await fetchScopeInfo()
    } else {
      ElMessage.error(res.msg || '更新人员覆盖范围失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '更新人员覆盖范围失败')
  } finally {
    saveLoading.value = false
  }
}

const handleCanteensChange = async (canteenIds: number[]) => {
  if (!props.templateId) return

  saveLoading.value = true
  try {
    const res = await batchUpdateScopeCanteens(props.templateId, canteenIds)
    if (res.code === 20000) {
      ElMessage.success('食堂覆盖范围更新成功')
      await fetchScopeInfo()
    } else {
      ElMessage.error(res.msg || '更新食堂覆盖范围失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '更新食堂覆盖范围失败')
  } finally {
    saveLoading.value = false
  }
}

const handleSave = async () => {
  if (!props.templateId) return

  saveLoading.value = true
  try {
    const res = await updateTemplateFull(props.templateId, {
      scope: {
        users: scopeForm.users,
        canteens: scopeForm.canteens,
      },
      extra_config: scopeForm.extraConfig || undefined,
    })
    if (res.code === 20000) {
      ElMessage.success('保存成功')
      await fetchScopeInfo()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saveLoading.value = false
  }
}

const handleReset = () => {
  if (scopeInfo.value) {
    scopeForm.users = scopeInfo.value.users || []
    scopeForm.canteens = scopeInfo.value.canteens || []
    scopeForm.extraConfig = ''
  }
}

const fetchAvailableUsers = async () => {
  // TODO: 从用户API获取可选人员列表
  // 此处模拟数据，实际应从接口获取
  availableUsers.value = [
    { id: 1, real_name: '张三', username: 'zhangsan' },
    { id: 2, real_name: '李四', username: 'lisi' },
    { id: 3, real_name: '王五', username: 'wangwu' },
  ]
}

const fetchAvailableCanteens = async () => {
  // TODO: 从食堂API获取可选食堂列表
  // 此处模拟数据，实际应从接口获取
  availableCanteens.value = [
    { id: 1, name: '第一食堂' },
    { id: 2, name: '第二食堂' },
    { id: 3, name: '第三食堂' },
  ]
}

onMounted(async () => {
  await Promise.all([
    fetchScopeInfo(),
    fetchAvailableUsers(),
    fetchAvailableCanteens(),
  ])
})
</script>

<style scoped>
.template-scope-container {
  padding: 16px;
}

.scope-card {
  margin-bottom: 16px;
}

.scope-info-card {
  margin-top: 16px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
