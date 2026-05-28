# 全局JSON-Schema规范 V1.5（正式版）

**文档版本**：V1.5
**生效日期**：2026-05-07
**版本状态**：正式版（ALERT_RECEIVED 事件 Payload Schema 调整，Day4评审后V1.0~V1.4增量更新）
**适用范围**：食安大模型Agent集群项目全链路、全模块、全分组
**设计依据**：中枢路由Agent组需求、数据分析Agent组需求、边缘盒子YOLO告警原始数据格式、项目4条核心红线规则
**核心约束**：本规范为项目唯一数据宪法，全项目所有数据流转、接口交互、模型定义、代码开发必须100%遵循本规范，任何组不得私自修改、新增核心字段与结构，变更必须经架构师审批后发布新版规范。

---

> **历史演进说明**：本正式版 V1.0 基于前期草案 V1.1~V1.4 迭代评审结果收敛定稿，代码实现见 `src/core/schemas.py`。以下变更摘要保留以追溯规范演进过程。

**V1.4 修订摘要**（详见第九节《变更记录》）：

1. 2.4 节新增 `SeverityLevelEnum`（严重等级枚举）与 `VerificationMethodEnum`（校验方式枚举），支撑监管研判 Agent（A组）VLM 二次校验结果的标准化枚举表达，与 `AlertLevelEnum` 区分职责边界；
2. 3.3 节新增 `ViolationEventModel`（违规事件核心模型），完整覆盖 A 组 11 个研判产出字段 + 12 个透传字段，建立"输入 = AlertCoreModel / 输出 = ViolationEventModel"双实体契约，从源头区分"原始告警"与"二次校验事件"。
   **V1.3 修订摘要**（详见第九节《变更记录》）：
3. 1.2 节保留字段命名收敛为 `created_at` / `updated_at`（废弃 `create_time` / `update_time`），`UserInfoModel`、`SessionContext`、`RoutePlanModel`、`ConfirmationModel` 同步改造，全项目统一与 `AlertCoreModel`、数据库通用约定一致；
4. 3.2 节 `AlertCoreModel` 新增 `store_id` 字段，与权限模型 `store_ids` 严格对齐，数据 Agent SQL 权限过滤可直接落到 `WHERE store_id IN (...)`；
5. 2.4 节新增 `RectificationStatusEnum`，6.2 / 6.5 节新增 `SqlGenerationStatusEnum` / `DbExecuteStatusEnum`，`AlertCoreModel.rectification_status`、`AlertListQueryRequest.rectification_status`、`SQLGenerateResult.sql_generation_status`、`DBExecuteResult.db_execute_status` 由 `str` 升级为强约束枚举。
   **V1.2 修订摘要**：5.1 `AgentEventTypeEnum`、6.1 `FoodSafetyDataQueryRequest` 用户标识双写校验、6.6 `DataAgentResponse` 成功/失败一致性校验（详见第九节）。
   **V1.1 修订摘要**：1.3 时间工具/脱敏规范、2.2 `PageResponseBase`、2.3 错误码号段强约束、2.4 枚举 UNKNOWN 兜底、3.2 bbox 二维数组、3.5 列表分页基类继承等（详见第九节）。

---

## 一、文档总则

### 1.1 核心设计原则

| 原则                   | 详细说明                                                                                          |
| :--------------------- | :------------------------------------------------------------------------------------------------ |
| **全局唯一**     | 全项目所有核心数据结构、字段命名、枚举值、类型约束全局唯一，无重复定义、无歧义冲突                |
| **强类型约束**   | 所有模型基于Pydantic V2实现，严格定义字段类型、必填/非必填、校验规则，杜绝弱类型隐式转换          |
| **全链路可追溯** | 所有核心模型必须继承Trace基类，全链路透传trace_id，所有操作可通过trace_id串联追溯，符合可追溯红线 |
| **高内聚低耦合** | 按业务域拆分模型模块，模块间通过标准接口交互，内部字段变更不影响跨组调用                          |
| **可扩展兼容**   | 预留扩展字段与枚举空间，MVP后新增业务场景无需重构核心结构，保证向前兼容                           |
| **红线合规优先** | 所有模型设计严格贴合4条核心红线，从数据结构层面杜绝违规操作、架构腐化风险                         |

### 1.2 通用命名规范

1. **字段命名**：所有字段统一采用**蛇形命名法（snake_case）**，禁止驼峰命名、拼音命名，全英文小写，下划线分隔。
2. **枚举命名**：枚举类名采用大驼峰，枚举值采用全大写下划线分隔，如 `ALERT_LEVEL_HIGH`。
3. **模型命名**：所有Pydantic模型类名采用大驼峰，按「业务域+动作+类型」命名，如 `AlertPushRequest`、`IntentRecognitionResult`。
4. **保留字段**：`trace_id`、`created_at`、`updated_at`、`is_deleted` 为全局保留字段，命名与含义全局统一，不得修改；**强约束**：所有数据库实体表与 Pydantic 模型时间审计字段必须使用 `created_at` / `updated_at`（与数据库通用约定及 `AlertCoreModel` 对齐），禁止使用 `create_time` / `update_time` 旧命名，违反视为 Schema 红线。

### 1.3 通用类型与格式约束

1. **时间格式**：

   - 内部流转统一遵循 **ISO 8601** 并强制携带时区（如 `2026-04-26T15:30:00+08:00`），Python 类型为 Aware Datetime
   - **外部兼容**：EdgeAgent 等存量系统推送的 naive 时间字符串（如 `YYYY-MM-DD HH:MM:SS.ffffff`）由**网关层负责解析并转换为带时区格式**，禁止将 naive datetime 透传至下游
   - 前端展示格式可按需转换，底层流转必须严格遵循带时区格式
   - **统一时间生成函数**（强制要求）：全项目所有 `datetime` 字段的 `default_factory` 必须使用 `beijing_now`，**禁止直接使用 `datetime.now`**（生成 Naive Datetime，违反带时区约束，会导致 8 小时时区错乱）：

   ```python
   from datetime import datetime, timezone, timedelta

   # 北京时间固定时区（UTC+8），全项目唯一标准
   BEIJING_TZ = timezone(offset=timedelta(hours=8), name="Asia/Shanghai")

   def beijing_now() -> datetime:
       """全项目统一时间生成函数，返回带北京时区的 Aware Datetime。"""
       return datetime.now(BEIJING_TZ)
   ```
2. **ID格式**：

   - 全局trace_id：32位UUID小写字符串，全链路唯一
   - 告警ID：固定格式 `ALT{13位毫秒时间戳}{8位随机字母数字}`，如 `ALT1745733600123A7F9X2K1`
   - 会话ID：固定格式 `SES{13位毫秒时间戳}{8位随机字母数字}`
   - 确认单ID：固定格式 `CNF{13位毫秒时间戳}{8位随机字母数字}`
   - 事件ID：固定格式 `EVE{13位毫秒时间戳}{8位随机字母数字}`，如 `EVE1745733600123A7F9X2K1`
   - **设计演进**：原方案使用 3 位大写字母（`26³ = 17,576` 种组合），在边缘告警风暴场景（同一毫秒 20+ 张图）下冲突风险不可忽视。现方案使用 `secrets` 模块生成 8 位字母数字混合随机串（`36⁸ ≈ 2.8 万亿`），彻底消除分布式冲突。代码实现见 `src/core/schemas.py::generate_id(prefix, random_length=8)`。
   - **兼容说明**：存量 EdgeAgent 生成的秒级时间戳 ID（如 `ALT1740500123A7F`）作为历史数据保留，新系统接收后重新生成毫秒级 ID，新旧格式并存不影响业务
3. **数值类型**：

   - 置信度、概率类字段：采用 `float`类型，范围 `0.0-1.0`，保留2位小数
   - 枚举类字段：优先采用 `Enum`类型，数据库存储采用对应字符串格式
4. **必填约束**：核心业务字段必须标记为必填，非必填字段必须设置默认值，禁止无意义的空值传递。
5. **敏感信息脱敏规范**（强制要求，覆盖日志/审计/非业务必要存储场景，违反视为合规红线）：

   - **敏感字段清单**：`password`、`api_key`、`secret`、`token`、`access_token`、`refresh_token`、`phone`、`email`、`id_card`、`address` 等个人信息与密钥信息均为强制脱敏字段；该清单可在 `src/core/logger.py` 中维护，新增字段须同步更新本规范。
   - **标准脱敏规则**：
     - 手机号：保留前 3 位 + 后 4 位，中间 4 位打星，如 `138****1234`
     - 邮箱：保留首字符 + 域名，中间打星，如 `l***@example.com`
     - 密钥/密码/Token：全量打星并记录长度，如 `****** (len=32)`
     - 身份证号：保留前 6 位 + 后 4 位，中间打星，如 `310115********1234`
     - 地址：保留省市，详细门牌打星，如 `上海市浦东新区****`
   - **执行约束**：
     1. 日志、审计、非必要业务存储场景敏感信息**必须脱敏**，禁止明文落库；
     2. 业务必要存储的敏感信息**必须加密存储**（AES-256 / KMS 托管密钥），禁止明文持久化；
     3. 网关、Agent、数据层均需在序列化前统一调用 `src/core/logger.py` 提供的脱敏工具，业务代码不得自行实现脱敏逻辑，避免规则不一致。

---

## 二、全局通用基础模型

### 2.1 全链路追踪基类

