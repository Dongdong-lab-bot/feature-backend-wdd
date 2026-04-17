<template>
  <div class="details-container">
    <div class="detail-card" v-loading="loading">
      <div class="header-section">
        <h2>{{ titleText }}</h2>
        <div class="meta-info">
          <span class="meta-item">时间：{{ dateText }}</span>
          <span class="meta-item">提交人：{{ submitterText }}</span>
          <span class="meta-item">状态：{{ statusText }}</span>
        </div>
      </div>

      <el-alert
        v-if="loadError"
        :title="loadError"
        type="warning"
        :closable="false"
        show-icon
        class="page-alert"
      />

      <div v-else class="content-wrapper">
        <div class="sidebar">
          <div class="sidebar-header">检查大项</div>
          <div
            v-for="category in categories"
            :key="category"
            class="category-item"
            :class="{ active: currentCategory === category }"
            @click="currentCategory = category"
          >
            {{ category }}
          </div>
        </div>

        <div class="main-content">
          <div class="table-header">
            <div class="header-cell issue-col">问题小项</div>
            <div class="header-cell rectify-col">整改反馈情况</div>
          </div>

          <div class="issue-list">
            <div v-for="issue in currentIssues" :key="issue.id" class="issue-row">
              <!-- 左侧：问题详情 -->
              <div class="issue-cell">
                <div class="issue-title">
                  <span class="status-dot" :class="issue.status"></span>
                  {{ issue.content }}
                </div>
                <div class="issue-standard">标准：{{ issue.standard }}</div>
                <div class="issue-remark">备注：{{ issue.remark || '无' }}</div>
                <div class="issue-photos" v-if="issue.photos.length > 0">
                  <el-image
                    v-for="(photo, idx) in issue.photos"
                    :key="idx"
                    :src="photo"
                    :preview-src-list="issue.photos"
                    fit="cover"
                    class="photo-item"
                  />
                </div>
              </div>

              <!-- 右侧：整改反馈 -->
              <div class="rectify-cell">
                <template v-if="taskStatus === 'REJECTED' || taskStatus === 'RECTIFYING'">
                  <!-- 编辑态 -->
                  <div class="form-item">
                    <span class="label">整改描述：</span>
                    <el-input
                      v-model="issue.rectifyRemark"
                      type="textarea"
                      :rows="2"
                      placeholder="请输入整改情况说明"
                    />
                  </div>
                  <div class="form-item">
                    <span class="label">整改照片：</span>
                    <!-- 模拟上传组件 -->
                    <div class="upload-placeholder">
                      <el-icon><Plus /></el-icon>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <!-- 查看态 -->
                  <div class="form-item">
                    <span class="label">整改描述：</span>
                    <span class="text">{{ issue.rectifyRemark || '无' }}</span>
                  </div>
                  <div class="form-item" v-if="issue.rectifyPhotos.length > 0">
                    <span class="label">整改照片：</span>
                    <div class="rectify-photos">
                      <el-image
                        v-for="(photo, idx) in issue.rectifyPhotos"
                        :key="idx"
                        :src="photo"
                        :preview-src-list="issue.rectifyPhotos"
                        fit="cover"
                        class="photo-item"
                      />
                    </div>
                  </div>
                </template>
              </div>
            </div>
            
            <el-empty v-if="currentIssues.length === 0" description="该大项下暂无检查项" />
          </div>

          <div class="content-footer" v-if="taskStatus === 'REJECTED' || taskStatus === 'RECTIFYING'">
            <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
              提交整改内容
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getVideoInspectionTaskDetail, rectifyVideoInspectionTask } from '@/api/video-inspection'
import { getStoredUserInfo } from '@/utils/auth-storage'

interface Issue {
  id: number | string
  resultId?: number
  category: string
  content: string
  standard: string
  status: 'pass' | 'fail'
  photos: string[]
  remark: string
  rectifyRemark: string
  rectifyPhotos: string[]
}

const route = useRoute()
const loading = ref(false)
const loadError = ref('')
const submitLoading = ref(false)

const inspectionId = ref<number | null>(null)
const titleText = ref('视频巡检详情')
const dateText = ref('-')
const submitterText = ref('-')
const statusText = ref('-')
const taskStatus = ref('')

const categories = ref<string[]>([])
const currentCategory = ref('')
const allIssues = ref<Issue[]>([])

const currentIssues = computed(() => {
  return allIssues.value.filter(issue => issue.category === currentCategory.value)
})

const loadInspectionDetail = async () => {
  const id = Number(route.query.id)
  if (!id) {
    ElMessage.warning('缺少任务ID，当前为默认展示')
    return
  }
  inspectionId.value = id
  loading.value = true
  loadError.value = ''

  try {
    const res = await getVideoInspectionTaskDetail(id)
    if (!res) {
      loadError.value = '获取详情失败，返回数据为空'
      return
    }

    // 安全解析后端返回的数据结构
    const taskInfo = (res as Record<string, any>)?.task_info || (res as Record<string, any>)?.data?.task_info || (res as Record<string, any>)
    const formSnapshot = (res as Record<string, any>)?.form_snapshot || (res as Record<string, any>)?.data?.form_snapshot || (taskInfo as Record<string, any>)?.form_snapshot

    if (taskInfo?.canteen_name) {
      titleText.value = `${taskInfo.canteen_name} 视频巡检详情`
    } else if (taskInfo?.canteen_name_snapshot) {
      titleText.value = `${taskInfo.canteen_name_snapshot} 视频巡检详情`
    }

    if (taskInfo?.business_date) {
      dateText.value = taskInfo.business_date
    } else if (taskInfo?.submission_date) {
      const d = new Date(taskInfo.submission_date)
      if (!Number.isNaN(d.getTime())) {
        dateText.value = `${d.getFullYear()}.${d.getMonth() + 1}.${d.getDate()}`
      }
    }

    if (taskInfo?.inspector_name) {
      submitterText.value = taskInfo.inspector_name
    } else if (taskInfo?.executor_name_snapshot) {
      submitterText.value = taskInfo.executor_name_snapshot
    }

    if (taskInfo?.status) {
      taskStatus.value = taskInfo.status
      if (taskInfo.status === 'PENDING') statusText.value = '待检查'
      else if (taskInfo.status === 'RECTIFYING' || taskInfo.status === 'REJECTED') statusText.value = '待整改'
      else if (taskInfo.status === 'COMPLETED') statusText.value = '已完成'
      else statusText.value = taskInfo.status
    }

    // 解析 form_snapshot 中的 major_items
    let snapshotMajorItems: any[] = []
    if (formSnapshot && Array.isArray(formSnapshot.major_items)) {
      snapshotMajorItems = formSnapshot.major_items
    } else if (Array.isArray(formSnapshot)) {
      snapshotMajorItems = formSnapshot
    }

    if (snapshotMajorItems.length > 0) {
      const parsedIssues: Issue[] = []
      const catSet = new Set<string>()

      snapshotMajorItems.forEach((major: any, index: number) => {
        const catName = major.title || major.category || `检查大项 ${index + 1}`
        catSet.add(catName)

        const minors = Array.isArray(major.minor_items) ? major.minor_items : (Array.isArray(major.items) ? major.items : [])
        
        minors.forEach((minor: any) => {
          parsedIssues.push({
            id: minor.item_id || minor.id || Math.random(),
            resultId: typeof minor.result_id === 'number' ? minor.result_id : undefined,
            category: catName,
            content: minor.content || minor.name || '未知检查项',
            standard: minor.standard || minor.requirement || '按规定执行',
            status: minor.is_qualified === false ? 'fail' : (minor.is_qualified === true ? 'pass' : 'fail'),
            photos: Array.isArray(minor.photos) ? minor.photos : (Array.isArray(minor.inspection_photos) ? minor.inspection_photos : []),
            remark: minor.description || minor.remark || minor.inspection_description || '',
            rectifyRemark: minor.rectification_description || minor.rectify_desc || '',
            rectifyPhotos: Array.isArray(minor.rectification_photos) ? minor.rectification_photos : []
          })
        })
      })

      allIssues.value = parsedIssues
      categories.value = Array.from(catSet)
      if (categories.value.length > 0) {
        currentCategory.value = categories.value[0]
      }
    } else {
      ElMessage.info('该任务暂无检查项明细')
    }

  } catch (err: any) {
    console.error('获取视频巡检详情失败:', err)
    if (err?.response?.status === 422) {
      loadError.value = '后端数据结构验证失败 (422)。这通常是因为测试数据不完整导致的。'
    } else if (err?.response?.status === 403) {
      loadError.value = '您没有查看该视频巡检详情的权限 (403)'
    } else {
      loadError.value = err?.message || '获取视频巡检详情时发生错误'
    }
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!inspectionId.value) return
  
  const feedback = allIssues.value
    .filter(issue => issue.resultId && issue.rectifyRemark.trim())
    .map(issue => ({
      result_id: issue.resultId!,
      description: issue.rectifyRemark.trim(),
      photos: issue.rectifyPhotos
    }))

  if (feedback.length === 0) {
    ElMessage.warning('请至少填写一条需要整改项的说明')
    return
  }

  const currentUser = getStoredUserInfo<{ username?: string; id?: number }>()
  const rectifierId = currentUser?.username || (currentUser?.id ? String(currentUser.id) : 'unknown')

  submitLoading.value = true
  try {
    await rectifyVideoInspectionTask(inspectionId.value, {
      rectifier_id: rectifierId,
      feedback_per_item: feedback
    })
    ElMessage.success('提交整改成功')
    await loadInspectionDetail()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.msg || '提交整改失败')
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadInspectionDetail()
})
</script>

