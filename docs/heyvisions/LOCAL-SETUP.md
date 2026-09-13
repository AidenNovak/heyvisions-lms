# 开发环境

本 fork 的开发栈跑在构建机上（`vultr-sg`），不在本地 Mac 上：本地机器资源紧张，
编译与长驻进程放服务器，本机只留编辑与轻量检查。

## 拓扑

```
本机 Mac                          vultr-sg
  │                                  │
  ├─ 编辑器改代码 ──rsync──────────▶ /srv/heyvisions-lms
  │                                  │
  ├─ SSH 隧道 -L 3011 -L 1349 ──────▶  Web :3011   API :1349   units :8022
  │                                     └ Docker: Postgres+pgvector :15432, Redis :16379
  └─ 浏览器 http://127.0.0.1:3011
```

隧道映射**同样的端口号**（3011/1349/8022）：Web 的运行时配置里写死了 API 地址，
换成别的本地端口浏览器就取不到 API。

## 目录

| 路径 | 内容 |
| --- | --- |
| `/srv/heyvisions-lms` | 仓库工作副本（rsync 同步，不含 `.git`/`node_modules`/`.next`） |
| `/srv/heyvisions-content` | 课程合同与单元 Markdown（来自 website 仓库） |
| `/srv/heyvisions-website` | 软链到上面那份内容，用来喂 `import-course.py --website` |
| `/srv/heyvisions-secrets/lms.env` | JWT 密钥、管理员密码（600，不入 Git） |
| `/srv/heyvisions-run/` | 进程 pid 与日志 |
| `/opt/hv-node` | Node 22（Next.js 要求 ≥20，系统包是 18，不动系统包） |
| `/root/.bun` | bun 1.4.2 |

## 启动

```bash
# 一次性准备（幂等）：数据服务、API venv、Web 依赖、Web 构建
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-setup.sh'

# 启动全部；也可以 units|api|web 单独起
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-up.sh all'
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-up.sh status'
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-up.sh stop'
```

单改 Web 代码后的最小循环：

```bash
rsync -az --exclude node_modules --exclude .next \
  apps/web/components apps/web/app apps/web/locales vultr-sg:/srv/heyvisions-lms/apps/web/
ssh vultr-sg 'cd /srv/heyvisions-lms/apps/web && PATH=/opt/hv-node/bin:$PATH bun run next build'
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-setup.sh'   # 补 standalone 产物
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-up.sh stop && ./scripts/heyvisions/server-up.sh all'
```

## 访问

```bash
# 隧道（端口号与服务器一致，浏览器直接用 127.0.0.1:3011）
ssh -f -N -o ExitOnForwardFailure=yes \
  -L 3011:127.0.0.1:3011 -L 1349:127.0.0.1:1349 -L 8022:127.0.0.1:8022 vultr-sg
```

## 课程导入

```bash
ssh vultr-sg 'cd /srv/heyvisions-lms && \
  LEARNHOUSE_INITIAL_ADMIN_EMAIL=admin@heyvisions.com \
  python3 scripts/heyvisions/import-course.py \
    --website /srv/heyvisions-website \
    --units-base http://127.0.0.1:8022/units \
    --secrets /srv/heyvisions-secrets/lms.env'
```

脚本幂等，可重复执行。它还会**校正**已存在活动的 `markdown_url` —— 换了部署形态
（主机、端口、路径前缀）后重跑一次即可修好 404 的单元正文。

`--website` 指向一个只含 `example/src/course/curriculum.js` 与
`example/src/course-content/units/` 的目录，脚本用 node 读课程合同。

## 已知坑

1. **`localhost` 在这台机器上先解析到 `::1`**（`/etc/hosts` 同时给了 `127.0.0.1` 与
   `::1 localhost`）。Next.js standalone 的 middleware 对绝对 URL 的 rewrite 会走一次
   真实 HTTP 请求，主机名是 `localhost`；Web 只绑 `127.0.0.1` 时那一跳连不上，
   页面 500、日志刷 `Failed to proxy`。所以 Web 绑 `0.0.0.0`（`HV_WEB_BIND` 可改）。
   端口不对公网开放由 ufw 默认拒绝兜底，已实测公网不可达。

