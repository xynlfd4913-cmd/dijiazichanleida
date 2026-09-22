# Source Adapter 开发规范

## 1. 目的

所有平台通过同一个 Adapter 边界进入系统。上层业务只依赖统一 Asset、CostItem、Snapshot 和 ChangeEvent，不关心记录来自正式 API、HTML、浏览器还是本地 fixture。

BaseAdapter 位于 `crawler/core/base_adapter.py`。

## 2. 生命周期

```text
DiscoveryQuery
  → discover
  → fetch_detail
  → fetch_attachments
  → parse
  → normalize
  → fingerprint
  → diff / snapshot
  → persistence and deterministic engines
```

职责分界：

- `discover(query)`：返回轻量候选记录；不得执行业务评分。
- `fetch_detail(record_or_id)`：取得一个标的的完整来源表示。
- `fetch_attachments(detail)`：返回附件描述或允许保存的本地内容。
- `parse(raw)`：把来源响应转换为来源字段映射，不推断未知事实。
- `normalize(parsed)`：别名、金额、时间、枚举和空值标准化。
- `fingerprint(normalized)`：生成稳定 SHA-256 内容指纹。
- `diff(before, after)`：返回 JSON Pointer 定位的 added / removed / changed 列表。

## 3. 同步与异步兼容

来源可以用普通函数或协程实现五个 I/O/转换方法。未知实现风格的调用方统一使用异步 facade：

```python
records = await adapter.adiscover(query)
detail = await adapter.afetch_detail(records[0])
attachments = await adapter.afetch_attachments(detail)
parsed = await adapter.aparse(detail)
asset = await adapter.anormalize(parsed)
```

纯计算的 `fingerprint()` 和 `diff()` 始终同步。不要在事件循环内用线程包装纯函数。

## 4. DiscoveryQuery

通用过滤字段：`province`、`city`、`category`、`min_price`、`max_price`、`limit`。来源特有参数暂放 `extras`，但业务层不得永久依赖私有字段。

过滤能力不足时，Adapter 可以返回较宽候选集，由统一层再次过滤；不得假称来源已执行其不支持的过滤。

## 5. Normalize 契约

`normalize_asset()` 的最低必填字段是：

- `source_platform`；
- `external_id`；
- `title`。

规范化约定：

- 金额输出为两位十进制字符串；
- 未知值为 `None` / JSON `null`；
- 时间输出为带时区 ISO-8601；
- 中文阶段和状态映射为稳定英文代码；
- 附件 URL 去重但保持首次出现顺序；
- 来源原文应另存快照或证据，不塞入伪造的标准字段。

标准化只清理表达形式，不计算总成本、ROI、评分和建议出价。

## 6. 指纹与差异

指纹对映射键排序，并支持 Decimal、日期、枚举与 bytes。默认忽略 `first_seen_at`、`last_seen_at`、`fetched_at`、`captured_at`，因此单纯重新抓取不会制造业务变化。

列表顺序默认有意义。若某来源附件顺序不稳定，Adapter 应在 normalize 阶段按稳定键排序，而不是全局忽略列表顺序。

差异路径使用 JSON Pointer 转义。例如 `/fees/transport` 和 `/attachment_urls/1`。业务事件转换器再把结构变化解释为“降价”“新增附件”等事件。

## 7. 错误处理

错误必须显式分类，禁止静默回退：

- 网络在当前阶段关闭：`NetworkAccessDisabledError`；
- 本地 fixture 不存在：来源自己的 `FixtureNotFoundError`；
- fixture 或解析格式不支持：`UnsupportedFixtureError`；
- 必填字段不足或值格式不合法：`NormalizationError`；
- 尚未进入开发阶段的来源：`SourceNotImplementedError`。

单个记录失败应被调度层隔离。只有来源级契约变化、授权失效或持续高错误率才把来源标为 degraded / paused。

## 8. 本地基础设施

- `api_client.ApiClient`：只响应已注册的 `fixture://`，HTTP/HTTPS 必然失败。
- `browser.OfflineBrowser`：只读取指定 fixture 根目录内的文件，阻止目录逃逸和网页导航。
- `session_manager.SessionManager`：只保存无秘密的会话元数据，不保存 cookie 或 token。
- `scheduler.LocalScheduler`：没有后台线程，只有显式调用 `run_due()` 才执行。
- `snapshot.SnapshotStore`：保存规范化 JSON 快照，目录名净化并使用原子替换。

这些是可替换边界，不代表 Phase 0 具有真实采集能力。

## 9. 新来源检查表

1. 分配稳定的 `source_platform` 代码和显示名；
2. 记录授权方式、条款、robots、限速与数据保留约束；
3. 默认关闭真实网络，准备脱敏 fixture；
4. 实现七个统一方法及错误分类；
5. 为金额、时区、空值、分页、重复记录和结构变化编写测试；
6. 保存解析证据和原始快照引用；
7. 验证 `(source_platform, external_id)` 的稳定性；
8. 验证未知费用不会变成 0；
9. 验证单来源失败不会停止其他来源；
10. 通过安全评审后才允许显式开启真实网络。

## 10. Phase 0 来源状态

| 来源 | 代码 | 状态 |
| --- | --- | --- |
| 阿里拍卖 / 阿里资产 / 捡漏 | `ali_jianlou` | fixture-only 骨架 |
| 武汉光谷联合产权交易所 | `ovupre` | 占位，未实现 |
| 公拍网 | `gpai` | 占位，未实现 |
| 全国企业破产重整案件信息网 | `pccz` | 占位，未实现 |
| 京东资产 | `jd_asset` | 占位，未实现 |
| 人民法院诉讼资产网 | `rmfysszc` | 占位，未实现 |
| 中拍平台 | `caa123` | 占位，未实现 |

