#!/usr/bin/env bash
# ============================================================
# 路由 Agent API 联调测试脚本
# 无需 Redis / 无需 LLM / 无需基建组客户端
# 依赖：JWT_DISABLE_VERIFY=true（开发模式）
# 用法: bash scripts/test_router_api.sh
# ============================================================

BASE_URL="http://localhost:8000"
# 开发模式 JWT（JSON字符串，JWT_DISABLE_VERIFY=true 时可用）
# role_type 可选: store_manager / area_supervisor / enterprise_admin
DEV_JWT='{"user_id":"dev_user","role_type":"enterprise_admin","exp":9999999999}'

PASS=0
FAIL=0

check() {
    local test_name="$1"
    local http_code="$2"
    local response="$3"
    local expected_code="$4"

    if [ "$http_code" == "200" ] || [ "$http_code" == "201" ]; then
        # 提取 code 字段
        local code=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','FAIL'))" 2>/dev/null)
        if [ "$code" == "$expected_code" ] || [ "$expected_code" == "" ]; then
            echo "[PASS] $test_name (HTTP=$http_code code=$code)"
            PASS=$((PASS + 1))
        else
            echo "[FAIL] $test_name (expected code=$expected_code, got=$code)"
            echo "  Response: $response"
            FAIL=$((FAIL + 1))
        fi
    else
        echo "[FAIL] $test_name (HTTP=$http_code, expected 200/201)"
        echo "  Response: $response"
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================"
echo "路由 Agent API 联调测试"
echo "BASE_URL=$BASE_URL"
echo "========================================"
echo ""

# ---- TC01: 创建会话 ----
echo "--- TC01: 创建会话 ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/sessions" \
    -H "Authorization: Bearer $DEV_JWT" \
    -H "Content-Type: application/json" \
    -d '{}')
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC01-创建会话" "$HTTP_CODE" "$BODY" "0000"

# 提取 session_id
SESSION_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('session_id',''))" 2>/dev/null)
echo "  SESSION_ID=$SESSION_ID"
echo ""

# ---- TC02: 查询告警（QUERY_DETAIL） ----
echo "--- TC02: 查询告警 ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/messages" \
    -H "Authorization: Bearer $DEV_JWT" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"user_id\":\"dev_user\",\"message_text\":\"今天店里有多少违规抓拍\",\"input_type\":\"text\"}")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC02-查询告警" "$HTTP_CODE" "$BODY" "0000"
echo "  Response: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer_payload',''))" 2>/dev/null)"
echo ""

# ---- TC03: 查询报表（QUERY_SUMMARY） ----
echo "--- TC03: 查询报表 ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/messages" \
    -H "Authorization: Bearer $DEV_JWT" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"user_id\":\"dev_user\",\"message_text\":\"查一下上周的告警统计报表\",\"input_type\":\"text\"}")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC03-查询报表" "$HTTP_CODE" "$BODY" "0000"
echo "  Response: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer_payload',''))" 2>/dev/null)"
echo ""

# ---- TC04: 查询整改进度（QUERY_RECTIFICATION） ----
echo "--- TC04: 查询整改进度 ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/messages" \
    -H "Authorization: Bearer $DEV_JWT" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"user_id\":\"dev_user\",\"message_text\":\"看看整改状态\",\"input_type\":\"text\"}")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC04-整改进度" "$HTTP_CODE" "$BODY" "0000"
echo "  Response: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer_payload',''))" 2>/dev/null)"
echo ""

# ---- TC05: 高危操作 - 需要确认（SEND_NOTICE） ----
echo "--- TC05: 高危操作-下发通知 ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/messages" \
    -H "Authorization: Bearer $DEV_JWT" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"user_id\":\"dev_user\",\"message_text\":\"下发整改通知到南山店\",\"input_type\":\"text\"}")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC05-下发通知" "$HTTP_CODE" "$BODY" "0000"
echo "  Response: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer_payload',''))" 2>/dev/null)"
echo "  ResponseType: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('response_type',''))" 2>/dev/null)"

# 提取 confirmation_id
CNF_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('pending_confirmation',{}).get('confirmation_id',''))" 2>/dev/null)
echo "  CONFIRMATION_ID=$CNF_ID"
echo ""

# ---- TC06: 确认高危操作 ----
if [ -n "$CNF_ID" ] && [ "$CNF_ID" != "None" ]; then
    echo "--- TC06: 确认高危操作 ---"
    RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/confirmations/$CNF_ID/confirm" \
        -H "Authorization: Bearer $DEV_JWT" \
        -H "Content-Type: application/json")
    HTTP_CODE=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')
    check "TC06-确认操作" "$HTTP_CODE" "$BODY" "0000"
    echo "  Response: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer_payload',''))" 2>/dev/null)"
    echo ""
fi

# ---- TC07: 越域请求（OUT_OF_DOMAIN） ----
echo "--- TC07: 越域请求 ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/chat/messages" \
    -H "Authorization: Bearer $DEV_JWT" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"user_id\":\"dev_user\",\"message_text\":\"今天天气怎么样\",\"input_type\":\"text\"}")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC07-越域请求" "$HTTP_CODE" "$BODY" "0000"
echo "  Response: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('answer_payload',''))" 2>/dev/null)"
echo ""

# ---- TC08: 查看会话历史 ----
echo "--- TC08: 会话历史 ---"
RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/chat/sessions/$SESSION_ID/history?page_num=1&page_size=10" \
    -H "Authorization: Bearer $DEV_JWT")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "TC08-会话历史" "$HTTP_CODE" "$BODY" "0000"
echo "  History items count: $(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('total',0))" 2>/dev/null)"
echo ""

# ---- TC09: 越权测试 ----
echo "--- TC09: 越权测试（使用不同user_id的JWT） ---"
DEV_JWT_OTHER='{"user_id":"hacker_user","role_type":"store_manager","exp":9999999999}'
RESP=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/chat/sessions/$SESSION_ID" \
    -H "Authorization: Bearer $DEV_JWT_OTHER")
HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
# 预期 403 或 error
if [ "$HTTP_CODE" == "200" ]; then
    CODE=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code',''))" 2>/dev/null)
    if [ "$CODE" == "3003" ]; then
        echo "[PASS] TC09-越权测试 (code=3003)"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] TC09-越权测试 (未返回权限拒绝)"
        FAIL=$((FAIL + 1))
    fi
else
    echo "[PASS] TC09-越权测试 (HTTP=$HTTP_CODE 权限拦截)"
    PASS=$((PASS + 1))
fi
echo ""

# ---- 总结 ----
echo "========================================"
echo "测试结果汇总"
echo "========================================"
echo "通过: $PASS"
echo "失败: $FAIL"
echo "========================================"
