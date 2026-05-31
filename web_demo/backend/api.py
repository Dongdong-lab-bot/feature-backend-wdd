"""
Web Demo CRUD API（简化版）
4张表：stores, violations, users, tasks
展示数据库核心知识点：主键、外键、JOIN、GROUP BY、逻辑删除
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

# ==================== 模拟用户登录 ====================
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
    """模拟登录"""
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


# ==================== 违规记录 API（核心 CRUD）====================

@router.get("/violations")
async def list_violations(
    store_id: Optional[str] = None,
    level: Optional[str] = None,
    violation_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    conn = get_connection()
    where = ["v.is_deleted=0"]
    params = []
    if store_id:
        where.append("v.store_id=?")
        params.append(store_id)
    if level:
        where.append("v.level=?")
        params.append(level)
    if violation_type:
        where.append("v.violation_type=?")
        params.append(violation_type)

    count_sql = f"SELECT COUNT(*) FROM violations v WHERE {' AND '.join(where)}"
    total = conn.execute(count_sql, params).fetchone()[0]

    sql = f"""
        SELECT v.*, s.name as store_name
        FROM violations v
        LEFT JOIN stores s ON v.store_id = s.id
        WHERE {' AND '.join(where)}
        ORDER BY v.timestamp DESC
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


@router.get("/violations/{violation_id}")
async def get_violation(violation_id: str):
    conn = get_connection()
    row = conn.execute(
        """SELECT v.*, s.name as store_name
           FROM violations v
           LEFT JOIN stores s ON v.store_id = s.id
           WHERE v.id=? AND v.is_deleted=0""",
        (violation_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "违规记录不存在")
    return {"code": "0000", "data": _dict_from_row(row)}


class ViolationCreate(BaseModel):
    store_id: str
    message: str
    violation_type: str = "A00"
    level: str = "medium"
    confidence: float = 0.8
    timestamp: Optional[str] = None


@router.post("/violations")
async def create_violation(v: ViolationCreate):
    vid = _generate_id("VIO")
    ts = v.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute(
        """INSERT INTO violations (id,store_id,message,violation_type,level,confidence,rectification_status,timestamp)
           VALUES (?,?,?,?,?,?,?,?)""",
        (vid, v.store_id, v.message, v.violation_type, v.level, v.confidence, "pending", ts)
    )
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "违规记录创建成功", "data": {"id": vid}}


class ViolationUpdate(BaseModel):
    level: Optional[str] = None
    rectification_status: Optional[str] = None


@router.put("/violations/{violation_id}")
async def update_violation(violation_id: str, update: ViolationUpdate):
    fields = []
    params = []
    if update.level is not None:
        fields.append("level=?")
        params.append(update.level)
    if update.rectification_status is not None:
        fields.append("rectification_status=?")
        params.append(update.rectification_status)
    if not fields:
        raise HTTPException(400, "没有要更新的字段")
    fields.append("updated_at=CURRENT_TIMESTAMP")
    params.append(violation_id)
    conn = get_connection()
    conn.execute(f"UPDATE violations SET {','.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "违规记录更新成功"}


@router.delete("/violations/{violation_id}")
async def delete_violation(violation_id: str):
    """逻辑删除"""
    conn = get_connection()
    conn.execute("UPDATE violations SET is_deleted=1 WHERE id=?", (violation_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "违规记录已删除（逻辑删除）"}


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
            FROM tasks t
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
        """INSERT INTO tasks (task_id,violation_id,store_id,title,assignee,status,created_by,deadline)
           VALUES (?,?,?,?,?,?,?,?)""",
        (task_id, task.get("violation_id"), task["store_id"], task["title"],
         task.get("assignee"), "pending", task.get("created_by", "admin"),
         task.get("deadline"))
    )
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "工单创建成功", "data": {"task_id": task_id}}


@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    conn = get_connection()
    conn.execute("UPDATE tasks SET status=? WHERE task_id=?", (status, task_id))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": f"工单状态已更新为 {status}"}


# ==================== 统计数据 API ====================

@router.get("/stats")
async def get_stats():
    conn = get_connection()
    total_violations = conn.execute("SELECT COUNT(*) FROM violations WHERE is_deleted=0").fetchone()[0]
    pending_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='pending' AND is_deleted=0").fetchone()[0]
    critical_violations = conn.execute("SELECT COUNT(*) FROM violations WHERE level='critical' AND is_deleted=0").fetchone()[0]
    completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed' AND is_deleted=0").fetchone()[0]

    store_stats = conn.execute("""
        SELECT s.id, s.name, COUNT(v.id) as violation_count
        FROM stores s
        LEFT JOIN violations v ON s.id = v.store_id AND v.is_deleted=0
        WHERE s.is_deleted=0
        GROUP BY s.id
        ORDER BY violation_count DESC
    """).fetchall()

    type_stats = conn.execute("""
        SELECT violation_type, COUNT(*) as count
        FROM violations WHERE is_deleted=0
        GROUP BY violation_type ORDER BY count DESC
    """).fetchall()

    conn.close()
    return {
        "code": "0000",
        "data": {
            "total_violations": total_violations,
            "pending_tasks": pending_tasks,
            "critical_violations": critical_violations,
            "completed_tasks": completed_tasks,
            "store_stats": [_dict_from_row(r) for r in store_stats],
            "type_stats": [_dict_from_row(r) for r in type_stats],
        }
    }