**核心作用**：所有请求、事件、模型必须继承该基类，保障全链路可追溯，符合可追溯红线。

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class TraceBase(BaseModel):
    """全链路追踪基类，所有核心模型必须继承"""
    trace_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        description="全链路唯一追踪ID，全流程透传",
        min_length=32,
        max_length=32
    )
```

### 2.2 通用请求/响应基类

```python
from typing import Optional, Any, Union, Dict, List

class RequestBase(TraceBase):
    """所有HTTP/WS接口请求基类"""
    user_id: str = Field(description="操作用户唯一ID")
    request_time: datetime = Field(
        default_factory=beijing_now,
        description="请求发起时间（Aware Datetime，带北京时区）"
    )

class ResponseBase(TraceBase):
    """所有HTTP/WS接口响应基类"""
    code: str = Field(description="全局统一响应码，0000为成功，其余为失败")
    message: str = Field(description="响应描述信息")
    success: bool = Field(description="请求是否成功")
    response_time: datetime = Field(
        default_factory=beijing_now,
        description="响应返回时间（Aware Datetime，带北京时区）"
    )
    data: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None, description="响应业务数据")

class PageResponseBase(ResponseBase):
    """全项目通用分页响应基类，所有列表查询响应必须继承。

    使用约束：
    1. 列表数据字段统一命名为 `items`，由继承方按业务类型声明（如 `items: List[AlertCoreModel]`）；
    2. 分页参数 `page_num`、`page_size` 与请求侧 `RequestBase` 子类保持一致，禁止使用 offset/limit 等其他命名；
    3. `total_pages` 由后端基于 `total` 与 `page_size` 计算填充，前端禁止自行二次推导。
    """
    total: int = Field(description="符合条件的总条数", ge=0)
    page_num: int = Field(description="当前页码", ge=1)
    page_size: int = Field(description="每页条数", ge=1, le=100)
    total_pages: int = Field(description="总页数", ge=0)
```

> **对话消息标准结构（ChatMessage）**：用于 `SessionContext.chat_history` 及多轮对话上下文，替代原 `List[Dict[str, Any]]` 松散结构，提供类型安全与字段约束。
>
> ```python
> class ChatMessage(BaseModel):
>     role: str = Field(description="消息角色：user / assistant / system")
>     content: str = Field(description="消息内容文本")
>     timestamp: datetime = Field(default_factory=beijing_now, description="消息发送时间")
>     intent_type: Optional[UserIntentEnum] = Field(default=None, description="消息关联的用户意图（可选）")
> ```

### 2.3 全局统一错误码规范

**编码规则**：5位数字，前2位为业务域，后3位为错误序号；0000为成功，通用错误以10开头。

**号段分配规则**（强约束，禁止跨域使用，新增错误码必须在本节注册）：

| 号段 | 归属业务域 / 组别 | 说明                                       |
| :--- | :---------------- | :----------------------------------------- |
| 0000 | 全局成功          | 唯一成功响应码，固定不可改                 |
| 10xx | 全局通用          | 参数、配置、协议层通用错误，所有组可复用   |
| 20xx | 大模型通用        | 大模型/VLM 调用、响应解析、熔断相关        |
| 30xx | 数据分析 Agent 组 | SQL 生成/校验、AST 拦截、数据查询专属      |
| 40xx | 数据库通用        | 数据库连接、执行、超时、权限相关           |
| 50xx | Agent 通用        | Agent 初始化、生命周期、通用路由           |
| 60xx | 中枢路由 Agent 组 | 意图识别、路由分发、会话管理、二次确认专属 |
| 70xx | 监管研判 Agent 组 | VLM 校验、告警降噪、整改核验、时空去重专属 |
| 80xx | 核心基建组        | 网关、中间件、存储、消息总线、文件接收专属 |

**强约束**：

1. 各组只能在自己的号段内新增错误码，禁止跨号段定义；权限相关错误（如 `3003 PERMISSION_DENIED`）属于"权限体系横切关注点"，可在通用号段或归属业务域内出现，但不允许同一含义错误码重复定义于多个号段；
2. 全局通用错误（10xx）可由所有组复用，但不允许各组将通用错误重新编号；
3. 新增错误码必须在本规范错误码注册表中登记（含触发场景、归属、抛出位置），私自下沉到代码常量等价于违反 Schema 红线；
4. 已发布错误码禁止修改语义、禁止删除，废弃只能通过新版本规范标注 `Deprecated`。

**错误码注册表**：

| 错误码 | 错误名称                  | 触发场景                                                                                                                         | 所属业务域           |
| :----- | :------------------------ | :------------------------------------------------------------------------------------------------------------------------------- | :------------------- |
| 0000   | SUCCESS                   | 请求处理成功                                                                                                                     | 全局通用             |
| 1001   | PARAM_ERROR               | 请求参数缺失、格式非法、校验不通过                                                                                               | 全局通用             |
| 1002   | CONFIG_ERROR              | 系统配置错误、环境变量缺失                                                                                                       | 全局通用             |
| 2001   | LLM_CALL_FAILED           | 大模型调用连续3次失败,触发熔断                                                                                                   | 大模型通用           |
| 2002   | LLM_RESPONSE_INVALID      | 大模型返回内容格式异常、无法解析                                                                                                 | 大模型通用           |
| 2003   | LLM_FUSE_TRIGGERED        | 大模型连续失败触发熔断降级                                                                                                       | 大模型通用           |
| 3001   | SQL_SECURITY_BLOCKED      | AST安全拦截检测到破坏性写操作                                                                                                    | 数据Agent            |
| 3002   | SQL_PERFORMANCE_BLOCKED   | AST性能拦截检测到全表扫描/笛卡尔积                                                                                               | 数据Agent            |
| 3003   | PERMISSION_DENIED         | 数据查询场景用户权限不足、越权操作                                                                                               | 数据Agent / 权限横切 |
| 4001   | DB_CONNECT_FAILED         | 数据库连接失败、网络异常、认证错误                                                                                               | 数据库通用           |
| 4002   | DB_EXECUTE_FAILED         | SQL执行失败、语法错误、查询超时                                                                                                  | 数据库通用           |
| 4003   | DB_RESULT_EMPTY           | 数据库查询结果为空                                                                                                               | 数据库通用           |
| 5001   | AGENT_INIT_FAILED         | Agent实例初始化失败、依赖缺失                                                                                                    | Agent通用            |
| 5002   | AGENT_HANDLE_FAILED       | Agent业务处理异常、流程执行失败                                                                                                  | Agent通用            |
| 5003   | ROUTE_FAILED              | Agent路由失败（通用级）                                                                                                          | Agent通用            |
| 6001   | INTENT_RECOGNITION_FAILED | 用户意图识别失败、置信度不足                                                                                                     | 路由Agent            |
| 6002   | ROUTE_DISPATCH_FAILED     | Agent路由分发失败、目标Agent不可用                                                                                               | 路由Agent            |
| 6003   | CONFIRMATION_EXPIRED      | 高危操作二次确认单已过期                                                                                                         | 路由Agent            |
| 7001   | ALERT_PUSH_FAILED         | **Deprecated**：原"边缘告警推送失败"，归属网关层错误，自 V1.1 起改用 `8002 EDGE_ALERT_PUSH_FAILED`，本码保留不再新增引用 | 监管Agent（已废弃）  |
| 7002   | ALERT_DUPLICATE           | 告警数据重复、时空去重拦截                                                                                                       | 监管Agent            |
| 7003   | VLM_VERIFY_FAILED         | VLM二次校验调用失败、结果解析异常                                                                                                | 监管Agent            |
| 8001   | GATEWAY_REQUEST_INVALID   | 网关层请求解析失败、协议/签名校验不通过                                                                                          | 核心基建             |
| 8002   | EDGE_ALERT_PUSH_FAILED    | 边缘告警数据推送失败、网关格式校验不通过（替代 7001）                                                                            | 核心基建             |
| 8003   | STORAGE_FAILED            | 文件/对象存储写入失败、消息总线投递失败                                                                                          | 核心基建             |

### 2.4 全局枚举通用规范

**枚举值冲突约束**（强约束，违反视为 Schema 红线）：
不同枚举类即使字符串值相同，也代表不同业务语义（如 `AlertLevelEnum.CRITICAL` 表示 YOLO 初始告警级别，`SeverityLevelEnum.CRITICAL` 表示 VLM 确认的严重度）。
落库、缓存、日志、跨系统传输时，**禁止仅以字符串值做业务判断**；必须同时携带字段名或枚举类名做上下文区分，避免"同值不同义"导致统计口径错误。

#### 2.4.1 用户角色枚举

```python
from enum import Enum

class UserRoleEnum(str, Enum):
    """全局用户角色枚举，路由/数据/权限模块通用"""
    STORE_MANAGER = "store_manager"
    AREA_SUPERVISOR = "area_supervisor"
    ENTERPRISE_ADMIN = "enterprise_admin"
