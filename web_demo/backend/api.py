"""
Web Demo CRUD API
提供告警、门店、违规事件、整改工单的增删改查接口
"""

from __future__ import annotations

import json
import time
import secrets
import string
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from web_demo.backend.db_init import get_connection

router = APIRouter(prefix="/api/demo", tags=["web-demo"])

# ==================== 模拟用户会话（仅 Demo 用）====================
# 简化：密码统一为 "123456"
_LOGIN_USERS = {
    "admin01": {"password": "123456", "user_id": "admin01"},
    "super01": {"password": "123456", "user_id": "super01"},
    "mgr001":  {"password": "123456", "user_id": "mgr001"},
    "mgr002":  {"password": "123456", "user_id": "mgr002"},
    "emp001":  {"password": "123456", "user_id": "emp001"},
}

class LoginRequest(BaseModel):
    user_id: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    """模拟登录，返回用户信息"""
    user = _LOGIN_USERS.get(req.user_id)
    if not user or user["password"] != req.password:
        return {"code": "4001", "message": "用户ID或密码错误", "data": None}
    conn = get_connection()
    row = conn.execute(
        "SELECT user_id, user_name, role_type, phone, store_ids FROM users WHERE user_id=? AND is_deleted=0",
        (req.user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"code": "4001", "message": "用户不存在", "data": None}
    return {"code": "0000", "data": dict(row)}

@router.get("/user/{user_id}")
async def get_user(user_id: str):
    """获取用户信息"""
    conn = get_connection()
    row = conn.execute(
        "SELECT user_id, user_name, role_type, phone, store_ids FROM users WHERE user_id=? AND is_deleted=0",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"code": "4001", "message": "用户不存在", "data": None}
    user = dict(row)
    import json
    user["store_ids"] = json.loads(user["store_ids"])
    return {"code": "0000", "data": user}


def _generate_id(prefix: str) -> str:
    ts = int(time.time() * 1000)
    rand = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}{ts}{rand}"


def _dict_from_row(row) -> dict:
    return dict(row)


# ==================== 门店 API ====================

@router.get("/stores")
async def list_stores():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM stores WHERE is_deleted=0 ORDER BY id").fetchall()
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows]}


# ==================== 告警 API (CRUD 完整演示) ====================

@router.get("/alerts")
async def list_alerts(
    store_id: Optional[str] = None,
    level: Optional[str] = None,
    violation_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    conn = get_connection()
    where = ["a.is_deleted=0"]
    params = []
    if store_id:
        where.append("a.store_id=?")
        params.append(store_id)
    if level:
        where.append("a.level=?")
        params.append(level)
    if violation_type:
        where.append("a.violation_type=?")
        params.append(violation_type)

    # 查总数
    count_sql = f"SELECT COUNT(*) FROM alerts a WHERE {' AND '.join(where)}"
    total = conn.execute(count_sql, params).fetchone()[0]

    # 查列表（联表 camera + store 取名称）
    sql = f"""
        SELECT a.*, c.name as camera_name, s.name as store_name
        FROM alerts a
        LEFT JOIN cameras c ON a.camera_id = c.id
        LEFT JOIN stores s ON a.store_id = s.id
        WHERE {' AND '.join(where)}
        ORDER BY a.timestamp DESC
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(sql, params + [page_size, (page - 1) * page_size]).fetchall()
    conn.close()

    return {
        "code": "0000",
        "data": [_dict_from_row(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    conn = get_connection()
    row = conn.execute(
        """SELECT a.*, c.name as camera_name, s.name as store_name
           FROM alerts a
           LEFT JOIN cameras c ON a.camera_id = c.id
           LEFT JOIN stores s ON a.store_id = s.id
           WHERE a.id=? AND a.is_deleted=0""",
        (alert_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "告警不存在")
    return {"code": "0000", "data": _dict_from_row(row)}


class AlertCreate(BaseModel):
    camera_id: str
    store_id: str
    message: str
    violation_type: str = "A00"
    level: str = "medium"
    confidence: float = 0.8
    timestamp: Optional[str] = None


@router.post("/alerts")
async def create_alert(alert: AlertCreate):
    alert_id = _generate_id("ALT")
    trace_id = _generate_id("TRC")
    ts = alert.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    conn.execute(
        """INSERT INTO alerts (id,trace_id,camera_id,store_id,message,violation_type,level,confidence,timestamp)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (alert_id, trace_id, alert.camera_id, alert.store_id, alert.message,
         alert.violation_type, alert.level, alert.confidence, ts)
    )
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "告警创建成功", "data": {"id": alert_id}}


class AlertUpdate(BaseModel):
    level: Optional[str] = None
    rectification_status: Optional[str] = None
    verify_result: Optional[str] = None
    is_verified: Optional[int] = None


