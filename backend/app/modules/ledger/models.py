# 文件路径：backend/app/modules/ledger/models.py
from datetime import datetime
from typing import List, Optional, Dict, Any

# 注意：这里使用 SQLAlchemy 2.0 的新语法
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, Boolean, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# 1. 引入你发给我的地基文件
from app.db.base import Base
from app.db.mixins import TenantMixin

# 2. 引入刚才定义的常量
from app.modules.ledger.constants import LedgerStatus

# ==========================================
# 表1: 台账模板 (LedgerTemplate)
# 职责：存储 JSON Schema 定义
# ==========================================
class LedgerTemplate(Base, TenantMixin):
    __tablename__ = "biz_ledger_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), comment="模板标题")
    description: Mapped[Optional[str]] = mapped_column(String(255), default=None, comment="模板描述")
    
    # 核心字段：存储 JSON Schema
    # 对应任务文档：ledger_template 存储表单定义
    schema: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="表单Schema定义")
    
    # 版本控制用
    hash: Mapped[Optional[str]] = mapped_column(String(64), comment="Schema哈希值")
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="软删除标记")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# ==========================================
# 表2: SOP 调度任务 (LedgerTask)
# 职责：定义每天何时生成什么表
# ==========================================
class LedgerTask(Base, TenantMixin):
    __tablename__ = "biz_ledger_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="任务名称")
    
    # 关联模板
    template_id: Mapped[int] = mapped_column(ForeignKey("biz_ledger_template.id"), index=True)
    
    # 对应任务文档：存储 SOP 规则
    cron: Mapped[str] = mapped_column(String(50), comment="Cron表达式")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    
    # 派发范围配置（JSON结构，逻辑由Service层处理）
    target_config: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="派发范围配置")
    
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class SOPTask(Base, TenantMixin):
    __tablename__ = "biz_sop_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="SOP任务名称")
    description: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    template_id: Mapped[int] = mapped_column(ForeignKey("biz_ledger_template.id"), index=True)
    cron_expression: Mapped[str] = mapped_column(String(64), comment="Cron 表达式")
    scope: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, comment="派发范围")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

# ==========================================
# 表3: 台账实例 (LedgerInstance)
# 职责：存储具体填报数据，工业级冗余
# ==========================================
class LedgerInstance(Base, TenantMixin):
    __tablename__ = "biz_ledger_instance"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "canteen_id",
            "template_id",
            "create_date",
            name="uq_ledger_instance_daily",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 关联信息
    template_id: Mapped[int] = mapped_column(ForeignKey("biz_ledger_template.id"), index=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("biz_ledger_task.id"), index=True)
    canteen_id: Mapped[int] = mapped_column(Integer, index=True, comment="所属食堂ID")
    
    # 状态机：使用 Enum 约束
    status: Mapped[LedgerStatus] = mapped_column(
        String(20), 
        default=LedgerStatus.PENDING, 
        index=True, 
        comment="状态: PENDING/FILLING/SIGNED/ARCHIVED"
    )

    # =============== 核心红线字段 ===============
    
    # 1. 快照 (Snapshot)
    # 对应文档：ledger_instance 中必须包含 schema_snapshot
    schema_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="生成时的模板快照")
    
    # 2. 内容 (Content)
    # 对应文档：实际填报数据，扁平化结构
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, default={}, comment="填报内容")
    
    # 3. 防篡改 (Hash)
    # 对应文档：签字后生成 security_hash
    security_hash: Mapped[Optional[str]] = mapped_column(String(64), comment="防篡改Hash")
    
    # 补充：签字图片
    signature_image: Mapped[Optional[str]] = mapped_column(String(255), comment="签字图片URL")

    # 时间字段
    create_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="业务日期",
    )
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    submit_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="提交时间")
    
    
# 表4
# 职责：暂存硬件原始数据，供前端自动填充 (对应任务书 3.1 硬件隔离)
# ==========================================
class DeviceBuffer(Base, TenantMixin):
    __tablename__ = "biz_device_buffer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 设备标识 (如 MAC地址或设备序列号)
    device_uid: Mapped[str] = mapped_column(String(64), index=True, comment="设备唯一标识")
    
    # 原始数据 (JSON格式，存体温、晨检结果等)
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="硬件原始数据")
    
    # 数据接收时间
    receive_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # 是否已处理 (防止重复读取)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # 过期时间 (缓冲数据通常保留24小时)
    expire_time: Mapped[datetime] = mapped_column(DateTime, index=True)


class ExportLog(Base):
    """记录报表导出行为，便于审计追踪。"""

    __tablename__ = "export_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    export_date: Mapped[str] = mapped_column(String(10), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    canteen_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    export_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TemplateScope(Base, TenantMixin):
    """模板覆盖范围（人员、食堂维度）。

    用于管理哪些人员和食堂需要填写某个模板。
    """

    __tablename__ = "biz_ledger_template_scope"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("biz_ledger_template.id"),
        index=True,
        comment="关联模板ID",
    )
    user_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="覆盖人员ID列表")
    canteen_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="覆盖食堂ID列表")
    extra_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, default=None, comment="扩展配置"
    )
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    update_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