<style scoped>
.details-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 84px);
}

.detail-card {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  min-height: 500px;
  display: flex;
  flex-direction: column;
}

.header-section {
  padding: 20px 24px;
  border-bottom: 1px solid #ebeef5;
}

.header-section h2 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: #303133;
}

.meta-info {
  display: flex;
  gap: 24px;
  color: #606266;
  font-size: 14px;
}

.page-alert {
  margin: 20px;
}

.content-wrapper {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 240px;
  background: #f8f9fa;
  border-right: 1px solid #ebeef5;
}

.sidebar-header {
  padding: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  background: #f0f2f5;
}

.category-item {
  padding: 16px;
  cursor: pointer;
  color: #606266;
  border-bottom: 1px solid #ebeef5;
  transition: all 0.3s;
}

.category-item:hover {
  background-color: #e6f1fc;
}

.category-item.active {
  background-color: #fff;
  color: #409eff;
  font-weight: 500;
  border-left: 3px solid #409eff;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: flex;
  background: #f0f2f5;
  border-bottom: 1px solid #ebeef5;
}

.header-cell {
  padding: 12px 16px;
  font-weight: 600;
  color: #303133;
}

.issue-col {
  flex: 1;
  border-right: 1px solid #ebeef5;
}

.rectify-col {
  width: 400px;
}

.issue-list {
  flex: 1;
  overflow-y: auto;
}

.issue-row {
  display: flex;
  border-bottom: 1px solid #ebeef5;
}

.issue-cell {
  flex: 1;
  padding: 20px;
  border-right: 1px solid #ebeef5;
}

.rectify-cell {
  width: 400px;
  padding: 20px;
  background: #fafafa;
}

.issue-title {
  font-weight: 500;
  font-size: 15px;
  color: #303133;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
}

.status-dot.pass { background-color: #67c23a; }
.status-dot.fail { background-color: #f56c6c; }

.issue-standard, .issue-remark {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  line-height: 1.5;
}

.issue-photos, .rectify-photos {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.photo-item {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.form-item {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item .label {
  width: 80px;
  font-size: 14px;
  color: #606266;
  flex-shrink: 0;
  line-height: 32px;
}

.form-item .text {
  font-size: 14px;
  color: #303133;
  line-height: 32px;
}

.upload-placeholder {
  width: 80px;
  height: 80px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  background: #fff;
  cursor: pointer;
}

.upload-placeholder:hover {
  border-color: #409eff;
  color: #409eff;
}

.content-footer {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  background: #fff;
}

@media (max-width: 1200px) {
  .rectify-col, .rectify-cell {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #ebeef5;
  }
  .category-item {
    display: inline-block;
    border-bottom: none;
    border-right: 1px solid #ebeef5;
  }
  .category-item.active {
    border-left: none;
    border-bottom: 3px solid #409eff;
  }
  .table-header {
    display: none;
  }
  .issue-row {
    flex-direction: column;
  }
  .issue-cell, .rectify-cell {
    width: 100%;
    border-right: none;
  }
  .issue-cell {
    border-bottom: 1px dashed #ebeef5;
  }
}
</style>