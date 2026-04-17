from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.modules.device.service import _build_record_data, _get_record_type


def test_get_record_type_mapping():
    assert _get_record_type("MORNING_CHECK_RECORD").value == "MORNING_CHECK"
    assert _get_record_type("AI_BOX_RECORD").value == "AI_BOX"
    assert _get_record_type("SAMPLING_RECORD").value == "SAMPLING"
    assert _get_record_type("UNKNOWN_RECORD").value == "GENERIC"


def test_build_record_data_morning_check():
    payload = {
        "temperature": 36.7,
        "has_mask": True,
        "has_wound": False,
        "employee_id": "EMP001",
    }
    detail_json = {
        "device_info": {"timestamp": "2026-04-01T08:30:00"},
        "employee_info": {"employee_id": "EMP001", "employee_name": "张三"},
        "inspection_data": {
            "temperature": 36.7,
            "has_mask": True,
            "has_wound": False,
            "capture_image_url": "https://cdn.example.com/morning.jpg",
        },
    }
    result = _build_record_data("MORNING_CHECK_RECORD", payload, detail_json)
    data = result.model_dump()
    assert data["employee_id"] == "EMP001"
    assert data["employee_name"] == "张三"
    assert data["temperature_status"] == "NORMAL"
    assert data["occurred_at"] == "2026-04-01T08:30:00"


def test_build_record_data_ai_box():
    payload = {
        "operator": "RecordPush",
        "info": {
            "time": "2026-04-01 10:30:00",
            "event_type": "HELMET_DETECT",
            "region_name": "后厨区域",
            "snapshot_url": "https://cdn.example.com/snapshot.jpg",
        },
    }
    detail_json = {
        "detect_result": "NOT_WEAR_HELMET",
        "confidence": 0.95,
    }
    result = _build_record_data("AI_BOX_RECORD", payload, detail_json)
    data = result.model_dump()
    assert data["event_type"] == "HELMET_DETECT"
    assert data["event_type_label"] == "头盔检测"
    assert data["detect_result"] == "NOT_WEAR_HELMET"
    assert data["confidence"] == 0.95
    assert data["occurred_at"] == "2026-04-01 10:30:00"


def test_build_record_data_sampling():
    payload = {
        "dish_name": "红烧肉",
        "operator_name": "李四",
        "weight": 250.0,
        "unit": "g",
    }
    detail_json = {
        "dish_name": "红烧肉",
        "stall_name": "切配间",
        "timestamp": "2026-04-01T12:00:00",
    }
    result = _build_record_data("SAMPLING_RECORD", payload, detail_json)
    data = result.model_dump()
    assert data["dish_name"] == "红烧肉"
    assert data["stall_name"] == "切配间"
    assert data["operator_name"] == "李四"
    assert data["weight"] == 250.0
    assert data["weight_unit"] == "g"


def test_build_record_data_generic():
    payload = {"raw_key": "payload-value"}
    detail_json = {"raw_key": "detail-value"}
    result = _build_record_data("UNKNOWN_RECORD", payload, detail_json)
    data = result.model_dump()
    assert data["raw_payload"] == {"raw_key": "payload-value"}
    assert data["raw_detail"] == {"raw_key": "detail-value"}
