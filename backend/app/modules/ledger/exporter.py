from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Sequence, Tuple

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.modules.ledger.models import LedgerInstance


def build_table(instances: Sequence[LedgerInstance]) -> Tuple[List[str], List[List[Any]]]:
    if not instances:
        return [], []

    sample = instances[0]
    schema = getattr(sample, "schema_snapshot", {}) or {}
    properties: Dict[str, Dict[str, Any]] = schema.get("properties") or {}

    dynamic_fields: List[Tuple[str, str]] = []
    for key, prop in properties.items():
        title = prop.get("title") or key
        dynamic_fields.append((key, title))

    headers: List[str] = ["date", "canteenId", "status"]
    headers.extend(title for _, title in dynamic_fields)

    rows: List[List[Any]] = []
    for inst in instances:
        row: List[Any] = [
            getattr(inst, "create_date", None),
            getattr(inst, "canteen_id", None),
            getattr(inst, "status", None),
        ]
        content: Dict[str, Any] = getattr(inst, "content", {}) or {}
        for field_key, _ in dynamic_fields:
            row.append(content.get(field_key))
        rows.append(row)

    return headers, rows


def export_excel(instances: Sequence[LedgerInstance]) -> bytes:
    headers, rows = build_table(instances)

    wb = Workbook()
    ws = wb.active
    if headers:
        ws.append(headers)
    for row in rows:
        ws.append(row)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def export_pdf(instances: Sequence[LedgerInstance]) -> bytes:
    headers, rows = build_table(instances)

    buffer = BytesIO()
    # 使用系统中的宋体以正确显示中文（Windows 环境下通常存在）
    try:
        pdfmetrics.registerFont(TTFont("SimSun", r"C:/Windows/Fonts/simsun.ttc"))
        font_name = "SimSun"
    except Exception:
        # 回退到默认字体，避免因为字体缺失导致导出失败
        font_name = "Helvetica"

    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont(font_name, 12)
    width, height = A4

    x_margin = 40
    y = height - 40
    line_height = 16

    if headers:
        pdf.drawString(x_margin, y, " | ".join(str(h) for h in headers))
        y -= line_height

    for row in rows:
        if y < 40:
            pdf.showPage()
            y = height - 40
        pdf.drawString(
            x_margin,
            y,
            " | ".join("" if v is None else str(v) for v in row),
        )
        y -= line_height

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()