# 低价资产雷达 Web

Phase 0 的 Next.js + TypeScript + Tailwind CSS 前端。默认使用本地模拟数据，禁止访问真实拍卖网站；启动 FastAPI 后可通过 `NEXT_PUBLIC_API_BASE_URL` 对接本地 API。

## Windows 本地启动

```powershell
cd apps\web
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`。

后端默认地址为 `http://localhost:8000/api`。需要覆盖时，可复制 `.env.example` 为 `.env.local` 并修改地址。

## 验证

```powershell
npm run typecheck
npm run build
```

## 页面

- `/` 我的重启进度
- `/radar` 低价资产雷达
- `/assets/[id]` 资产详情
- `/subscriptions` 我的订阅
- `/watchlist` 关注列表
- `/capital` 资本阶梯
- `/settings` 用户画像设置
- `/admin` 系统后台
