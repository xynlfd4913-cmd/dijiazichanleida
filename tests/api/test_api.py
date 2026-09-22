from fastapi.testclient import TestClient

from services.api.main import create_app


def test_health_and_admin_make_offline_mode_explicit(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["network_access"] is False
    admin = client.get("/api/admin/status").json()
    assert admin["runtime_mode"] == "offline_mock"
    assert admin["real_network_enabled"] is False
    assert admin["totals"]["assets"] >= 30
    assert admin["totals"]["unknown_cost_items"] > 0


def test_seed_can_be_disabled_by_environment(monkeypatch) -> None:
    monkeypatch.setenv("SEED_ON_START", "false")
    app = create_app("sqlite+pysqlite:///:memory:", seed=None)
    with TestClient(app) as unseeded:
        assert unseeded.get("/health").status_code == 200
        assert unseeded.get("/api/admin/status").json()["totals"]["assets"] == 0


def test_asset_list_is_paginated_filterable_and_mock_only(client: TestClient) -> None:
    response = client.get("/api/assets", params={"category": "工具", "page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert len(body["items"]) == 2
    assert all(item["category"] == "工具" for item in body["items"])
    assert all(item["source_mode"] == "mock" for item in body["items"])
    assert all(item["source_url"].startswith("mock://") for item in body["items"])


def test_asset_detail_separates_deposit_and_preserves_unknown_nulls(client: TestClient) -> None:
    detail = client.get("/api/assets/1")
    assert detail.status_code == 200
    body = detail.json()
    assert body["deposit"] != body["opportunity"]["all_in_cost_max"]
    unknown = [item for item in body["costs"] if item["status"] == "unknown"]
    assert unknown
    assert unknown[0]["min_amount"] is None
    assert unknown[0]["max_amount"] is None
    assert body["opportunity"]["unknown_cost_count"] == len(unknown)
    assert body["opportunity"]["cost_estimate_complete"] is False
    assert body["opportunity"]["margin_is_provisional"] is True
    assert body["opportunity"]["grade"] not in {"S", "A"}
    assert len(body["comparables"]) == 3
    assert body["start_time"].endswith("Z") or body["start_time"].endswith("+00:00")


def test_missing_asset_is_404(client: TestClient) -> None:
    assert client.get("/api/assets/9999").status_code == 404


def test_dashboard_exposes_three_accounts_and_funnel(client: TestClient) -> None:
    body = client.get("/api/dashboard").json()
    assert body["accounts"]["living_reserve_protected"] is True
    assert set(body["accounts"]) >= {
        "living_reserve",
        "asset_capital",
        "debt_repayment_fund",
    }
    assert body["scan_stats"]["scanned"] >= 30
    assert body["scan_stats"]["with_market_reference"] >= 30
    assert body["capital_progress"]["current_level"] == "L2"


def test_profile_update_syncs_asset_account_and_recalculates_fit(client: TestClient) -> None:
    response = client.put(
        "/api/settings",
        json={"available_capital": "1000", "max_single_exposure": "1000", "skills": ["摄影"]},
    )
    assert response.status_code == 200
    profile = response.json()
    asset_account = next(item for item in profile["accounts"] if item["account_type"] == "asset_capital")
    assert asset_account["balance"] == "1000.00"
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["scan_stats"]["capital_fit"] == 0


def test_profile_rejects_negative_protected_balance(client: TestClient) -> None:
    assert client.put("/api/profile", json={"living_reserve": "-1"}).status_code == 422


def test_profile_rejects_explicit_null_patch_values(client: TestClient) -> None:
    assert client.put("/api/profile", json={"available_capital": None}).status_code == 422
    assert client.put("/api/profile", json={"skills": None}).status_code == 422


def test_subscription_crud(client: TestClient) -> None:
    initial = client.get("/api/subscriptions").json()
    assert len(initial) == 1
    created = client.post(
        "/api/subscriptions",
        json={
            "name": "武汉工具测试订阅",
            "province": "湖北",
            "city": "武汉",
            "max_all_in_cost": "3000",
            "min_safe_margin": "500",
            "min_safe_roi": "0.2",
            "categories": ["工具"],
        },
    )
    assert created.status_code == 201
    subscription_id = created.json()["id"]
    updated = client.put(f"/api/subscriptions/{subscription_id}", json={"enabled": False})
    assert updated.json()["enabled"] is False
    assert client.delete(f"/api/subscriptions/{subscription_id}").status_code == 204


def test_subscription_rejects_nulls_and_negative_safety_thresholds(client: TestClient) -> None:
    assert client.put("/api/subscriptions/1", json={"name": None}).status_code == 422
    assert client.put("/api/subscriptions/1", json={"max_all_in_cost": None}).status_code == 422
    base = {"name": "不安全阈值", "max_all_in_cost": "3000"}
    assert client.post("/api/subscriptions", json={**base, "min_safe_margin": "-1"}).status_code == 422
    assert client.post("/api/subscriptions", json={**base, "min_safe_roi": "-0.1"}).status_code == 422


def test_watchlist_crud_and_duplicate_protection(client: TestClient) -> None:
    initial = client.get("/api/watchlist").json()
    assert len(initial) == 1
    created = client.post("/api/watchlist", json={"asset_id": 2, "note": "检查设备"})
    assert created.status_code == 201
    assert created.json()["asset"]["id"] == 2
    assert client.post("/api/watchlist", json={"asset_id": 2}).status_code == 409
    assert client.delete("/api/watchlist/2").status_code == 204


def test_capital_ladder_has_all_levels(client: TestClient) -> None:
    body = client.get("/api/capital-ladder").json()
    assert [level["code"] for level in body["levels"]] == ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
    assert body["current"]["next_target"] == "10000.00"
