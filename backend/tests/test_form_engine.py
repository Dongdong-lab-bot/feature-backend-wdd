"""Ledger Form Engine 的测试。"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.modules.ledger.context import AUTO_FILL_CANTEEN_NAME, AUTO_FILL_USER_NAME
from app.modules.ledger.exceptions import FieldValidationError
from app.modules.ledger.form_engine import auto_fill, validate_data


def test_missing_required_field() -> None:
    schema = {
        "fields": [
            {"field_id": "f_temp_01", "type": "number", "required": True, "min": 35, "max": 42},
        ]
    }
    data = {}

    with pytest.raises(FieldValidationError) as excinfo:
        validate_data(schema, data)

    assert excinfo.value.field_id == "f_temp_01"
    assert "required" in excinfo.value.message


def test_type_error() -> None:
    schema = {"fields": [{"field_id": "f_is_clean", "type": "boolean", "required": True}]}
    data = {"f_is_clean": "yes"}

    with pytest.raises(FieldValidationError) as excinfo:
        validate_data(schema, data)

    assert excinfo.value.field_id == "f_is_clean"
    assert "boolean" in excinfo.value.message


def test_regex_error() -> None:
    schema = {
        "fields": [
            {"field_id": "f_phone", "type": "string", "required": True, "regex": r"^1[3-9]\\d{9}$"}
        ]
    }
    data = {"f_phone": "123"}

    with pytest.raises(FieldValidationError) as excinfo:
        validate_data(schema, data)

    assert excinfo.value.field_id == "f_phone"
    assert "regex" in excinfo.value.message


def test_number_out_of_range() -> None:
    schema = {
        "fields": [
            {"field_id": "f_temp_01", "type": "number", "required": True, "min": 35, "max": 42},
        ]
    }
    data = {"f_temp_01": 50}

    with pytest.raises(FieldValidationError) as excinfo:
        validate_data(schema, data)

    assert excinfo.value.field_id == "f_temp_01"
    assert "less than or equal" in excinfo.value.message


def test_auto_fill_inject_success() -> None:
    schema = {
        "fields": [
            {"field_id": "f_time", "type": "string", "auto_fill": "current_time"},
            {"field_id": "f_canteen", "type": "string", "auto_fill": "canteen_name"},
            {"field_id": "f_user", "type": "string", "auto_fill": "user_name"},
        ]
    }
    data = {"f_custom": "value"}
    context = {AUTO_FILL_CANTEEN_NAME: "食堂A", AUTO_FILL_USER_NAME: "张三"}

    filled = auto_fill(schema, data, context)

    assert filled is not data
    assert filled["f_custom"] == "value"
    assert filled["f_canteen"] == "食堂A"
    assert filled["f_user"] == "张三"
    datetime.fromisoformat(filled["f_time"])


def test_auto_fill_does_not_override() -> None:
    schema = {
        "fields": [
            {"field_id": "f_user", "type": "string", "auto_fill": "user_name"},
        ]
    }
    data = {"f_user": "前端值"}
    context = {AUTO_FILL_USER_NAME: "后端值"}

    filled = auto_fill(schema, data, context)

    assert filled["f_user"] == "前端值"


def test_pressure_50_fields() -> None:
    fields = []
    data = {}
    for index in range(50):
        field_id = f"f_{index:02d}"
        field_type = "number" if index % 2 == 0 else "string"
        field = {"field_id": field_id, "type": field_type, "required": True}
        if field_type == "number":
            field.update({"min": 0, "max": 100})
            data[field_id] = 50
        else:
            field.update({"regex": r"^ok$"})
            data[field_id] = "ok"
        fields.append(field)

    schema = {"fields": fields}

    validate_data(schema, data)


def test_enum_validation_error() -> None:
    schema = {"fields": [{"field_id": "status", "type": "string", "enum": ["A", "B"]}]}

    with pytest.raises(FieldValidationError):
        validate_data(schema, {"status": "C"})

    validate_data(schema, {"status": "A"})


def test_default_value_auto_fill() -> None:
    schema = {"fields": [{"field_id": "count", "type": "number", "default": 0}]}

    filled = auto_fill(schema, {}, {})

    assert filled["count"] == 0


def test_auto_fill_missing_context_raises() -> None:
    schema = {"fields": [{"field_id": "operator", "type": "string", "auto_fill": "user_name"}]}

    with pytest.raises(FieldValidationError) as excinfo:
        auto_fill(schema, {}, {})

    assert "context key" in excinfo.value.message
