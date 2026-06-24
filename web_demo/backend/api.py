"""
Web Demo CRUD API
权限体系：
- 员工(staff): 仅申诉 + 消息
- 店长(store_manager): 违规记录/工单CRUD + 消息(不能改申诉状态)
- 管理员(enterprise_admin): 审核 + 门店/用户CRUD + 申诉状态 + 消息
- 督导(area_supervisor): 等同店长
"""

from __future__ import annotations

import json
import time
import secrets
import string
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from web_demo.backend.db_init import get_connection

router = APIRouter(prefix="/api/demo", tags=["web-demo"])

# ==================== 审计日志 ====================

def _audit_log(action: str, target_table: str, target_id: str = None, detail: str = None):
    """记录审计日志"""
    if not _current_user:
        return
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, target_table, target_id, detail) VALUES (?,?,?,?,?)",
            (_current_user["user_id"], action, target_table, target_id, detail))
        conn.commit()
        conn.close()
    except Exception:
        pass  # 审计失败不影响主流程

# ==================== 触发器行为 ====================

def _auto_notify(to_user: str, content: str):
    """审核/申诉处理时自动发送通知消息"""
    if not _current_user:
        return
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO messages (from_user, to_user, content) VALUES (?,?,?)",
            (_current_user["user_id"], to_user, content))
        conn.commit()
        conn.close()
    except Exception:
        pass

# ==================== 模拟用户会话 ====================
_LOGIN_USERS = {
    "admin01": {"password": "123456", "user_id": "admin01", "role_type": "enterprise_admin"},
    "super01": {"password": "123456", "user_id": "super01", "role_type": "area_supervisor"},
    "mgr001":  {"password": "123456", "user_id": "mgr001",  "role_type": "store_manager"},
    "mgr002":  {"password": "123456", "user_id": "mgr002",  "role_type": "store_manager"},
    "emp001":  {"password": "123456", "user_id": "emp001",  "role_type": "staff"},
}

# 当前登录用户（简化为全局，Demo 用）
_current_user: Optional[dict] = None

# LLM 配置（用户通过界面设置）
_llm_config: dict = {
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-3.5-turbo",
}


def _permission_denied(msg: str = "权限不足"):
    return JSONResponse({"code": "4003", "message": msg, "data": None}, status_code=403)


def _require_role(*roles: str):
    """检查当前用户角色"""
    if not _current_user:
        return _permission_denied("请先登录")
    if _current_user["role_type"] not in roles:
        return _permission_denied()
    return None


def _is_admin():
    return _current_user and _current_user["role_type"] == "enterprise_admin"


def _is_manager_or_above():
    return _current_user and _current_user["role_type"] in ("enterprise_admin", "area_supervisor", "store_manager")


def _user_store_ids():
    if not _current_user:
        return []
    return json.loads(_current_user.get("store_ids", "[]"))


def _store_filter_clause(alias: str = "v"):
    """门店过滤：管理员看全部，其他人只看自己的门店"""
    if _is_admin():
        return "", []
    stores = _user_store_ids()
    if not stores:
        return f" AND 1=0", []
    placeholders = ",".join(["?"] * len(stores))
    return f" AND {alias}.store_id IN ({placeholders})", stores


class LoginRequest(BaseModel):
    user_id: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    global _current_user
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
    _current_user = dict(row)
    return {"code": "0000", "data": _current_user}

@router.post("/logout")
async def logout():
    global _current_user
    _current_user = None
    return {"code": "0000", "message": "已退出"}

@router.get("/me")
async def get_me():
    if not _current_user:
        return {"code": "4001", "message": "未登录", "data": None}
    return {"code": "0000", "data": _current_user}


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


class StoreCreate(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    region_id: Optional[str] = None


@router.post("/stores")
async def create_store(store: StoreCreate):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO stores (id,name,address,contact_phone,region_id) VALUES (?,?,?,?,?)",
            (store.id, store.name, store.address, store.contact_phone, store.region_id)
        )
        conn.commit()
        return {"code": "0000", "message": "门店创建成功"}
    except Exception as e:
        return {"code": "5000", "message": str(e)}
    finally:
        conn.close()


