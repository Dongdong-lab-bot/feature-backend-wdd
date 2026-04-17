<template>
  <div class="daily-check">
    <div class="dc-header">
      <div class="title">日管控提交</div>
    </div>
    <section class="check-list" v-loading="loading">
      <article class="check-item" v-for="item in displayList" :key="item.templateName">
        <div class="info">
          <h2>{{ item.templateName }}</h2>
          <p class="req">{{ item.req }}</p>
        </div>
        <div class="actions">
          <button class="btn primary" @click="openChecklist(item)">
            去提交
          </button>
        </div>
      </article>
      <div v-if="!loading && displayList.length === 0" class="empty-tip">暂无日管控模板</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getDailyControlTemplates, getDailyControlTasks } from '@/api/inspection'

interface DisplayItem {
  templateId: number
  templateName: string
  req: string
  taskId: number | null
}

interface TemplateLike {
  id: number
  template_name?: string | null
  start_time?: string | null
  end_time?: string | null
}

const displayList = ref<DisplayItem[]>([])
const loading = ref(false)
const router = useRouter()

const formatReqText = (rawTime?: string | null): string => {
  if (!rawTime) return '提交要求(待处理)'
  // 纯时间字符串 HH:mm 直接返回
  if (/^\d{2}:\d{2}(:\d{2})?$/.test(rawTime)) return `提交要求(${rawTime})`
  const dt = new Date(rawTime)
  if (Number.isNaN(dt.getTime())) return `提交要求(${rawTime})`
  const pad = (v: number) => String(v).padStart(2, '0')
  return `提交要求(${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())})`
}

const pickTemplateTime = (template?: TemplateLike): string | null => {
  if (!template) return null
  return template.start_time || template.end_time || null
}

const loadChecklist = async () => {
  loading.value = true
  try {
    const [templateResp, taskResp] = await Promise.all([
      getDailyControlTemplates().catch(() => null),
      getDailyControlTasks({ page: 1, page_size: 100, status: 'PENDING' }).catch(() => null),
    ])

    const templateRecords = Array.isArray(templateResp?.list)
      ? templateResp.list
      : Array.isArray(templateResp?.records)
        ? templateResp.records
        : []
    const taskRecords = Array.isArray(taskResp?.list) ? taskResp.list : []

    // 优先按 template_id 匹配，失败时才按名称匹配
    const taskById = new Map<number, { taskId: number; req: string }>()
    const taskByName = new Map<string, { taskId: number; req: string }>()
    for (const task of taskRecords) {
      const entry = { taskId: task.task_id, req: formatReqText(task.submission_date) }
      if (task.template_id) taskById.set(task.template_id, entry)
      const name = task.template_name || ''
      if (name && !taskByName.has(name)) taskByName.set(name, entry)
    }

    displayList.value = templateRecords.map((template) => {
      const name = template.template_name || ''
      const task = taskById.get(template.id) || taskByName.get(name)
      return {
        templateId: template.id,
        templateName: name,
        req: task?.req || formatReqText(pickTemplateTime(template)),
        taskId: task?.taskId ?? null,
      }
    })
  } catch {
    displayList.value = []
    ElMessage.warning('日管控模板加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const openChecklist = (item: DisplayItem) => {
  if (item.taskId) {
    router.push({
      path: '/daily/details',
      query: { id: String(item.taskId) },
    })
  } else {
    // 任务尚未生成，导航到模板预览页
    router.push({
      path: '/daily/details',
      query: { templateId: String(item.templateId) },
    })
  }
}

onMounted(() => {
  loadChecklist()
})
</script>

<style scoped>
.daily-check {
  min-height: 100%;
  background: rgb(238, 240, 248);
  padding: 20px;
  color: #303133;
}

.dc-header {
  margin-bottom: 20px;
  padding: 10px 0;
}

.dc-header .title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.check-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.check-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 100px;
  background: #fff;
  border-left: 4px solid #77a9ff;
  padding: 0 24px 0 18px;
}

.info {
  min-width: 0;
}

.info h2 {
  margin: 0 0 18px;
  font-size: 17px;
  font-weight: 600;
  color: #222;
}

.req {
  margin: 0;
  font-size: 14px;
  color: #9ba4b2;
}

.actions {
  flex-shrink: 0;
  padding-left: 20px;
}

.btn {
  min-width: 80px;
  height: 30px;
  border: none;
  background: #4b95f5;
  color: #fff;
  font-size: 14px;
  line-height: 30px;
  text-align: center;
  cursor: pointer;
}

.btn:hover {
  background: #3887ef;
}

.empty-tip {
  background: #fff;
  padding: 28px 16px;
  text-align: center;
  color: #909399;
}

@media (max-width: 768px) {
  .check-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
  }

  .actions {
    padding-left: 0;
    width: 100%;
  }

  .btn {
    width: 100%;
  }
}
</style>
