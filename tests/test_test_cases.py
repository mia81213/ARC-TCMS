"""测试用例 API 集成测试"""

import pytest


@pytest.mark.asyncio
async def test_create_test_case(client):
    """测试创建用例"""
    payload = {
        "title": "测试用例 — API测试",
        "module": "测试模块",
        "priority": "P1",
        "status": "active",
        "precondition": "测试前置条件",
        "steps": [
            {"seq": 1, "action": "打开页面", "expected": "显示正常"},
            {"seq": 2, "action": "点击按钮", "expected": "弹出提示"},
        ],
        "tags": ["api-test", "regression"],
    }
    resp = await client.post("/api/test-cases", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["title"] == payload["title"]
    assert data["module"] == payload["module"]
    assert len(data["steps"]) == 2
    assert len(data["tags"]) == 2


@pytest.mark.asyncio
async def test_list_test_cases(client):
    """测试用例列表"""
    # 先创建几条数据
    for i in range(3):
        await client.post("/api/test-cases", json={
            "title": f"测试用例 {i}", "module": "列表测试",
            "priority": "P2", "steps": [],
        })

    resp = await client.get("/api/test-cases")
    assert resp.status_code == 200
    data = resp.json()
    assert data["meta"]["total"] >= 3
    assert len(data["data"]) >= 3


@pytest.mark.asyncio
async def test_get_test_case(client):
    """测试获取单个用例"""
    # 创建
    create_resp = await client.post("/api/test-cases", json={
        "title": "获取测试", "module": "详情测试",
        "priority": "P0", "steps": [],
    })
    case_id = create_resp.json()["id"]

    # 获取
    resp = await client.get(f"/api/test-cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "获取测试"


@pytest.mark.asyncio
async def test_update_test_case(client):
    """测试更新用例"""
    # 创建
    create_resp = await client.post("/api/test-cases", json={
        "title": "更新前", "module": "更新测试",
        "priority": "P3", "steps": [],
    })
    case_id = create_resp.json()["id"]

    # 更新
    resp = await client.put(f"/api/test-cases/{case_id}", json={
        "title": "更新后", "priority": "P1",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "更新后"
    assert resp.json()["priority"] == "P1"


@pytest.mark.asyncio
async def test_delete_test_case(client):
    """测试删除用例"""
    # 创建
    create_resp = await client.post("/api/test-cases", json={
        "title": "待删除", "module": "删除测试",
        "priority": "P2", "steps": [],
    })
    case_id = create_resp.json()["id"]

    # 删除
    resp = await client.delete(f"/api/test-cases/{case_id}")
    assert resp.status_code == 200

    # 确认已删除
    get_resp = await client.get(f"/api/test-cases/{case_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_module(client):
    """测试按模块筛选"""
    await client.post("/api/test-cases", json={
        "title": "用例A", "module": "模块X", "priority": "P2", "steps": [],
    })
    await client.post("/api/test-cases", json={
        "title": "用例B", "module": "模块Y", "priority": "P2", "steps": [],
    })

    resp = await client.get("/api/test-cases?module=模块X")
    data = resp.json()
    for case in data["data"]:
        assert case["module"] == "模块X"


@pytest.mark.asyncio
async def test_filter_by_priority(client):
    """测试按优先级筛选"""
    await client.post("/api/test-cases", json={
        "title": "P0用例", "module": "筛选测试", "priority": "P0", "steps": [],
    })

    resp = await client.get("/api/test-cases?priority=P0")
    data = resp.json()
    assert len(data["data"]) > 0
    for case in data["data"]:
        assert case["priority"] == "P0"


@pytest.mark.asyncio
async def test_modules_list(client):
    """测试获取模块列表"""
    await client.post("/api/test-cases", json={
        "title": "M1", "module": "模块甲", "priority": "P2", "steps": [],
    })
    await client.post("/api/test-cases", json={
        "title": "M2", "module": "模块乙", "priority": "P2", "steps": [],
    })

    resp = await client.get("/api/test-cases/modules")
    data = resp.json()
    assert "模块甲" in data["data"]
    assert "模块乙" in data["data"]
