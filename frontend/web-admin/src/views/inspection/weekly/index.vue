<template>
  <div v-if="isCreateView" class="create-view">
    <div class="create-title">{{ isEditMode ? '编辑周排查检查表' : '新建周排查检查表' }}</div>

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
                  <el-input
                    v-model="item.totalScore"
                    class="mini-input"
                    placeholder="分值"
                    @blur="validateItemScore(item)"
                  />
                </template>
                <template v-else-if="createForm.tableType === 'OPTION'">
                  <span>满分:</span>
                  <el-input
                    v-model="item.totalScore"
                    class="mini-input"
                    placeholder="分值"
                    @blur="validateItemScore(item)"
                  />
                </template>
              </div>
              <!-- 评分控件：根据表格类型切换（始终占一个 grid 列） -->
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
          <div class="actions-right">
            <el-button class="save-create-btn" type="primary" @click="saveCreateChecklist">保存</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="isChecklistView" class="checklist-view">
    <div class="checklist-header">
      <div class="checklist-title">周排查模板</div>
      <div class="checklist-header-right">
        <el-button type="primary" class="new-template-btn" @click="router.push({ name: 'WeeklyCreate' })">+ 新建检查表</el-button>
      </div>
    </div>

    <div v-loading="templateLoading" class="template-list">
      <div v-for="item in templateCards" :key="item.id" class="template-card">
        <div class="card-main">
          <div class="card-name">{{ item.name }}</div>
          <div class="card-desc">共 {{ item.taskCount }} 个检查小项</div>
        </div>
        <div class="card-actions">
          <el-button class="outline-btn" @click="handleCoverUsers(item)">覆盖人员</el-button>
          <el-button class="outline-btn" @click="handleCoverCanteens(item)">覆盖食堂</el-button>
          <el-button type="success" class="dispatch-btn" @click="handleDispatch(item)">下发</el-button>
          <el-button type="primary" class="edit-btn" @click="handleEditTemplate(item)">编辑</el-button>
          <el-button class="delete-btn" @click="handleDeleteTemplate(item)">删除</el-button>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="isScoreView" class="score-view">
    <div class="score-toolbar">
      <div class="score-title">周排查巡检表分数统计</div>
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
            <el-option v-for="item in canteens" :key="`score-canteen-${item.id}`" :label="item.name" :value="String(item.id)" />
          </el-select>
        </div>
        <div class="score-control-item">
          <span class="label">表格筛选</span>
          <el-select v-model="scoreQuery.formName" class="score-select" placeholder="全部表格">
            <el-option label="全部表格" value="" />
            <el-option v-for="name in scoreFormOptions" :key="`score-form-${name}`" :label="name" :value="name" />
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
            <span :class="statusClass(scope.row.status)">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" align="center">
          <template #default="scope">
            <el-button link type="danger" @click="handleScoreCancel(scope.row)">删除</el-button>
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
    <!-- Picker mode: no templateId/id → let user pick a template first -->
    <template v-if="detailNeedsTemplatePick">
      <div class="detail-headline">请选择检查表</div>
      <div v-loading="templateLoading" class="picker-card-list">
        <div
          v-for="tpl in templateCards"
          :key="tpl.id"
          class="picker-card"
          @click="router.push({ name: 'WeeklyDetail', query: { templateId: String(tpl.id) } })"
        >
          <div class="picker-card-name">{{ tpl.name }}</div>
          <div class="picker-card-meta">共 {{ tpl.taskCount }} 项</div>
        </div>
        <div v-if="!templateLoading && templateCards.length === 0" class="picker-empty">暂无检查表模板，请先在「周排查管控表」页面创建</div>
      </div>
    </template>

    <!-- Normal detail content when templateId or id is present -->
    <template v-else>
    <div class="panel-container">
    <!-- ── 页面头部卡片 ── -->
    <div class="page-header-card">
      <h2 class="page-title">{{ detailRecordTitle }}</h2>
      <div class="page-meta">
        <span class="meta-item">时间：{{ detailDate }}</span>
        <span class="meta-item">提交人：{{ detailSubmitter }}</span>
        <el-tag
          v-if="detailTaskStatus"
          size="small"
          :type="detailTaskStatus === 'COMPLETED' ? 'success' : (detailTaskStatus === 'SUBMITTED' || detailTaskStatus === 'RECTIFIED') ? 'warning' : (detailTaskStatus === 'REJECTED' || detailTaskStatus === 'PENDING') ? 'danger' : 'info'"
        >{{ detailStatusText }}</el-tag>
      </div>
    </div>

    <!-- ── 主体布局 ── -->
    <div class="main-layout">
      <!-- 左侧大项导航 -->
      <div class="sidebar-card">
        <div class="sidebar-title">表格问题大项</div>
        <div
          v-for="section in detailSections"
          :key="section.id"
          class="sidebar-item"
          :class="{ active: selectedSectionId === section.id }"
          @click="handleSelectSection(section.id)"
        >{{ section.name }}</div>
      </div>

      <!-- 右侧内容区 -->
      <div class="content-area">
        <!-- 列标题行 -->
        <div v-if="detailHasRectification || detailCanAudit" class="col-header-row">
          <div class="col-header-cell col-header-problem">问题详情</div>
          <div v-if="detailHasRectification" class="col-header-cell col-header-rectify">整改反馈</div>
          <div v-if="detailCanAudit" class="col-header-cell col-header-audit">审核操作</div>
        </div>

        <div v-for="issue in currentSectionIssues" :key="issue.id" class="item-card">
          <!-- 卡片头部 -->
          <div class="card-header">
            <span class="item-indicator" :style="{ background: issue.tagColor }"></span>
            <span class="item-title">{{ issue.title }}</span>
            <div class="score-tags">
              <el-tag size="small" type="info" effect="plain">满分 {{ issue.fullScore }}</el-tag>
              <el-tag size="small" :type="issue.score < issue.fullScore ? 'danger' : 'success'" effect="plain">得分 {{ issue.score }}</el-tag>
            </div>
          </div>

          <!-- 卡片体：分栏 -->
          <div class="card-body" :class="{ 'card-body-split': detailHasRectification || detailCanAudit }">
            <!-- 问题详情列 -->
            <div class="problem-section" :class="{ 'no-border': !detailHasRectification && !detailCanAudit }">
              <!-- 可编辑模式（管理员预填） -->
              <template v-if="detailIsEditable">
                <template v-if="issue.fullScore > 0">
                  <div class="section-label">评分</div>
                  <div class="issue-edit-field issue-score-field" style="margin-bottom:10px">
                    <!-- 选项表：只能选 0 或满分 -->
                    <template v-if="detailFormType === 'OPTION' || detailFormType === 'OPTION_CHECK'">
                      <div class="score-option-btns">
                        <button
                          type="button"
                          class="score-opt-btn"
                          :class="{ active: issue.score === issue.fullScore }"
                          @click="issue.score = issue.fullScore"
                        >{{ issue.fullScore }}</button>
                        <button
                          type="button"
                          class="score-opt-btn zero-btn"
                          :class="{ active: issue.score === 0 }"
                          @click="issue.score = 0"
                        >0</button>
                      </div>
                    </template>
                    <!-- 选分表：从预设选项中选择 -->
                    <template v-else-if="(detailFormType === 'SELECT_SCORE' || detailFormType === 'SCORE_SELECT') && issue.scoringOptions.length > 0">
                      <div class="score-option-btns">
                        <button
                          v-for="opt in issue.scoringOptions"
                          :key="opt"
                          type="button"
                          class="score-opt-btn"
                          :class="{ active: issue.score === opt }"
                          @click="issue.score = opt"
                        >{{ opt }}</button>
                      </div>
                    </template>
                    <!-- 自由打分：任意数值输入 -->
                    <template v-else>
                      <el-input-number
                        v-model="issue.score"
                        :min="0"
                        :max="issue.fullScore"
                        :precision="0"
                        :step="1"
                        size="small"
                        style="width:110px"
                      />
                      <span class="score-max-hint">/ {{ issue.fullScore }} 分</span>
                    </template>
                  </div>
                </template>
                <div class="section-label">问题描述</div>
                <el-input
                  v-model="issue.description"
                  type="textarea"
                  :rows="2"
                  resize="none"
                  placeholder="添加检查说明（选填）"
                  style="margin-bottom:10px"
                />
                <div class="section-label">检查图片</div>
                <div class="photo-grid">
                  <div
                    v-for="(photo, idx) in issue.inspectionPhotos"
                    :key="`ip-${issue.id}-${idx}`"
                    class="photo-box"
                  >
                    <img :src="photo" class="photo-thumb" alt="检查图片" />
                    <button type="button" class="rm-photo" @click="removeDetailInspectionPhoto(issue.id, idx)">×</button>
                  </div>
                  <label
                    v-for="slot in Math.max(0, 3 - issue.inspectionPhotos.length)"
                    :key="`slot-${issue.id}-${slot}`"
                    class="upload-trigger"
                  >
                    <input
                      type="file"
                      accept="image/*"
                      class="upload-input"
                      @change="handleDetailInspectionPhotoChange($event, issue.id)"
                    />
                    <div class="upload-placeholder">
                      <el-icon><Plus /></el-icon>
                    </div>
                  </label>
                </div>
              </template>

              <!-- 只读模式 -->
              <template v-else>
                <div class="section-label">问题描述</div>
                <p class="section-text">{{ issue.description || '-' }}</p>
                <div class="photo-grid">
                  <template v-if="issue.inspectionPhotos.length">
                    <el-image
                      v-for="p in issue.inspectionPhotos"
                      :key="p"
                      :src="p"
                      class="photo-thumb"
                      fit="cover"
                      :preview-src-list="issue.inspectionPhotos"
                    />
                  </template>
                  <span v-else class="no-photo-text">暂无图片</span>
                </div>
              </template>
            </div>

            <!-- 整改反馈列 -->
            <div v-if="detailHasRectification" class="rectify-section">
              <div class="section-label">整改描述</div>
              <p class="section-text">{{ issue.rectifyDesc || '暂无' }}</p>
              <div class="photo-grid">
                <template v-if="issue.rectificationPhotos.length">
                  <el-image
                    v-for="p in issue.rectificationPhotos"
                    :key="p"
                    :src="p"
                    class="photo-thumb"
                    fit="cover"
                    :preview-src-list="issue.rectificationPhotos"
                  />
                </template>
                <span v-else class="no-photo-text">暂无整改图片</span>
              </div>
            </div>

            <!-- 审核操作列 -->
            <div v-if="detailCanAudit" class="audit-section">
              <div class="audit-score-row">
                <span class="audit-score-label">评分：</span>
                <!-- 选项表：只能选 0 或满分 -->
                <template v-if="detailFormType === 'OPTION' || detailFormType === 'OPTION_CHECK'">
                  <div class="score-option-btns">
                    <button
                      type="button"
                      class="score-opt-btn"
                      :class="{ active: issue.auditScore === issue.fullScore }"
                      @click="issue.auditScore = issue.fullScore"
                    >{{ issue.fullScore }}</button>
                    <button
                      type="button"
                      class="score-opt-btn zero-btn"
                      :class="{ active: issue.auditScore === 0 }"
                      @click="issue.auditScore = 0"
                    >0</button>
                  </div>
                </template>
                <!-- 选分表：从预设选项中选择 -->
                <template v-else-if="(detailFormType === 'SELECT_SCORE' || detailFormType === 'SCORE_SELECT') && issue.scoringOptions.length > 0">
                  <div class="score-option-btns">
                    <button
                      v-for="opt in issue.scoringOptions"
                      :key="opt"
                      type="button"
                      class="score-opt-btn"
                      :class="{ active: issue.auditScore === opt }"
                      @click="issue.auditScore = opt"
                    >{{ opt }}</button>
                  </div>
                </template>
                <!-- 自由打分：任意数值输入 -->
                <template v-else>
                  <el-input-number
                    v-model="issue.auditScore"
                    :min="0"
                    :max="issue.fullScore"
                    :precision="0"
                    :step="1"
                    size="small"
                    style="width:110px"
                  />
                  <span class="audit-score-max">/ {{ issue.fullScore }}</span>
                </template>
              </div>
              <div class="action-btns">
                <el-button class="pass-btn" :class="{ active: issue.decision === 'pass' }" @click="issue.decision = 'pass'">通过</el-button>
                <el-button class="reject-btn" :class="{ active: issue.decision === 'reject' }" @click="issue.decision = 'reject'">驳回</el-button>
              </div>
              <el-input
                v-model="issue.rejectReason"
                type="textarea"
                :rows="2"
                placeholder="驳回描述（选填）"
                class="reject-input"
                style="margin-top:8px"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dispatch bar: only shown in draft/pre-dispatch mode -->
    <div v-if="detailIsDraft" class="detail-dispatch-bar">
      <span class="dispatch-bar-label">确认下发：</span>
      <el-date-picker
        v-model="dispatchDetailForm.businessDate"
        type="date"
        placeholder="选择检查日期"
        value-format="YYYY-MM-DD"
        style="width:180px"
      />
      <span v-if="detailTemplateCanteenName" class="dispatch-canteen-info">
        食堂：{{ detailTemplateCanteenName }}
      </span>
      <el-button
        type="primary"
        :loading="dispatchDetailSubmitting"
        style="margin-left:16px;color:#fff"
        @click="confirmDispatchFromDetail"
      >确认下发</el-button>
    </div>

    <!-- Footer -->
    <div class="footer-bar">
      <el-button
        v-if="detailCanAudit"
        type="primary"
        @click="handleDetailSubmit"
      >提交审核</el-button>
      <template v-else-if="detailTaskStatus === 'PENDING'">
        <span class="detail-status-tip pending">等待食堂端提交整改内容...</span>
        <el-button
          type="primary"
          :loading="savePrefillSubmitting"
          style="margin-left: 16px"
          @click="savePrefillInfo"
        >保存预填信息</el-button>
      </template>
      <span v-else-if="detailTaskStatus === 'COMPLETED'" class="detail-status-tip completed">✓ 审核已通过，流程完成</span>
      <span v-else-if="detailTaskStatus === 'REJECTED'" class="detail-status-tip rejected">已退回，等待食堂端重新整改提交...</span>
    </div>
    </div><!-- /panel-container -->
    </template>
  </div>

  <div v-else class="record-view">
    <header class="rv-header">
      <div class="title">{{ pageTitle }}</div>
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
            <el-option label="待审核" value="待审核" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </div>
        <div class="control-item">
          <span class="label">搜索</span>
          <el-input
            v-model="query.keyword"
            clearable
            placeholder="搜索提交食堂/提交人/表格"
            style="width: 240px"
            @keyup.enter="handleSearch"
          />
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
        <el-table-column prop="submitCanteen" label="提交食堂" min-width="170" show-overflow-tooltip />
        <el-table-column prop="submitter" label="提交人" min-width="95" />
        <el-table-column prop="submitForm" label="提交表格" min-width="170" show-overflow-tooltip />
        <el-table-column prop="score" label="检查分数" min-width="120" align="center" />
        <el-table-column prop="redline" label="红线问题数" min-width="100" align="center" />
        <el-table-column prop="yellowline" label="黄线问题数" min-width="105" align="center" />
        <el-table-column prop="submitDate" label="提交日期" min-width="120" align="center" />
        <el-table-column prop="status" label="状态" min-width="95" align="center">
          <template #default="scope">
            <span :class="statusClass(scope.row.status)">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="130" align="center">
          <template #default="scope">
            <el-button link type="primary" @click="handleViewRecord(scope.row)">查看</el-button>
            <el-button link type="danger" @click="handleCancel(scope.row)">删除</el-button>
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
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </footer>
  </div>


