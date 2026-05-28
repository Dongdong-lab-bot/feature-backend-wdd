"""
数据库初始化脚本（SQLite）
模拟 MySQL DDL，展示数据库设计知识点：
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

    # 表2：摄像头表（外键→stores）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id              VARCHAR(64)     PRIMARY KEY,
            name            VARCHAR(128)    DEFAULT NULL,
            store_id        VARCHAR(32)     NOT NULL,
            location        VARCHAR(128)    DEFAULT NULL,
            is_deleted      INTEGER         NOT NULL DEFAULT 0,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT
        )
    """)

    # 表3：告警表（核心表，外键→cameras + stores）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id                  VARCHAR(32)     PRIMARY KEY,
            trace_id            VARCHAR(32)     NOT NULL,
            camera_id           VARCHAR(64)     NOT NULL,
            store_id            VARCHAR(32)     DEFAULT NULL,
            message             VARCHAR(512)    NOT NULL,
            violation_type      VARCHAR(3)      NOT NULL DEFAULT 'A00',
            level               VARCHAR(16)     NOT NULL,
            confidence          REAL            NOT NULL,
            is_verified         INTEGER         NOT NULL DEFAULT 0,
            verify_result       VARCHAR(16)     DEFAULT 'unknown',
            rectification_status VARCHAR(16)    NOT NULL DEFAULT 'pending',
            timestamp           DATETIME        NOT NULL,
            created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted          INTEGER         NOT NULL DEFAULT 0,
            FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE RESTRICT,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT
        )
    """)

    # 表4：违规事件表（外键→alerts，UNIQUE event_id）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violation_events (
            id                      INTEGER     PRIMARY KEY AUTOINCREMENT,
            event_id                VARCHAR(32) NOT NULL UNIQUE,
            alert_id                VARCHAR(32) NOT NULL,
            store_id                VARCHAR(32) DEFAULT NULL,
            is_violation_confirmed  INTEGER     NOT NULL DEFAULT 0,
            severity_level          VARCHAR(16) DEFAULT NULL,
            verification_method     VARCHAR(16) NOT NULL,
            verified_at             DATETIME    NOT NULL,
            timestamp               DATETIME    NOT NULL,
            created_at              DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted              INTEGER     NOT NULL DEFAULT 0,
            FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE RESTRICT
        )
    """)

    # 表5：用户表（UNIQUE user_id）
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

    # 表6：整改工单表（外键→stores）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rectification_tasks (
            id              INTEGER     PRIMARY KEY AUTOINCREMENT,
            task_id         VARCHAR(32) NOT NULL UNIQUE,
            alert_id        VARCHAR(32) DEFAULT NULL,
            event_id        VARCHAR(32) DEFAULT NULL,
            store_id        VARCHAR(32) NOT NULL,
            title           VARCHAR(256) NOT NULL,
            description     TEXT        DEFAULT NULL,
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
        # cameras
        cursor.executemany(
            "INSERT INTO cameras (id,name,store_id,location,is_deleted) VALUES (?,?,?,?,?)",
            [("CAM001","南山后厨1号","STORE001","后厨操作区",0),
             ("CAM002","南山后厨2号","STORE001","洗碗间",0),
             ("CAM003","福田后厨1号","STORE002","后厨操作区",0),
             ("CAM004","天河后厨1号","STORE003","后厨操作区",0),
             ("CAM005","白云后厨1号","STORE004","备餐区",0),
             ("CAM006","陆家嘴后厨1号","STORE005","后厨操作区",0)]
        )
        # alerts
        cursor.executemany(
            "INSERT INTO alerts (id,trace_id,camera_id,store_id,message,violation_type,level,confidence,is_verified,verify_result,rectification_status,timestamp,is_deleted) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [("ALT001","TRC001","CAM001","STORE001","检测到: 未戴口罩","A01","high",0.95,1,"true_violation","completed","2026-05-20 08:30:00",0),
             ("ALT002","TRC002","CAM001","STORE001","检测到: 未戴口罩","A01","high",0.88,1,"true_violation","processing","2026-05-21 09:15:00",0),
             ("ALT003","TRC003","CAM002","STORE001","检测到: 未穿工作服","A03","medium",0.76,1,"true_violation","pending","2026-05-21 10:00:00",0),
             ("ALT004","TRC004","CAM003","STORE002","检测到: 未戴工帽","A02","medium",0.82,0,"unknown","pending","2026-05-21 10:30:00",0),
             ("ALT005","TRC005","CAM004","STORE003","检测到: 抽烟","A05","high",0.91,1,"true_violation","processing","2026-05-21 11:00:00",0),
             ("ALT006","TRC006","CAM005","STORE004","检测到: 未戴口罩","A01","high",0.93,1,"false_alarm","pending","2026-05-21 11:30:00",0),
             ("ALT007","TRC007","CAM003","STORE002","检测到: 鼠患","A04","critical",0.97,1,"true_violation","pending","2026-05-21 12:00:00",0),
             ("ALT008","TRC008","CAM006","STORE005","检测到: 未戴口罩","A01","high",0.85,0,"unknown","pending","2026-05-21 13:00:00",0),
             ("ALT009","TRC009","CAM004","STORE003","检测到: 未穿工作服","A03","low",0.65,0,"unknown","pending","2026-05-21 14:00:00",0),
             ("ALT010","TRC010","CAM006","STORE005","检测到: 未戴工帽","A02","medium",0.79,0,"unknown","pending","2026-05-21 14:30:00",0)]
        )
        # violation_events
        cursor.executemany(
            "INSERT INTO violation_events (event_id,alert_id,store_id,is_violation_confirmed,severity_level,verification_method,verified_at,timestamp,is_deleted) VALUES (?,?,?,?,?,?,?,?,?)",
            [("EVE001","ALT001","STORE001",1,"major","vlm","2026-05-20 08:35:00","2026-05-20 08:30:00",0),
             ("EVE002","ALT002","STORE001",1,"major","vlm","2026-05-21 09:20:00","2026-05-21 09:15:00",0),
             ("EVE003","ALT003","STORE001",1,"minor","vlm","2026-05-21 10:05:00","2026-05-21 10:00:00",0),
             ("EVE004","ALT005","STORE003",1,"critical","vlm","2026-05-21 11:05:00","2026-05-21 11:00:00",0),
             ("EVE005","ALT007","STORE002",1,"critical","vlm","2026-05-21 12:05:00","2026-05-21 12:00:00",0)]
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
        # rectification_tasks
        cursor.executemany(
            "INSERT INTO rectification_tasks (task_id,alert_id,event_id,store_id,title,assignee,status,created_by,deadline) VALUES (?,?,?,?,?,?,?,?,?)",
            [("TSK001","ALT001","EVE001","STORE001","南山店-未戴口罩整改","王店长","completed","admin01","2026-05-25"),
             ("TSK002","ALT002","EVE002","STORE001","南山店-再次未戴口罩整改","王店长","processing","admin01","2026-05-28"),
             ("TSK003","ALT003","EVE003","STORE001","南山店-未穿工作服整改","王店长","pending","super01","2026-05-28"),
             ("TSK004","ALT005","EVE004","STORE003","天河店-抽烟整改","赵店长","pending","admin01","2026-05-26"),
             ("TSK005","ALT007","EVE005","STORE002","福田店-鼠患整改","赵店长","pending","admin01","2026-05-24")]
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
