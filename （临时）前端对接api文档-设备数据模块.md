# 设备接口

### 获取食堂/区域下的设备树 -- GET /devices/tree
response：
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "id": 1,
      "name": "朝阳区",
      "org_type": "AREA",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "北京市第一中学",
          "org_type": "SCHOOL",
          "parent_id": 1,
          "children": [
            {
              "id": 3,
              "name": "第一食堂",
              "org_type": "CANTEEN",
              "parent_id": 2,
              "children": [],
              "devices": [
                {
                  "id": 101,
                  "device_code": "MAC-001",
                  "device_name": "入口测温仪",
                  "status": "ONLINE",
                  "last_heartbeat": "2026-03-25T10:00:00Z"
                },
                {
                  "id": 102,
                  "device_code": "CAM-001",
                  "device_name": "后厨摄像头",
                  "status": "ONLINE",
                  "last_heartbeat": "2026-03-25T10:00:00Z"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 查询设备详情 -- GET /devices/{id}

**功能描述**: 根据ID查询单个设备的详细信息

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 设备ID |

**响应示例**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": 101,
    "device_name": "手部晨检仪",
    "device_code": "AC1256EF456E",
    "status": "ONLINE",
    "created_at": "2026-01-15T08:30:00Z",
    "org_id": 3,
    "org_name": "第一食堂"
  }
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 设备ID |
| device_name | string | 设备名称 |
| device_code | string | 设备唯一码 |
| status | string | 状态：ONLINE/OFFLINE |
| created_at | string | 添加日期 |
| org_id | int | 所属食堂ID |
| org_name | string | 所属食堂 |

### 新增设备 -- POST /devices

**功能描述**: 新增一个设备

**请求体**:
```json
{
  "device_name": "手部晨检仪",
  "device_code": "AC1256EF456E",
  "org_id": 3,
  "status": "OFFLINE"
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device_name | string | 是 | 设备名称 |
| device_code | string | 是 | 设备唯一码 |
| org_id | int | 是 | 所属食堂ID |

**响应示例**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": 101,
    "device_name": "手部晨检仪",
    "device_code": "AC1256EF456E",
    "status": "OFFLINE",
    "created_at": "2026-03-25T10:00:00Z",
    "org_id": 3,
    "org_name": "第一食堂"
  }
}
```

### 更新设备 -- PUT /devices/{id}

**功能描述**: 更新设备信息

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 设备ID |

**请求体**:
```json
{
  "device_name": "手部晨检仪（升级版）",
  "device_code": "AC1256EF456E",
  "status": "ONLINE"
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device_name | string | 否 | 设备名称 |
| status | string | 否 | 状态：ONLINE/OFFLINE/MAINTENANCE |

**响应示例**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": 101,
    "device_name": "手部晨检仪（升级版）",
    "status": "ONLINE",
    "updated_at": "2026-03-25T14:30:00Z"
  }
}
```

### 删除设备 -- DELETE /devices/{id}

**功能描述**: 删除设备（软删除）

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 设备ID |

**响应示例**:
```json
{
  "code": 200,
  "msg": "success",
  "data": null
}
```
 |
| page_size | int | 每页条数 |
| records | array | 设备列表 |
| records[].id | int | 设备ID |
| records[].device_name | string | 设备名称 |
| records[].device_code | string | 设备唯一码 |
| records[].status | string | 状态：ONLINE/OFFLINE |
| records[].created_at | string | 添加日期 |
| records[].org_name | string | 所属食堂 |

### 设备消息记录列表 -- GET /devices/records

**功能描述**: 获取设备消息记录列表，用于渲染"设备消息记录"列表页面

**Query参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| page | int | 否 | 页码（默认1） |
| page_size | int | 否 | 每页条数（默认20） |

**响应示例**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 156,
    "page": 1,
    "page_size": 20,
    "records": [
      {
        "id": 1001,
        "org_name": "第一食堂",
        "device_name": "手部晨检仪",
        "device_code": "AC1256EF456E",
        "data_type": "晨检消息记录",
        "is_related_ledger": true,
        "submit_date": "2026-03-25",
        "status": "ONLINE"
      },
      {
        "id": 1002,
        "org_name": "第一食堂",
        "device_name": "AI盒子8路",
        "device_code": "CAM-001",
        "data_type": "AI盒子消息记录",
        "is_related_ledger": false,
        "submit_date": "2026-03-25",
        "status": "OFFLINE"
      }
    ]
  }
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| total | int | 总记录数 |
| page | int | 当前页码 |
| page_size | int | 每页条数 |
| records | array | 记录列表 |
| records[].id | int | 记录ID |
| records[].org_name | string | 提交食堂 |
| records[].device_name | string | 设备名称 |
| records[].device_code | string | 设备编码 |
| records[].data_type | string | 设备数据类型 |
| records[].is_related_ledger | bool | 是否已关联电子台账 |
| records[].submit_date | string | 提交日期 |
| records[].status | string | 状态：ONLINE/OFFLINE |

### 设备消息记录详情 -- GET /devices/records/{id}

**功能描述**: 查看设备消息记录详情（json/csv格式）

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 记录ID |

**响应示例**:
- 不清楚具体响应结构

### 编辑设备消息记录 -- PUT /devices/records/{id}

**功能描述**: 编辑设备消息记录内容

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 记录ID |

**请求体**:
不清楚消息记录数据结构

**响应示例**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "id": 1001,
    "is_related_ledger": true,
    "updated_at": "2026-03-25T15:00:00Z"
  }
}
```

### 导出设备消息记录 -- GET /devices/records/export

**功能描述**: 下载（导出为Excel/PDF）

**Query参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | string | 否 | 导出格式：excel（默认）/ pdf |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应**: 文件流下载