2. **不用 `next start`**：`output: standalone` 下它额外套一层到 `localhost` 的代理，
   徒增一个失败点。直接跑 `.next/standalone/server-wrapper.js`，与生产镜像同构。

3. **standalone 产物不自带 `public/` 与 `.next/static/`**：生产镜像是靠 Dockerfile 里
   两步 COPY 补上的。`server-setup.sh` 等价补一遍 —— 少了会得到没有任何样式的页面。

4. **`LEARNHOUSE_INITIAL_ADMIN_EMAIL` 不能用 `.local`**：`.local` 是保留域，
   email-validator 会拒，自动安装直接失败并留下半截数据。用真实域名即可。

5. **自动安装只在数据库为空时跑**。中途失败重来要重置库：
   ```bash
   ssh vultr-sg "docker exec hv-lms-postgres psql -U learnhouse -d postgres \
     -c 'DROP DATABASE learnhouse WITH (FORCE);' -c 'CREATE DATABASE learnhouse;'"
   ssh vultr-sg "docker exec hv-lms-postgres psql -U learnhouse -d learnhouse \
     -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
   ```

6. **单元静态服务的 `--root` 要指向 `course-content`**（其下是 `units/`），
   不是 `units/` 本身：活动的 `markdown_url` 形如 `<base>/units/<unitKey>.md`。
   传错会让所有单元 404，页面显示 `Failed to fetch markdown (404)`。

7. **API 与 units 服务只绑回环**，经 SSH 隧道访问。

## 与 PROD 的隔离

这台机器同时是没猫饼的 PROD，所以：

- 开发栈用独立目录、独立容器名（`hv-lms-*`）、独立端口段
  （15432/16379 与 PROD 的 5432/6379 不冲突）
- 构建一次只跑一个，起停后确认 PROD 容器正常：
  `ssh vultr-sg "docker ps | grep meimaobing-alpha"`

## 品牌配置

平台品牌走运行时配置，默认值即 HeyVisions（见 `apps/web/services/config/brand.ts`）：

| 键 | 默认值 | 用途 |
| --- | --- | --- |
| `NEXT_PUBLIC_BRAND_NAME` | `HeyVisions` | 页脚版权、登录页措辞 |
| `NEXT_PUBLIC_BRAND_SITE_URL` | `https://heyvisions.com` | 首页 "Powered by" 的指向 |
| `NEXT_PUBLIC_BRAND_TERMS_URL` | 空 | 留空则不渲染条款链接与整句措辞 |
| `NEXT_PUBLIC_BRAND_PRIVACY_URL` | 空 | 留空则不渲染隐私链接 |
| `NEXT_PUBLIC_BRAND_WATERMARK` | `false` | 是否展示上游推广水印 |

locale 里出现的 `{{brand}}` 是占位符，由组件传入 `getBrandName()` 的结果。
**不要**在 locale 里写死品牌名 —— 22 个语言文件各写一份无法维护，换品牌名必漏改。

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `server-setup.sh` | 幂等准备：数据服务、venv、依赖、构建、standalone 产物 |
| `server-up.sh` | 起停与状态（`all` / `units` / `api` / `web` / `status` / `stop`） |
| `import-course.py` | 幂等导入课程，并校正单元 URL |
| `serve-units.py` | 带 CORS 的单元 Markdown 静态服务 |
| `merge-locale-keys.py` | 往 locale 补键，不重排既有格式 |
| `localize-brand-strings.py` | 把 locale 里平台自指的品牌名变量化为 `{{brand}}` |
| `docker-compose.yml` | 本地数据服务（pgvector + Redis） |