@router.put("/stores/{store_id}")
async def update_store(store_id: str, data: dict):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    conn = get_connection()
    fields = []
    params = []
    for k in ("name", "address", "contact_phone", "region_id"):
        if k in data:
            fields.append(f"{k}=?")
            params.append(data[k])
    if not fields:
        return {"code": "4000", "message": "没有要更新的字段"}
    params.append(store_id)
    conn.execute(f"UPDATE stores SET {','.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "门店更新成功"}


@router.delete("/stores/{store_id}")
async def delete_store(store_id: str):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    conn = get_connection()
    conn.execute("UPDATE stores SET is_deleted=1 WHERE id=?", (store_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "门店已删除（逻辑删除）"}


# ==================== 用户管理（仅管理员）====================

@router.get("/users")
async def list_users():
    perm = _require_role("enterprise_admin")
    if perm: return perm
    conn = get_connection()
    rows = conn.execute("SELECT user_id, user_name, role_type, phone, store_ids FROM users WHERE is_deleted=0 ORDER BY user_id").fetchall()
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows]}


class UserCreate(BaseModel):
    user_id: str
    user_name: str
    role_type: str
    phone: Optional[str] = None
    store_ids: Optional[list] = []


@router.post("/users")
async def create_user(u: UserCreate):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (user_id,user_name,role_type,phone,store_ids) VALUES (?,?,?,?,?)",
            (u.user_id, u.user_name, u.role_type, u.phone, json.dumps(u.store_ids or []))
        )
        conn.commit()
        return {"code": "0000", "message": "用户创建成功"}
    except Exception as e:
        return {"code": "5000", "message": str(e)}
    finally:
        conn.close()


