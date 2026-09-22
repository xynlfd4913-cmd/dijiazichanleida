# 负债人低价资产雷达

面向中重度负债人的本地单机 MVP：隔离生活保障金，用有限的资产本金筛选真正可承受、费用可核验、具备生产或保守转卖价值的低价资产。

当前版本是 **Phase 0 / 离线模拟版**。它不会访问真实拍卖网站，不会自动竞价、付款、购买、贷款或借款；全部 32 条资产均为确定性模拟数据。

## 已完成功能

- 三账户：生活保障、资产本金、化债账户；生活保障金永不进入购买预算。
- L0–L6 资本阶梯与单笔暴露上限。
- Asset、CostItem、Comparable、Opportunity、Subscription、Watchlist 数据模型。
- 全口径成本、现金门槛、保守变现价、安全价差、安全 ROI、最大建议出价和透明评分纯函数。
- 未知费用保持 `null`，不会被当作 0；存在未知费用时结果标记为暂估，机会最高只能为 B 级。
- 保证金单独作为现金门槛展示，不重复计入最终成本。
- 32 条离线种子资产，覆盖机器设备、工具、车辆、库存、房产、电脑和商用设备。
- 8 个中文页面：首页、资产雷达、资产详情、订阅、关注、资本阶梯、设置、后台。
- 统一来源 Adapter、快照、差异、会话、调度和阿里捡漏 fixture-only 骨架。
- FastAPI OpenAPI 文档、SQLite、本地 Windows 脚本、Docker Compose 和 GitHub Actions。

## Windows 快速启动

要求：Python 3.12、Node.js 22+、npm。Codex 桌面环境会自动使用随附的 Python 3.12 运行时。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

然后打开两个 PowerShell 终端：

```powershell
# 终端 1：FastAPI
powershell -ExecutionPolicy Bypass -File .\scripts\start-api.ps1

# 终端 2：Next.js
powershell -ExecutionPolicy Bypass -File .\scripts\start-web.ps1
```

访问：

- Web：<http://localhost:3000>
- API 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

`setup.ps1` 会从示例文件创建未纳入 Git 的 `.env` 与 `apps/web/.env.local`。可用配置见 [.env.example](./.env.example) 和 [apps/web/.env.example](./apps/web/.env.example)。

## Docker 启动

```powershell
docker compose up --build
```

Web 和 API 仍分别位于 3000、8000 端口；SQLite 数据保存在 `radar_data` volume。

## 验证

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

也可以分别执行：

```powershell
.\.venv\Scripts\python.exe -m pytest
cd apps\web
npm run typecheck
npm run build
```

本版本交付前验证结果：Python `73 passed`；TypeScript 类型检查通过；Next.js 生产构建通过。

## 核心安全口径

```text
all_in_cost_min = 当前价 + 已知费用低值 + 估算费用低值
all_in_cost_max = 当前价 + 已知费用高值 + 估算费用高值
safe_margin = 保守快速变现价 - all_in_cost_max
safe_roi = safe_margin / all_in_cost_max
```

- 未知费用不进入上述数值区间，但会令 `cost_estimate_complete=false`、`margin_is_provisional=true`，并阻止 S/A 评级。
- 没有有效成交参照时，变现价、价差、ROI 和建议出价均为 `null`，机会为 `Skip`。
- 成交参照优先；只有没有成交数据时才对挂牌价打折后使用。
- 金额按分计算，ROI 等比例保留至少四位精度后再展示。
- 最低现金门槛未知或超过 `min(available_capital, max_single_exposure)` 时，不进入默认预算结果。

详细定义见 [产品边界](./docs/PRODUCT.md)、[数据模型](./docs/DATA_MODEL.md) 和 [成本引擎](./docs/COST_ENGINE.md)。

## 主要 API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/health` | 离线模式与数据库健康 |
| GET | `/api/dashboard` | 三账户、资本阶梯与筛选漏斗 |
| GET | `/api/assets` | 资产筛选和分页 |
| GET | `/api/assets/{id}` | 费用、参照和机会详情 |
| GET/PUT | `/api/profile` | 用户画像 |
| GET/PUT | `/api/settings` | 设置别名 |
| GET/POST/PUT/DELETE | `/api/subscriptions` | 预算订阅 |
| GET/POST/DELETE | `/api/watchlist` | 关注列表 |
| GET | `/api/capital-ladder` | L0–L6 阶梯 |
| GET | `/api/admin/status` | 数据源与离线状态 |

## 目录

```text
apps/web/                  Next.js / TypeScript / Tailwind 前端
services/api/              FastAPI、SQLAlchemy、SQLite、路由与种子
engine/                    金额、成本、估值、评分、画像和订阅纯函数
crawler/core/              Adapter、快照、会话、调度等统一边界
crawler/adapters/          阿里 fixture 骨架与后续来源占位
config/                    来源、费用、关键词和调度配置
tests/                     API、引擎和抓取器离线测试
docs/                      产品、模型、成本和接入文档
scripts/                   Windows 安装、启动与验证脚本
data/                      本地数据库、快照和导出目录
```

## Phase 1：阿里捡漏 Adapter 清单

Phase 1 开始前先完成平台条款、robots、访问权限和数据用途评审。随后：

1. 确认正式授权 API；没有授权 API 时再评估公开结构化数据或页面解析。
2. 保存脱敏 fixture，为 discover/detail/attachment/parse/normalize/fingerprint/diff 建立测试。
3. 映射价格、保证金、拍卖阶段、时区、权属、占用、税费、欠费和附件证据。
4. 真实网络必须通过显式开关启用；验证码出现即暂停，不绕过。
5. 将标准化记录经 `services/api/services/asset_mapper.py` 写入统一模型。
6. 缺失费用与市场参照必须保持未知，不能让半解析资产获得可推荐等级。
7. 验证降价、二拍、流拍、变卖、再上拍、附件与公告变化。

完整约束见 [ALI_JIANLOU.md](./docs/ALI_JIANLOU.md) 和 [SOURCE_ADAPTER.md](./docs/SOURCE_ADAPTER.md)。

## 风险声明

本项目只帮助缩小人工核验范围，不构成投资、法律、债务或购买建议，也不承诺收益。任何真实资产都必须核验权属、交付、税费、欠费、占用、维修、运输及实际变现能力。
