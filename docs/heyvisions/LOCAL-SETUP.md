# 本地启动

本 fork 的本地环境。三个服务：API、Web、单元 Markdown 静态服务。

## 前置

- Docker（Postgres 16 + pgvector、Redis 7）
- `bun`
- Python 3.14.6（API 锁定了 `>=3.14.6,<3.14.7`）
- node（读取 website 仓库的课程合同用）

## 1. 数据库与 Redis

```bash
docker compose -f scripts/heyvisions/docker-compose.yml up -d
# 首次需要（课程 embedding 依赖 pgvector）：
docker exec hv-lms-postgres psql -U learnhouse -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

端口用 `15432`（Postgres）与 `16379`（Redis），避开本机已占用的 5432/6379。

> 上游官方自托管走 `npx learnhouse setup`，会自己生成 compose。
> 这份 compose 是本地跑 API + Web 时用的等价物。

## 2. API 依赖

API 锁定 Python 3.14.6，uv 需 ≥ 0.11.31 才认识该版本；本机网络下 uv 下载 wheel 容易超时，
用清华镜像 + `--no-deps` 更稳：

```bash
cd apps/api
UV_PYTHON=3.14.6 UV_PYTHON_DOWNLOADS=auto ~/.local/bin/uv venv --seed --python 3.14.6
~/.local/bin/uv export --format requirements-txt --no-hashes --no-dev -o /tmp/lh-req.txt
.venv/bin/pip install --no-deps -r /tmp/lh-req.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 3. 凭据

```bash
cp <某处的 .demo-secrets> apps/api/.demo-secrets && chmod 600 apps/api/.demo-secrets
```

需要含 `LEARNHOUSE_INITIAL_ADMIN_PASSWORD`。**不要提交这个文件。**

## 4. 启动

```bash
# 单元 Markdown 静态服务（指向 website 仓库，不在本仓库留正文副本）
python3 scripts/heyvisions/serve-units.py --root ~/projects/website/example/src/course-content/units

# API（单租户 + localhost）
cd apps/api && .venv/bin/uvicorn app:app --host 0.0.0.0 --port 1349

# Web
cd apps/web && bun install
bun run next start -p 3011
```

Web 的运行时配置来自 `apps/web/public/runtime-config.js`，生产构建下这是客户端配置的**唯一**来源：

```js
window.__RUNTIME_CONFIG__ = {
  "NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL": "http://localhost:1349",
  "NEXT_PUBLIC_LEARNHOUSE_API_URL": "http://localhost:1349/api/v1/",
  "NEXT_PUBLIC_LEARNHOUSE_DOMAIN": "localhost:3011",
  "NEXT_PUBLIC_LEARNHOUSE_HTTPS": "false"
};
```

## 5. 导入课程

```bash
python3 scripts/heyvisions/import-course.py \
  --website ~/projects/website \
  --api http://localhost:1349/api/v1 \
  --units-base http://127.0.0.1:8022/units
```

脚本幂等，可重复执行；只导入 `publication=published` 的单元。

## 已知坑

1. `NEXT_PUBLIC_LEARNHOUSE_API_URL` **必须带尾斜杠**，否则 URL 拼成 `/api/v1orgs/…`，全站 OrgNotFound。
2. 本机 Clash fake-ip 会劫持 `lvh.me` 子域，一律用 `localhost`；API 需单租户模式（多租户拒绝 localhost）。
3. Web 路由用**去掉 `course_` 前缀**的 uuid：`/course/<uuid>`，前端会自动补前缀。
4. Markdown 活动的 URL 由浏览器直接拉取，内容源必须带 CORS 头（`serve-units.py` 已带）。
5. 课程正文的事实源是 website 仓库，**不要**把 `.md` 复制进本仓库。

## 品牌配置

平台品牌走运行时配置，默认值即 HeyVisions（见 `apps/web/services/config/brand.ts`）：

| 键 | 默认值 | 用途 |
| --- | --- | --- |
| `NEXT_PUBLIC_BRAND_NAME` | `HeyVisions` | 页脚版权、登录页条款措辞 |
| `NEXT_PUBLIC_BRAND_SITE_URL` | `https://heyvisions.com` | 首页 "Powered by" 的指向 |
| `NEXT_PUBLIC_BRAND_TERMS_URL` | 空 | 留空则不渲染服务条款链接 |
| `NEXT_PUBLIC_BRAND_PRIVACY_URL` | 空 | 留空则不渲染隐私政策链接 |
| `NEXT_PUBLIC_BRAND_WATERMARK` | `false` | 是否展示上游推广水印 |