@router.put("/users/{user_id}")
async def update_user(user_id: str, data: dict):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    conn = get_connection()
    fields = []
    params = []
    for k in ("user_name", "role_type", "phone"):
        if k in data:
            fields.append(f"{k}=?")
            params.append(data[k])
    if "store_ids" in data:
        fields.append("store_ids=?")
        params.append(json.dumps(data["store_ids"]))
    if not fields:
        return {"code": "4000", "message": "没有要更新的字段"}
    params.append(user_id)
    conn.execute(f"UPDATE users SET {','.join(fields)} WHERE user_id=?", params)
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "用户更新成功"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    if user_id == "admin01":
        return {"code": "4000", "message": "不能删除主管理员"}
    conn = get_connection()
    conn.execute("UPDATE users SET is_deleted=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "用户已删除"}


# ==================== 违规记录 API ====================

@router.get("/violations")
async def list_violations(
    store_id: Optional[str] = None,
    level: Optional[str] = None,
    violation_type: Optional[str] = None,
    review_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    if not _current_user:
        return _permission_denied("请先登录")
    conn = get_connection()
    where = ["v.is_deleted=0"]
    params = []

    store_clause, store_params = _store_filter_clause("v")
    where.append(store_clause.lstrip(" AND "))
    params.extend(store_params)

    if store_id:
        where.append("v.store_id=?")
        params.append(store_id)
    if level:
        where.append("v.level=?")
        params.append(level)
    if violation_type:
        where.append("v.violation_type=?")
        params.append(violation_type)
    if review_status:
        where.append("v.review_status=?")
        params.append(review_status)

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


class ViolationCreate(BaseModel):
    store_id: str
    message: str
    violation_type: str = "A00"
    level: str = "medium"
    confidence: float = 0.8
    timestamp: Optional[str] = None


@router.post("/violations")
async def create_violation(v: ViolationCreate):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    violation_id = _generate_id("VIO")
    ts = v.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute(
        """INSERT INTO violations (id,store_id,message,violation_type,level,confidence,timestamp)
           VALUES (?,?,?,?,?,?,?)""",
        (violation_id, v.store_id, v.message, v.violation_type, v.level, v.confidence, ts))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "违规记录创建成功", "data": {"id": violation_id}}


class ViolationUpdate(BaseModel):
    message: Optional[str] = None
    level: Optional[str] = None
    violation_type: Optional[str] = None
    confidence: Optional[float] = None
    rectification_status: Optional[str] = None


@router.put("/violations/{violation_id}")
async def update_violation(violation_id: str, update: ViolationUpdate):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    fields = []
    params = []
    for k in ("message", "level", "violation_type", "confidence", "rectification_status"):
        val = getattr(update, k, None)
        if val is not None:
            fields.append(f"{k}=?")
            params.append(val)
    if not fields:
        return {"code": "4000", "message": "没有要更新的字段"}
    fields.append("updated_at=CURRENT_TIMESTAMP")
    params.append(violation_id)
    conn = get_connection()
    conn.execute(f"UPDATE violations SET {','.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "违规记录更新成功"}


@router.delete("/violations/{violation_id}")
async def delete_violation(violation_id: str):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    conn = get_connection()
    conn.execute("UPDATE violations SET is_deleted=1 WHERE id=?", (violation_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "违规记录已删除"}


# ==================== 审核（仅管理员）====================

class ReviewAction(BaseModel):
    review_status: str  # approved / rejected
    remark: Optional[str] = None


@router.put("/violations/{violation_id}/review")
async def review_violation(violation_id: str, action: ReviewAction):
    perm = _require_role("enterprise_admin")
    if perm: return perm
    if action.review_status not in ("approved", "rejected"):
        return {"code": "4000", "message": "审核状态只能为 approved 或 rejected"}
    conn = get_connection()
    row = conn.execute("SELECT store_id, message FROM violations WHERE id=?", (violation_id,)).fetchone()
    store_id = row["store_id"] if row else None
    message = row["message"] if row else ""
    conn.execute(
        "UPDATE violations SET review_status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (action.review_status, violation_id))
    conn.commit()
    # 触发器：审核后通知相关门店店长（在 conn 关闭前查询）
    if store_id:
        store_users = conn.execute("SELECT user_id FROM users WHERE store_ids LIKE ? AND is_deleted=0", (f'%{store_id}%',)).fetchall()
        for u in store_users:
            _auto_notify(u["user_id"], f"违规记录 {violation_id} 审核结果: {action.review_status} - {message}")
    conn.close()
    _audit_log(action.review_status, "violations", violation_id, f"审核{violation_id}: {action.review_status}")
    return {"code": "0000", "message": f"审核完成: {action.review_status}"}


# ==================== 申诉 ====================

class AppealRequest(BaseModel):
    appeal_reason: str


@router.put("/violations/{violation_id}/appeal")
async def appeal_violation(violation_id: str, req: AppealRequest):
    """员工提起申诉（仅 staff）"""
    perm = _require_role("staff")
    if perm: return perm
    conn = get_connection()
    conn.execute(
        "UPDATE violations SET appeal_status='pending', appeal_reason=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (req.appeal_reason, violation_id))
    conn.commit()
    conn.close()
    _audit_log("appeal", "violations", violation_id, f"申诉: {req.appeal_reason}")
    _auto_notify("admin01", f"员工 {_current_user['user_id']} 对 {violation_id} 提起申诉: {req.appeal_reason}")
    return {"code": "0000", "message": "申诉已提交"}


class AppealResolve(BaseModel):
    appeal_status: str  # resolved / rejected


@router.put("/violations/{violation_id}/appeal/resolve")
async def resolve_appeal(violation_id: str, action: AppealResolve):
    """管理员处理申诉"""
    perm = _require_role("enterprise_admin")
    if perm: return perm
    if action.appeal_status not in ("resolved", "rejected"):
        return {"code": "4000", "message": "申诉处理状态只能为 resolved 或 rejected"}
    conn = get_connection()
    conn.execute(
        "UPDATE violations SET appeal_status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (action.appeal_status, violation_id))
    conn.commit()
    conn.close()
    _audit_log("appeal_resolve", "violations", violation_id, f"申诉处理: {action.appeal_status}")
    _auto_notify("emp001", f"管理员已处理你对 {violation_id} 的申诉: {action.appeal_status}")
    return {"code": "0000", "message": f"申诉已处理: {action.appeal_status}"}


# ==================== 整改工单 API ====================

@router.get("/tasks")
async def list_tasks(store_id: Optional[str] = None, status: Optional[str] = None):
    if not _current_user:
        return _permission_denied("请先登录")
    conn = get_connection()
    where = ["t.is_deleted=0"]
    params = []

    store_clause, store_params = _store_filter_clause("t")
    where.append(store_clause.lstrip(" AND "))
    params.extend(store_params)

    if store_id:
        where.append("t.store_id=?")
        params.append(store_id)
    if status:
        where.append("t.status=?")
        params.append(status)

    rows = conn.execute(
        f"""SELECT t.*, s.name as store_name, v.message as violation_message
            FROM rectification_tasks t
            LEFT JOIN stores s ON t.store_id = s.id
            LEFT JOIN violations v ON t.violation_id = v.id
            WHERE {' AND '.join(where)}
            ORDER BY t.created_at DESC""",
        params).fetchall()
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows]}


@router.post("/tasks")
async def create_task(task: dict):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    task_id = _generate_id("TSK")
    conn = get_connection()
    conn.execute(
        """INSERT INTO rectification_tasks (task_id,violation_id,store_id,title,assignee,status,created_by,deadline)
           VALUES (?,?,?,?,?,?,?,?)""",
        (task_id, task.get("violation_id"), task["store_id"], task["title"],
         task.get("assignee"), "pending", task.get("created_by", _current_user["user_id"]),
         task.get("deadline")))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "工单创建成功", "data": {"task_id": task_id}}


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, task: dict):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    fields = []
    params = []
    for k in ("title", "assignee", "status", "deadline"):
        if k in task:
            fields.append(f"{k}=?")
            params.append(task[k])
    if not fields:
        return {"code": "4000", "message": "没有要更新的字段"}
    params.append(task_id)
    conn = get_connection()
    conn.execute(f"UPDATE rectification_tasks SET {','.join(fields)} WHERE task_id=?", params)
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "工单更新成功"}


@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    conn = get_connection()
    conn.execute("UPDATE rectification_tasks SET status=? WHERE task_id=?", (status, task_id))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": f"工单状态已更新为 {status}"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    perm = _require_role("enterprise_admin", "area_supervisor", "store_manager")
    if perm: return perm
    conn = get_connection()
    conn.execute("UPDATE rectification_tasks SET is_deleted=1 WHERE task_id=?", (task_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "工单已删除"}


# ==================== 消息 API ====================

@router.get("/messages")
async def list_messages():
    if not _current_user:
        return _permission_denied("请先登录")
    conn = get_connection()
    uid = _current_user["user_id"]
    rows = conn.execute(
        """SELECT m.*, u.user_name as from_name
           FROM messages m
           LEFT JOIN users u ON m.from_user = u.user_id
           WHERE m.to_user = ?
           ORDER BY m.created_at DESC""",
        (uid,)).fetchall()
    unread = conn.execute("SELECT COUNT(*) FROM messages WHERE to_user=? AND is_read=0", (uid,)).fetchone()[0]
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows], "unread": unread}


