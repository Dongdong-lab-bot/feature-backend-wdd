"""
数据库初始化脚本（SQLite）
表结构：
- stores（门店表）
- users（用户表，含 store_ids JSON 字段）
- violations（违规记录表，合并原 alerts + violation_events）
- rectification_tasks（整改工单表）
- messages（消息表）
"""

import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safefood.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ========================
    # 表1：门店表
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id              VARCHAR(32)     PRIMARY KEY,
            name            VARCHAR(128)    NOT NULL,
            address         VARCHAR(256)    DEFAULT NULL,
            contact_phone   VARCHAR(16)     DEFAULT NULL,
            region_id       VARCHAR(32)     DEFAULT NULL,
            is_deleted      INTEGER         NOT NULL DEFAULT 0
        )
    """)

    # ========================
    # 表2：用户表（含 store_ids JSON 字段）
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            user_id         VARCHAR(32) NOT NULL UNIQUE,
            user_name       VARCHAR(64) NOT NULL,
            role_type       VARCHAR(32) NOT NULL,
            phone           VARCHAR(16) DEFAULT NULL,
            store_ids       TEXT         DEFAULT '[]',
            is_deleted      INTEGER     NOT NULL DEFAULT 0
        )
    """)

    # ========================
    # 表3：违规记录表（合并 alerts + violation_events）
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id                  VARCHAR(32)     PRIMARY KEY,
            store_id            VARCHAR(32)     NOT NULL,
            message             VARCHAR(512)    NOT NULL,
            violation_type      VARCHAR(3)      NOT NULL DEFAULT 'A00',
            level               VARCHAR(16)     NOT NULL DEFAULT 'medium',
            confidence          REAL            NOT NULL DEFAULT 0.8,
            review_status       VARCHAR(16)     NOT NULL DEFAULT 'pending',
            appeal_status       VARCHAR(16)     NOT NULL DEFAULT 'none',
            appeal_reason       TEXT            DEFAULT NULL,
            rectification_status VARCHAR(16)    DEFAULT 'pending',
            timestamp           DATETIME        NOT NULL,
            updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted          INTEGER         NOT NULL DEFAULT 0,
            FOREIGN KEY (store_id) REFERENCES stores(id)
        )
    """)

    # ========================
    # 表4：整改工单表
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rectification_tasks (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            task_id         VARCHAR(32) NOT NULL UNIQUE,
            violation_id    VARCHAR(32) NOT NULL,
            store_id        VARCHAR(32) NOT NULL,
            title           VARCHAR(256) NOT NULL,
            assignee        VARCHAR(64)  DEFAULT NULL,
            status          VARCHAR(16) NOT NULL DEFAULT 'pending',
            created_by      VARCHAR(32) DEFAULT 'admin',
            deadline        DATETIME    DEFAULT NULL,
            created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted      INTEGER     NOT NULL DEFAULT 0,
            FOREIGN KEY (violation_id) REFERENCES violations(id),
            FOREIGN KEY (store_id) REFERENCES stores(id)
        )
    """)

    # ========================
    # 表5：消息表
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            from_user       VARCHAR(32) NOT NULL,
            to_user         VARCHAR(32) NOT NULL,
            content         TEXT        NOT NULL,
            is_read         INTEGER     NOT NULL DEFAULT 0,
            created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user) REFERENCES users(user_id),
            FOREIGN KEY (to_user)   REFERENCES users(user_id)
        )
    """)

    # ========================
    # 种子数据
    # ========================
    cursor.execute("SELECT COUNT(*) FROM stores")
    if cursor.fetchone()[0] == 0:
        # ----- stores（5条）-----
        cursor.executemany(
            "INSERT INTO stores (id,name,address,contact_phone,region_id,is_deleted) VALUES (?,?,?,?,?,?)",
            [("STORE001","南山旗舰店","深圳市南山区科技园","13800001111","REGION_SZ",0),
             ("STORE002","福田中心店","深圳市福田区CBD","13800002222","REGION_SZ",0),
             ("STORE003","广州天河店","广州市天河区体育中心","13800003333","REGION_GZ",0),
             ("STORE004","广州白云店","广州市白云区万达广场","13800004444","REGION_GZ",0),
             ("STORE005","上海陆家嘴店","上海市浦东新区陆家嘴","13800005555","REGION_SH",0)]
        )

        # ----- users（5条，含 store_ids JSON）-----
        cursor.executemany(
            "INSERT INTO users (user_id,user_name,role_type,phone,store_ids,is_deleted) VALUES (?,?,?,?,?,?)",
            [("admin01","张总","enterprise_admin","13900000001",
              json.dumps(["STORE001","STORE002","STORE003","STORE004","STORE005"]),0),
             ("super01","李督导","area_supervisor","13900000002",
              json.dumps(["STORE001","STORE002"]),0),
             ("mgr001","王店长","store_manager","13900000003",
              json.dumps(["STORE001"]),0),
             ("mgr002","赵店长","store_manager","13900000004",
              json.dumps(["STORE002"]),0),
             ("emp001","小李","staff","13900000005",
              json.dumps(["STORE001"]),0)]
        )

        # ----- violations（5条）-----
        cursor.executemany(
            """INSERT INTO violations
               (id,store_id,message,violation_type,level,confidence,
                review_status,appeal_status,rectification_status,timestamp,is_deleted)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [("VIO001","STORE001","检测到: 未戴口罩","A01","high",0.95,
              "approved","none","verified","2026-05-20 08:30:00",0),
             ("VIO002","STORE001","检测到: 未戴口罩","A01","high",0.88,
              "approved","none","verified","2026-05-21 09:15:00",0),
             ("VIO003","STORE001","检测到: 未穿工作服","A03","medium",0.76,
              "pending","none","verified","2026-05-21 10:00:00",0),
             ("VIO004","STORE003","检测到: 抽烟","A05","high",0.91,
              "pending","none","verified","2026-05-21 11:00:00",0),
             ("VIO005","STORE002","检测到: 鼠患","A04","critical",0.97,
              "pending","none","verified","2026-05-21 12:00:00",0)]
        )

        # ----- rectification_tasks（5条）-----
        cursor.executemany(
            """INSERT INTO rectification_tasks
               (task_id,violation_id,store_id,title,assignee,status,created_by,deadline,created_at,is_deleted)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [("TSK001","VIO001","STORE001","南山店-未戴口罩整改","王店长","completed","admin01",
              "2026-05-25","2026-05-20 08:35:00",0),
             ("TSK002","VIO002","STORE001","南山店-再次未戴口罩整改","王店长","processing","admin01",
              "2026-05-28","2026-05-21 09:20:00",0),
             ("TSK003","VIO003","STORE001","南山店-未穿工作服整改","王店长","pending","super01",
              "2026-05-28","2026-05-21 10:05:00",0),
             ("TSK004","VIO004","STORE003","天河店-抽烟整改","赵店长","pending","admin01",
              "2026-05-26","2026-05-21 11:05:00",0),
             ("TSK005","VIO005","STORE002","福田店-鼠患整改","赵店长","pending","admin01",
              "2026-05-24","2026-05-21 12:05:00",0)]
        )

        # ----- messages（2条）-----
        cursor.executemany(
            "INSERT INTO messages (from_user,to_user,content,is_read,created_at) VALUES (?,?,?,?,?)",
            [("admin01","mgr001","请尽快处理南山店未戴口罩的整改工单",0,"2026-05-21 10:00:00"),
             ("admin01","mgr002","福田店鼠患问题严重，请优先处理",0,"2026-05-21 12:10:00")]
        )

        conn.commit()

    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")


def drop_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️  数据库已删除: {DB_PATH}")


if __name__ == "__main__":
    init_db()