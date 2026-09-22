# 数据模型与不变量

本文描述领域语义和跨模块契约。数据库字段类型可以按 ORM 实现调整，但不得改变以下不变量。

## 1. 金额与时间约定

- 货币默认为 CNY，计算使用 `Decimal`，数据库使用定点数；禁止使用二进制浮点参与金额公式。
- API 层金额可序列化为十进制字符串，例如 `"5000.00"`。
- 未知金额使用 `null` 和状态 `unknown`，不得使用 `0` 代替。
- 时间保存为带时区的 ISO-8601；来源未给时区时，境内拍卖数据按 `Asia/Shanghai` 解释。
- 所有枚举保存稳定代码，中文展示名由前端或字典映射。

## 2. UserProfile

| 字段 | 语义 |
| --- | --- |
| `available_capital` | 当前可用于资产循环的本金，不含生活保障金 |
| `monthly_new_capital` | 每月预计可新增资产本金 |
| `living_reserve` | 不得用于资产购买的生活保障资金 |
| `city` / `search_radius` | 地理筛选基准 |
| `skills` | 用户可真实执行的技能标签集合 |
| `storage_available` | 是否具备仓储条件 |
| `vehicle_available` | 是否具备运输车辆 |
| `preferred_asset_types` | 偏好资产类型集合 |
| `preferred_strategy` | `production` / `resale` / `hybrid` |
| `max_single_exposure` | 单个机会可占用的最大本金 |

不变量：`available_capital` 和 `max_single_exposure` 均不得包含 `living_reserve`。

## 3. Account / CapitalLevel

三个逻辑账户：

- `living_reserve`：生活保障；
- `asset_capital`：资产发现与执行预算；
- `debt_repayment_fund`：化债资金。

CapitalLevel 使用稳定代码 `L0` 至 `L6`。等级由本金纯函数计算，不由用户手填。边界规则详见 [PRODUCT.md](./PRODUCT.md)。

## 4. Asset

### 来源与身份

| 字段 | 类型建议 | 说明 |
| --- | --- | --- |
| `source_platform` | string | 稳定来源代码，如 `ali_jianlou` |
| `source_mode` | enum | `fixture` / `api` / `html` / `browser` / `manual` |
| `source_url` | nullable string | 原始详情页或 API 资源定位符 |
| `external_id` | string | 来源内稳定标识 |
| `title` | string | 标的标题 |

`(source_platform, external_id)` 必须唯一。`source_url` 不是身份键，页面改版不应生成重复资产。

### 分类与地点

`category`、`subcategory`、`province`、`city`、`district`、`seller_or_court`。

### 拍卖状态

`auction_stage`、`status`、`start_time`、`end_time`、`payment_deadline`、`previous_round_price`、`previous_round_result`。

建议的 `auction_stage` 稳定值：`first`、`second`、`liquidation`、`other`。来源文本保存在证据或快照中。

### 价格

`appraisal_price`、`start_price`、`current_price`、`deposit`、`bid_increment`。

保证金是现金门槛，不默认作为额外最终成本相加。若平台明确说明保证金不抵成交款，才通过费用证据另行处理。

### 资产属性

`brand`、`model`、`year`、`quantity`、`condition`、`ownership_status`、`occupancy_status`、`inspection_available`、`attachment_urls`。

### 观测字段

`first_seen_at`、`last_seen_at`。它们用于数据新鲜度，不参与内容指纹。

## 5. CostItem

| 字段 | 说明 |
| --- | --- |
| `fee_name` | 稳定费用名称，如 `transport` 或展示名“运输” |
| `min_amount` / `max_amount` | 已知或估计区间；未知时均为 `null` |
| `status` | `known` / `estimated` / `unknown` |
| `evidence_text` | 支持该费用判断的最小必要原文 |
| `evidence_source` | 公告、附件、人工询价或规则的定位信息 |
| `confidence` | 0–1 的证据置信度，不改变金额计算本身 |
| `updated_at` | 最近核验时间 |

不变量：

- `min_amount <= max_amount`；
- `unknown` 不得同时携带伪造的 0–0 区间；
- `estimated` 必须说明估计来源；
- 同一费用可以有多条证据，但计算时必须避免重复计费。

## 6. Comparable

字段包括：`source_url`、`price`、`region`、`brand`、`model`、`condition`、`listing_or_sold`、`notes`，并建议补充 `observed_at` 与证据可信度。

挂牌价和成交价不能混用。保守快速变现价优先使用近期低位成交、本地回收价或人工真实询价；仅在没有成交证据时，才使用经过保守折扣的挂牌价。缺少有效参照时应保持未知。

## 7. Opportunity

| 字段 | 说明 |
| --- | --- |
| `conservative_resale_value` | 保守快速变现价；没有证据时为 `null` |
| `all_in_cost_min` / `all_in_cost_max` | 已确认及可估算费用形成的成本区间 |
| `safe_margin` | 保守变现价减全口径最大成本 |
| `safe_roi` | `safe_margin / all_in_cost_max` |
| `max_recommended_bid` | 在目标利润和风险准备金约束下的出价上限 |
| `minimum_cash_required` | 执行交易时最低现金门槛 |
| 六项子评分 | 本金、流动性、技能、生产、费用确定性、距离等维度 |
| `overall_score` / `grade` | 排序分和 S/A/B/C/Skip 等级 |

若关键输入未知，则依赖该输入的结果也应为未知或不可推荐，不得用 0 补齐后继续生成高分。当前安全门规则：存在未知费用时金额结果标记为暂估且评级最高为 B；未知项超过允许阈值或缺少市场参照时为 `Skip`。

## 8. Subscription / Watch

预算订阅建议包含：用户、来源、资产类别、地区、搜索半径、价格上下限、安全价差、安全 ROI、最大未知费用数、拍卖阶段、提醒频率与策略偏好。

关注记录保存资产关联、关注时间与最后通知状态。变化事件由快照差异生成，不直接覆盖历史。

## 9. Snapshot / ChangeEvent

Snapshot 保存：`source_platform`、`external_id`、`captured_at`、`fingerprint` 和规范化 payload。原始 HTML 或附件应存于独立受控存储，只在元数据中引用。

ChangeEvent 至少包含：变化路径、变化类型、前值、后值、前后指纹与检测时间。常见业务事件包括降价、阶段变化、重新挂牌、附件变化、保证金变化、公告变化、截止临近和费用状态变化。

## 10. 来源标准化边界

`crawler/core/normalize.py` 输出 JSON 兼容映射：金额为两位十进制字符串，时间为带时区 ISO 字符串，未知为 `null`，附件 URL 去重。它只做语法和别名标准化，不推断市场价、不计算机会分，也不把来源缺失字段“补全”为事实。
