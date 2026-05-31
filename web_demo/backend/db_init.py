"""
数据库初始化脚本（SQLite）
展示数据库设计知识点：
- 实体完整性（PRIMARY KEY, UNIQUE）
- 参照完整性（FOREIGN KEY）
- 逻辑删除（is_deleted）
- 索引（INDEX）
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safefood.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 表1：门店表
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

    # 表2：违规记录表（核心表，外键→stores）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id                  VARCHAR(32)     PRIMARY KEY,
            store_id            VARCHAR(32)     NOT NULL,
            message             VARCHAR(512)    NOT NULL,
            violation_type      VARCHAR(3)      NOT NULL DEFAULT 'A00',
            level               VARCHAR(16)     NOT NULL,
            confidence          REAL            NOT NULL,
            rectification_status VARCHAR(16)    NOT NULL DEFAULT 'pending',
            timestamp           DATETIME        NOT NULL,
            created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted          INTEGER         NOT NULL DEFAULT 0,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT
        )
    """)

    # 表3：用户表（UNIQUE user_id）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            user_id         VARCHAR(32) NOT NULL UNIQUE,
            user_name       VARCHAR(64) NOT NULL,
            role_type       VARCHAR(32) NOT NULL,
            phone           VARCHAR(16) DEFAULT NULL,
            store_ids       TEXT        DEFAULT '[]',
            is_deleted      INTEGER     NOT NULL DEFAULT 0
        )
    """)

    # 表4：整改工单表（外键→stores）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            task_id         VARCHAR(32) NOT NULL UNIQUE,
            violation_id    VARCHAR(32) DEFAULT NULL,
            store_id        VARCHAR(32) NOT NULL,
            title           VARCHAR(256) NOT NULL,
            assignee        VARCHAR(64) DEFAULT NULL,
            status          VARCHAR(16) NOT NULL DEFAULT 'pending',
            created_by      VARCHAR(32) NOT NULL,
            created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deadline        DATETIME    DEFAULT NULL,
            is_deleted      INTEGER     NOT NULL DEFAULT 0,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT
        )
    """)

    # 种子数据
    cursor.execute("SELECT COUNT(*) FROM stores")
    if cursor.fetchone()[0] == 0:
        # stores
        cursor.executemany(
            "INSERT INTO stores (id,name,address,contact_phone,region_id,is_deleted) VALUES (?,?,?,?,?,?)",
            [("STORE001","南山旗舰店","深圳市南山区科技园","13800001111","REGION_SZ",0),
             ("STORE002","福田中心店","深圳市福田区CBD","13800002222","REGION_SZ",0),
             ("STORE003","广州天河店","广州市天河区体育中心","13800003333","REGION_GZ",0),
             ("STORE004","广州白云店","广州市白云区万达广场","13800004444","REGION_GZ",0),
             ("STORE005","上海陆家嘴店","上海市浦东新区陆家嘴","13800005555","REGION_SH",0)]
        )
        # violations
        cursor.executemany(
            "INSERT INTO violations (id,store_id,message,violation_type,level,confidence,rectification_status,timestamp,is_deleted) VALUES (?,?,?,?,?,?,?,?,?)",
            [("VIO001","STORE001","检测到: 未戴口罩","A01","high",0.95,"completed","2026-05-20 08:30:00",0),
             ("VIO002","STORE001","检测到: 未戴口罩","A01","high",0.88,"processing","2026-05-21 09:15:00",0),
             ("VIO003","STORE001","检测到: 未穿工作服","A03","medium",0.76,"pending","2026-05-21 10:00:00",0),
             ("VIO004","STORE002","检测到: 未戴工帽","A02","medium",0.82,"pending","2026-05-21 10:30:00",0),
             ("VIO005","STORE003","检测到: 抽烟","A05","high",0.91,"processing","2026-05-21 11:00:00",0),
             ("VIO006","STORE004","检测到: 未戴口罩","A01","high",0.93,"pending","2026-05-21 11:30:00",0),
             ("VIO007","STORE002","检测到: 鼠患","A04","critical",0.97,"pending","2026-05-21 12:00:00",0),
             ("VIO008","STORE005","检测到: 未戴口罩","A01","high",0.85,"pending","2026-05-21 13:00:00",0),
             ("VIO009","STORE003","检测到: 未穿工作服","A03","low",0.65,"pending","2026-05-21 14:00:00",0),
             ("VIO010","STORE005","检测到: 未戴工帽","A02","medium",0.79,"pending","2026-05-21 14:30:00",0)]
        )
        # users
        cursor.executemany(
            "INSERT INTO users (user_id,user_name,role_type,phone,store_ids,is_deleted) VALUES (?,?,?,?,?,?)",
            [("admin01","张总","enterprise_admin","13900000001",'["STORE001","STORE002","STORE003","STORE004","STORE005"]',0),
             ("super01","李督导","area_supervisor","13900000002",'["STORE001","STORE002"]',0),
             ("mgr001","王店长","store_manager","13900000003",'["STORE001"]',0),
             ("mgr002","赵店长","store_manager","13900000004",'["STORE002"]',0),
             ("emp001","小李","staff","13900000005",'["STORE001"]',0)]
        )
        # tasks
        cursor.executemany(
            "INSERT INTO tasks (task_id,violation_id,store_id,title,assignee,status,created_by,deadline) VALUES (?,?,?,?,?,?,?,?)",
            [("TSK001","VIO001","STORE001","南山店-未戴口罩整改","王店长","completed","admin01","2026-05-25"),
             ("TSK002","VIO002","STORE001","南山店-再次未戴口罩整改","王店长","processing","admin01","2026-05-28"),
             ("TSK003","VIO003","STORE001","南山店-未穿工作服整改","王店长","pending","super01","2026-05-28"),
             ("TSK004","VIO005","STORE003","天河店-抽烟整改","赵店长","pending","admin01","2026-05-26"),
             ("TSK005","VIO007","STORE002","福田店-鼠患整改","赵店长","pending","admin01","2026-05-24")]
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