</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { getAllDepts, getWeeklyTaskDetail, getWeeklyTaskList, getWeeklyTemplateList, getWeeklyTemplateDetail, createWeeklyTemplate, updateWeeklyTemplate, deleteWeeklyTemplate, deleteWeeklyTask, dispatchWeeklyTemplate, updateWeeklyTaskSnapshot } from '@/api/canteen'
import { auditWeeklyTask, buildIdempotencyKey } from '@/api/inspection'
import { getUserList } from '@/api/user'

interface CanteenOption {
  id: number
  name: string
}

type WeeklyStatus = '待整改' | '待审核' | '已完成'

interface WeeklyRow {
  id: number
  canteenId: number
  submitCanteen: string
  submitter: string
  submitForm: string
  score: string
  redline: number
  yellowline: number
  submitDate: string
  status: WeeklyStatus
  rawStatus: string
}

interface WeeklyScoreRow {
  id: number
  canteenId: number
  canteen: string
  form: string
  score: string
  redline: number
  yellowline: number
  status: WeeklyStatus
  submitDate: string
}

interface WeeklyTemplateCard {
  id: number
  name: string
  taskCount: number
  isFallback?: boolean
}

interface WeeklyDetailIssue {
  id: number
  resultId: number | null
  title: string
  fullScore: number
  score: number
  auditScore: number        // admin-editable score during audit
  scoringOptions: number[]  // predefined score choices; empty = free input
  description: string
  rectifyDesc: string
  tagColor: string
  inspectionPhotos: string[]
  rectificationPhotos: string[]
  decision: '' | 'pass' | 'reject'
  rejectReason: string
}

