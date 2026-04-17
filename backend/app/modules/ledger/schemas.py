from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.ledger.constants import LedgerStatus


class BaseSchemaModel(BaseModel):
    """统一的 BaseModel，允许使用 schema 等关键字段名。"""

    model_config = ConfigDict(protected_namespaces=())


class LedgerFormField(BaseSchemaModel):
    field_id: str = Field(..., description="字段唯一标识")
    type: str = Field(..., description="字段类型，例如 string/number/boolean/array")
    label: Optional[str] = Field(default=None, description="显示名称")
    required: bool = Field(default=False, description="是否必填")
    placeholder: Optional[str] = None
    regex: Optional[str] = None
    min_value: Optional[float] = Field(default=None, alias="min")
    max_value: Optional[float] = Field(default=None, alias="max")
    min_length: Optional[int] = Field(default=None, alias="minLength")
    max_length: Optional[int] = Field(default=None, alias="maxLength")
    auto_fill: Optional[str] = Field(default=None, alias="auto_fill")
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class LedgerFormSchema(BaseSchemaModel):
    version: str = Field(default="v1", description="Schema 版本号")
    fields: List[LedgerFormField]

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, value: List[LedgerFormField]) -> List[LedgerFormField]:
        if value is None:
            raise ValueError("schema.fields must be provided")
        seen = set()
        for field in value:
            if field.field_id in seen:
                raise ValueError(f"Duplicate field_id '{field.field_id}' detected")
            seen.add(field.field_id)
        return value


# 旧版 API 契约 -------------------------------------------------------------
class SubmitRequest(BaseSchemaModel):
    content: dict


class LedgerResponse(BaseSchemaModel):
    id: int
    content: dict
    schema_snapshot: dict
    security_hash: Optional[str]
    status: LedgerStatus
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class TemplateRequest(BaseSchemaModel):
    title: str
    description: Optional[str] = None
    schema_definition: LedgerFormSchema = Field(alias="schema")

    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    @property
    def schema(self) -> Dict[str, Any]:
        return self.schema_definition.model_dump(by_alias=True)

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)


class TemplateResponse(BaseSchemaModel):
    id: int
    title: str
    description: Optional[str] = None
    schema_definition: LedgerFormSchema = Field(alias="schema")
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(protected_namespaces=(), from_attributes=True, populate_by_name=True)

    @property
    def schema(self) -> Dict[str, Any]:
        return self.schema_definition.model_dump(by_alias=True)


class SOPTaskRequest(BaseSchemaModel):
    name: str
    description: Optional[str] = None
    template_id: int
    cron_expression: str
    scope: dict


class SOPTaskResponse(BaseSchemaModel):
    id: int
    name: str
    description: Optional[str] = None
    template_id: int
    cron_expression: str
    scope: dict
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class SOPTaskStatusRequest(BaseSchemaModel):
    is_active: int


class GenericResponse(BaseSchemaModel):
    code: int = 20000
    msg: str = "success"
    request_id: Optional[str] = None
    data: Optional[dict] = None


# 新版契约草案 --------------------------------------------------------------
class LedgerTemplateBase(BaseSchemaModel):
    title: str = Field(..., description="模板标题")
    schema_data: LedgerFormSchema = Field(..., alias="schema", description="表单Schema定义")

    @property
    def schema(self) -> Dict[str, Any]:
        return self.schema_data.model_dump(by_alias=True)


class LedgerTemplateCreate(LedgerTemplateBase):
    pass


class LedgerTemplateResponse(LedgerTemplateBase):
    id: int
    hash: Optional[str]
    create_time: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LedgerTaskBase(BaseModel):
    name: str
    template_id: int
    cron: str = Field(..., description="Cron表达式 (e.g., '0 8 * * *')")
    target_config: Dict[str, Any] = Field(default={}, description="派发范围配置")
    is_active: bool = True


class LedgerTaskCreate(LedgerTaskBase):
    pass


class LedgerTaskResponse(LedgerTaskBase):
    id: int
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)


class LedgerInstanceBase(BaseModel):
    template_id: int
    canteen_id: int
    status: LedgerStatus = Field(default=LedgerStatus.PENDING)


class LedgerInstanceDetail(LedgerInstanceBase):
    id: int
    title: str = Field(..., description="模板标题快照")
    schema_snapshot: LedgerFormSchema
    content: Dict[str, Any]
    security_hash: Optional[str]
    signature_image: Optional[str]
    create_date: datetime
    submit_time: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    @property
    def schema(self) -> Dict[str, Any]:
        return self.schema_snapshot.model_dump(by_alias=True)


class LedgerSubmitRequest(BaseModel):
    """新版签字提交契约，增加扁平结构校验。"""

    form_data: Dict[str, Any] = Field(..., description="填报数据")
    signature_image: str = Field(..., description="签字图片OSS地址")

    @field_validator("form_data")
    def validate_flat_structure(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        for key, raw in value.items():
            if isinstance(raw, dict):
                raise ValueError(f"字段 '{key}' 的值不能是字典（必须扁平化）")
        return value


# ==================== 模板覆盖范围相关 DTO ====================

class TemplateScopeRequest(BaseSchemaModel):
    """模板覆盖范围更新请求。

    包含描述、覆盖范围对象、扩展配置。
    """

    description: Optional[str] = Field(
        default=None,
        description="模板描述",
        min_length=1,
        max_length=500,
    )
    scope: Optional["TemplateScopeData"] = Field(
        default=None,
        description="覆盖范围（人员、食堂）",
    )
    extra_config: Optional[str] = Field(
        default=None,
        description="扩展配置（JSON字符串）",
    )


class TemplateScopeData(BaseSchemaModel):
    """覆盖范围数据结构。"""

    users: Optional[List[int]] = Field(default=None, description="覆盖人员ID列表")
    canteens: Optional[List[int]] = Field(default=None, description="覆盖食堂ID列表")


class TemplateScopeResponse(BaseSchemaModel):
    """模板覆盖范围响应。"""

    template_id: int = Field(..., description="模板ID")
    description: Optional[str] = Field(default=None, description="模板描述")
    users: List[int] = Field(default_factory=list, description="覆盖人员ID列表")
    canteens: List[int] = Field(default_factory=list, description="覆盖食堂ID列表")
    extra_config: Optional[Dict[str, Any]] = Field(default=None, description="扩展配置")
    user_details: Optional[List["UserBriefInfo"]] = Field(
        default=None, description="人员详细信息列表"
    )
    canteen_details: Optional[List["CanteenBriefInfo"]] = Field(
        default=None, description="食堂详细信息列表"
    )


class UserBriefInfo(BaseSchemaModel):
    """人员简要信息。"""

    id: int
    real_name: str = Field(..., description="真实姓名")
    username: str = Field(..., description="用户名")
    org_id: int = Field(..., description="组织ID")


class CanteenBriefInfo(BaseSchemaModel):
    """食堂简要信息。"""

    id: int
    name: str = Field(..., description="食堂名称")
    org_id: int = Field(..., description="组织ID")


class BatchScopeRequest(BaseSchemaModel):
    """批量更新覆盖范围请求。"""

    ids: List[int] = Field(default_factory=list, description="ID列表")

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, value: List[int]) -> List[int]:
        if len(value) > 1000:
            raise ValueError("单次批量操作最多支持1000条")
        return value


class BatchScopeResponse(BaseSchemaModel):
    """批量更新覆盖范围响应。"""

    template_id: int = Field(..., description="模板ID")
    updated_count: int = Field(..., description="更新数量")
    scope: TemplateScopeData = Field(..., description="当前覆盖范围")

