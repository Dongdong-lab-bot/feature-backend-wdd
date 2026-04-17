/** 模板管理相关 API（电子台账中心）。

该文件按智慧食安平台通用规范实现。
*/

import { get, post, put } from '@/utils/request'

/** 通用 API 响应结构 */
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

/** 模板覆盖范围数据结构 */
export interface TemplateScopeData {
  users?: number[]
  canteens?: number[]
}

/** 模板覆盖范围响应 */
export interface TemplateScopeResponse {
  template_id: number
  description?: string
  users: number[]
  canteens: number[]
  extra_config?: Record<string, any>
}

/** 模板完整更新请求参数 */
export interface TemplateUpdateParams {
  title?: string
  description?: string
  scope?: TemplateScopeData
  extra_config?: string
}

/** 模板详情响应 */
export interface TemplateDetail {
  id: number
  title: string
  description?: string
  schema?: Record<string, any>
  scope?: TemplateScopeData
  extra_config?: Record<string, any>
  create_time?: string
}

/** 批量更新覆盖范围响应 */
export interface BatchScopeResponse {
  template_id: number
  updated_count: number
  scope: TemplateScopeData
}

/** 更新模板（编辑页真实保存）。
 * PUT /ledger/templates/{id}/full
 */
export function updateTemplateFull(
  id: number,
  data: TemplateUpdateParams
): Promise<ApiResponse<TemplateDetail>> {
  return put<ApiResponse<TemplateDetail>>(`/ledger/templates/${id}/full`, data)
}

/** 获取模板覆盖范围（人员、食堂）。
 * GET /ledger/templates/{id}/scope
 */
export function getTemplateScope(
  id: number
): Promise<ApiResponse<TemplateScopeResponse>> {
  return get<ApiResponse<TemplateScopeResponse>>(`/ledger/templates/${id}/scope`)
}

/** 批量覆盖人员。
 * POST /ledger/templates/{id}/scope/users/batch
 */
export function batchUpdateScopeUsers(
  id: number,
  userIds: number[]
): Promise<ApiResponse<BatchScopeResponse>> {
  return post<ApiResponse<BatchScopeResponse>>(
    `/ledger/templates/${id}/scope/users/batch`,
    { ids: userIds }
  )
}

/** 批量覆盖食堂。
 * POST /ledger/templates/{id}/scope/canteens/batch
 */
export function batchUpdateScopeCanteens(
  id: number,
  canteenIds: number[]
): Promise<ApiResponse<BatchScopeResponse>> {
  return post<ApiResponse<BatchScopeResponse>>(
    `/ledger/templates/${id}/scope/canteens/batch`,
    { ids: canteenIds }
  )
}
