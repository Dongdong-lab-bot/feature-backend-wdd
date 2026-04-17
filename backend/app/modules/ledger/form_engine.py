from __future__ import annotations

import re
from typing import Any, Dict, Union

from app.modules.ledger.context import get_auto_fill_value
from app.modules.ledger.exceptions import FieldValidationError
from app.modules.ledger.schemas import LedgerFormField, LedgerFormSchema

SchemaInput = Union[LedgerFormSchema, Dict[str, Any]]


def validate_data(schema_snapshot: SchemaInput, form_data: Dict[str, Any]) -> bool:
    """校验表单数据是否满足 schema 约束。"""

    schema = _ensure_schema(schema_snapshot)
    payload = form_data or {}

    for field in schema.fields:
        field_id = field.field_id

        if field.required and field_id not in payload:
            raise FieldValidationError(field_id, f"Field '{field_id}' is required")

        if field_id not in payload:
            continue

        _validate_single_field(field, payload[field_id])

    return True


def auto_fill(
    schema_snapshot: SchemaInput,
    form_data: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """根据 schema 的 auto_fill 定义补全缺失字段。"""

    schema = _ensure_schema(schema_snapshot)
    filled_data = dict(form_data or {})
    context = context or {}

    for field in schema.fields:
        field_id = field.field_id

        if field_id in filled_data and filled_data[field_id] is not None:
            continue

        if field.default is not None:
            filled_data[field_id] = field.default
            continue

        auto_fill_type = field.auto_fill
        if not auto_fill_type:
            continue

        try:
            filled_data[field_id] = get_auto_fill_value(auto_fill_type, context)
        except KeyError as exc:
            raise FieldValidationError(
                field_id,
                f"Missing auto-fill context key '{exc.args[0]}'",
            ) from exc
        except ValueError as exc:
            raise FieldValidationError(field_id, str(exc)) from exc

    return filled_data


def _ensure_schema(schema_snapshot: SchemaInput) -> LedgerFormSchema:
    if isinstance(schema_snapshot, LedgerFormSchema):
        return schema_snapshot
    if not isinstance(schema_snapshot, dict):
        raise TypeError("schema_snapshot must be dict or LedgerFormSchema")
    return LedgerFormSchema.model_validate(schema_snapshot)


def _validate_single_field(field: LedgerFormField, value: Any) -> None:
    field_type = (field.type or "").lower()
    field_id = field.field_id

    if field_type == "string":
        if not isinstance(value, str):
            raise FieldValidationError(field_id, f"Field '{field_id}' should be a string")
        if field.regex and not re.fullmatch(_normalize_regex(field.regex), value):
            raise FieldValidationError(field_id, f"Field '{field_id}' does not match regex pattern")
        if field.min_length is not None and len(value) < field.min_length:
            raise FieldValidationError(
                field_id,
                f"Field '{field_id}' should be at least {field.min_length} characters long",
            )
        if field.max_length is not None and len(value) > field.max_length:
            raise FieldValidationError(
                field_id,
                f"Field '{field_id}' should be at most {field.max_length} characters long",
            )
    elif field_type == "number":
        if not _is_number(value):
            raise FieldValidationError(field_id, f"Field '{field_id}' should be a number")
        _validate_number_ranges(field, float(value))
    elif field_type == "integer":
        if not _is_int(value):
            raise FieldValidationError(field_id, f"Field '{field_id}' should be an integer")
        _validate_number_ranges(field, float(value))
    elif field_type == "boolean":
        if not isinstance(value, bool):
            raise FieldValidationError(field_id, f"Field '{field_id}' should be a boolean")
    elif field_type == "array":
        if not isinstance(value, list):
            raise FieldValidationError(field_id, f"Field '{field_id}' should be an array")
    elif field_type:
        raise FieldValidationError(field_id, f"Unsupported field type '{field.type}'")

    if field.enum is not None and value not in field.enum:
        raise FieldValidationError(field_id, f"Field '{field_id}' must be one of {field.enum}")


def _validate_number_ranges(field: LedgerFormField, numeric_value: float) -> None:
    if field.min_value is not None and numeric_value < field.min_value:
        raise FieldValidationError(
            field.field_id,
            f"Field '{field.field_id}' should be greater than or equal to {field.min_value}",
        )
    if field.max_value is not None and numeric_value > field.max_value:
        raise FieldValidationError(
            field.field_id,
            f"Field '{field.field_id}' should be less than or equal to {field.max_value}",
        )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _normalize_regex(pattern: str) -> str:
    if "\\\\" in pattern:
        return pattern.replace("\\\\", "\\")
    return pattern
