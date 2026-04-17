from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.modules.inspection.models import CompletionMethod


class DailyControlSubmitResultItem(BaseModel):
    item_id: int
    is_qualified: bool
    description: Optional[str] = None
    photos: Optional[List[str]] = None


class DailyControlSubmitRequest(BaseModel):
    submitter_id: str
    actual_start_time: datetime
    results: List[DailyControlSubmitResultItem]


class RectificationItem(BaseModel):
    result_id: int
    description: Optional[str] = None
    photos: Optional[List[str]] = None


class DailyRectifyRequest(BaseModel):
    rectifier_id: str
    feedback_per_item: List[RectificationItem]


class WeeklyInspectionSubmitResultItem(BaseModel):
    item_id: int
    score_given: float
    description: Optional[str] = None
    photos: Optional[List[str]] = None
    rectification_description: Optional[str] = None
    rectification_photos: Optional[List[str]] = None


class WeeklyInspectionSubmitRequest(BaseModel):
    inspector_id: str
    actual_start_time: datetime
    results: List[WeeklyInspectionSubmitResultItem]


class WeeklyRectifyRequest(BaseModel):
    rectifier_id: str
    feedback_per_item: List[RectificationItem]


class WeeklyDispatchRequest(BaseModel):
    template_id: int
    business_date: str  # YYYY-MM-DD
    canteen_ids: List[int]  # 要下发的食堂 org_id 列表
    form_snapshot: Optional[dict] = None  # 管理员预填写的表单快照，若提供则覆盖自动生成的快照


class WeeklySnapshotUpdateRequest(BaseModel):
    form_snapshot: dict  # 更新 PENDING 任务的预填快照

class DailyTemplateItemRequest(BaseModel):
    sort_order: int = 0
    content: str
    completion_method: Optional[CompletionMethod] = None


class DailyTemplateRequest(BaseModel):
    template_name: str
    executor_role: Optional[str] = None
    approver_role: Optional[str] = None
    target_node_ids: List[int]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    items: List[DailyTemplateItemRequest]


class WeeklyTemplateMinorItemRequest(BaseModel):
    sort_order: int = 0
    content: str
    issue_type: Optional[str] = None
    total_score: Optional[float] = None
    scoring_options: Optional[List[float]] = None


class WeeklyTemplateMajorItemRequest(BaseModel):
    sort_order: int = 0
    title: str
    minor_items: List[WeeklyTemplateMinorItemRequest]


class WeeklyTemplateRequest(BaseModel):
    template_name: str
    executor_role: Optional[str] = None
    approver_role: Optional[str] = None
    target_node_ids: List[int]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    form_type: Optional[str] = None
    major_items: List[WeeklyTemplateMajorItemRequest]


class VideoTemplateMinorItemRequest(BaseModel):
    sort_order: int = 0
    content: str
    issue_type: Optional[str] = None
    total_score: Optional[float] = None
    scoring_options: Optional[List[float]] = None
    associated_camera_ids: Optional[List[str]] = None


class VideoTemplateMajorItemRequest(BaseModel):
    sort_order: int = 0
    title: str
    minor_items: List[VideoTemplateMinorItemRequest]


class VideoTemplateRequest(BaseModel):
    template_name: str
    executor_role: Optional[str] = None
    approver_role: Optional[str] = None
    target_node_ids: List[int]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    form_type: Optional[str] = None
    major_items: List[VideoTemplateMajorItemRequest]


class TemplateStatusRequest(BaseModel):
    is_active: bool

# ==================== 月调度报告请求 Schema ====================

class MonthlyReportPreviewRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    data_sources: List[int]

class MonthlyReportExportRequest(BaseModel):
    start_date: str
    end_date: str
    data_sources: List[int]
    export_format: str = "pdf"

class MonthlyReportUploadRequest(BaseModel):
    title: str
    canteen_id: int
    file_key: Optional[str] = None
    remark: Optional[str] = None

class MonthlyReportFileUploadResponse(BaseModel):
    file_key: str
    file_url: str
    public_url: str
    expires_at: str

class MonthlyReportDeleteResponse(BaseModel):
    id: int

# ==================== 月调度报告响应 Schema ====================

class CanteenSummary(BaseModel):
    canteen_id: int
    canteen_name: str
    task_count: int
    issue_count: int
    total_score: Optional[float] = None
    rectification_rate: float = 0.0

class IssueRankingItem(BaseModel):
    item_id: int
    content: str
    issue_count: int
    canteen_ids: List[int]

class MonthlyReportPreviewResponse(BaseModel):
    period: dict
    canteen_summary: List[CanteenSummary]
    issue_ranking: List[IssueRankingItem]
    rectification_rate: dict
    generated_at: str

# ==================== 联合巡检特有 Schema ====================

class JointSignRequest(BaseModel):
    participant_id: str
    signature: str  # Base64 或 URL