interface WeeklyDetailSection {
  id: string
  name: string
  issues: WeeklyDetailIssue[]
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

type DataMode = 'mock' | 'actual'

const route = useRoute()
const router = useRouter()
const isCreateView = computed(() => route.name === 'WeeklyCreate')
const isEditMode = computed(() => !!Number(route.query.templateId || 0) && route.name === 'WeeklyCreate')
const isChecklistView = computed(() => route.name === 'WeeklyChecklist')
const isScoreView = computed(() => route.name === 'WeeklyScore')
const isDetailView = computed(() => route.name === 'WeeklyDetail')
// Picker mode: detail route accessed with no query params → show template list first
const detailNeedsTemplatePick = computed(() => isDetailView.value && !Number(route.query.templateId || 0) && !Number(route.query.id || 0))

// Detail view: draft mode (templateId in query = pre-dispatch fill) vs task mode (id in query)
const detailIsDraft = computed(() => isDetailView.value && !!Number(route.query.templateId || 0) && !Number(route.query.id || 0))
const detailTaskStatus = ref<string>('')
const detailHasRectification = computed(() => ['SUBMITTED', 'REJECTED', 'RECTIFIED', 'COMPLETED'].includes(detailTaskStatus.value))
const detailCanAudit = computed(() => ['SUBMITTED', 'RECTIFIED'].includes(detailTaskStatus.value))
const detailIsEditable = computed(() => detailIsDraft.value || detailTaskStatus.value === 'PENDING')
const detailStatusTextMap: Record<string, string> = { PENDING: '待整改', SUBMITTED: '待审核', REJECTED: '待整改', RECTIFIED: '待审核', COMPLETED: '已完成', DRAFT: '草稿' }
const detailStatusText = computed(() => detailStatusTextMap[detailTaskStatus.value] || detailTaskStatus.value || '')

// Dispatch from detail (draft mode)
const dispatchDetailForm = reactive({ businessDate: '' })
const dispatchDetailSubmitting = ref(false)
const detailTemplateCanteenIds = ref<number[]>([])
const detailTemplateCanteenName = ref('')
const routeTitleMap: Record<string, string> = {
  WeeklyRecords: '周排查记录',
  WeeklyDetail: '周排查记录详情',
  WeeklyChecklist: '周排查检查表',
  WeeklyScore: '周排查分数统计'
}

const pageTitle = computed(() => routeTitleMap[String(route.name || '')] || '周排查记录')

const loading = ref(false)
const canteens = ref<CanteenOption[]>([])
const allRows = ref<WeeklyRow[]>([])
const templateLoading = ref(false)
const templateCards = ref<WeeklyTemplateCard[]>([])
const dataMode = ref<DataMode>('actual')
const detailRecordTitle = ref('')
const detailDate = ref('')
const detailSubmitter = ref('')
const detailSections = ref<WeeklyDetailSection[]>([])
const selectedSectionId = ref<string>('')
const detailFormType = ref<string>('')  // 'OPTION_CHECK' | 'SCORE_SELECT' | 'SCORE_INPUT'
const selectedTaskId = ref<number | null>(null)
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
  dateRange: [] as string[],
  status: '',
  keyword: ''
})

const scoreQuery = reactive({
  dateRange: [] as string[],
  canteenId: '',
  formName: '',
  keyword: ''
})

const page = ref(1)
const pageSize = ref(10)
const scorePage = ref(1)
const scorePageSize = ref(10)

const resolveCanteenName = (id: number) => {
  return canteens.value.find((item) => item.id === id)?.name || `食堂${id || '-'}`
}

const statusMap: Record<string, WeeklyStatus> = {
  pending: '待整改',
  submitted: '待审核',
  rejected: '待整改',
  rectified: '待审核',
  completed: '已完成',
  // legacy keys
  filling: '待整改',
  signed: '待审核',
  archived: '已完成',
}

