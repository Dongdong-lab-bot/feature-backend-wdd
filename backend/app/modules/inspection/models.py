from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.enums import InspectionTaskStatus
from app.db.base import Base
from app.db.mixins import TenantMixin


class InspectionType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    JOINT = "JOINT"
    VIDEO = "VIDEO"


class InspectionFormType(str, Enum):
    SCORE_SELECT = "SCORE_SELECT"
    SCORE_INPUT = "SCORE_INPUT"
    OPTION_CHECK = "OPTION_CHECK"


class CompletionMethod(str, Enum):
    CONFIRM_ONLY = "CONFIRM_ONLY"
    PHOTO_REQUIRED = "PHOTO_REQUIRED"
    INPUT_REQUIRED = "INPUT_REQUIRED"


class IssueType(str, Enum):
    RED_LINE = "RED_LINE"
    YELLOW_LINE = "YELLOW_LINE"
    BLUE_LINE = "BLUE_LINE"


class ItemType(str, Enum):
    GROUP = "GROUP"
    ITEM = "ITEM"


class InspectionTemplate(Base, TenantMixin):
    __tablename__ = "biz_inspection_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    inspection_type: Mapped[InspectionType] = mapped_column(
        String(20), nullable=False, index=True
    )
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    executor_role: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    approver_role: Mapped[Optional[str]] = mapped_column(String(64), default=None)

    form_type: Mapped[Optional[InspectionFormType]] = mapped_column(
        String(32), default=None
    )

    start_time: Mapped[Optional[str]] = mapped_column(String(5), default=None)
    end_time: Mapped[Optional[str]] = mapped_column(String(5), default=None)

    target_node_ids_raw: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, default=None
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    items: Mapped[List["InspectionItem"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["InspectionTask"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class InspectionItem(Base, TenantMixin):
    __tablename__ = "biz_inspection_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    template_id: Mapped[int] = mapped_column(
        ForeignKey("biz_inspection_template.id"), nullable=False, index=True
    )
    parent_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("biz_inspection_item.id"), default=None, index=True
    )

    item_type: Mapped[ItemType] = mapped_column(String(16), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    content: Mapped[str] = mapped_column(String(255), nullable=False)

    completion_method: Mapped[Optional[CompletionMethod]] = mapped_column(
        String(32), default=None
    )

    issue_type: Mapped[Optional[IssueType]] = mapped_column(String(16), default=None)
    total_score: Mapped[Optional[Float]] = mapped_column(Float, default=None)
    scoring_options: Mapped[Optional[List[float]]] = mapped_column(
        JSON, default=None
    )
    associated_camera_ids: Mapped[Optional[List[str]]] = mapped_column(
        JSON, default=None
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    template: Mapped["InspectionTemplate"] = relationship(back_populates="items")
    parent: Mapped[Optional["InspectionItem"]] = relationship(
        remote_side="InspectionItem.id"
    )
    children: Mapped[List["InspectionItem"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )

    results: Mapped[List["InspectionResult"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class InspectionTask(Base, TenantMixin):
    __tablename__ = "biz_inspection_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    inspection_type: Mapped[InspectionType] = mapped_column(
        String(20), nullable=False, index=True
    )

    template_id: Mapped[int] = mapped_column(
        ForeignKey("biz_inspection_template.id"), nullable=False, index=True
    )

    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    canteen_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    canteen_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)

    executor_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    executor_name_snapshot: Mapped[Optional[str]] = mapped_column(
        String(100), default=None
    )

    inspector_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)

    approver_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    approver_name_snapshot: Mapped[Optional[str]] = mapped_column(
        String(100), default=None
    )

    status: Mapped[InspectionTaskStatus] = mapped_column(
        String(20), default=InspectionTaskStatus.PENDING, index=True
    )

    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )
    submission_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )
    rectified_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )
    completed_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )

    total_items: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    finished_items: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    total_score: Mapped[Optional[Float]] = mapped_column(Float, default=None)
    red_line_issues: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    form_snapshot: Mapped[Optional[Union[Dict[str, Any], List[Any]]]] = mapped_column(
        JSON, default=None
    )

    joint_participant_ids: Mapped[Optional[List[str]]] = mapped_column(
        JSON, default=None
    )
    joint_signatures: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, default=None
    )

    last_audit_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    last_audit_opinion: Mapped[Optional[str]] = mapped_column(
        Text, default=None
    )
    last_audit_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )

    audit_logs: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, default=None
    )

    last_idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(64), default=None
    )
    last_idempotency_action: Mapped[Optional[str]] = mapped_column(
        String(32), default=None
    )

    version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    template: Mapped["InspectionTemplate"] = relationship(back_populates="tasks")
    results: Mapped[List["InspectionResult"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    joint_participants: Mapped[List["JointInspectionParticipant"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

class JointInspectionParticipant(Base, TenantMixin):
    __tablename__ = "biz_joint_inspection_participant"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    task_id: Mapped[int] = mapped_column(
        ForeignKey("biz_inspection_task.id"), nullable=False, index=True
    )
    
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    role: Mapped[str] = mapped_column(String(32), default="participant")
    
    signature_url: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    task: Mapped["InspectionTask"] = relationship(back_populates="joint_participants")



class InspectionResult(Base, TenantMixin):
    __tablename__ = "biz_inspection_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("biz_inspection_task.id"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("biz_inspection_item.id"), nullable=False, index=True
    )

    inspection_type: Mapped[InspectionType] = mapped_column(
        String(20), nullable=False, index=True
    )

    is_qualified: Mapped[Optional[bool]] = mapped_column(Boolean, default=None)
    inspection_description: Mapped[Optional[str]] = mapped_column(
        Text, default=None
    )
    inspection_photos: Mapped[Optional[List[str]]] = mapped_column(
        JSON, default=None
    )

    score_given: Mapped[Optional[Float]] = mapped_column(Float, default=None)

    rectification_description: Mapped[Optional[str]] = mapped_column(
        Text, default=None
    )
    rectification_photos: Mapped[Optional[List[str]]] = mapped_column(
        JSON, default=None
    )
    rectified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )

    has_issue: Mapped[Optional[bool]] = mapped_column(Boolean, default=None)
    is_red_line_triggered: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    task: Mapped["InspectionTask"] = relationship(back_populates="results")
    item: Mapped["InspectionItem"] = relationship(back_populates="results")


class MonthlyReport(Base, TenantMixin):
    __tablename__ = "biz_inspection_monthly_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    reporter_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reporter_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)

    report_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, default=func.now(), server_default=func.now()
    )

    canteen_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    canteen_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)

    source_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=None)

    system_report_markdown: Mapped[Optional[str]] = mapped_column(Text, default=None)
    system_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )

    offline_report_url: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    offline_report_uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None
    )

    remark: Mapped[Optional[str]] = mapped_column(Text, default=None)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )