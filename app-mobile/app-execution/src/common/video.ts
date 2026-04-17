import { apiRequest } from './request'

export interface CameraTreeNode {
  id: number | string
  name: string
  type: string
  parentId?: number | string | null
  children?: CameraTreeNode[]
}

/**
 * 获取食堂/区域下摄像头树：GET /video/cameras/tree
 */
export function fetchCameraTree() {
  return apiRequest<{ tree: CameraTreeNode[] }>('/video/cameras/tree', {
    method: 'GET'
  })
}

export interface PlayParamsRequest {
  cameraId: string
  action: 'preview' | 'playback'
  begin?: string
  end?: string
}

/**
 * 获取播放参数（实时/回放）：POST /api/v1/video/hikvision/play-params
 * action: preview | playback
 * begin/end: 回放时必填，预览可不传（ISO8601 字符串）
 */
export function getPlayParams(params: PlayParamsRequest) {
  return apiRequest<any>('/api/v1/video/hikvision/play-params', {
    method: 'POST',
    data: {
      cameraId: params.cameraId,
      action: params.action,
      begin: params.begin,
      end: params.end
    }
  })
}

/**
 * 抓拍监控画面：POST /video-inspections/cameras/{camera_id}/capture
 */
export function captureSnapshot(
  cameraId: string,
  imageBase64: string,
  timestamp?: string
) {
  return apiRequest<{ photo_url: string }>(`/video-inspections/cameras/${cameraId}/capture`, {
    method: 'POST',
    data: {
      image_base64: imageBase64,
      timestamp
    }
  })
}