const statusToApi: Record<string, string> = {
  '待整改': 'PENDING',   // client-side filter covers both PENDING and REJECTED
  '待审核': 'SUBMITTED', // client-side filter covers both SUBMITTED and RECTIFIED
  '已完成': 'COMPLETED',
}

const submitterPool = ['张三', '李四', '王五']
const formPool = ['高中周排查检查表', '初中周排查检查表', '幼儿园周排查检查表']

const inRange = (date: string, start: string, end: string) => {
  if (!date || !start || !end) return true
  return date >= start && date <= end
}

const filteredRows = computed(() => {
  const [startDate, endDate] = query.dateRange || []
  const keyword = query.keyword.trim().toLowerCase()
  // '待整改' covers pending+rejected, '待审核' covers submitted+rectified
  const pendingSet = new Set(['pending', 'rejected'])
  const auditSet = new Set(['submitted', 'rectified'])
  return allRows.value.filter((item) => {
    let matchStatus = true
    if (query.status === '待整改') matchStatus = pendingSet.has(item.rawStatus)
    else if (query.status === '待审核') matchStatus = auditSet.has(item.rawStatus)
    else if (query.status === '已完成') matchStatus = item.rawStatus === 'completed'
    const matchDate = !startDate || !endDate || inRange(item.submitDate, startDate, endDate)
    const matchKeyword =
      !keyword ||
      `${item.submitCanteen} ${item.submitter} ${item.submitForm}`.toLowerCase().includes(keyword)
    return matchStatus && matchDate && matchKeyword
  })
})