@router.get("/messages/unread")
async def unread_count():
    if not _current_user:
        return {"code": "0000", "data": {"unread": 0}}
    conn = get_connection()
    unread = conn.execute("SELECT COUNT(*) FROM messages WHERE to_user=? AND is_read=0",
                          (_current_user["user_id"],)).fetchone()[0]
    conn.close()
    return {"code": "0000", "data": {"unread": unread}}


class MessageCreate(BaseModel):
    to_user: str
    content: str


@router.post("/messages")
async def send_message(msg: MessageCreate):
    if not _current_user:
        return _permission_denied("请先登录")
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (from_user,to_user,content) VALUES (?,?,?)",
        (_current_user["user_id"], msg.to_user, msg.content))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "消息已发送"}


@router.put("/messages/{msg_id}/read")
async def mark_read(msg_id: int):
    conn = get_connection()
    conn.execute("UPDATE messages SET is_read=1 WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return {"code": "0000", "message": "已读"}


@router.get("/messages/users")
async def message_users():
    """获取可发消息的用户列表"""
    if not _current_user:
        return _permission_denied("请先登录")
    conn = get_connection()
    rows = conn.execute(
        "SELECT user_id, user_name, role_type FROM users WHERE is_deleted=0 AND user_id != ? ORDER BY user_id",
        (_current_user["user_id"],)).fetchall()
    conn.close()
    return {"code": "0000", "data": [_dict_from_row(r) for r in rows]}


# ==================== 统计数据 API ====================

@router.get("/stats")
async def get_stats():
    if not _current_user:
        return _permission_denied("请先登录")
    conn = get_connection()

    store_clause, store_params = _store_filter_clause()
    base_where = "v.is_deleted=0" + store_clause

    total_violations = conn.execute(f"SELECT COUNT(*) FROM violations v WHERE {base_where}", store_params).fetchone()[0]
    pending_tasks = conn.execute(f"""SELECT COUNT(*) FROM rectification_tasks t WHERE t.is_deleted=0 AND t.status='pending' {store_clause.replace('v.','t.')}""", store_params).fetchone()[0]
    critical_violations = conn.execute(f"SELECT COUNT(*) FROM violations v WHERE {base_where} AND v.level='critical'", store_params).fetchone()[0]
    pending_review = conn.execute(f"SELECT COUNT(*) FROM violations v WHERE {base_where} AND v.review_status='pending'", store_params).fetchone()[0]

    store_stats = conn.execute(f"""
        SELECT s.id, s.name, COUNT(v.id) as violation_count
        FROM stores s
        LEFT JOIN violations v ON s.id = v.store_id AND v.is_deleted=0
        WHERE s.is_deleted=0
        GROUP BY s.id ORDER BY violation_count DESC
    """).fetchall()

    type_stats = conn.execute(f"""
        SELECT violation_type, COUNT(*) as count
        FROM violations v WHERE {base_where}
        GROUP BY violation_type ORDER BY count DESC
    """, store_params).fetchall()

    conn.close()
    return {
        "code": "0000",
        "data": {
            "total_violations": total_violations,
            "pending_tasks": pending_tasks,
            "critical_violations": critical_violations,
            "pending_review": pending_review,
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
        return {"code": "0000", "data": {"columns": columns, "rows": data, "count": len(data)}}
    except Exception as e:
        return {"code": "5000", "message": f"SQL 执行错误: {str(e)}", "data": None}


# ==================== NL → SQL（AI 自然语言转 SQL）====================

class NLQuery(BaseModel):
    question: str


@router.post("/nl-sql")
async def nl_to_sql(query: NLQuery):
    """自然语言转 SQL 查询（接入 AI Text-to-SQL 管道）"""
    try:
        # 检查是否配置了 API Key
        if not _llm_config.get("api_key"):
            return {"code": "4000", "message": "请先在下方设置 LLM API Key", "data": None}

        # 动态设置 LLM 配置到环境变量
        import os
        os.environ["LLM_API_KEY"] = _llm_config["api_key"]
        os.environ["LLM_BASE_URL"] = _llm_config["base_url"]
        os.environ["LLM_MODEL_NAME"] = _llm_config["model_name"]

        # 重新加载配置（覆盖默认值）
        from src.core.config import llm_settings
        llm_settings.llm_api_key = _llm_config["api_key"]
        llm_settings.llm_base_url = _llm_config["base_url"]
        llm_settings.llm_model_name = _llm_config["model_name"]

        from src.agents.data_agent.sql_generator import generate_sql_with_retry
        from src.core.llm_client import AsyncLLMClient

        # 构建当前数据库 schema 描述
        schema_text = """
## 门店表 (stores)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR | 门店ID (PK) |
| name | VARCHAR | 门店名称 |
| address | VARCHAR | 地址 |
| contact_phone | VARCHAR | 联系电话 |
| region_id | VARCHAR | 区域ID |

## 违规记录表 (violations)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR | 违规ID (PK) |
| store_id | VARCHAR | 门店ID (FK) |
| message | VARCHAR | 违规详情 |
| violation_type | VARCHAR | 违规类型 (A00-A05) |
| level | VARCHAR | 等级 (low/medium/high/critical) |
| confidence | FLOAT | 置信度 |
| review_status | VARCHAR | 审核状态 (pending/approved/rejected) |
| appeal_status | VARCHAR | 申诉状态 (none/pending/resolved/rejected) |
| rectification_status | VARCHAR | 整改状态 |
| timestamp | DATETIME | 创建时间 |

## 整改工单表 (rectification_tasks)
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | VARCHAR | 工单ID (PK) |
| violation_id | VARCHAR | 关联违规ID (FK) |
| store_id | VARCHAR | 门店ID (FK) |
| title | VARCHAR | 工单标题 |
| assignee | VARCHAR | 负责人 |
| status | VARCHAR | 状态 (pending/processing/completed) |
| created_by | VARCHAR | 创建人 |
| deadline | DATETIME | 截止日期 |
"""

        result = await generate_sql_with_retry(
            user_query=query.question,
            schema_context=schema_text,
            trace_id="web-demo"
        )

        # 执行生成的 SQL
        conn = get_connection()
        cursor = conn.execute(result.generated_sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        conn.close()

        return {
            "code": "0000",
            "data": {
                "generated_sql": result.generated_sql,
                "columns": columns,
                "rows": data,
                "count": len(data)
            }
        }
    except Exception as e:
        return {"code": "5000", "message": f"AI 生成 SQL 失败: {str(e)}", "data": None}


# ==================== LLM 配置 API ====================

class LLMConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-3.5-turbo"

@router.post("/llm-config")
async def save_llm_config(config: LLMConfig):
    """保存用户输入的 LLM 配置"""
    global _llm_config
    _llm_config = {"api_key": config.api_key, "base_url": config.base_url, "model_name": config.model_name}
    return {"code": "0000", "message": "LLM 配置已保存"}

@router.get("/llm-config")
async def get_llm_config():
    """获取当前 LLM 配置（隐藏 API Key）"""
    cfg = dict(_llm_config)
    cfg["api_key"] = (cfg["api_key"][:8] + "****" + cfg["api_key"][-4:]) if len(cfg["api_key"]) > 12 else ("****" if cfg["api_key"] else "")
    return {"code": "0000", "data": cfg}

# ==================== 预设 SQL ====================

@router.get("/demo-sql/presets")
async def get_presets():
    return {"code": "0000", "data": [
        {
            "id": "join_violation_store",
            "title": "违规+门店联合查询（JOIN）",
            "desc": "联表查询违规记录 + 门店，演示参照完整性",
            "sql": """SELECT v.id AS 违规ID, v.message AS 违规详情,
       s.name AS 门店名称, v.violation_type AS 违规类型,
       v.level AS 等级, v.confidence AS 置信度,
       v.review_status AS 审核状态, v.appeal_status AS 申诉状态
FROM violations v
LEFT JOIN stores s ON v.store_id = s.id
WHERE v.is_deleted = 0
LIMIT 10"""
        },
        {
            "id": "group_by_store",
            "title": "分组统计（GROUP BY）",
            "desc": "按门店分组统计违规数量",
            "sql": """SELECT s.name AS 门店名称,
       COUNT(v.id) AS 违规总数,
       SUM(CASE WHEN v.level = 'critical' THEN 1 ELSE 0 END) AS 严重违规数,
       ROUND(AVG(v.confidence), 2) AS 平均置信度
FROM stores s
LEFT JOIN violations v ON s.id = v.store_id AND v.is_deleted = 0
WHERE s.is_deleted = 0
GROUP BY s.id ORDER BY 违规总数 DESC"""
        },
        {
            "id": "logical_delete",
            "title": "逻辑删除演示",
            "desc": "逻辑删除前 vs 逻辑删除后",
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
            "desc": "检查违规表 store_id 参照完整性",
            "sql": """SELECT v.id AS 违规ID, v.store_id,
       CASE WHEN s.id IS NOT NULL THEN '有效' ELSE '无效' END AS 外键状态
FROM violations v LEFT JOIN stores s ON v.store_id = s.id
WHERE v.is_deleted = 0 LIMIT 10"""
        },
        {
            "id": "pending_tasks_detail",
            "title": "待处理工单详情",
            "desc": "待处理的整改工单及关联违规",
            "sql": """SELECT t.task_id AS 工单ID, t.title AS 工单标题,
       s.name AS 门店, t.assignee AS 负责人,
       v.message AS 关联违规, t.deadline AS 截止日期
FROM rectification_tasks t
LEFT JOIN stores s ON t.store_id = s.id
LEFT JOIN violations v ON t.violation_id = v.id
WHERE t.status = 'pending' AND t.is_deleted = 0"""
        }
    ]}


# ==================== E-R 图 ====================

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
                    "comment": "违规记录表（整合告警+违规事件）",
                    "columns": ["id(PK)", "store_id(FK→stores)", "message", "violation_type", "level", "confidence",
                                "review_status", "appeal_status", "rectification_status", "timestamp"],
                    "relations": [{"type": "N:1", "target": "stores", "via": "store_id"}]
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
                    "columns": ["task_id(PK)", "violation_id(FK→violations)", "store_id(FK→stores)",
                                "title", "status", "assignee", "created_by", "deadline"],
                    "relations": [
                        {"type": "N:1", "target": "violations", "via": "violation_id"},
                        {"type": "N:1", "target": "stores", "via": "store_id"}
                    ]
                },
                {
                    "name": "messages",
                    "comment": "消息表",
                    "columns": ["id(PK)", "from_user(FK→users)", "to_user(FK→users)", "content", "is_read", "created_at"],
                    "relations": [
                        {"type": "N:1", "target": "users", "via": "from_user"},
                        {"type": "N:1", "target": "users", "via": "to_user"}
                    ]
                }
            ]
        }
    }