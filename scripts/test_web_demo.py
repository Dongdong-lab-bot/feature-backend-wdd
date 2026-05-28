"""Web Demo 完整测试脚本（独立执行，无转义问题）"""
import urllib.request
import json

BASE = "http://127.0.0.1:8080"

def test(name, url, method="GET", body=None):
    try:
        if method == "GET":
            r = urllib.request.urlopen(url)
        else:
            data = json.dumps(body).encode() if body else None
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            if method == "PUT":
                req.get_method = lambda: "PUT"
            elif method == "DELETE":
                req.get_method = lambda: "DELETE"
            r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except Exception as e:
        print(f"  FAILED: {e}")
        return None


def main():
    print("=" * 50)
    print(" Web Demo 完整测试")
    print("=" * 50)

    # 1. stats
    data = test("GET /stats", f"{BASE}/api/demo/stats")
    assert data and data["code"] == "0000"
    print(f"[1/6] GET /stats -> {data['data']['total_alerts']} alerts, {data['data']['total_events']} events ✅")

    # 2. alerts list
    data = test("GET /alerts", f"{BASE}/api/demo/alerts?page=1&page_size=5")
    assert data and data["code"] == "0000"
    print(f"[2/6] GET /alerts -> {data['total']} total, page shows {len(data['data'])} ✅")

    # 3. POST create alert
    data = test("POST /alerts", f"{BASE}/api/demo/alerts", method="POST", body={
        "camera_id": "CAM002", "store_id": "STORE001",
        "message": "测试告警", "violation_type": "A01",
        "level": "high", "confidence": 0.91
    })
    assert data and data["code"] == "0000"
    new_id = data["data"]["id"]
    print(f"[3/6] POST /alerts -> 创建 {new_id} ✅")

    # 4. PUT update alert
    data = test(f"PUT /alerts/{new_id}", f"{BASE}/api/demo/alerts/{new_id}", method="PUT", body={
        "level": "critical", "rectification_status": "processing"
    })
    assert data and data["code"] == "0000"
    print(f"     PUT /alerts/{new_id} -> 更新成功 ✅")

    # 5. DELETE alert
    data = test(f"DELETE /alerts/{new_id}", f"{BASE}/api/demo/alerts/{new_id}", method="DELETE")
    assert data and data["code"] == "0000"
    print(f"     DELETE /alerts/{new_id} -> 逻辑删除成功 ✅")

    # 6. stores
    data = test("GET /stores", f"{BASE}/api/demo/stores")
    assert data and data["code"] == "0000"
    print(f"[4/6] GET /stores -> {len(data['data'])} stores ✅")

    # 7. events
    data = test("GET /events", f"{BASE}/api/demo/events")
    assert data and data["code"] == "0000"
    print(f"[5/6] GET /events -> {len(data['data'])} events ✅")

    # 8. tasks
    data = test("GET /tasks", f"{BASE}/api/demo/tasks")
    assert data and data["code"] == "0000"
    print(f"[6/6] GET /tasks -> {len(data['data'])} tasks ✅")

    # 9. frontend
    r = urllib.request.urlopen(f"{BASE}/demo")
    html = r.read().decode()
    assert "食安大模型" in html
    print(f"[7/6] GET /demo -> 前端加载成功 ({len(html)} bytes) ✅")

    # 10. er-info
    data = test("GET /er-info", f"{BASE}/api/demo/er-info")
    assert data and len(data["data"]["tables"]) == 6
    print(f"[8/6] GET /er-info -> {len(data['data']['tables'])} 张表 ✅")

    print()
    print("=" * 50)
    print(" ALL TESTS PASSED ✅ ")
    print("=" * 50)


if __name__ == "__main__":
    main()