@router.put("/alerts/{alert_id}")
async def update_alert(alert_id: str, update: AlertUpdate):
    fields = []
    params = []
    if update.level is not None:
        fields.append("level=?")
        params.append(update.level)
    if update.rectification_status is not None:
        fields.append("rectification_status=?")
        params.append(update.rectification_status)
    if update.verify_result is not None:
        fields.append("verify_result=?")
        params.append(update.verify_result)
    if update.is_verified is not None:
        fields.append("is_verified=?")
        params.append(update.is_verified)

    if not fields:
        raise HTTPException(400, "没有要更新的字段")

    fields.append("updated_at=CURRENT_TIMESTAMP")
    params.append(alert_id)

    conn = get_connection()
    conn.execute(f"UPDATE alerts SET {','.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "告警更新成功"}


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """逻辑删除（演示逻辑删除而非物理 DELETE）"""
    conn = get_connection()
    conn.execute("UPDATE alerts SET is_deleted=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "告警已删除（逻辑删除）"}


# ==================== 违规事件 API ====================

@router.get("/events")
async def list_events(store_id: Optional[str] = None):
    conn = get_connection()
    where = ["v.is_deleted=0"]
    params = []
    if store_id:
        where.append("v.store_id=?")
        params.append(store_id)

    rows = conn.execute(
        f"""SELECT v.*, a.message as alert_message, s.name as store_name
            FROM violation_events v
            LEFT JOIN alerts a ON v.alert_id = a.id
            LEFT JOIN stores s ON v.store_id = s.id
            WHERE {' AND '.join(where)}
            ORDER BY v.timestamp DESC""",
        params
    ).fetchall()
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows]}


# ==================== 整改工单 API ====================

@router.get("/tasks")
async def list_tasks(store_id: Optional[str] = None, status: Optional[str] = None):
    conn = get_connection()
    where = ["t.is_deleted=0"]
    params = []
    if store_id:
        where.append("t.store_id=?")
        params.append(store_id)
    if status:
        where.append("t.status=?")
        params.append(status)

    rows = conn.execute(
        f"""SELECT t.*, s.name as store_name
            FROM rectification_tasks t
            LEFT JOIN stores s ON t.store_id = s.id
            WHERE {' AND '.join(where)}
            ORDER BY t.created_at DESC""",
        params
    ).fetchall()
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows]}


@router.post("/tasks")
async def create_task(task: dict):
    task_id = _generate_id("TSK")
    conn = get_connection()
    conn.execute(
        """INSERT INTO rectification_tasks (task_id,alert_id,store_id,title,assignee,status,created_by,deadline)
           VALUES (?,?,?,?,?,?,?,?)""",
        (task_id, task.get("alert_id"), task["store_id"], task["title"],
         task.get("assignee"), "pending", task.get("created_by", "admin"),
         task.get("deadline"))
    )
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "工单创建成功", "data": {"task_id": task_id}}


@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    conn = get_connection()
    conn.execute("UPDATE rectification_tasks SET status=? WHERE task_id=?", (status, task_id))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": f"工单状态已更新为 {status}"}


# ==================== 统计数据 API（Dashboard）====================

@router.get("/stats")
async def get_stats():
    conn = get_connection()
    total_alerts = conn.execute("SELECT COUNT(*) FROM alerts WHERE is_deleted=0").fetchone()[0]
    total_events = conn.execute("SELECT COUNT(*) FROM violation_events WHERE is_deleted=0").fetchone()[0]
    pending_tasks = conn.execute("SELECT COUNT(*) FROM rectification_tasks WHERE status='pending' AND is_deleted=0").fetchone()[0]
    critical_alerts = conn.execute("SELECT COUNT(*) FROM alerts WHERE level='critical' AND is_deleted=0").fetchone()[0]
    
    # 按门店统计告警数
    store_stats = conn.execute("""
        SELECT s.id, s.name, COUNT(a.id) as alert_count
        FROM stores s
        LEFT JOIN alerts a ON s.id = a.store_id AND a.is_deleted=0
        WHERE s.is_deleted=0
        GROUP BY s.id
        ORDER BY alert_count DESC
    """).fetchall()

    # 按违规类型统计
    type_stats = conn.execute("""
        SELECT violation_type, COUNT(*) as count
        FROM alerts WHERE is_deleted=0
        GROUP BY violation_type ORDER BY count DESC
    """).fetchall()

    conn.close()
    return {
        "code": "0000",
        "data": {
            "total_alerts": total_alerts,
            "total_events": total_events,
            "pending_tasks": pending_tasks,
            "critical_alerts": critical_alerts,
            "store_stats": [_dict_from_row(r) for r in store_stats],
            "type_stats": [_dict_from_row(r) for r in type_stats],
        }
    }


# ==================== SQL 查询面板（数据库演示核心）====================

class SQLQuery(BaseModel):
    sql: str
    params: Optional[list] = None


@router.post("/sql")
async def execute_sql(query: SQLQuery):
    """执行 SQL 查询并返回结果（仅 SELECT，写操作拦截）"""
    sql = query.sql.strip().upper()
    # 安全拦截：只允许 SELECT 查询
    if not sql.startswith("SELECT"):
        return {"code": "4000", "message": "仅允许 SELECT 查询", "data": None}

    try:
        conn = get_connection()
        cursor = conn.execute(query.sql, query.params or [])
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return {
            "code": "0000",
            "data": {
                "columns": columns,
                "rows": data,
                "count": len(data)
            }
        }
    except Exception as e:
        return {"code": "5000", "message": f"SQL 执行错误: {str(e)}", "data": None}