```

#### 2.4.2 告警级别枚举

```python
class AlertLevelEnum(str, Enum):
    """全局告警级别枚举，边缘/监管/数据模块通用。

    UNKNOWN 兜底约束：网关层接收 EdgeAgent 推送的 level 字符串时，
    无法匹配的值统一映射为 UNKNOWN 并记录 warn 日志，不阻断告警主流程。
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"  # 高危（与 SeverityLevelEnum.CRITICAL 值相同但语义不同，禁止混用；见 1.3 节存储规范）
    UNKNOWN = "unknown"  # 兜底项：兼容存量 EdgeAgent 异常 level 字符串，避免数据丢失
```

#### 2.4.3 VLM校验结果枚举

```python
class VerifyResultEnum(str, Enum):
    """VLM二次校验结果枚举，监管Agent专用"""
    TRUE_VIOLATION = "true_violation"   # 确认违规
    FALSE_ALARM = "false_alarm"         # 确认误报
    UNCERTAIN = "uncertain"             # VLM无法确定（需人工复核或兜底为违规）
```

#### 2.4.4 违规类型枚举

```python
class ViolationTypeEnum(str, Enum):
    """全局违规类型枚举，监管/数据/路由模块通用。MVP阶段基础值，后续按业务扩展。

    UNKNOWN 与 OTHER 语义差异：
    - OTHER (A99)：业务侧已识别为违规但未归入既有类目，需后续运营补类目；
    - UNKNOWN (A00)：网关层无法将外部输入映射到任何已知类目（含 OTHER），统一兜底，记录 warn 日志，不阻断告警主流程。
    """
    NO_MASK = "A01"
    NO_HAT = "A02"
    NO_UNIFORM = "A03"
    RAT_PRESENCE = "A04"
    SMOKING = "A05"
    OTHER = "A99"
    UNKNOWN = "A00"  # 兜底项：仅用于网关无法识别外部输入时映射，禁止业务侧主动赋值
```

#### 2.4.5 用户意图枚举

```python
class UserIntentEnum(str, Enum):
    """全局用户意图枚举，路由/数据/监管模块通用"""
    QUERY_SUMMARY = "query_summary"
    QUERY_DETAIL = "query_detail"
    QUERY_TREND = "query_trend"
    QUERY_RANKING = "query_ranking"
    QUERY_RECTIFICATION = "query_rectification"
    EXPORT_REPORT = "export_report"
    SEND_NOTICE = "send_notice"
    CREATE_TASK = "create_task"
    CONFIRM_ACTION = "confirm_action"
    REJECT_ACTION = "reject_action"
    NEED_CLARIFICATION = "need_clarification"
    OUT_OF_DOMAIN = "out_of_domain"
```

#### 2.4.6 整改状态枚举

```python
class RectificationStatusEnum(str, Enum):
    """全局整改状态枚举，告警/监管/数据/路由模块通用。

    覆盖告警全生命周期的整改流转：待处理 → 处理中 → 完成 / 过期；
    所有 SQL 过滤、API 入参、状态字段必须使用本枚举，禁止业务代码自由拼装字符串，
    避免出现 'Pending' / 'complete' 等大小写或拼写漂移导致 WHERE 命中率异常。
    """
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    EXPIRED = "expired"          # 已过期
```

#### 2.4.7 违规严重等级枚举

```python
class SeverityLevelEnum(str, Enum):
    """违规严重等级枚举，监管研判 Agent（A组）VLM 二次校验后专用，与 `AlertLevelEnum` 职责区分。

    职责边界：
    - `AlertLevelEnum` 描述 YOLO 初始告警级别（high / medium / low），来自边缘端推送；
    - `SeverityLevelEnum` 描述经 VLM 二次校验后确认的违规严重程度（critical / major / minor），
      仅当 `is_violation_confirmed=True` 时非空，误报场景必须为 null。

    禁止将两个枚举混用——数据 Agent 查询报表时若需区分"初始级别"与"确认严重度"，
    必须同时持有 `level`（AlertLevelEnum）与 `severity_level`（SeverityLevelEnum）字段。
    """
    CRITICAL = "critical"  # 严重：抽烟、鼠患、生熟混放等高危违规（值与 AlertLevelEnum.CRITICAL 相同，但语义不同，禁止混用；见 1.3 节存储规范）
    MAJOR = "major"        # 一般：未戴口罩、垃圾桶未加盖等中危违规
    MINOR = "minor"        # 轻微：工帽滑落、物品轻微乱摆等低危违规
```

#### 2.4.8 校验方式枚举

```python
class VerificationMethodEnum(str, Enum):
    """校验方式枚举，监管研判 Agent（A组）专用。

    区分正常模式与降级模式，下游消费方必须据此区分结论可信度：
    - vlm：云端 VLM 视觉大模型校验，可信度高，正常业务首选；
    - edge_rule：边缘端规则校验，降级模式，云端异常（VLM 熔断、网络中断、超时耗尽）时自动切换。

    审计要求：所有 `ViolationEventModel` 必须记录本字段，禁止在降级模式下仍伪装为 vlm。
    """
    VLM = "vlm"                # 云端 VLM 视觉大模型校验（正常模式）
    EDGE_RULE = "edge_rule"    # 边缘端规则校验（降级模式，云端异常时自动切换）
```

#### 2.4.9 路由计划执行状态枚举

```python
class ExecutionStatusEnum(str, Enum):
    """路由计划执行状态枚举，路由Agent专用。

    强约束：所有 RoutePlanModel.execution_status 必须使用本枚举，禁止业务代码自由拼写字符串。
    """
    PLANNED = "planned"
    RUNNING = "running"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
```

#### 2.4.10 高危操作类型枚举

```python
class ActionTypeEnum(str, Enum):
    """高危操作类型枚举，ConfirmationModel / 路由Agent专用。

    强约束：所有 ConfirmationModel.action_type 必须使用本枚举，禁止业务代码自由拼写字符串。
    """
    EXPORT_REPORT = "export_report"
    SEND_NOTICE = "send_notice"
    CREATE_TASK = "create_task"
```

#### 2.4.11 AST安全拦截类型枚举

```python
class BlockedTypeEnum(str, Enum):
    """AST安全拦截类型枚举，数据Agent / 基建拦截器专用。

    强约束：所有 ASTSecurityCheckResult.blocked_type 必须使用本枚举。
    """
    DML = "DML"
    DDL = "DDL"
    MULTI_STATEMENT = "MULTI_STATEMENT"
    STORED_PROCEDURE = "STORED_PROCEDURE"
    FUNCTION_CALL = "FUNCTION_CALL"
```

#### 2.4.12 数据查询场景枚举

```python
class QuerySceneEnum(str, Enum):
    """数据查询场景枚举，FoodSafetyDataQueryRequest 专用。

    强约束：所有 scene 字段必须使用本枚举，新增场景须经 Schema 变更申请单审批。
    """
    ALARM_QUERY = "alarm_query"
    EVENT_QUERY = "event_query"
    RECTIFICATION_QUERY = "rectification_query"
    STATISTICS_QUERY = "statistics_query"
```

#### 2.4.13 用户权限动作枚举

```python
class PermissionActionEnum(str, Enum):
    """用户权限动作枚举，UserInfoModel / PermissionContext 专用。

    强约束：所有 permission_actions 列表元素必须使用本枚举，禁止业务代码自由拼写字符串。
    """
    QUERY_ALERT = "query_alert"
    EXPORT_REPORT = "export_report"
    SEND_NOTICE = "send_notice"
    CREATE_RECTIFICATION = "create_rectification"
    CONFIRM_ACTION = "confirm_action"
    VIEW_DATA = "view_data"
```

---

## 三、告警数据核心模型

**适用模块**：边缘盒子、基建组网关、监管Agent、数据Agent、路由Agent
**核心说明**：完全兼容边缘盒子原始推送格式，同时满足全链路流转需求，为项目核心主数据模型。

### 3.1 边缘告警推送协议

**通信协议**：EdgeAgent → 基建网关采用 `POST multipart/form-data`

| 项目                   | 值                                  |
| ---------------------- | ----------------------------------- |
| **Method**       | `POST`                            |
| **Endpoint**     | `/api/alerts/`                    |
| **Content-Type** | `multipart/form-data`             |
| **认证 Header**  | `X-API-KEY: <EDGE_AGENT_API_KEY>` |

**Form 字段**：

| 字段名         | 类型          | 必填 | 说明                           |
| -------------- | ------------- | ---- | ------------------------------ |
| `alert_data` | string (JSON) | 是   | 告警核心数据 JSON 序列化字符串 |
| `file`       | file (JPEG)   | 否   | 带检测框标注的截图             |

---

### 3.1.1 EdgeAgent 原始 Payload 模型

```python
class EdgeAlertPayload(BaseModel):
    """EdgeAgent 原始 JSON payload（嵌入在 multipart 的 alert_data 字段中）。

    注意：此模型仅用于网关层接收和解析，不做枚举校验，最大限度兼容存量 EdgeAgent。
    """
    camera_id: str = Field(description="摄像头唯一标识")
    message: str = Field(description="告警描述，固定格式[{model_name}] 检测到: {class_name}")
    level: str = Field(description="告警级别原始字符串（high/medium/low 等），由 EdgeAgent models.json 配置决定")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    timestamp: str = Field(description="原始时间字符串，格式为 'YYYY-MM-DD HH:MM:SS.ffffff'，无时区后缀")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
```

---

### 3.1.2 网关解析后内部模型

```python
from typing import Optional, List

class AlertPushRequest(TraceBase):
    """基建网关解析 EdgeAgent 推送后的内部模型。

    网关层职责：
    1. 解析 multipart，提取 alert_data JSON 和 file
    2. 保存截图到 /app/alert_images/，生成 image_url
    3. 将 naive 时间字符串转换为带时区的 Aware Datetime
    4. 将 level 字符串映射为 AlertLevelEnum

    注意：本模型仅用于 HTTP 推送请求的网关内部解析，不直接作为消息总线事件 payload。
    ALERT_RECEIVED 事件投递的是入库后的完整 AlertCoreModel（详见 5.1.1 AgentEventTypeEnum 及 API 契约文档 4.2 节）。
    """
    camera_id: str = Field(description="摄像头唯一标识")
    message: str = Field(description="告警描述")
    level: AlertLevelEnum = Field(description="告警级别（网关层映射后的枚举）")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    timestamp: datetime = Field(description="告警抓拍时间（Aware Datetime，内部流转统一带时区）")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
    image_url: Optional[str] = Field(default=None, description="告警截图相对路径，如 /alert_images/{uuid}.jpg")

class AlertPushResponse(ResponseBase):
    """告警推送响应模型"""
    alert_id: Optional[str] = Field(default=None, description="系统生成的告警唯一ID")
```

### 3.2 告警核心存储模型

```python
class AlertCoreModel(TraceBase):
    """告警数据核心存储模型，全项目唯一标准"""
    id: str = Field(description="告警唯一ID，固定格式ALT{timestamp}{random3}")
    camera_id: str = Field(description="摄像头唯一标识")
    camera_name: Optional[str] = Field(default=None, description="摄像头名称")
    store_id: Optional[str] = Field(default=None, description="摄像头所属门店唯一ID，与权限模型 `store_ids` / 接口 `permission_context.store_scope` 严格对齐，数据 Agent SQL 权限过滤直接基于该字段（如 `WHERE store_id IN ('STORE_001')`）；网关层从 camera_id 映射或前端透传，禁止业务侧自由拼装")
    location: Optional[str] = Field(default=None, description="摄像头所属门店/区域中文位置（如 '南山店'），仅用于前端展示与告警话术，**禁止用于权限过滤**；语义等价于 ViolationEventModel.camera_location")
    message: str = Field(description="告警描述")
    violation_type: ViolationTypeEnum = Field(description="违规类型编码")
    level: AlertLevelEnum = Field(description="告警级别")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    image_url: Optional[str] = Field(default=None, description="告警截图相对路径")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
    bbox: Optional[List[List[float]]] = Field(
        default=None,
        description="YOLO 检测框坐标列表，**二维数组**以兼容多目标场景；每个元素为单个目标的 [x_min, y_min, x_max, y_max]，采用相对坐标 0.0-1.0；由后端从截图或 YOLO 结果解析填充，非 EdgeAgent 直接推送。",
    )
    is_read: bool = Field(default=False, description="告警是否已读")
    is_verified: bool = Field(default=False, description="是否经过VLM二次校验")
    verify_result: Optional[VerifyResultEnum] = Field(default=None, description="VLM二次校验结果枚举")
    rectification_status: RectificationStatusEnum = Field(default=RectificationStatusEnum.PENDING, description="整改状态枚举，详见 2.4.6 RectificationStatusEnum")
    timestamp: datetime = Field(description="告警抓拍时间")
    created_at: datetime = Field(default_factory=beijing_now, description="告警数据入库时间（系统创建时间）")
    updated_at: datetime = Field(default_factory=beijing_now, description="数据更新时间")
```

### 3.3 违规事件核心模型（监管研判 Agent 产出）

```python
class ViolationEventModel(TraceBase):
    """违规事件核心模型，监管研判 Agent（A组）VLM 二次校验后产出，全项目唯一标准。

    与 AlertCoreModel 的区别：
    - AlertCoreModel 记录原始边缘告警（输入），核心维度是 camera_id + timestamp；
    - ViolationEventModel 记录经 VLM 二次校验后的判定结果（输出），核心维度是 event_id；
    - 二者通过 alert_id 关联，但代表不同业务实体，禁止混淆。

    审计约束：所有 `is_violation_confirmed=True` 的事件必须完整填充
    `event_id`、`verification_method`、`verified_at` 字段，禁止缺失。
    """
    # 透传字段（保留原始告警信息，与 A 组输入字段一一对应）
    alert_id: str = Field(description="原始告警ID，与 AlertCoreModel.id 一致，关联溯源")
    camera_id: str = Field(description="摄像头唯一标识")
    camera_location: Optional[str] = Field(default=None, description="摄像头位置描述，如'一楼大厅'；语义等价于 AlertCoreModel.location，SQL join 时按业务含义对齐")
    store_id: Optional[str] = Field(default=None, description="摄像头所属门店唯一ID；网关层从 camera_id 映射补上，与 AlertCoreModel.store_id 对齐")
    message: str = Field(description="告警描述")
    level: AlertLevelEnum = Field(description="告警级别，原始YOLO产出级别")
    confidence: float = Field(description="YOLO推理置信度", ge=0.0, le=1.0)
    image_url: Optional[str] = Field(default=None, description="原始告警图片URL；与 AlertCoreModel.image_url 对齐，原始告警无图时允许为 null")
    detection_tags: Optional[str] = Field(default=None, description="检测标签扩展字段")
    is_read: bool = Field(default=False, description="已读状态")
    timestamp: datetime = Field(description="告警实际发生时间")
    created_at: datetime = Field(description="告警记录创建时间")

    # 研判产出字段（A组 VLM 二次校验结论）
    event_id: str = Field(
        description="判定生成的事件ID，Agent生成，全局唯一，后续整改/查询/台账的核心引用"
    )
    is_violation_confirmed: bool = Field(
        description="是否确认违规。True=确有违规，False=误报（误报也要落库，审计要求）。映射规则：VerifyResultEnum.TRUE_VIOLATION → True；FALSE_ALARM / UNCERTAIN → False（UNCERTAIN 兜底为误报并触发人工复核）"
    )
    severity_level: Optional[SeverityLevelEnum] = Field(
        default=None,
        description="违规严重等级，详见 2.4.7 SeverityLevelEnum；仅确认违规时填写，误报时为null"
    )
    verified_image_url: str = Field(
        description="本次校验所用的图片URL（去重后选中的那张），审计留痕'判定依据的是哪张图'"
    )
    regulation_clause: Optional[str] = Field(
        default=None,
        description="关联的法规条款，如'GB 31654-2021 第8.2.3条'，需RAG匹配，当前阶段可选"
    )
    verification_method: VerificationMethodEnum = Field(
        description="校验方式，详见 2.4.8 VerificationMethodEnum；vlm=云端VLM，edge_rule=降级为边缘规则，下游需区分结论可信度"
    )
    vlm_confidence: Optional[float] = Field(
        default=None, description="VLM判定置信度(0~1)，降级模式时为null", ge=0.0, le=1.0
    )
    model_version: Optional[str] = Field(
        default=None, description="VLM模型版本号，审计可追溯性强制要求"
    )
    verified_at: datetime = Field(description="校验完成时间，审计可追溯性强制要求")
    determination_basis: Optional[str] = Field(
        default=None, description="判定依据文字说明，审计可追溯性强制要求"
    )
    aggregation_count: int = Field(
        default=1,
        description="聚合的原始告警数量，1=单条直传，>1=聚合（如10分钟10条同类告警聚合为1条事件）",
        ge=1,
    )
    updated_at: datetime = Field(default_factory=beijing_now, description="数据更新时间")
```

### 3.4 告警详情响应模型

```python
class AlertDetailResponse(ResponseBase):
    """告警详情查询响应模型，路由/监管/数据Agent通用"""
    alert_detail: AlertCoreModel = Field(description="告警详情")
```

### 3.5 告警列表查询请求模型

```python
from typing import Optional, List, Tuple

class AlertListQueryRequest(RequestBase):
    """告警列表查询请求模型"""
    time_range: Optional[Tuple[datetime, datetime]] = Field(default=None, description="查询时间范围")
    store_scope: Optional[List[str]] = Field(default=None, description="门店范围过滤")
    violation_type: Optional[List[ViolationTypeEnum]] = Field(default=None, description="违规类型过滤")
    risk_level: Optional[List[AlertLevelEnum]] = Field(default=None, description="告警级别过滤")
    rectification_status: Optional[List[RectificationStatusEnum]] = Field(default=None, description="整改状态过滤，详见 2.4.6 RectificationStatusEnum")
    page_num: int = Field(default=1, description="页码", ge=1)
    page_size: int = Field(default=20, description="每页条数", ge=1, le=100)
```

### 3.6 告警列表查询响应模型

```python
class AlertListQueryResponse(PageResponseBase):
    """告警列表查询响应模型，继承全项目通用分页基类。"""
    items: List[AlertCoreModel] = Field(description="当前页的告警列表数据")
```

### 3.7 WebSocket 实时推送模型

后端在告警入库后广播给所有前端连接：

```python
class AlertWebSocketMessage(BaseModel):
    """WebSocket 实时告警推送消息模型"""
    entity: str = Field(default="alert", description="实体类型：alert")
    action: str = Field(description="操作类型：create/update/delete")
    payload: AlertCoreModel = Field(description="告警数据载荷")
```

**WebSocket 端点**：`ws://host/ws/alerts`

### 3.8 MQTT 推送模型（第三方平台）

```python
class AlertMQTTMessage(BaseModel):
    """MQTT 告警推送消息模型，对接第三方平台"""
    operator: str = Field(default="RecordPush", description="操作标识")
    info: Dict[str, Any] = Field(description="推送详情，包含 RecordID、aibox_id、alarm_txt、time、pic 等字段")
```

**Topic 默认**：`mqtt/AI-BOX/alarm`
**图片编码**：Base64 JPEG（当 `use_base64_image=true` 时）

### 3.9 违规事件详情响应模型

```python
class EventDetailResponse(ResponseBase):
    """违规事件详情查询响应模型，路由/监管/数据Agent通用"""
    event_detail: ViolationEventModel = Field(description="违规事件详情，含 VLM 二次校验完整结论")
```

### 3.10 违规事件列表查询响应模型

```python
class EventListQueryResponse(PageResponseBase):
    """违规事件列表查询响应模型，继承全项目通用分页基类。"""
    items: List[ViolationEventModel] = Field(description="当前页的违规事件列表数据")
```

**请求复用说明**：事件列表查询的过滤条件（时间范围、门店、违规类型等）与告警列表基本一致，请求侧**复用 `3.5 AlertListQueryRequest`**，无需额外定义 `EventListQueryRequest`；响应侧通过 `EventListQueryResponse` 返回带 VLM 校验结论的完整事件数据。

---

## 四、用户与权限核心模型

**适用模块**：路由Agent、数据Agent、基建组权限管控、前端交互
**核心说明**：统一用户身份、权限范围、数据隔离规则，满足多角色差异化访问需求。

### 4.1 用户信息核心模型

```python
class UserInfoModel(TraceBase):
    """用户信息核心模型，全项目通用"""
    user_id: str = Field(description="用户唯一ID")
    user_name: str = Field(description="用户姓名")
    role_type: UserRoleEnum = Field(description="用户角色")
    phone: Optional[str] = Field(default=None, description="联系电话")
    email: Optional[str] = Field(default=None, description="邮箱")
    store_ids: List[str] = Field(default_factory=list, description="有权限访问的门店ID列表")
    region_ids: List[str] = Field(default_factory=list, description="有权限访问的区域ID列表")
    permission_actions: List[PermissionActionEnum] = Field(default_factory=list, description="可执行的操作权限枚举列表，详见 2.4.13 PermissionActionEnum")
    created_at: datetime = Field(default_factory=beijing_now, description="账号创建时间")
    last_login_time: Optional[datetime] = Field(default=None, description="最后登录时间")
```

### 4.2 权限上下文模型

```python
class PermissionContext(TraceBase):
    """权限上下文模型，全链路透传，用于数据隔离与权限校验"""
    user_id: str = Field(description="操作用户ID")
    role_type: UserRoleEnum = Field(description="用户角色")
    store_scope: List[str] = Field(default_factory=list, description="可访问的门店范围")
    region_scope: List[str] = Field(default_factory=list, description="可访问的区域范围")
    permission_actions: List[str] = Field(default_factory=list, description="可执行的操作权限")
```

### 4.3 会话上下文模型

```python
from typing import Dict, Any

class SessionContext(TraceBase):
    """会话上下文模型，路由Agent多轮对话专用。

    约束：chat_history 最大保留轮次不得超过 10 轮，超出时由服务端在组装 Prompt 前进行滑动窗口截断。
    """
    session_id: str = Field(description="会话唯一ID")
    user_id: str = Field(description="所属用户ID")
    last_intent: Optional[UserIntentEnum] = Field(default=None, description="上一轮用户意图")
    last_slots: Optional[Dict[str, Any]] = Field(default=None, description="上一轮已填充的槽位信息")
    last_result_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="上一轮查询结果快照")
    pending_confirmation_id: Optional[str] = Field(default=None, description="待确认的操作ID")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="对话历史列表，最大保留10轮，由 ChatMessage 强类型约束")
    created_at: datetime = Field(default_factory=beijing_now, description="会话创建时间")
    updated_at: datetime = Field(default_factory=beijing_now, description="会话更新时间")
    expire_time: datetime = Field(
        default_factory=lambda: beijing_now() + timedelta(minutes=30),
        description="会话过期时间，默认30分钟"
    )
```

---

## 五、Agent通信与路由核心模型

**适用模块**：基建组通信层、路由Agent、监管Agent、数据Agent
**核心说明**：统一Agent间通信标准、路由分发规则、意图识别格式，保障多Agent协同无歧义。

### 5.1 Agent间通信事件模型

#### 5.1.1 Agent 事件类型枚举

```python
class AgentEventTypeEnum(str, Enum):
    """Agent 间通信事件类型枚举，基建消息总线全局唯一标准。

    强约束：所有通过消息总线发布/订阅的事件，`event_type` 必须为本枚举注册值；
    新增类型必须通过《Schema 变更申请单》注册到本枚举，**禁止业务侧使用未注册字符串**，
    否则订阅方反序列化时直接抛 `PARAM_ERROR (1001)`，从结构上杜绝事件名漂移。
    """
    # —— 告警业务流转 ——
    ALERT_RECEIVED = "alert_received"          # 网关收到边缘告警
    ALERT_DEDUPED = "alert_deduped"            # 时空去重判定完成
    ALERT_DISPATCHED = "alert_dispatched"      # 告警下发至监管 Agent
    ALERT_VERIFIED = "alert_verified"          # VLM 校验完成（成功/否决均会触发）
    # —— LLM/VLM 校验 ——
    VERIFY_COMPLETED = "verify_completed"      # 二次校验完成
    VERIFY_FAILED = "verify_failed"            # 二次校验失败/异常
    # —— 数据查询 ——
    SQL_GENERATED = "sql_generated"            # Text-to-SQL 生成完成
    SQL_EXECUTED = "sql_executed"              # SQL 执行完成
    SQL_BLOCKED = "sql_blocked"                # AST 拦截
    # —— 意图与路由 ——
    INTENT_RECOGNIZED = "intent_recognized"    # 意图识别完成
    ROUTE_DISPATCHED = "route_dispatched"      # 路由分发已下发
    ROUTE_COMPLETED = "route_completed"        # 路由计划执行完成
    ROUTE_FAILED = "route_failed"              # 路由计划执行失败
    # —— 用户交互 ——
    USER_QUERY_RECEIVED = "user_query_received"
    USER_CONFIRMED = "user_confirmed"
    USER_REJECTED = "user_rejected"
    # —— 整改业务 ——
    RECTIFICATION_CREATED = "rectification_created"
    RECTIFICATION_UPDATED = "rectification_updated"
    # —— 系统层 ——
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_ERROR = "agent_error"
    SYSTEM_EVENT = "system_event"
```

#### 5.1.2 Agent 事件模型

```python
class AgentEventModel(TraceBase):
    """Agent间通信事件标准模型，基建组消息总线通用。"""
    event_id: str = Field(description="事件唯一ID")
    event_type: AgentEventTypeEnum = Field(
        description="事件类型，必须为 AgentEventTypeEnum 注册枚举值；新增事件须经 Schema 变更申请单审批"
    )
    source_agent: str = Field(description="事件来源Agent：router_agent/triage_agent/data_agent/infra")
    target_agent: Optional[str] = Field(default=None, description="目标Agent，为空则广播")
    payload: Dict[str, Any] = Field(description="事件业务数据，遵循对应场景Schema")
    timestamp: datetime = Field(default_factory=beijing_now, description="事件触发时间")
    priority: int = Field(default=1, description="事件优先级，1-5，1最高")
```

### 5.2 意图识别结果模型

```python
class IntentRecognitionResult(TraceBase):
    """意图识别结果模型，路由Agent核心输出"""
    user_query: str = Field(description="用户原始提问")
    intent_type: UserIntentEnum = Field(description="识别出的用户意图")
    intent_confidence: float = Field(description="意图识别置信度", ge=0.0, le=1.0)
    slots: Dict[str, Any] = Field(default_factory=dict, description="已提取的槽位信息")
    missing_slots: List[str] = Field(default_factory=list, description="缺失的必填槽位")
    target_agent: str = Field(description="目标处理Agent")
    target_tool: Optional[str] = Field(default=None, description="目标调用工具名称")
    tool_args: Optional[Dict[str, Any]] = Field(default=None, description="工具调用入参")
    need_clarification: bool = Field(default=False, description="是否需要向用户澄清")
    clarification_content: Optional[str] = Field(default=None, description="澄清话术")
    is_out_of_domain: bool = Field(default=False, description="是否为领域外问题")
```

### 5.3 路由执行计划模型

```python
class RoutePlanModel(TraceBase):
    """路由执行计划模型，复杂任务编排专用"""
    plan_id: str = Field(description="执行计划唯一ID")
    session_id: str = Field(description="所属会话ID")
    user_id: str = Field(description="操作用户ID")
    intent_type: UserIntentEnum = Field(description="用户意图")
    step_order: List[Dict[str, Any]] = Field(
        description="执行步骤顺序，每个元素包含 agent、tool、args、depends_on 字段"
    )
    current_step: int = Field(default=1, description="当前执行步骤")
    execution_status: ExecutionStatusEnum = Field(
        default=ExecutionStatusEnum.PLANNED,
        description="执行状态枚举，详见 2.4.9 ExecutionStatusEnum",
    )
    error_code: Optional[str] = Field(default=None, description="执行失败错误码")
    error_message: Optional[str] = Field(default=None, description="执行失败描述")
    retry_count: int = Field(default=0, description="已重试次数")
    max_retry: int = Field(default=3, description="最大重试次数")
    created_at: datetime = Field(default_factory=beijing_now, description="计划创建时间")
    updated_at: datetime = Field(default_factory=beijing_now, description="计划更新时间")
```

### 5.4 二次确认操作模型

```python
class ConfirmationModel(TraceBase):
    """高危操作二次确认模型，路由Agent专用"""
    confirmation_id: str = Field(description="确认单唯一ID")
    session_id: str = Field(description="所属会话ID")
    user_id: str = Field(description="操作用户ID")
    action_type: ActionTypeEnum = Field(description="操作类型枚举，详见 2.4.10 ActionTypeEnum")
    action_preview: str = Field(description="操作预览描述，展示给用户确认")
    action_params: Dict[str, Any] = Field(description="操作执行入参")
    confirmation_status: str = Field(
        default="pending",
        description="确认状态：pending/confirmed/rejected/expired"
    )
    created_at: datetime = Field(default_factory=beijing_now, description="创建时间")
    expires_at: datetime = Field(
        default_factory=lambda: beijing_now() + timedelta(minutes=15),
        description="过期时间，默认15分钟"
    )
```

### 5.5 前端聊天接口模型

```python
class ChatMessageRequest(RequestBase):
    """前端→路由Agent聊天消息请求模型"""
    session_id: str = Field(description="会话ID")
    message_text: str = Field(description="用户输入文本内容")
    input_type: str = Field(default="text", description="输入类型：text/button/file/confirmation")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")
    confirmation_id: Optional[str] = Field(default=None, description="确认/取消操作对应的确认单ID")

class ChatMessageResponse(ResponseBase):
    """路由Agent→前端聊天消息响应模型"""
    session_id: str = Field(description="会话ID")
    response_type: str = Field(
        description="响应类型：answer/clarification/confirmation_preview/refusal/error/guidance"
    )
    answer_payload: str = Field(description="响应文本内容")
    structured_summary: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None, description="结构化数据，用于前端卡片/图表渲染")
    guidance_type: str = Field(default="none", description="引导类型：none/followup_query/rectification/export/notify")
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list, description="建议操作按钮列表")
    pending_confirmation: Optional[ConfirmationModel] = Field(default=None, description="待确认操作信息")
```

---

## 六、数据Agent专用模型

**适用模块**：数据分析Agent组、基建组SQL拦截器、路由Agent
**核心说明**：统一Text-to-SQL全流程数据格式，严格贴合数据安全红线要求。

### 6.1 统一数据查询请求模型

```python
from pydantic import model_validator

class FoodSafetyDataQueryRequest(RequestBase):
    """路由Agent→数据Agent统一查询请求模型，Function Calling专用。

    实例化约束（解决基类必填字段缺失问题）：
    1. 调用方既可显式传入 `user_id`，也可仅传 `permission_context`，由前置验证器自动从
       `permission_context.user_id` 回填基类的 `user_id`，避免基类必填字段缺失报错；
    2. 若两者同时传入但取值不一致，校验失败并抛出 `ValueError`（建议网关包装为 `PARAM_ERROR / 1001`），
       从源头杜绝越权风险；
    3. `trace_id`、`request_time` 由 `TraceBase` / `RequestBase` 的 `default_factory` 自动生成，无需显式传入。
    """
    user_query: str = Field(description="用户自然语言查询问题")
    scene: QuerySceneEnum = Field(default=QuerySceneEnum.ALARM_QUERY, description="查询场景枚举，详见 2.4.12 QuerySceneEnum")
    time_range: Optional[Tuple[datetime, datetime]] = Field(default=None, description="时间范围槽位")
    store_scope: Optional[List[str]] = Field(default=None, description="门店范围槽位")
    region_scope: Optional[List[str]] = Field(default=None, description="区域范围槽位")
    violation_type: Optional[List[ViolationTypeEnum]] = Field(default=None, description="违规类型槽位")
    risk_level: Optional[List[AlertLevelEnum]] = Field(default=None, description="风险等级槽位")
    event_id: Optional[str] = Field(default=None, description="告警 ID（AlertCoreModel.id）或事件 ID（ViolationEventModel.event_id）槽位；数据 Agent 需根据查询意图选择目标表字段")
    task_id: Optional[str] = Field(default=None, description="整改工单ID槽位")
    chat_history: Optional[List[ChatMessage]] = Field(default=None, description="对话历史，用于多轮指代消解，由 ChatMessage 强类型约束")
    permission_context: PermissionContext = Field(description="权限上下文，用于数据隔离")

    @model_validator(mode="before")
    @classmethod
    def _auto_fill_user_id(cls, data: Any) -> Any:
        """前置：未显式传 user_id 但已传 permission_context 时，自动回填，避免基类必填字段缺失。"""
        if isinstance(data, dict) and not data.get("user_id"):
            ctx = data.get("permission_context")
            ctx_user_id = (
                ctx.get("user_id") if isinstance(ctx, dict) else getattr(ctx, "user_id", None)
            )
            if ctx_user_id:
                data["user_id"] = ctx_user_id
        return data

    @model_validator(mode="after")
    def _ensure_user_id_match_context(self) -> "FoodSafetyDataQueryRequest":
        """后置：强制 user_id 与 permission_context.user_id 一致，杜绝两路标识漂移引发的越权。"""
        if self.user_id != self.permission_context.user_id:
            raise ValueError(
                f"user_id ({self.user_id!r}) 必须与 permission_context.user_id "
                f"({self.permission_context.user_id!r}) 严格一致"
            )
        return self
```

### 6.2 SQL生成结果模型

```python
class SqlGenerationStatusEnum(str, Enum):
    """SQL 生成状态枚举，数据Agent专用。

    所有 SQL 生成结果模型必须使用本枚举，禁止业务代码自由拼写字符串，
    避免出现 'sucess' / 'parse_err' 等拼写漂移导致状态判断失败。
    """
    SUCCESS = "success"                  # 生成成功
    EMPTY_RESPONSE = "empty_response"    # LLM 返回空响应
    PARSE_ERROR = "parse_error"          # 响应解析失败（非 SQL / Markdown 包裹异常等）
    RETRY_EXHAUSTED = "retry_exhausted"  # 重试耗尽仍失败


class SQLGenerateResult(TraceBase):
    """SQL生成结果模型，数据Agent内部流转专用"""
    user_query: str = Field(description="用户原始查询")
    generated_sql: str = Field(description="生成的纯净SQL语句")
    sql_generation_status: SqlGenerationStatusEnum = Field(
        description="SQL 生成状态枚举，详见上方 SqlGenerationStatusEnum"
    )
    error_message: Optional[str] = Field(default=None, description="错误描述")
    retry_count: int = Field(default=0, description="已重试次数")
```

### 6.3 AST安全校验结果模型

```python
class ASTSecurityCheckResult(TraceBase):
    """AST安全校验结果模型，数据Agent/基建拦截器通用"""
    original_sql: str = Field(description="原始SQL语句")
    is_pass: bool = Field(description="是否校验通过")
    blocked_type: Optional[BlockedTypeEnum] = Field(
        default=None,
        description="拦截类型枚举，详见 2.4.11 BlockedTypeEnum",
    )
    reason: str = Field(description="校验结果描述/拦截原因")
```

### 6.4 AST性能校验结果模型

```python
class ASTPerformanceCheckResult(TraceBase):
    """AST性能校验结果模型，数据Agent/基建拦截器通用"""
    original_sql: str = Field(description="原始SQL语句")
    is_pass: bool = Field(description="是否校验通过")
    is_modified: bool = Field(description="是否自动修正SQL")
    processed_sql: str = Field(description="处理后的SQL语句")
    auto_limit_value: Optional[int] = Field(default=None, description="自动追加的LIMIT值")
    reason: str = Field(description="校验结果描述/拦截原因")
```

### 6.5 数据库执行结果模型

```python
class DbExecuteStatusEnum(str, Enum):
    """数据库执行状态枚举，数据Agent / 基建拦截器通用。

    覆盖 SQL 执行全链路所有结果分支，便于上层用枚举做精准分支判断，
    禁止业务代码自由拼写字符串。
    """
    SUCCESS = "success"                      # 执行成功
    CONNECTION_FAILED = "connection_failed"  # 连接失败 / 网络异常 / 认证错误
    QUERY_TIMEOUT = "query_timeout"          # 查询超时
    PERMISSION_DENIED = "permission_denied"  # 权限不足
    SYNTAX_ERROR = "syntax_error"            # 语法错误


class DBExecuteResult(TraceBase):
    """数据库执行结果模型，数据Agent专用"""
    execute_sql: str = Field(description="最终执行的SQL语句")
    db_result_data: List[Dict[str, Any]] = Field(default_factory=list, description="查询结果数据集")
    db_result_rows: int = Field(description="查询结果行数")
    db_execute_status: DbExecuteStatusEnum = Field(
        description="数据库执行状态枚举，详见上方 DbExecuteStatusEnum"
    )
    db_execution_latency_ms: int = Field(description="SQL执行耗时，单位毫秒")
    error_message: Optional[str] = Field(default=None, description="错误描述")
```

### 6.6 数据Agent统一响应模型

```python
class DataAgentResponse(ResponseBase):
    """数据Agent→路由Agent统一响应模型。

    消费契约（强约束，违反将导致路由 Agent 把错误描述误读为查询结果）：
    1. 调用方在读取业务字段前，**必须**先校验基类 `success=True` **且** `code=='0000'`，二者缺一不可；
    2. 失败场景（`success=False` 或 `code!='0000'`）下，`translated_text` 与 `structured_summary` 必须为 `None`，
       错误详情统一走基类的 `message` / `code` / `data` 字段，禁止把错误描述塞进 `translated_text`；
    3. 严禁仅以 `translated_text` 是否非空作为成功判断依据。

    模型自身通过 `model_validator` 强制上述契约，违反约束的实例无法构造，
    从源头消除"接收方忘看 code/success → 误判"风险。
    """
    translated_text: Optional[str] = Field(
        default=None,
        description="自然语言翻译后的查询结果，**仅在 success=True 且 code='0000' 时填充**；失败场景必须为 None"
    )
    structured_summary: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default=None,
        description="结构化数据摘要，与 translated_text 同步填充/置空，失败场景必须为 None"
    )
    original_sql: Optional[str] = Field(default=None, description="执行的原始SQL，仅审计用")
    execute_latency_ms: Optional[int] = Field(default=None, description="执行总耗时")

    @model_validator(mode="after")
    def _ensure_payload_match_status(self) -> "DataAgentResponse":
        """成功响应必须有业务结果；失败响应必须置空业务字段。"""
        is_success = self.success and self.code == "0000"
        if is_success:
            if self.translated_text is None:
                raise ValueError("成功响应（success=True 且 code='0000'）必须填充 translated_text")
        else:
            if self.translated_text is not None or self.structured_summary is not None:
                raise ValueError(
                    "失败响应禁止填充 translated_text/structured_summary，错误详情请走 message/code/data"
                )
        return self
```

---

## 七、审计日志核心模型

**适用模块**：全项目所有分组、所有模块
**核心说明**：严格贴合可追溯红线，统一全项目审计日志格式，所有核心操作必须按此模型埋点。

### 7.1 审计事件类型枚举

```python
class AuditEventTypeEnum(str, Enum):
    """全局审计事件类型枚举"""
    # 用户操作类
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_QUERY = "user_query"
    USER_EXPORT = "user_export"
    USER_ACTION_CONFIRM = "user_action_confirm"
    USER_ACTION_REJECT = "user_action_reject"
    # 大模型调用类
    INTENT_RESOLVED = "intent_resolved"
    LLM_CALL = "llm_call"
    SQL_GENERATED = "sql_generated"
    VLM_VERIFY = "vlm_verify"
    # 工具调用类
    TOOL_CALLED = "tool_called"
    AGENT_ROUTE = "agent_route"
    DB_EXECUTE = "db_execute"
    # 安全拦截类
    SQL_SECURITY_BLOCKED = "sql_security_blocked"
    SQL_PERFORMANCE_BLOCKED = "sql_performance_blocked"
    PERMISSION_DENIED = "permission_denied"
    LLM_FUSE_TRIGGERED = "llm_fuse_triggered"
    # 告警业务类
    ALERT_RECEIVED = "alert_received"
    ALERT_VERIFIED = "alert_verified"
    RECTIFICATION_UPDATED = "rectification_updated"
    # 系统类
    CONFIRMATION_CREATED = "confirmation_created"
    CONFIRMATION_EXPIRED = "confirmation_expired"
    SYSTEM_ERROR = "system_error"
```

### 7.2 审计日志核心模型

```python
class AuditLogModel(TraceBase):
    """全局审计日志核心模型，全项目通用。

    脱敏强约束：`input_data`、`output_data` 落库前**必须**经 `src/core/logger.py` 提供的统一脱敏工具处理，
    禁止明文写入手机号/邮箱/密钥/Token/身份证/详细地址等敏感字段（清单见 1.3 节第 5 条）。
    """
    audit_id: str = Field(description="审计日志唯一ID")
    event_type: AuditEventTypeEnum = Field(description="审计事件类型")
    operator: str = Field(description="操作主体：user_id/系统/agent名称")
    action: str = Field(description="操作描述")
    input_data: Optional[str] = Field(default=None, description="操作入参（**已脱敏**）的 JSON 字符串")
    output_data: Optional[str] = Field(default=None, description="操作出参（**已脱敏**）的 JSON 字符串")
    success: bool = Field(description="操作是否成功")
    error_code: Optional[str] = Field(default=None, description="操作失败错误码")
    error_message: Optional[str] = Field(default=None, description="操作失败描述")
    latency_ms: Optional[int] = Field(default=None, description="操作耗时，单位毫秒")
    user_id: Optional[str] = Field(default=None, description="关联操作用户ID")
    session_id: Optional[str] = Field(default=None, description="关联会话ID")
    alert_id: Optional[str] = Field(default=None, description="关联告警ID")
    event_time: datetime = Field(default_factory=beijing_now, description="事件发生时间（带北京时区）")
```

---

## 八、Schema变更管理规范

1. **变更申请**：任何组需要修改、新增Schema内容，必须提交《Schema变更申请单》，说明变更原因、变更内容、影响范围、兼容性方案。
2. **变更评审**：所有变更必须经架构师组织全项目评审通过，方可纳入规范。
3. **版本管理**：每次变更发布新版规范，小版本号+1，重大变更大版本号+1，保留所有历史版本。
4. **向前兼容**：所有变更必须保证向前兼容，禁止修改已发布的核心字段含义、类型，禁止删除已发布的核心字段。
5. **全量同步**：新版规范发布后，必须组织全项目培训，确保所有组同步更新代码，严格遵循新版规范。
6. **红线约束**：任何私自修改、新增核心Schema的行为，视为违反项目红线，一票否决对应组周度里程碑。

---

## 九、变更记录

### V1.5（2026-05-07）

- **背景**：架构评审发现 `ALERT_RECEIVED` 事件协议定义与代码实现不一致——`event_protocol.py` 声明 payload_schema 为 `AlertPushRequest`，但网关层实际仅投递 `{"alert_id": ...}`，导致 triage_agent 消费方必须二次查询网关存储层获取完整数据，形成不必要的耦合与延迟。
- **修订项**：

  | # | 章节 | 变更内容 | 影响面 |
  | :- | :--- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
  | 1 | 3.1.2 | `AlertPushRequest` 注释补充说明：本模型仅用于网关层解析 EdgeAgent HTTP 推送后的内部流转，**不直接作为消息总线事件 payload** | 基建网关、事件协议消费方 |
  | 2 | — | `ALERT_RECEIVED` 事件 payload_schema 由 `AlertPushRequest` 调整为 `AlertCoreModel`（详见 `docs/API接口契约文档.md` 4.2 节）；网关层直接序列化完整 `AlertCoreModel` 投递，triage_agent 消费方可直接反序列化使用，无需二次查询 | 基建消息总线、监管 Agent、存储层耦合 |

- **兼容性说明**：
  - `AlertPushRequest` 模型字段无任何变更，仅调整其在事件协议中的引用位置，向前兼容；
  - `AlertCoreModel` 本身无字段变更，仅作为 `ALERT_RECEIVED` 事件 payload 的承载模型，消费方需从"提取 alert_id 二次查询"改为"直接反序列化 AlertCoreModel"；
  - 变更后 triage_agent 与 gateway 存储层解耦，新增消费者无需接入 gateway 内部存储即可消费完整告警数据。

### V1.4（2026-04-27）

- **背景**：A 组（监管研判组）提交《监管研判 Agent Schemas 定义》，明确"输入 = Alert / 输出 = Event"双实体模型；V1.3 的 `AlertCoreModel` 仅覆盖部分透传字段与 2 个校验结果字段，缺失 9 个核心研判产出字段。
- **修订项**：

  | # | 章节 | 变更内容 | 影响面 |
  | :- | :--- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
  | 1 | 2.4 | 新增 `2.4.7 SeverityLevelEnum`（`CRITICAL/MAJOR/MINOR`），区分 `AlertLevelEnum`（YOLO 初始级别）与 `SeverityLevelEnum`（VLM 确认严重度）的职责边界 | 监管 Agent VLM 校验、数据 Agent 报表查询 |
  | 2 | 2.4        | 新增 `2.4.8 VerificationMethodEnum`（`VLM/EDGE_RULE`），明确正常模式与降级模式的枚举表达，禁止降级伪装为 vlm                                                                                                                                       | 监管 Agent 校验链路、审计追溯、下游可信度判断          |
  | 3 | 3.3        | 新增 `ViolationEventModel`（违规事件核心模型），含 12 个透传字段 + 11 个研判产出字段，完整覆盖 A 组输入/输出契约；与 `AlertCoreModel` 通过 `alert_id` 关联，禁止混淆"原始告警"与"二次校验事件"                                                   | 监管 Agent 输出、数据 Agent 查询、整改台账、审计全链路 |
  | 4 | 1.3        | 新增 `event_id` 格式规范：`EVE{13位毫秒时间戳}{3位随机大写字母}`                                                                                                                                                                                   | 事件生成、落库、查询                                   |
  | 5 | 2.4        | 新增"枚举值冲突约束"：不同枚举字符串值相同但语义不同时，禁止仅以值做业务判断，必须按字段名/枚举类名区分                                                                                                                                                | 落库、缓存、跨系统传输                                 |
  | 6 | 3.2        | `AlertCoreModel.created_at` 描述统一为"告警数据入库时间（系统创建时间）"，与 `ViolationEventModel` 语义对齐                                                                                                                                        | 文档一致性                                             |
  | 7 | 3.3        | `ViolationEventModel.store_id` / `image_url` 由 `str` 改为 `Optional[str]`，与 `AlertCoreModel` 必填性对齐；`is_violation_confirmed` 增加 `UNCERTAIN → False` 映射规则；`camera_location` 增加与 `AlertCoreModel.location` 等价注释 | 字段类型一致性、校验链路完整                           |
  | 8 | 3.9 / 3.10 | 新增 `EventDetailResponse` / `EventListQueryResponse`，使 `ViolationEventModel` 可被前端/数据 Agent 消费                                                                                                                                         | 前端展示、数据查询                                     |
  | 9 | 6.1        | `FoodSafetyDataQueryRequest.event_id` 描述细化，明确区分 `alert_id` 与 `event_id` 的查询场景                                                                                                                                                     | 数据 Agent SQL 生成                                    |
- **兼容性说明**：
  - `SeverityLevelEnum` / `VerificationMethodEnum` 为纯新增枚举，无存量冲突，向前兼容；
  - `ViolationEventModel` 为纯新增模型，不改动 `AlertCoreModel` 任何现有字段，向前兼容；但 A 组代码需从"单 Alert 模型"切换为"Alert 输入 → Event 输出"双模型模式，建议在 `src/agents/triage_agent/` 中新建 `event_service.py` 做事件生成与落库；
  - `store_id` / `image_url` 改为 `Optional[str]` 是放宽约束，原有非空值不受影响；
  - `EventDetailResponse` / `EventListQueryResponse` 为纯新增接口模型，不影响现有 `AlertDetailResponse` / `AlertListQueryResponse`；事件列表请求侧复用 `AlertListQueryRequest`，无需新增请求模型。

### V1.3（2026-04-27）

- **背景**：B 组（数据组）联合代码评审反馈三处规范对齐隐患——保留字段命名矛盾、AlertCoreModel 缺权限关联字段、状态字段未按 Enum 强约束。
- **修订项**：

  | # | 章节 | 变更内容 | 影响面 |
  | :- | :--- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
  | 1 | 1.2 | 保留字段命名收敛：`create_time` / `update_time` 全局废弃，统一为 `created_at` / `updated_at`，与 `AlertCoreModel` 与数据库通用约定一致；`UserInfoModel`、`SessionContext`、`RoutePlanModel`、`ConfirmationModel` 同步改造 | 全项目所有用户/会话/路由/确认模型、对应表结构与 SQL |
  | 2 | 3.2  | `AlertCoreModel` 新增 `store_id: Optional[str]` 字段，描述与权限模型 `store_ids` 严格对齐；`location` 退化为展示字段，禁止用于权限过滤                                                                                              | 网关写入、监管 Agent、数据 Agent SQL 权限过滤、前端展示 |
  | 3 | 2.4  | 新增 `2.4.6 RectificationStatusEnum`（`PENDING/PROCESSING/COMPLETED/EXPIRED`），`AlertCoreModel.rectification_status`、`AlertListQueryRequest.rectification_status` 由 `str` 升级为该枚举                                         | 监管 Agent、数据 Agent 查询、前端筛选                   |
  | 4 | 6.2  | 新增 `SqlGenerationStatusEnum`（`SUCCESS/EMPTY_RESPONSE/PARSE_ERROR/RETRY_EXHAUSTED`），`SQLGenerateResult.sql_generation_status` 由 `str` 升级为该枚举                                                                             | 数据 Agent SQL 生成器、重试与降级链路                   |
  | 5 | 6.5  | 新增 `DbExecuteStatusEnum`（`SUCCESS/CONNECTION_FAILED/QUERY_TIMEOUT/PERMISSION_DENIED/SYNTAX_ERROR`），`DBExecuteResult.db_execute_status` 由 `str` 升级为该枚举                                                                   | 数据 Agent DB 执行层、错误码映射、审计                  |
- **兼容性说明**：
  - **保留字段重命名**为破坏性变更——所有现存用户表、会话表、路由计划表、确认单表的列名必须同步迁移；ORM 层、SQL 写入/读取、Pydantic 模型都需要全量改造，建议在 V1.3 上线前由 DB Owner 出具迁移脚本，并通过《Schema 变更申请单》备案；
  - **`store_id` 新增**为非破坏性增强，老数据 `store_id=None` 时 SQL 过滤可临时 fallback 到 `location` 字段做模糊匹配，但 fallback 仅作过渡方案，三个月内全量回填后即移除；
  - **状态字段枚举化**（`rectification_status` / `sql_generation_status` / `db_execute_status`）属于结构变更，老代码若以字符串赋值（如 `'pending'`）构造模型仍可工作（Pydantic V2 自动校验并转为枚举实例），但反向取值时需通过 `.value` 取字符串；建议各组在升级时统一切换为枚举常量，避免字符串硬编码再次漂移。

### V1.2（2026-04-26）

- **背景**：B/C 组联合代码评审反馈 3 处 V1.1 残留隐患——基类必填字段在子模型实例化时缺失、跨 Agent 响应消费契约缺失、Agent 事件类型字符串漂移。
- **修订项**：

  | # | 章节 | 变更内容 | 影响面 |
  | :- | :--- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------- |
  | 1 | 5.1 | 新增 `AgentEventTypeEnum`（5.1.1）；`AgentEventModel.event_type` 由 `str` 升级为 `AgentEventTypeEnum`（5.1.2），未注册类型构造即失败                 | 基建消息总线、所有发布/订阅事件的 Agent |
  | 2 | 6.1  | `FoodSafetyDataQueryRequest` 增加 `model_validator(mode='before')` 自动从 `permission_context.user_id` 回填 `user_id`，`mode='after'` 强制两者一致 | 路由 Agent → 数据 Agent 调用链         |
  | 3 | 6.6  | `DataAgentResponse.translated_text` 由 `str` 改为 `Optional[str]`（默认 None）；新增成功/失败一致性校验，强制消费方先读基类 `success/code`           | 数据 Agent 输出方、路由 Agent 消费方    |
- **兼容性说明**：
  - **5.1 事件枚举化**为破坏性变更——订阅方旧的自由字符串若未在新枚举中注册将反序列化失败；上线前各组需提交未注册事件清单走《Schema 变更申请单》一次性纳入；
  - **6.1 验证器自动回填**为非破坏性增强，原本显式传 `user_id` 的代码无需改动；不一致的取值现在会被验证器拦截，建议网关层将 `ValueError` 包装为 `PARAM_ERROR (1001)`；
  - **6.6 `translated_text` 改 Optional** 对生产端是放宽（允许 None），消费端若已有"先看 success 再读字段"的代码不受影响；未做该校验的旧代码必须立即整改，避免 `translated_text=None` 时触发 `AttributeError`。

### V1.1（2026-04-26）

- **背景**：基于内部代码评审《优化建议》对 V1.0 草案做隐患修复，全部为兼容性增强修订，向前兼容。
- **修订项**：

  | # | 章节 | 变更内容 | 影响面 |
  | :- | :---- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------- |
  | 1 | 1.3 | 新增 `BEIJING_TZ` / `beijing_now()` 标准时间工具，要求所有 `default_factory` 使用 `beijing_now`，禁止 `datetime.now`                                             | 全项目所有模型默认时间字段                 |
  | 2  | 1.3   | 新增"敏感信息脱敏规范"（字段清单 / 标准规则 / 强制要求）                                                                                                                   | 日志、审计、网关、数据层                   |
  | 3  | 2.2   | 新增 `PageResponseBase` 通用分页响应基类                                                                                                                                 | 所有列表查询响应模型                       |
  | 4  | 2.2   | `RequestBase` / `ResponseBase` 默认时间改为 `beijing_now`                                                                                                            | 所有继承请求/响应模型                      |
  | 5  | 2.3   | 新增错误码号段强约束分配表，新增 80xx 核心基建组号段；将 `7001 ALERT_PUSH_FAILED` 标记为 Deprecated（保留可读但不再新增引用），新增 `8002 EDGE_ALERT_PUSH_FAILED` 替代 | 网关、监管 Agent 错误码引用方需迁移到 8002 |
  | 6  | 2.4.2 | `AlertLevelEnum` 新增 `UNKNOWN` 兜底项                                                                                                                                 | 网关 level 映射                            |
  | 7  | 2.4.4 | `ViolationTypeEnum` 新增 `UNKNOWN`（A00），与 `OTHER`（A99）语义区分                                                                                                 | 网关违规类型映射                           |
  | 8  | 3.2   | `AlertCoreModel.bbox` 由 `Optional[List[float]]` 升级为 `Optional[List[List[float]]]`，兼容多目标场景                                                                | 监管 Agent VLM 校验、前端检测框渲染        |
  | 9  | 3.5   | `AlertListQueryResponse` 改为继承 `PageResponseBase`                                                                                                                   | 数据 Agent / 路由 Agent 列表查询调用方     |
  | 10 | 7.2   | `AuditLogModel` 强化 `input_data` / `output_data` 脱敏约束注释，落库强制走统一脱敏工具                                                                               | 全项目审计埋点                             |
- **兼容性说明**：bbox 由一维数组升级为二维数组属于结构变更，需要消费侧（监管 Agent、前端）配合升级；其余均为新增字段、新增枚举值、默认值替换或错误码新增，均向前兼容。`7001 ALERT_PUSH_FAILED` 仅作 Deprecated 标记保留，新调用方一律使用 `8002`。
