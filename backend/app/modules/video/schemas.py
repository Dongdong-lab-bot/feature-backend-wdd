from typing import Optional

from pydantic import BaseModel, Field


class VideoCaptureRequest(BaseModel):
    image_base64: str = Field(..., alias="image_base64", min_length=16)
    timestamp: Optional[str] = Field(None, alias="timestamp")

    model_config = {"populate_by_name": True}


class HikvisionChannelSyncRequest(BaseModel):
    device_serial: str = Field(..., alias="deviceSerial")
    page_size: int = Field(50, ge=1, le=200, alias="pageSize")

    model_config = {"populate_by_name": True}


class HikvisionEncryptOffRequest(BaseModel):
    device_serial: str = Field(..., alias="deviceSerial")
    validate_code: Optional[str] = Field(None, alias="validateCode")

    model_config = {"populate_by_name": True}


class HikvisionPlayParamsRequest(BaseModel):
    camera_id: str = Field(..., alias="cameraId")
    action: str = Field(..., alias="action", pattern="^(preview|playback)$")
    begin: Optional[str] = Field(None, alias="begin")
    end: Optional[str] = Field(None, alias="end")

    model_config = {"populate_by_name": True}