# ==================== SQL 查询面板 ====================

class SQLQuery(BaseModel):
    sql: str
    params: Optional[list] = None


@router.post("/sql")
async def execute_sql(query: SQLQuery):
    """执行 SQL 查询（仅 SELECT，写操作拦截）"""
    sql = query.sql.strip().upper()
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


# ==================== 预设 SQL 演示 ====================

@router.get("/demo-sql/presets")
async def get_presets():
    return {"code": "0000", "data": [
        {
            "id": "join_2tables",
            "title": "2 表联合查询（JOIN）",
            "desc": "联表查询违规记录 + 门店，演示外键关联",
            "sql": """SELECT v.id AS 违规ID, v.message AS 违规描述,
       s.name AS 门店名称, v.level AS 级别, v.confidence AS 置信度
FROM violations v
LEFT JOIN stores s ON v.store_id = s.id
WHERE v.is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "group_by_store",
            "title": "分组统计（GROUP BY）",
            "desc": "按门店分组统计违规数量，演示聚合函数",
            "sql": """SELECT s.name AS 门店名称,
       COUNT(v.id) AS 违规总数,
       SUM(CASE WHEN v.level = 'critical' THEN 1 ELSE 0 END) AS 严重违规数,
       ROUND(AVG(v.confidence), 2) AS 平均置信度
FROM stores s
LEFT JOIN violations v ON s.id = v.store_id AND v.is_deleted = 0
WHERE s.is_deleted = 0
GROUP BY s.id
ORDER BY 违规总数 DESC"""
        },
        {
            "id": "logical_delete",
            "title": "逻辑删除演示",
            "desc": "展示逻辑删除前 vs 逻辑删除后的数据对比",
            "sql": """SELECT '已逻辑删除' AS 状态, id, message, level
FROM violations WHERE is_deleted = 1
UNION ALL
SELECT '未删除' AS 状态, id, message, level
FROM violations WHERE is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "foreign_key_check",
            "title": "外键关联检查",
            "desc": "检查违规表中 store_id 是否都能匹配门店表，演示参照完整性",
            "sql": """SELECT v.id AS 违规ID,
       v.store_id AS 门店ID,
       CASE WHEN s.id IS NOT NULL THEN '✅ 有效' ELSE '❌ 无效' END AS 外键状态
FROM violations v
LEFT JOIN stores s ON v.store_id = s.id
WHERE v.is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "pending_tasks_detail",
            "title": "待处理工单详情",
            "desc": "查询所有待处理的整改工单及关联违规记录",
            "sql": """SELECT t.task_id AS 工单ID, t.title AS 工单标题,
       s.name AS 门店, t.assignee AS 负责人,
       v.message AS 违规描述, t.deadline AS 截止日期
FROM tasks t
LEFT JOIN stores s ON t.store_id = s.id
LEFT JOIN violations v ON t.violation_id = v.id
WHERE t.status = 'pending' AND t.is_deleted = 0"""
        }
    ]}


# ==================== E-R 图说明 API ====================

@router.get("/er-info")
async def get_er_info():
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
                    "name": "violations",
                    "comment": "违规记录表（核心）",
                    "columns": ["id(PK)", "store_id(FK→stores)", "message", "violation_type", "level", "confidence", "rectification_status"],
                    "relations": [
                        {"type": "N:1", "target": "stores", "via": "store_id"},
                        {"type": "1:N", "target": "tasks", "via": "violation_id"}
                    ]
                },
                {
                    "name": "users",
                    "comment": "用户表",
                    "columns": ["user_id(PK)", "user_name", "role_type", "phone", "store_ids"],
                    "relations": []
                },
                {
                    "name": "tasks",
                    "comment": "整改工单表",
                    "columns": ["task_id(PK)", "violation_id(FK→violations)", "store_id(FK→stores)", "title", "status", "assignee", "deadline"],
                    "relations": [
                        {"type": "N:1", "target": "stores", "via": "store_id"},
                        {"type": "N:1", "target": "violations", "via": "violation_id"}
                    ]
                }
            ]
        }
    }
