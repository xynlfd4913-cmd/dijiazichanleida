"""Deterministic, network-free Phase 0 demonstration dataset."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from engine.hidden_cost.calculator import minimum_cash_required, summarize_costs
from engine.money import decimal
from engine.scoring.opportunity import (
    capital_fit_score,
    cost_certainty_score,
    distance_convenience_score,
    score_opportunity,
    skill_match_score,
)
from engine.types import ComparableInput, CostInput
from engine.valuation.calculator import calculate_valuation
from services.api.models import (
    Account,
    Asset,
    Comparable,
    CostItem,
    Opportunity,
    Subscription,
    UserProfile,
    Watchlist,
)

SEED_NOW = datetime(2026, 9, 22, 8, 0, tzinfo=timezone.utc)

ASSET_FIXTURES: tuple[tuple[str, str, str, int, int, str], ...] = (
    ("木工推台锯与吸尘设备一批", "机械设备", "木工机械", 2600, 35, "武汉"),
    ("二手工业缝纫机 6 台", "机械设备", "轻工机械", 4200, 62, "孝感"),
    ("小型激光雕刻机", "机械设备", "广告设备", 3600, 28, "鄂州"),
    ("台钻与砂轮机组合", "工具", "五金工具", 980, 18, "武汉"),
    ("锂电电动工具套装", "工具", "电动工具", 1450, 42, "黄冈"),
    ("木工气泵与钉枪套装", "工具", "木工工具", 1850, 55, "咸宁"),
    ("2015 年轻型厢式货车", "车辆", "商用车辆", 16800, 78, "武汉"),
    ("二手电动三轮运输车", "车辆", "生产运输", 3200, 25, "武汉"),
    ("小型面包车现状处置", "车辆", "商用车辆", 9800, 96, "荆州"),
    ("五金紧固件尾货一批", "库存", "五金库存", 2800, 48, "武汉"),
    ("家装灯具清仓库存", "库存", "家装库存", 4600, 82, "襄阳"),
    ("餐饮包装耗材库存", "库存", "餐饮库存", 1900, 32, "武汉"),
    ("小户型商住公寓", "房产", "商住", 92000, 110, "武汉"),
    ("乡镇临街小商铺", "房产", "商铺", 68000, 135, "钟祥"),
    ("工业园仓储用房使用权", "房产", "仓储", 128000, 88, "鄂州"),
    ("设计工作站电脑 2 台", "电脑", "工作站", 3900, 12, "武汉"),
    ("直播电脑与采集卡套装", "电脑", "直播设备", 3300, 40, "黄石"),
    ("办公笔记本电脑 8 台", "电脑", "办公电脑", 7200, 65, "孝感"),
    ("双头商用咖啡机", "商用设备", "餐饮设备", 4800, 20, "武汉"),
    ("不锈钢操作台与冷柜", "商用设备", "餐饮设备", 3000, 44, "武汉"),
    ("广告写真机与覆膜机", "商用设备", "广告设备", 5600, 70, "黄冈"),
    ("小型数控车床", "机械设备", "机加工", 11800, 58, "武汉"),
    ("空气压缩机两台", "机械设备", "通用机械", 2700, 76, "仙桃"),
    ("手持测量仪器一批", "工具", "测量工具", 2300, 36, "武汉"),
    ("汽修举升机", "商用设备", "汽修设备", 4100, 92, "荆门"),
    ("便利店货架与收银设备", "商用设备", "零售设备", 2400, 15, "武汉"),
    ("儿童服装尾货 600 件", "库存", "服装库存", 3500, 50, "武汉"),
    ("品牌瓷砖余货一批", "库存", "建材库存", 5200, 105, "宜昌"),
    ("摄影灯与背景架套装", "工具", "摄影设备", 1600, 22, "武汉"),
    ("企业办公台式机 12 台", "电脑", "办公电脑", 8400, 74, "黄石"),
    ("单门商用蒸饭柜", "商用设备", "餐饮设备", 1200, 30, "武汉"),
    ("小型封口包装机", "机械设备", "包装机械", 2100, 46, "武汉"),
)

CATEGORY_RULES: dict[str, dict[str, object]] = {
    "机械设备": {
        "skills": ["机械维修", "电工"], "unknown": "缺件与维修费", "estimated": "拆装运输费",
        "range": (300, 900), "liquidity": 68, "production": 92, "income": 1800,
    },
    "工具": {
        "skills": ["木工"], "unknown": "电池或耗材更换费", "estimated": "运输费",
        "range": (80, 260), "liquidity": 86, "production": 88, "income": 900,
    },
    "车辆": {
        "skills": ["汽修"], "unknown": "违章与证件补办费", "estimated": "拖车停车维修费",
        "range": (800, 2600), "liquidity": 78, "production": 70, "income": 2200,
    },
    "库存": {
        "skills": ["电商", "仓储物流"], "unknown": "实际破损与缺件损失", "estimated": "搬运仓储物流费",
        "range": (250, 950), "liquidity": 66, "production": 55, "income": 1000,
    },
    "房产": {
        "skills": ["家装"], "unknown": "税费、欠费与腾退成本", "estimated": "登记与基础维修费",
        "range": (2500, 9000), "liquidity": 42, "production": 35, "income": 1200,
    },
    "电脑": {
        "skills": ["电脑维修", "短视频"], "unknown": "硬盘健康与维修费", "estimated": "检测与运输费",
        "range": (160, 650), "liquidity": 88, "production": 82, "income": 1500,
    },
    "商用设备": {
        "skills": ["餐饮", "电工"], "unknown": "安装改造与维修费", "estimated": "搬运安装费",
        "range": (220, 780), "liquidity": 65, "production": 90, "income": 1700,
    },
}

PLATFORMS = ("阿里捡漏（模拟）", "湖北产权（模拟）", "公拍网（模拟）", "破产资产（模拟）")
STAGES = ("一拍", "二拍", "变卖")


def _money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def seed_database(session: Session) -> None:
    """Insert the same complete fixture set once per database."""

    if session.scalar(select(func.count(Asset.id))):
        return

    profile = UserProfile(
        id=1,
        available_capital=_money(5000),
        monthly_new_capital=_money(800),
        living_reserve=_money(6000),
        debt_repayment_fund=_money(1200),
        city="武汉",
        province="湖北",
        search_radius=100,
        skills=["木工", "家具", "安装", "电工"],
        storage_available=True,
        vehicle_available=False,
        preferred_asset_types=["机械设备", "工具", "电脑", "商用设备"],
        preferred_strategy="production",
        max_single_exposure=_money(4500),
    )
    profile.accounts = [
        Account(account_type="living_reserve", balance=profile.living_reserve, protected=True),
        Account(account_type="asset_capital", balance=profile.available_capital, protected=False),
        Account(account_type="debt_repayment_fund", balance=profile.debt_repayment_fund, protected=True),
    ]
    session.add(profile)
    session.flush()

    created_assets: list[Asset] = []
    for index, (title, category, subcategory, current, distance, city) in enumerate(ASSET_FIXTURES, start=1):
        rule = CATEGORY_RULES[category]
        platform = PLATFORMS[(index - 1) % len(PLATFORMS)]
        stage = STAGES[(index - 1) % len(STAGES)]
        current_price = _money(current)
        start_price = _money(current_price * Decimal("0.92"))
        appraisal = _money(current_price * Decimal("1.62"))
        deposit = _money(max(200, int(current * 0.12)))
        started = SEED_NOW - timedelta(days=(index % 6) + 1)
        ends = SEED_NOW + timedelta(hours=8 + index * 5)
        asset = Asset(
            source_platform=platform,
            source_mode="mock",
            source_url=f"mock://phase-0/assets/{index:03d}",
            external_id=f"MOCK-{index:03d}",
            title=title,
            category=category,
            subcategory=subcategory,
            province="湖北",
            city=city,
            district="模拟区域",
            seller_or_court="Phase 0 模拟处置方",
            auction_stage=stage,
            status="bidding" if index % 7 else "preview",
            start_time=started,
            end_time=ends,
            first_seen_at=SEED_NOW,
            last_seen_at=SEED_NOW,
            appraisal_price=appraisal,
            start_price=start_price,
            current_price=current_price,
            deposit=deposit,
            bid_increment=_money(max(50, int(current * 0.02))),
            payment_deadline=ends + timedelta(days=5),
            previous_round_price=_money(current_price * Decimal("1.15")) if stage != "一拍" else None,
            previous_round_result="流拍" if stage != "一拍" else None,
            brand="模拟品牌",
            model=f"SIM-{index:03d}",
            year=2018 + index % 7,
            quantity=1 + index % 8 if category in {"库存", "电脑"} else 1,
            condition="现状交付，关键状态需现场核验",
            ownership_status="公告显示可处置，权属材料待人工核验",
            occupancy_status="待核验" if category == "房产" else "不适用",
            inspection_available=index % 5 != 0,
            attachment_urls=[],
            required_skills=list(rule["skills"]),
            distance_km=distance,
            estimated_monthly_income=_money(rule["income"]),
            notice_summary="离线模拟公告：现状交付，费用承担与设备完整性需人工核验。",
        )

        low, high = rule["range"]
        service_fee = _money(current_price * Decimal("0.015"))
        reserve_low = _money(current_price * Decimal("0.03"))
        reserve_high = _money(current_price * Decimal("0.06"))
        item_specs: list[CostInput] = [
            CostInput("平台服务费", "known", service_fee, service_fee),
            CostInput(str(rule["estimated"]), "estimated", low, high),
            CostInput("风险准备金", "estimated", reserve_low, reserve_high),
        ]
        # Three quarters of fixtures contain an explicit unknown fee; no amount is stored.
        if index % 4:
            item_specs.append(CostInput(str(rule["unknown"]), "unknown"))
        asset.cost_items = [
            CostItem(
                fee_name=item.fee_name,
                min_amount=item.min_amount,
                max_amount=item.max_amount,
                status=item.status.value,
                evidence_text=(
                    "公告未给出明确金额，必须在决策前核验。"
                    if item.status.value == "unknown"
                    else "依据 Phase 0 模拟公告或费用模板。"
                ),
                evidence_source="mock://phase-0/evidence",
                confidence=Decimal("0.00") if item.status.value == "unknown" else Decimal("0.80"),
                updated_at=SEED_NOW,
            )
            for item in item_specs
        ]

        resale_anchor = current_price * (Decimal("1.55") if index % 5 in {1, 2} else Decimal("1.28"))
        comparable_specs = (
            ComparableInput(_money(resale_anchor * Decimal("1.08")), "listing"),
            ComparableInput(_money(resale_anchor * Decimal("0.96")), "sold"),
            ComparableInput(_money(resale_anchor), "sold"),
        )
        asset.comparables = [
            Comparable(
                source_url=f"mock://phase-0/comparables/{index:03d}/{number}",
                price=item.price,
                region="湖北",
                brand="模拟品牌",
                model=f"SIM-{index:03d}",
                condition="正常二手可用",
                listing_or_sold=item.listing_or_sold,
                notes="人工录入的离线模拟参照，不是实时市场报价。",
            )
            for number, item in enumerate(comparable_specs, start=1)
        ]

        cost_summary = summarize_costs(current_price, item_specs)
        valuation = calculate_valuation(
            comparables=comparable_specs,
            all_in_cost_max=cost_summary.all_in_cost_max,
            non_bid_costs_max=cost_summary.all_in_cost_max - current_price,
            target_profit=max(Decimal("300"), resale_anchor * Decimal("0.20")),
        )
        assert valuation.safe_margin is not None
        assert valuation.conservative_resale_value is not None
        assert valuation.max_recommended_bid is not None
        capital_score = capital_fit_score(
            budget=profile.max_single_exposure,
            all_in_cost_max=cost_summary.all_in_cost_max,
            deposit=deposit,
        )
        skill_score = skill_match_score(asset.required_skills, profile.skills)
        certainty = cost_certainty_score(item.status.value for item in item_specs)
        distance_score = distance_convenience_score(distance, profile.search_radius)
        scores = score_opportunity(
            capital_fit=capital_score,
            safe_roi=valuation.safe_roi,
            liquidity=rule["liquidity"],
            skill_fit=skill_score,
            production=rule["production"],
            cost_certainty=certainty,
            distance=distance_score,
            unknown_cost_count=cost_summary.unknown_cost_count,
            valuation_available=valuation.is_available,
            preferred_strategy=profile.preferred_strategy,
        )
        monthly_income = decimal(asset.estimated_monthly_income or 0)
        payback = (
            (cost_summary.all_in_cost_max / monthly_income).quantize(Decimal("0.01"))
            if monthly_income > 0
            else None
        )
        reason_parts = [
            "本金范围内" if capital_score > 0 else "超过当前单笔本金上限",
            "存在正安全价差" if valuation.safe_margin > 0 else "安全价差不足",
            f"{cost_summary.unknown_cost_count} 项未知费用待核验",
        ]
        asset.opportunity = Opportunity(
            conservative_resale_value=valuation.conservative_resale_value,
            all_in_cost_min=cost_summary.all_in_cost_min,
            all_in_cost_max=cost_summary.all_in_cost_max,
            safe_margin=valuation.safe_margin,
            safe_roi=valuation.safe_roi,
            max_recommended_bid=valuation.max_recommended_bid,
            minimum_cash_required=minimum_cash_required(deposit, cost_summary.all_in_cost_max),
            capital_fit_score=scores.capital_fit_score,
            liquidity_score=scores.liquidity_score,
            skill_fit_score=scores.skill_fit_score,
            production_score=scores.production_score,
            cost_certainty_score=scores.cost_certainty_score,
            distance_score=scores.distance_score,
            overall_score=scores.overall_score,
            grade=scores.grade,
            valuation_basis=valuation.valuation_basis,
            decision_status=scores.decision_status,
            margin_is_provisional=scores.is_provisional,
            unknown_cost_count=cost_summary.unknown_cost_count,
            cost_estimate_complete=cost_summary.estimate_complete,
            recommendation_reason="；".join(reason_parts)
            + ("；安全价差与 ROI 为暂估值。" if scores.is_provisional else "。"),
            recommended_use="自用生产优先" if scores.production_score >= Decimal("75") else "转卖前先询价",
            payback_months=payback,
        )
        session.add(asset)
        created_assets.append(asset)

    session.flush()
    session.add(
        Subscription(
            profile_id=profile.id,
            name="湖北 5000 元生产型资产",
            platform="阿里捡漏（模拟）",
            province="湖北",
            city=None,
            max_all_in_cost=_money(5000),
            min_safe_margin=_money(800),
            min_safe_roi=Decimal("0.2000"),
            max_unknown_costs=2,
            categories=["机械设备", "工具", "商用设备"],
            auction_stages=["一拍", "二拍", "变卖"],
            preferred_use="production",
            alert_frequency="daily",
            enabled=True,
            created_at=SEED_NOW,
        )
    )
    session.add(Watchlist(profile_id=profile.id, asset=created_assets[0], note="核验电机状态与拆装条件"))
    session.commit()
