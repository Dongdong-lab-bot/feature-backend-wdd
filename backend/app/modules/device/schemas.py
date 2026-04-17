from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, model_validator


class GenericResponse(BaseModel):
    code: int = 200
    msg: str = "success"
    request_id: Optional[str] = None
    data: Optional[Any] = None


class DeviceStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class DeviceDataType(str, Enum):
    MORNING_CHECK_RECORD = "MORNING_CHECK_RECORD"
    AI_BOX_RECORD = "AI_BOX_RECORD"
    SAMPLING_RECORD = "SAMPLING_RECORD"


class DeviceRecordType(str, Enum):
    MORNING_CHECK = "MORNING_CHECK"
    AI_BOX = "AI_BOX"
    SAMPLING = "SAMPLING"
    GENERIC = "GENERIC"


class DeviceCreateRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=128)
    device_code: str = Field(..., min_length=1, max_length=64)
    org_id: int = Field(..., ge=1)
    status: DeviceStatus = DeviceStatus.OFFLINE
    device_type: Optional[str] = Field(default=None, max_length=32)


class DeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    status: Optional[DeviceStatus] = None
    device_type: Optional[str] = Field(default=None, max_length=32)


class DeviceListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    keyword: Optional[str] = Field(default=None, max_length=128)
    status: Optional[DeviceStatus] = None
    org_id: Optional[int] = Field(default=None, ge=1)


class DeviceDetailResponse(BaseModel):
    id: int
    device_name: str
    device_code: str
    status: str
    created_at: datetime
    org_id: int
    org_name: Optional[str] = None
    device_type: Optional[str] = None


class DeviceRegenerateKeyResponse(BaseModel):
    id: int
    api_key: Optional[str] = None
    api_key_masked: Optional[str] = None


class DeviceInfoPayload(BaseModel):
    device_code: str = Field(..., min_length=1, max_length=64)
    timestamp: datetime


class EmployeeInfoPayload(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=64)
    employee_name: str = Field(..., min_length=1, max_length=128)


class InspectionDataPayload(BaseModel):
    temperature: float = Field(..., ge=30.0, le=45.0)
    has_mask: bool
    has_wound: bool
    capture_image_url: Optional[str] = Field(default=None, max_length=512)


class MorningCheckUploadRequest(BaseModel):
    device_info: DeviceInfoPayload
    employee_info: EmployeeInfoPayload
    inspection_data: InspectionDataPayload


class DeviceRefreshRequest(BaseModel):
    device_code: str = Field(..., min_length=1, max_length=64)


class SamplingUploadRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    dish_name: str = Field(..., min_length=1, max_length=100)
    stall_name: Optional[str] = Field(default=None, max_length=100)
    operator_name: Optional[str] = Field(default=None, max_length=64)
    weight: float = Field(..., ge=0)
    timestamp: int = Field(..., description="留样时间戳（毫秒）")


class DeviceRecordQuery(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "DeviceRecordQuery":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be less than or equal to end_date")
        return self


class DeviceRecordExportQuery(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: str = Field(default="excel", pattern="^(excel|pdf|csv)$")

    @model_validator(mode="after")
    def validate_dates(self) -> "DeviceRecordExportQuery":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be less than or equal to end_date")
        return self


class DeviceRecordUpdateRequest(BaseModel):
    is_related_ledger: Optional[bool] = None
    status: Optional[DeviceStatus] = None
    data_type: Optional[DeviceDataType] = None
    source: Optional[str] = Field(default=None, max_length=32)
    process_result: Optional[str] = Field(default=None, max_length=32)
    submit_date: Optional[date] = None
    payload: Optional[dict] = None
    detail_json: Optional[dict] = None


class DeviceRecordListItem(BaseModel):
    id: int
    org_name: Optional[str] = None
    device_name: str
    device_code: str
    data_type: str
    data_type_label: str
    is_related_ledger: bool
    submit_date: date
    status: str
    source: str
    trace_id: Optional[str] = None
    process_result: str
    record_type: DeviceRecordType


class DeviceRecordListData(BaseModel):
    total: int
    page: int
    page_size: int
    records: list[DeviceRecordListItem]


class DeviceRecordDetailResponse(BaseModel):
    id: int
    org_name: Optional[str] = None
    device_name: str
    device_code: str
    data_type: str
    data_type_label: str
    is_related_ledger: bool
    submit_date: date
    status: str
    source: str
    trace_id: Optional[str] = None
    process_result: str
    created_at: datetime
    record_type: DeviceRecordType
    record_data: Optional[
        Union["MorningCheckRecordData", "AIBoxRecordData", "SamplingRecordData", "GenericRecordData"]
    ] = None


class MorningCheckRecordData(BaseModel):
    employee_id: str
    employee_name: str
    temperature: float
    temperature_status: str
    has_mask: bool
    has_wound: bool
    capture_image_url: Optional[str] = None
    occurred_at: str


class AIBoxRecordData(BaseModel):
    event_type: str
    event_type_label: str
    region_name: Optional[str] = None
    detect_result: Optional[str] = None
    confidence: Optional[float] = None
    snapshot_url: Optional[str] = None
    occurred_at: str


class SamplingRecordData(BaseModel):
    dish_name: str
    stall_name: Optional[str] = None
    operator_name: Optional[str] = None
    weight: float
    weight_unit: str = "g"
    occurred_at: str


class GenericRecordData(BaseModel):
    raw_payload: Optional[dict] = None
    raw_detail: Optional[dict] = None
