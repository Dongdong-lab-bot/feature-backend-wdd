"""
数据库初始化脚本（SQLite）
重构版：5张表
- stores（门店表）
- users（用户表）
- user_store（用户门店关联表）
- violations（违规记录表）
- tasks（整改工单表）
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
    # 表2：用户表（移除 store_ids）
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            user_id         VARCHAR(32) NOT NULL UNIQUE,
            user_name       VARCHAR(64) NOT NULL,
            role_type       VARCHAR(32) NOT NULL,
            phone           VARCHAR(16) DEFAULT NULL,
            is_deleted      INTEGER     NOT NULL DEFAULT 0
        )
    """)

    # ========================
    # 表3：用户门店关联表（多对多）
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_store (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            user_id         VARCHAR(32) NOT NULL,
            store_id        VARCHAR(32) NOT NULL,
            is_deleted      INTEGER     NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id)  REFERENCES users(user_id) ON DELETE RESTRICT,
            FOREIGN KEY (store_id) REFERENCES stores(id)     ON DELETE RESTRICT,
            UNIQUE(user_id, store_id)
        )
    """)

    # ========================
    # 表4：违规记录表（4个外键）
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id                  VARCHAR(32)     PRIMARY KEY,
            user_id             VARCHAR(32)     DEFAULT NULL,
            store_id            VARCHAR(32)     NOT NULL,
            reporter_id         VARCHAR(32)     NOT NULL,
            auditor_id          VARCHAR(32)     DEFAULT NULL,
            message             VARCHAR(512)    NOT NULL,
            violation_type      VARCHAR(3)      NOT NULL DEFAULT 'A00',
            level               VARCHAR(16)     NOT NULL,
            confidence          REAL            NOT NULL,
            status              VARCHAR(16)     NOT NULL DEFAULT 'pending',
            verify_result       VARCHAR(16)     DEFAULT 'unknown',
            timestamp           DATETIME        NOT NULL,
            created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted          INTEGER         NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id)     REFERENCES users(user_id) ON DELETE RESTRICT,
            FOREIGN KEY (store_id)    REFERENCES stores(id)     ON DELETE RESTRICT,
            FOREIGN KEY (reporter_id) REFERENCES users(user_id) ON DELETE RESTRICT,
            FOREIGN KEY (auditor_id)  REFERENCES users(user_id) ON DELETE RESTRICT
        )
    """)

    # ========================
    # 表5：整改工单表（3个外键）
    # 无 store_id / description，有 create_time
    # ========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            task_id         VARCHAR(32) NOT NULL UNIQUE,
            violation_id    VARCHAR(32) NOT NULL UNIQUE,
            title           VARCHAR(256) NOT NULL,
            issuer_id       VARCHAR(32) NOT NULL,
            assignee_id     VARCHAR(32) DEFAULT NULL,
            status          VARCHAR(16) NOT NULL DEFAULT 'pending',
            create_time     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deadline        DATETIME    DEFAULT NULL,
            is_deleted      INTEGER     NOT NULL DEFAULT 0,
            FOREIGN KEY (violation_id) REFERENCES violations(id) ON DELETE RESTRICT,
            FOREIGN KEY (issuer_id)    REFERENCES users(user_id) ON DELETE RESTRICT,
            FOREIGN KEY (assignee_id)  REFERENCES users(user_id) ON DELETE RESTRICT
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

        # ----- users（5条，移除 store_ids）-----
        cursor.executemany(
            "INSERT INTO users (user_id,user_name,role_type,phone,is_deleted) VALUES (?,?,?,?,?)",
            [("admin01","张总","enterprise_admin","13900000001",0),
             ("super01","李督导","area_supervisor","13900000002",0),
             ("mgr001","王店长","store_manager","13900000003",0),
             ("mgr002","赵店长","store_manager","13900000004",0),
             ("emp001","小李","staff","13900000005",0)]
        )

        # ----- user_store（从原 store_ids 解构）-----
        cursor.executemany(
            "INSERT INTO user_store (user_id,store_id,is_deleted) VALUES (?,?,?)",
            [("admin01","STORE001",0), ("admin01","STORE002",0),
             ("admin01","STORE003",0), ("admin01","STORE004",0),
             ("admin01","STORE005",0),
             ("super01","STORE001",0), ("super01","STORE002",0),
             ("mgr001","STORE001",0),
             ("mgr002","STORE002",0),
             ("emp001","STORE001",0)]
        )

        # ----- violations（5条，合并原 alerts + violation_events）-----
        cursor.executemany(
            """INSERT INTO violations
               (id,user_id,store_id,reporter_id,auditor_id,message,
                violation_type,level,confidence,status,verify_result,timestamp,is_deleted)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [("ALT001","emp001","STORE001","admin01","admin01",
              "检测到: 未戴口罩","A01","high",0.95,"verified","true_violation",
              "2026-05-20 08:30:00",0),
             ("ALT002","emp001","STORE001","admin01","admin01",
              "检测到: 未戴口罩","A01","high",0.88,"verified","true_violation",
              "2026-05-21 09:15:00",0),
             ("ALT003","emp001","STORE001","admin01","admin01",
              "检测到: 未穿工作服","A03","medium",0.76,"verified","true_violation",
              "2026-05-21 10:00:00",0),
             ("ALT005",None,"STORE003","admin01","admin01",
              "检测到: 抽烟","A05","high",0.91,"verified","true_violation",
              "2026-05-21 11:00:00",0),
             ("ALT007",None,"STORE002","admin01","admin01",
              "检测到: 鼠患","A04","critical",0.97,"verified","true_violation",
              "2026-05-21 12:00:00",0)]
        )

        # ----- tasks（5条，violation_id 替换原 alert_id/event_id）-----
        cursor.executemany(
            "INSERT INTO tasks (task_id,violation_id,title,issuer_id,assignee_id,status,deadline,is_deleted) VALUES (?,?,?,?,?,?,?,?)",
            [("TSK001","ALT001","南山店-未戴口罩整改","admin01","mgr001","completed","2026-05-25",0),
             ("TSK002","ALT002","南山店-再次未戴口罩整改","admin01","mgr001","processing","2026-05-28",0),
             ("TSK003","ALT003","南山店-未穿工作服整改","super01","mgr001","pending","2026-05-28",0),
             ("TSK004","ALT005","天河店-抽烟整改","admin01","mgr002","pending","2026-05-26",0),
             ("TSK005","ALT007","福田店-鼠患整改","admin01","mgr002","pending","2026-05-24",0)]
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