const total = computed(() => filteredRows.value.length)

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const scoreRows = computed<WeeklyScoreRow[]>(() => {
  return allRows.value.map((item) => {
    const scoreStatus: WeeklyStatus = item.rawStatus === 'completed' ? '已完成'
      : (item.rawStatus === 'submitted' || item.rawStatus === 'rectified') ? '待审核' : '待整改'
    return {
      id: item.id,
      canteenId: item.canteenId,
      canteen: item.submitCanteen,
      form: item.submitForm,
      score: item.score,
      redline: item.redline,
      yellowline: item.yellowline,
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

const handleSelectSection = (id: string) => {
  selectedSectionId.value = id
}

const makeCreateItem = (id: string, text: string): CreateIssueItem => ({
  id,
  text,
  issueType: '红线',
  totalScore: '--',
  scoringOptions: [],
  needRectify: true
})

const makeDefaultCreateSections = (): CreateSection[] => [
  {
    id: 'food',
    name: '食材问题排查',
    items: [
      makeCreateItem('food-1', '1、食堂无三无、腐烂、过期食材'),
      makeCreateItem('food-2', '2、食堂无三无、腐烂、过期食材'),
      makeCreateItem('food-3', '3、食堂无三无、腐烂、过期食材')
    ]
  },
  {
    id: 'env',
    name: '环境问题排查',
    items: [makeCreateItem('env-1', '2、食堂地面无明显积水，清洁到位')]
  },
  {
    id: 'dish',
    name: '就餐问题排查',
    items: [makeCreateItem('dish-1', '1、前厅餐后桌面卫生整洁')]
  },
  {
    id: 'fire',
    name: '消防问题排查',
    items: [makeCreateItem('fire-1', '1、灭火器均在使用期限内')]
  }
]

const loadCreateUsers = async () => {
  try {
    const res: any = await getUserList({ page: 1, size: 200 })
    const records = res?.data?.records || []
    createUserOptions.value = records.map((u: any) => ({
      id: u.id,
      name: u.real_name || u.username || `用户${u.id}`
    }))
  } catch {
    createUserOptions.value = []
  }
}

const initCreateView = async () => {
  await loadCreateUsers()
  await loadCanteens()
  const templateId = Number(route.query.templateId || 0)
  if (!templateId) {
    // 全新新建——重置表单，空检查项
    createForm.name = String(route.query.templateName || '')
    createForm.executorRole = ''
    createForm.approverRole = ''
    createForm.startTime = ''
    createForm.endTime = '20:00'
    createForm.tableType = 'SELECT_SCORE'
    createForm.canteenId = canteens.value[0]?.id || 0
    createSections.value = []
    return
  }
  try {
    const res: any = await getWeeklyTemplateDetail(templateId)
    const tpl = res?.data
    if (tpl) {
      createForm.name = tpl.template_name || tpl.name || ''
      createForm.executorRole = String(tpl.executor_role || '')
      createForm.approverRole = String(tpl.approver_role || '')
      createForm.tableType = String(tpl.form_type || 'SELECT_SCORE')
      // Restore saved canteen from template's target_node_ids
      const savedNodeId = Array.isArray(tpl.target_node_ids) && tpl.target_node_ids.length ? Number(tpl.target_node_ids[0]) : 0
      createForm.canteenId = savedNodeId || canteens.value[0]?.id || 0
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
      .filter((item: any) => item.org_type === 'CANTEEN')
      .map((item: any) => ({ id: item.id, name: item.name }))
  } catch {
    canteens.value = []
  }
}

const loadRows = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = query.dateRange || []
    const res: any = await getWeeklyTaskList({
      page: 1,
      page_size: 500,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      status: undefined, // 不传status，由客户端filteredRows筛选以支持合并状态
      keyword: query.keyword || undefined
    })
    const records = Array.isArray(res?.data?.list) ? res.data.list : []
    allRows.value = records.map((item: any) => {
      const rawStatus = String(item.status || '').toLowerCase()
      const canteenId = Number(item.canteen_id || 0)
      const maxScore = item.max_score != null ? Number(item.max_score) : 0
      const actualScore = item.total_score != null ? Number(item.total_score) : null
      const scoreDisplay = maxScore > 0
        ? `${actualScore != null ? actualScore : '-'}/${maxScore}`
        : (actualScore != null ? String(actualScore) : '-')
      return {
        id: item.id,
        canteenId,
        submitCanteen: String(item.canteen_name || resolveCanteenName(canteenId)),
        submitter: String(item.executor_name || '-'),
        submitForm: String(item.template_name || '-'),
        score: scoreDisplay,
        redline: Number(item.red_line_count ?? item.red_line_issues ?? 0),
        yellowline: Number(item.yellow_line_count ?? 0),
        submitDate: String(item.submission_date || item.business_date || item.created_at || '').slice(0, 10) || '',
        status: statusMap[rawStatus] || '待整改',
        rawStatus
      } as WeeklyRow
    })
  } catch {
    allRows.value = []
    ElMessage.warning('周排查记录接口暂不可用')
  } finally {
    loading.value = false
  }
}

const calcTaskCount = (description?: string | null) => {
  const text = String(description || '')
  const matched = text.match(/\d+/)
  if (!matched) return 0
  return Number(matched[0]) || 0
}

const loadTemplateCards = async () => {
  templateLoading.value = true
  try {
    const res: any = await getWeeklyTemplateList({ page: 1, page_size: 100 })
    const records = Array.isArray(res?.data?.list) ? res.data.list : []
    templateCards.value = records.map((item: any, index: number) => ({
      id: item.id,
      name: String(item.template_name || item.name || `周排查模板${index + 1}`),
      taskCount: typeof item.minor_item_count === 'number' ? item.minor_item_count : 0
    }))
  } catch {
    templateCards.value = []
    ElMessage.warning('周排查模板接口暂不可用')
  } finally {
    templateLoading.value = false
  }
}

const createIssue = (idBase: number, title: string, score: number, color: string): WeeklyDetailIssue => ({
  id: idBase,
  title,
  fullScore: 6,
  score,
  description: '发现卫生或流程细节需整改的问题',
  rectifyDesc: '已完成现场整改并补充整改记录',
  tagColor: color,
  inspectionPhotos: [],
  rectificationPhotos: [],
  decision: '',
  rejectReason: ''
})

const buildDefaultDetailSections = (): WeeklyDetailSection[] => {
  return [
    {
      id: 'food',
      name: '食材问题排查',
      issues: [
        createIssue(1, '1、食堂无三无、腐烂、过期食材', 3, '#f5222d'),
        createIssue(2, '2、食堂地面无明显积水，清洁到位', 3, '#d4d600'),
        createIssue(3, '3、前厅餐后桌面卫生整洁', 3, '#409eff')
      ]
    },
    {
      id: 'people',
      name: '人员问题排查',
      issues: [
        createIssue(4, '1、工作人员证照齐全并在有效期内', 4, '#409eff'),
        createIssue(5, '2、晨检记录完整且符合规范', 4, '#409eff'),
        createIssue(6, '3、操作流程按岗位标准执行', 4, '#409eff')
      ]
    },
    {
      id: 'environment',
      name: '环境问题排查',
      issues: [
        createIssue(7, '1、后厨通风与照明符合标准', 4, '#409eff'),
        createIssue(8, '2、垃圾分类与清运记录完整', 4, '#409eff'),
        createIssue(9, '3、消杀记录可追溯', 4, '#409eff')
      ]
    },
    {
      id: 'device',
      name: '设备问题排查',
      issues: [
        createIssue(10, '1、留样冰箱温控正常', 4, '#409eff'),
        createIssue(11, '2、晨检设备在线并可用', 4, '#409eff'),
        createIssue(12, '3、设备巡检记录齐全', 4, '#409eff')
      ]
    },
    {
      id: 'risk',
      name: '消费风险排查',
      issues: [
        createIssue(13, '1、投诉问题闭环处理及时', 4, '#409eff'),
        createIssue(14, '2、高风险菜品有重点监控', 4, '#409eff'),
        createIssue(15, '3、风险预警机制运行正常', 4, '#409eff')
      ]
    }
  ]
}

const initDetailByRoute = async () => {
  const templateId = Number(route.query.templateId || 0)
  const id = Number(route.query.id || 0)
  selectedTaskId.value = id || null
  detailTaskStatus.value = ''
  // 每次进入/切换详情页前先清空，避免旧数据残留导致大项无法切换
  detailSections.value = []
  selectedSectionId.value = ''
  detailFormType.value = ''

  // ── Picker mode: no query params → load template list for user to choose ──
  if (!templateId && !id) {
    await loadTemplateCards()
    return
  }
  if (templateId && !id) {
    detailTaskStatus.value = 'DRAFT'
    const today = new Date()
    detailDate.value = `${today.getFullYear()}.${today.getMonth() + 1}.${today.getDate()}`
    detailSections.value = []
    try {
      const userStore = (await import('@/store/user')).useUserStore()
      detailSubmitter.value = userStore.userInfo?.nickname || userStore.userInfo?.username || '当前用户'
      await loadCanteens()
      const res: any = await getWeeklyTemplateDetail(templateId)
      const tpl = res?.data
      if (tpl) {
        detailRecordTitle.value = `${tpl.template_name || tpl.name || ''}周排查管控记录`
        // Capture canteen IDs from template (set during editing)
        const nodeIds: number[] = Array.isArray(tpl.target_node_ids) ? tpl.target_node_ids.map(Number).filter(Boolean) : []
        const nodeNames: Record<number, string> = tpl.target_node_names || {}
        detailTemplateCanteenIds.value = nodeIds
        if (nodeIds.length) {
          detailTemplateCanteenName.value = nodeIds.map((id) => nodeNames[id] || `食堂#${id}`).join('、')
        } else {
          detailTemplateCanteenName.value = ''
        }
        detailFormType.value = String(tpl.form_type || '')
        detailSections.value = (tpl.major_items || []).map((major: any, mi: number) => ({  
          id: `major-${mi}`,
          name: String(major.title || `第${mi + 1}大项`),
          issues: (major.minor_items || []).map((minor: any, ii: number) => ({
            id: minor.item_id || ii,
            resultId: null,
            title: String(minor.content || `检查项${ii + 1}`),
            fullScore: Number(minor.total_score) || 0,
            score: Number(minor.total_score) || 0,
            auditScore: Number(minor.total_score) || 0,
            scoringOptions: Array.isArray(minor.scoring_options) ? minor.scoring_options.map(Number) : [],
            description: '',
            rectifyDesc: '',
            tagColor: minor.issue_type === '红线' ? '#f5222d' : minor.issue_type === '黄线' ? '#d4d600' : '#409eff',
            inspectionPhotos: [],
            rectificationPhotos: [],
            decision: '' as '' | 'pass' | 'reject',
            rejectReason: ''
          }))
        }))
        selectedSectionId.value = detailSections.value[0]?.id || ''
      }
    } catch {
      ElMessage.error('加载模板失败')
    }
    return
  }

  // ── Task mode: load existing task by id ──
  if (id) {
    const matched = allRows.value.find((item) => item.id === id)
    if (matched) {
      detailRecordTitle.value = `${matched.submitCanteen}周排查管控记录`
      detailDate.value = matched.submitDate.replace(/-/g, '.')
      detailSubmitter.value = matched.submitter
    }
    try {
      const res: any = await getWeeklyTaskDetail(id)
      const data = res?.data
      const info = data?.task_info
      if (info) {
        const canteenName = info.canteen_name || detailRecordTitle.value
        detailRecordTitle.value = `${canteenName}周排查管控记录`
        detailTaskStatus.value = String(info.status || '')
        // For PENDING tasks, submitter = current logged-in admin (dispatcher)
        if (info.status === 'PENDING') {
          const userStore = (await import('@/store/user')).useUserStore()
          detailSubmitter.value = userStore.userInfo?.nickname || userStore.userInfo?.username || info.inspector_name || '-'
        } else {
          detailSubmitter.value = info.inspector_name || detailSubmitter.value
        }
        if (info.submission_date) {
          detailDate.value = String(info.submission_date).slice(0, 10).replace(/-/g, '.')
        } else {
          // Use today's date for PENDING tasks
          const today = new Date()
          detailDate.value = `${today.getFullYear()}.${today.getMonth() + 1}.${today.getDate()}`
        }
      }
      const snapshot = data?.form_snapshot
      const majorItems = snapshot?.major_items
      if (Array.isArray(majorItems) && majorItems.length) {
        detailFormType.value = String(snapshot?.form_type || '')
        detailSections.value = majorItems.map((major: any, mi: number) => ({
          id: `major-${mi}`,
          name: String(major.title || major.name || `第${mi + 1}项`),
          issues: (major.minor_items || []).map((minor: any, ii: number) => ({
            id: minor.item_id || ii,
            resultId: minor.result_id != null ? Number(minor.result_id) : null,
            title: String(minor.content || `检查项${ii + 1}`),
            fullScore: Number(minor.total_score) || 0,
            score: Number(minor.score_given ?? minor.total_score ?? 0),
            auditScore: Number(minor.score_given ?? minor.total_score ?? 0),
            scoringOptions: Array.isArray(minor.scoring_options) ? minor.scoring_options.map(Number) : [],
            description: String(minor.inspection_description || ''),
            rectifyDesc: String(minor.rectification_description || ''),
            tagColor: minor.issue_type === '红线' ? '#f5222d' : minor.issue_type === '黄线' ? '#d4d600' : '#409eff',
            inspectionPhotos: Array.isArray(minor.inspection_photos) ? minor.inspection_photos.map(String).filter(Boolean) : [],
            rectificationPhotos: Array.isArray(minor.rectification_photos) ? minor.rectification_photos.map(String).filter(Boolean) : [],
            decision: '' as '' | 'pass' | 'reject',
            rejectReason: ''
          }))
        }))
        selectedSectionId.value = detailSections.value[0]?.id || ''
        return
      }
    } catch {
      ElMessage.warning('任务详情加载失败')
    }
  }

  detailSections.value = []
  selectedSectionId.value = ''
}

const handleSearch = () => {
  page.value = 1
}

// ==================== Detail view: photo editing (PENDING / DRAFT mode) ====================
const readDetailPhotoAsDataUrl = (file: File): Promise<string> => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(String(reader.result || ''))
  reader.onerror = () => reject(reader.error)
  reader.readAsDataURL(file)
})

const handleDetailInspectionPhotoChange = async (event: Event, issueId: number) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  for (const section of detailSections.value) {
    const issue = section.issues.find((i) => i.id === issueId)
    if (issue) {
      if (issue.inspectionPhotos.length >= 3) {
        ElMessage.warning('每项最多上传3张图片')
        target.value = ''
        return
      }
      const photo = await readDetailPhotoAsDataUrl(file)
      issue.inspectionPhotos.push(photo)
      break
    }
  }
  target.value = ''
}

const removeDetailInspectionPhoto = (issueId: number, photoIndex: number) => {
  for (const section of detailSections.value) {
    const issue = section.issues.find((i) => i.id === issueId)
    if (issue) {
      issue.inspectionPhotos.splice(photoIndex, 1)
      return
    }
  }
}

// ==================== Dispatch from detail (draft mode) ====================
const confirmDispatchFromDetail = async () => {
  const templateId = Number(route.query.templateId || 0)
  if (!templateId) return
  if (!dispatchDetailForm.businessDate) {
    ElMessage.warning('请选择检查日期')
    return
  }
  const canteenIds = detailTemplateCanteenIds.value
  if (!canteenIds.length) {
    ElMessage.warning('该检查表未关联食堂，请先在编辑页面为检查表选择食堂')
    return
  }
  const formSnapshot = {
    major_items: detailSections.value.map((section, si) => ({
      item_id: section.id,
      title: section.name,
      sort_order: si,
      minor_items: section.issues.map((issue) => ({
        item_id: issue.id,
        content: issue.title,
        issue_type: issue.tagColor === '#f5222d' ? '红线' : issue.tagColor === '#d4d600' ? '黄线' : '蓝线',
        total_score: issue.fullScore,
        scoring_options: issue.scoringOptions,
        score_given: issue.score,
        sort_order: 0,
        inspection_description: issue.description,
        inspection_photos: issue.inspectionPhotos
      }))
    }))
  }
  dispatchDetailSubmitting.value = true
  try {
    const res: any = await dispatchWeeklyTemplate({
      template_id: templateId,
      business_date: dispatchDetailForm.businessDate,
      canteen_ids: canteenIds,
      form_snapshot: formSnapshot
    })
    const created: number[] = res?.data?.created ?? []
    const skipped: number[] = res?.data?.skipped ?? []
    ElMessage.success(`下发成功：新建 ${created.length} 个任务，跳过 ${skipped.length} 个（已存在）`)
    if (created.length === 1) {
      router.replace({ name: 'WeeklyDetail', query: { id: String(created[0]) } })
    } else {
      router.push({ name: 'WeeklyRecords' })
    }
  } catch {
    ElMessage.error('下发失败，请重试')
  } finally {
    dispatchDetailSubmitting.value = false
  }
}

// ==================== Save pre-fill info for PENDING tasks ====================
const savePrefillSubmitting = ref(false)

const savePrefillInfo = async () => {
  const taskId = Number(route.query.id || 0)
  if (!taskId || detailTaskStatus.value !== 'PENDING') return
  const formSnapshot = {
    major_items: detailSections.value.map((section, si) => ({
      item_id: section.id,
      title: section.name,
      sort_order: si,
      minor_items: section.issues.map((issue) => ({
        item_id: issue.id,
        content: issue.title,
        issue_type: issue.tagColor === '#f5222d' ? '红线' : issue.tagColor === '#d4d600' ? '黄线' : '蓝线',
        total_score: issue.fullScore,
        scoring_options: issue.scoringOptions,
        score_given: issue.score,
        sort_order: 0,
        inspection_description: issue.description,
        inspection_photos: issue.inspectionPhotos
      }))
    }))
  }
  savePrefillSubmitting.value = true
  try {
    await updateWeeklyTaskSnapshot(taskId, formSnapshot)
    ElMessage.success('预填信息已保存，执行端可见')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    savePrefillSubmitting.value = false
  }
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

const refreshCurrentViewData = async () => {
  if (isCreateView.value) {
    await initCreateView()
    return
  }
  if (isChecklistView.value) {
    await loadTemplateCards()
    return
  }
  if (isDetailView.value) {
    await initDetailByRoute()
    return
  }
  await loadCanteens()
  await loadRows()
}

const handleViewRecord = (row: WeeklyRow) => {
  router.push({ name: 'WeeklyDetail', query: { id: String(row.id) } })
}

const handleCancel = async (row: WeeklyRow) => {
  try {
    await ElMessageBox.confirm(`确定删除记录「${row.form}」吗？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteWeeklyTask(row.id)
    ElMessage.success('记录已删除')
    await loadRows()
  } catch {
    ElMessage.error('删除失败，请重试')
  }
}

const handleScoreCancel = async (row: WeeklyScoreRow) => {
  try {
    await ElMessageBox.confirm(`确定删除记录「${row.form}」吗？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteWeeklyTask(row.id)
    ElMessage.success('记录已删除')
    await loadRows()
  } catch {
    ElMessage.error('删除失败，请重试')
  }
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
  a.download = '周排查分数统计.csv'
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

  // Collect items with custom scores
  const allIssues = detailSections.value.flatMap((s) => s.issues)
  const itemScores = allIssues
    .filter((issue) => issue.resultId != null)
    .map((issue) => ({ result_id: issue.resultId as number, score: issue.auditScore }))

  try {
    const userStore = (await import('@/store/user')).useUserStore()
    const auditorId = String(userStore.userInfo?.id || '')
    await auditWeeklyTask(
      selectedTaskId.value,
      {
        auditor_id: auditorId,
        action: hasReject ? 'REJECT' : 'PASS',
        opinion: opinion || undefined,
        item_scores: itemScores.length ? itemScores : undefined
      },
      buildIdempotencyKey()
    )
    ElMessage.success('周排查审核提交成功')
    router.push({ name: 'WeeklyRecords' })
  } catch {
    ElMessage.error('周排查审核提交失败，请稍后重试')
  }
}

const handleCoverUsers = (item: WeeklyTemplateCard) => {
  ElMessage.info(`模板 #${item.id} 覆盖人员功能待后端接口支持`)
}

const handleCoverCanteens = (item: WeeklyTemplateCard) => {
  ElMessage.info(`模板 #${item.id} 覆盖食堂功能待后端接口支持`)
}

// ==================== 下发逻辑 ====================

const handleDispatch = (item: WeeklyTemplateCard) => {
  router.push({ name: 'WeeklyDetail', query: { templateId: String(item.id) } })
}

const handleEditTemplate = (item: WeeklyTemplateCard) => {
  if (item.isFallback) {
    // fallback 模板没有真实后端 ID，直接进新建页并预填名称
    router.push({ name: 'WeeklyCreate', query: { templateName: item.name } })
  } else {
    router.push({ name: 'WeeklyCreate', query: { templateId: String(item.id) } })
  }
}

const handleDeleteTemplate = async (item: WeeklyTemplateCard) => {
  try {
    await ElMessageBox.confirm(`确定删除模板「${item.name}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    await deleteWeeklyTemplate(item.id)
    ElMessage.success('模板已删除')
    await loadTemplateCards()
  } catch {
    // cancelled
  }
}

const handleSetupScore = async (sectionId: string, itemId: string) => {
  const section = createSections.value.find((s) => s.id === sectionId)
  const item = section?.items.find((it) => it.id === itemId)
  if (!item) return

  const currentOptions = item.scoringOptions.length ? item.scoringOptions.join(',') : ''
  let inputVal: string | null = null
  try {
    const { value } = await ElMessageBox.prompt(
      '请输入打分选项，用英文逗号分隔（例如: 1,2,3,4）',
      '设置打分项',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: currentOptions,
        inputPlaceholder: '例如: 1,2,3,4,5',
        inputValidator: (val: string) => {
          if (!val || !val.trim()) return true // 允许清空
          const parts = val.split(',').map((p) => p.trim()).filter((p) => p !== '')
          if (parts.length < 2) return '至少需要 2 个打分选项'
          if (parts.length > 10) return '打分选项最多 10 个'
          for (const p of parts) {
            if (!/^\d+$/.test(p)) return '请输入非负整数，用英文逗号分隔'
            const n = Number(p)
            if (n > 100) return '单个分值不能超过 100'
          }
          const nums = parts.map(Number)
          const unique = new Set(nums)
          if (unique.size !== nums.length) return '分值不能有重复'
          const sorted = [...nums].sort((a, b) => a - b)
          if (sorted.join(',') !== nums.join(',')) return '请按从小到大的顺序输入'
          return true
        }
      }
    )
    inputVal = String(value || '').trim()
  } catch {
    return
  }

  if (!inputVal) {
    item.scoringOptions = []
    ElMessage.success('已清除打分项')
    return
  }

  const options = inputVal.split(',').map((p) => Number(p.trim())).filter((n) => !Number.isNaN(n))
  item.scoringOptions = options
  // 自动将总分设为最大分（如果未手动设置）
  if (item.totalScore === '--' || item.totalScore === '') {
    item.totalScore = String(Math.max(...options))
  }
  ElMessage.success(`已设置 ${options.length} 个打分选项`)
}

const promptText = async (title: string, placeholder: string, defaultValue = ''): Promise<string | null> => {
  try {
    const { value } = await ElMessageBox.prompt('请输入内容', title, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: defaultValue,
      inputPlaceholder: placeholder,
      inputValidator: (val: string) => !!val.trim() || '内容不能为空'
    })
    return String(value || '').trim()
  } catch {
    return null
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
  await deleteMajorSection(selectedId)
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
  if (!val || val === '--') return
  if (!/^\d+(\.\d{0,1})?$/.test(val)) {
    ElMessage.warning('总分请输入数字，最多一位小数')
    item.totalScore = '--'
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
      ElMessage.warning(`"${section.name}" 中存在未填写内容的小项`)
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
          ElMessage.warning(`「${item.text}」未设置打分项，请点击"设置打分项"进行设置`)
          return
        }
      }
    }
  }

  if (createForm.tableType === 'SCORE') {
    for (const section of createSections.value) {
      for (const item of section.items) {
        const val = item.totalScore.trim()
        if (val !== '--' && val !== '' && !/^\d+(\.\d{0,1})?$/.test(val)) {
          ElMessage.warning(`"${item.text}" 的总分格式不正确，最多一位小数`)
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
  try {
    let resolvedId = templateId
    // 未通过编辑入口（无 templateId）时，查找同名模板做覆盖
    if (!resolvedId) {
      const listRes: any = await getWeeklyTemplateList({ page: 1, page_size: 100 })
      const sameNameItem = (listRes?.data?.list || []).find(
        (t: any) => String(t.template_name || t.name || '').trim() === createForm.name.trim()
      )
      if (sameNameItem) {
        resolvedId = Number(sameNameItem.id)
      }
    }

    const payload = {
      template_name: createForm.name,
      executor_role: createForm.executorRole || undefined,
      approver_role: createForm.approverRole || undefined,
      form_type: createForm.tableType || undefined,
      start_time: createForm.startTime || undefined,
      end_time: createForm.endTime || undefined,
      target_node_ids: targetNodeIds,
      major_items: majorItems
    }
    if (resolvedId) {
      await updateWeeklyTemplate(resolvedId, payload)
      ElMessage.success('周排查检查表更新成功')
    } else {
      await createWeeklyTemplate(payload)
      ElMessage.success('周排查检查表创建成功')
    }
    router.push({ name: 'WeeklyChecklist' })
  } catch {
    ElMessage.error('保存失败，请稍后重试')
  }
}

const statusClass = (status: WeeklyStatus) => {
  if (status === '待整改') return 'status-pending'
  if (status === '待审核') return 'status-submitted'
  if (status === '已完成') return 'status-success'
  return 'status-pending'
}

onMounted(async () => {
  await refreshCurrentViewData()
})

watch(
  () => [route.name, route.query.id],
  async () => {
    await refreshCurrentViewData()
  }
)
</script>

<style scoped>
.checklist-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 10px;
  background: #f7f7f7;
  border-bottom: 1px solid #e5e7ef;
}

.checklist-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.new-template-btn {
  background: #4a8ded;
  border-color: #4a8ded;
  height: 32px;
  padding: 0 16px;
  font-size: 14px;
}

.checklist-view {
  padding: 0;
  background: #eef0f8;
  min-height: calc(100vh - 84px);
}

.checklist-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.template-list {
  padding: 20px 10px;
}

.template-card {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  background: #f5f5f5;
  margin-bottom: 20px;
  min-height: 101px;
  border: 1px solid #ededed;
  overflow: hidden;
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

.card-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding-right: 16px;
  flex-shrink: 0;
}

.outline-btn {
  width: 88px;
  height: 36px;
  border-color: #4a8ded;
  color: #4a8ded;
  font-size: 14px;
}

.dispatch-btn {
  width: 88px;
  height: 36px;
  font-size: 14px;
  color: #fff !important;
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

.mode-toggle-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-label {
  font-size: 14px;
  color: #606266;
}

.mode-inline {
  margin-left: 6px;
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
  white-space: nowrap;
  line-height: 1;
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
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 2px;
}

.section-name-text {
  font-size: 14px;
  color: #303133;
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

.item-text-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.item-text-label {
  font-size: 14px;
  color: #303133;
}

.item-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
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

.score-input {
  width: 100px;
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
  font-size: 14px;
  color: #303133;
}

.actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 10px 0 0;
  gap: 12px;
}

.actions-left,
.actions-right {
  display: flex;
  align-items: center;
}

.add-major-btn {
  min-width: 100px;
  height: 30px;
}

.save-create-btn {
  min-width: 100px;
  height: 30px;
}

.detail-view {
  background: #E5E7EB;
  min-height: calc(100vh - 84px);
  padding: 20px;
}

/* Panel container */
.panel-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

/* Page header card */
.page-header-card {
  background: #fff;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #E5E7EB;
  margin-bottom: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px;
}

.page-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 14px;
  color: #666;
}

.meta-item {
  color: #606266;
}

/* ── Main layout ─────────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 0;
  border-bottom: 1px solid #E5E7EB;
}

/* ── Sidebar card ────────────────────────────────── */
.sidebar-card {
  background: #F9FAFB;
  border-right: 1px solid #E5E7EB;
  overflow: hidden;
  align-self: stretch;
}

.sidebar-title {
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 700;
  color: #6B7280;
  border-bottom: 1px solid #E5E7EB;
  background: #F3F4F6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-item {
  padding: 11px 16px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  border-bottom: 1px solid #EAECEF;
  transition: all 0.15s;
}

.sidebar-item:last-child {
  border-bottom: none;
}

.sidebar-item:hover {
  background: #EFF6FF;
  color: #2563EB;
}

.sidebar-item.active {
  background: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
  border-left: 3px solid #2563EB;
  padding-left: 13px;
}

/* ── Content area ────────────────────────────────── */
.content-area {
  background: #F3F4F6;
  padding: 16px;
  min-width: 0;
}

.col-header-row {
  display: flex;
  margin-bottom: 8px;
  gap: 8px;
}

.col-header-cell {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #E5E7EB;
}

.col-header-problem {
  flex: 0 0 calc(55% - 8px);
}

.col-header-rectify {
  flex: 1;
}

.col-header-audit {
  flex: 0 0 180px;
}

/* ── Item cards ──────────────────────────────────── */
.item-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  border: 1px solid #E5E7EB;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.item-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 3px;
}

.item-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  line-height: 1.5;
}

.score-tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.card-body {
  padding: 14px 16px;
}

.card-body-split {
  display: flex;
  padding: 0;
}

.problem-section {
  flex: 0 0 55%;
  padding: 14px 16px;
  border-right: 1px solid #f0f2f5;
}

.problem-section.no-border {
  border-right: none;
  flex: 1;
}

.rectify-section {
  flex: 1;
  padding: 14px 16px;
  border-right: 1px solid #f0f2f5;
}

.audit-section {
  flex: 0 0 180px;
  padding: 14px 16px;
}

.section-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  margin-bottom: 6px;
}

.section-text {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin: 0 0 10px;
}

/* ── Photos ──────────────────────────────────────── */
.photo-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.photo-thumb {
  width: 72px;
  height: 54px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  cursor: pointer;
}

.photo-box {
  position: relative;
  width: 72px;
  height: 54px;
}

.rm-photo {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

.upload-trigger {
  cursor: pointer;
}

.upload-input {
  display: none;
}

.upload-placeholder {
  width: 72px;
  height: 54px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  background: #fafafa;
}

/* ── Audit column ────────────────────────────────── */
.audit-score-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  padding: 6px 10px;
  background: #f5f7fa;
  border-radius: 6px;
}

.audit-score-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

.audit-score-max {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
}

.action-btns {
  display: flex;
  flex-direction: column;
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

/* ── Editable score fields ───────────────────────── */
.issue-edit-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.issue-score-field {
  flex-direction: row;
  align-items: center;
}

.score-option-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.score-opt-btn {
  padding: 3px 14px;
  border: 1px solid #d9e2f5;
  border-radius: 4px;
  background: #f5f7fa;
  color: #303133;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.score-opt-btn:hover {
  border-color: #4a8ded;
  color: #4a8ded;
}

.score-opt-btn.active {
  background: #4a8ded;
  border-color: #4a8ded;
  color: #fff;
}

.score-max-hint {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
  margin-left: 4px;
}

/* ── Footer bar ──────────────────────────────────── */
.footer-bar {
  margin-top: 0;
  padding: 14px 24px;
  background: #fff;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

/* Dispatch bar inside panel */
.detail-dispatch-bar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background: #EFF6FF;
  border-top: 1px solid #BFDBFE;
  border-bottom: 1px solid #BFDBFE;
}

.dispatch-bar-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-right: 8px;
}

.dispatch-canteen-info {
  font-size: 14px;
  color: #303133;
  margin-left: 12px;
  padding: 0 12px;
  height: 32px;
  line-height: 32px;
  background: #f0f7ff;
  border-radius: 4px;
  border: 1px solid #d0e8ff;
  display: inline-block;
}

.detail-status-tip {
  font-size: 14px;
}

.detail-status-tip.completed {
  color: #67c23a;
}

.detail-status-tip.pending {
  color: #909399;
}

.detail-status-tip.rejected {
  color: #f56c6c;
}

/* Template picker styles */
.picker-card-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 20px 0;
  min-height: 120px;
}

.picker-card {
  width: 220px;
  padding: 18px 20px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
  background: #fff;
}

.picker-card:hover {
  border-color: #4a8ded;
  box-shadow: 0 2px 12px rgba(74, 141, 237, 0.18);
}

.picker-card-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  word-break: break-all;
}

.picker-card-meta {
  font-size: 13px;
  color: #909399;
}

.picker-empty {
  font-size: 14px;
  color: #909399;
  padding: 32px 0;
}

.record-view {
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  padding: 20px;
  background-color: #fff;
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

.no-photo-text {
  color: #c0c4cc;
  font-size: 13px;
}

.status-pending {
  color: #f56c6c;
}

.status-submitted {
  color: #e6a23c;
}

.status-success {
  color: #67c23a;
}
</style>
