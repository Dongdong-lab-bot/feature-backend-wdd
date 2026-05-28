Day1:
新建prompt文件夹，3个核心角色的差异化System Prompt:
```
store_manager_prompt.py
area_supervisor_prompt.py
enterprise_admin_prompt.py
```
新建prompt_manager.py

运行结果：
运行结果展示了根据用户角色返回不同的系统 Prompt（提示词）。`prompt_manager.py` 的作用就是根据登录用户的不同角色（店长/督导/管理员），动态返回对应的系统指令，让AI助手知道该以什么身份、什么风格、什么权限范围来回答问题。代码已经成功运行，没有报错。

Day2:
prompts新增intent_recognition_prompt.py
router_agent新增intent_service.py
Safefood-Agent/tests新增test_intent_service.py
### 测试运行结果
测试成功运行，输出结果如下：

__输入查询__：`"帮我查一下今天违规最多的门店"`

__意图识别结果__：

- __trace_id__：`b8754286161c4b39999e028b2079194d` — 唯一追踪ID
- __intent_type__：`QUERY_RANKING`（查询排名意图）— 正确识别了"最多"关键词
- __intent_confidence__：`0.9`（90%置信度，很高）
- __target_agent__：`data_agent` — 路由到数据智能体处理
- __is_out_of_domain__：`False` — 查询在业务范围内

__总结__：`intent_service.py` 的 `recognize()` 方法成功工作。它通过关键词匹配（"最多" → 排名，"趋势" → 趋势，"整改" → 整改）判断用户意图，并将查询路由到对应的处理智能体（data_agent）。这里用户问"违规最多的门店"，命中"最多"关键词，被正确识别为排名查询，置信度0.9。


### 测试运行结果
PS C:\Users\Hi\Safefood-Agent\Safefood-Agent> cd C:\Users\Hi\Safefood-Agent; $env:PYTHONPATH="C:\Users\Hi\Safefood-Agent\Safefood-Agent"; python tests/test_intent_service.py
trace_id='7c6a8beb38354ab2bf658a610b7ff8ff' user_query='查询深圳区域最近7天高风险告警趋势' intent_type=<UserIntentEnum.QUERY_TREND: 'query_trend'> intent_confidence=0.9 slots={'time_range': 'last_7_days', 'risk_level': 'high', 'region': '深圳'} missing_slots=[] target_agent='data_agent' target_tool=None tool_args=None need_clarification=False clarification_content=None is_out_of_domain=False
{'time_range': 'last_7_days', 'risk_level': 'high', 'region': '深圳'}
测试已成功运行。输出结果如下：

__输入查询__：`"查询深圳区域最近7天高风险告警趋势"`

__意图识别结果__：

- __intent_type__：`QUERY_TREND`（查询趋势意图）— 正确识别了"趋势"关键词

- __intent_confidence__：`0.9`

- __slots（提取的关键信息）__：

  - `time_range`：`last_7_days`（从"最近7天"提取）
  - `risk_level`：`high`（从"高风险"提取）
  - `region`：`深圳`（从"深圳"提取）

- __target_agent__：`data_agent`

可以看到，除了意图识别，`extract_slots()` 方法也成功从查询中提取了时间范围、风险等级和区域三个关键参数。