# ==================== 预设数据库演示 ====================

@router.get("/demo-sql/presets")
async def get_presets():
    """返回预设 SQL 演示列表"""
    return {"code": "0000", "data": [
        {
            "id": "join_3tables",
            "title": "3 表联合查询（JOIN）",
            "desc": "联表查询告警 + 门店 + 摄像头，演示参照完整性",
            "sql": """SELECT a.id AS 告警ID, a.message AS 告警消息,
       s.name AS 门店名称, c.name AS 摄像头位置,
       a.level AS 级别, a.confidence AS 置信度
FROM alerts a
LEFT JOIN stores s ON a.store_id = s.id
LEFT JOIN cameras c ON a.camera_id = c.id
WHERE a.is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "group_by_store",
            "title": "分组统计（GROUP BY）",
            "desc": "按门店分组统计告警数量，演示聚合函数",
            "sql": """SELECT s.name AS 门店名称,
       COUNT(a.id) AS 告警总数,
       SUM(CASE WHEN a.level = 'critical' THEN 1 ELSE 0 END) AS 严重告警数,
       ROUND(AVG(a.confidence), 2) AS 平均置信度
FROM stores s
LEFT JOIN alerts a ON s.id = a.store_id AND a.is_deleted = 0
WHERE s.is_deleted = 0
GROUP BY s.id
ORDER BY 告警总数 DESC"""
        },
        {
            "id": "logical_delete",
            "title": "逻辑删除演示",
            "desc": "展示逻辑删除前 vs 逻辑删除后的数据对比",
            "sql": """SELECT '已逻辑删除' AS 状态, id, message, level
FROM alerts WHERE is_deleted = 1
UNION ALL
SELECT '未删除' AS 状态, id, message, level
FROM alerts WHERE is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "foreign_key_check",
            "title": "外键关联检查",
            "desc": "检查告警表中 store_id 是否都能匹配门店表，演示参照完整性",
            "sql": """SELECT a.id AS 告警ID,
       a.store_id AS 告警门店ID,
       CASE WHEN s.id IS NOT NULL THEN '✅ 有效' ELSE '❌ 无效' END AS 外键状态
FROM alerts a
LEFT JOIN stores s ON a.store_id = s.id
WHERE a.is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "pending_tasks_detail",
            "title": "待处理工单详情",
            "desc": "查询所有待处理的整改工单及关联告警",
            "sql": """SELECT t.task_id AS 工单ID, t.title AS 工单标题,
       s.name AS 门店, t.assignee AS 负责人,
       a.message AS 关联告警, t.deadline AS 截止日期
FROM rectification_tasks t
LEFT JOIN stores s ON t.store_id = s.id
LEFT JOIN alerts a ON t.alert_id = a.id
WHERE t.status = 'pending' AND t.is_deleted = 0"""
        }
    ]}


# ==================== E-R 图说明 API ====================

@router.get("/er-info")
async def get_er_info():
    """返回数据库表结构说明，用于前端 E-R 图展示"""
    return {
        "code": "0000",
        "data": {
            "tables": [
                {
                    "name": "stores",
                    "comment": "门店表",
                    "columns": ["id(PK)", "name", "address", "contact_phone", "region_id"],
                    "relations": []
                },
                {
                    "name": "cameras",
                    "comment": "摄像头表",
                    "columns": ["id(PK)", "name", "store_id(FK→stores)", "location"],
                    "relations": [{"type": "N:1", "target": "stores", "via": "store_id"}]
                },
                {
                    "name": "alerts",
                    "comment": "告警记录表（核心）",
                    "columns": ["id(PK)", "camera_id(FK→cameras)", "store_id(FK→stores)", "message", "violation_type", "level", "confidence", "rectification_status"],
                    "relations": [
                        {"type": "N:1", "target": "cameras", "via": "camera_id"},
                        {"type": "N:1", "target": "stores", "via": "store_id"},
                        {"type": "1:1", "target": "violation_events", "via": "alert_id"}
                    ]
                },
                {
                    "name": "violation_events",
                    "comment": "违规事件表（VLM 校验后产出）",
                    "columns": ["event_id(PK)", "alert_id(FK→alerts)", "is_violation_confirmed", "severity_level", "verification_method"],
                    "relations": [{"type": "1:1", "target": "alerts", "via": "alert_id"}]
                },
                {
                    "name": "users",
                    "comment": "用户表",
                    "columns": ["user_id(PK)", "user_name", "role_type", "phone", "store_ids"],
                    "relations": []
                },
                {
                    "name": "rectification_tasks",
                    "comment": "整改工单表",
                    "columns": ["task_id(PK)", "alert_id", "store_id(FK→stores)", "title", "status", "assignee", "deadline"],
                    "relations": [{"type": "N:1", "target": "stores", "via": "store_id"}]
                }
            ]
        }
    }
