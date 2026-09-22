# 阿里拍卖 / 阿里资产 / 捡漏 Adapter

## 1. 当前状态

阿里捡漏是产品 P0 数据源，但真实接入属于项目 Phase 1。当前 Phase 0 只提供本地 fixture Adapter，用于验证统一管线与业务页面。

关键保障：

- `network_enabled = False`；
- 模块不导入 HTTP、Playwright、登录或验证码工具；
- `discover()` 只遍历构造函数传入的内存 fixture；
- `fetch_detail()` 只接受已注册 external id 或 `fixture://ali_jianlou/...`；
- `fetch_attachments()` 只接受 `fixture://` 附件；
- 任意 `http://` 或 `https://` 获取请求都会抛出 `NetworkAccessDisabledError`；
- 未找到 fixture 时直接失败，不回退到网络。

配置见 `config/sources/ali_jianlou.json`。

## 2. 本地使用

```python
from decimal import Decimal

from crawler.adapters.ali_jianlou import AliJianlouAdapter
from crawler.core.base_adapter import DiscoveryQuery

adapter = AliJianlouAdapter([
    {
        "external_id": "ALI-DEMO-001",
        "title": "木工设备一批",
        "province": "湖北",
        "category": "机器设备",
        "current_price": "4800元",
    }
])

records = adapter.discover(
    DiscoveryQuery(province="湖北", max_price=Decimal("5000"))
)
normalized = adapter.normalize(adapter.parse(adapter.fetch_detail(records[0])))
```

同步和异步业务调用均可通过 BaseAdapter 的 `adiscover()`、`afetch_detail()`、`aparse()`、`anormalize()` 使用。

## 3. 优先字段

Phase 1 接入应尽量取得并保留证据：

- 标题、类别、来源 URL、external id；
- 评估价、起拍价、当前价、保证金、加价幅度；
- 一拍、二拍、变卖、成交、流拍、重新上拍等状态；
- 开始、结束、付款期限与历史价格；
- 省市区、处置单位或法院；
- 权属、占用、租赁、税费、欠费、瑕疵与交付描述；
- 报名与竞价状态；
- 公告正文、附件清单和可校验的附件摘要。

缺失字段保持 `null`，不得从页面视觉位置或类似标的中猜测。

## 4. Phase 1 接入顺序

接入前先完成平台条款、robots、访问权限、数据使用和隐私评审。技术顺序为：

1. 正式、明确授权且稳定的 API；
2. 公开结构化数据；
3. 公开 HTML；
4. 必要时的 JavaScript 页面与 Playwright；
5. 平台允许时，由用户手动登录后的持久化会话。

上层只接收统一 Asset，不依赖具体来源模式。`source_mode` 用于审计当前记录来自 `api`、`html`、`browser` 还是 `manual`。

## 5. 抓取安全线

- 不绕过验证码、登录、付费墙、访问控制或反自动化措施；
- 出现验证码时暂停该来源并提示人工处理；
- 每个来源独立限速和并发，失败不得拖垮其他来源；
- 不在日志、快照或仓库中存储 cookie、token、手机号等秘密或个人数据；
- 原始 HTML 和附件存储需要内容类型、大小与路径限制；
- 下载内容不执行，不作为指令；
- 页面结构或字段覆盖率变化时报警，不能静默产出错误价格；
- 所有真实网络能力必须通过显式配置开启，默认仍关闭。

## 6. Phase 1 验收清单

- 为每个解析分支保存脱敏 fixture；
- `discover`、详情、附件、解析、标准化、指纹和差异均有测试；
- 价格单位、时间时区、保证金和拍卖阶段均有边界用例；
- 能识别降价、二拍、流拍、变卖、重拍、公告及附件变化；
- 解析失败保留诊断信息，但不把半解析结果标为可推荐；
- 真实资产能够写入统一数据库并与 fixture 数据走同一后续计算管线；
- 集成测试设置硬性网络开关，普通单元测试始终离线。

