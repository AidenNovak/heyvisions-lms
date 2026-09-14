# 生产部署

[文档导航](../INDEX.md) · [开发环境](LOCAL-SETUP.md) · [改动记录](CHANGELOG.md)

本文是学习平台**对外服务形态**的事实源：跑在哪个主机名、由哪些进程承担、配置在哪、
怎么更新、怎么验证，以及当前明确没做的事。开发栈（SSH 隧道 + `server-up.sh`）见
[开发环境](LOCAL-SETUP.md)，两者端口相同，**不能同时跑**。

## 形态

```
浏览器
  │  https://learn.yettodawn.com/            → 127.0.0.1:3011  Next.js Web
  │  https://learn.yettodawn.com/api/v1/…    → 127.0.0.1:1349  FastAPI
  │  https://learn.yettodawn.com/units/…     → 127.0.0.1:8022  单元 Markdown
  ▼
Cloudflare DNS（A 记录，DNS-only 不走橙云）
  ▼
vultr-sg 45.76.152.44
  ├─ ufw：放行 22 / 80 / 443
  ├─ nginx stream ：443 → SNI 分流（www.samsung.com → Xray REALITY，其余 → 127.0.0.1:9443）
  ├─ nginx http   ：9443 → 按路径分发到上面三个进程（单主机名，同源）
  └─ Docker       ：hv-lms-postgres 127.0.0.1:15432 · hv-lms-redis 127.0.0.1:16379
```

**单主机名按路径分流**是刻意的：登录 cookie 是 host-only + `SameSite=Lax`，
把 Web 与 API 拆到两个主机名（或只是两个端口）都会让会话 cookie 在跨源请求里
不再发送，表现为登录后一刷新就掉线、进度保存静默失败。同源就没有这类问题。

## 进程与配置

| 单元 | 作用 | 监听 |
| --- | --- | --- |
| `hv-lms-web.service` | Next.js standalone | `0.0.0.0:3011` |
| `hv-lms-api.service` | FastAPI / uvicorn | `127.0.0.1:1349` |
| `hv-lms-units.service` | 单元 Markdown 静态服务 | `127.0.0.1:8022` |

```bash
systemctl status hv-lms-web hv-lms-api hv-lms-units
systemctl restart hv-lms-api          # 改密钥后
journalctl -u hv-lms-web -n 50        # 追错误
tail -f /srv/heyvisions-run/logs/web.log
```

- 单元文件源：`scripts/heyvisions/systemd/`，改完 `server-install-prod.sh` 会重装。
- nginx vhost 源：`scripts/heyvisions/nginx/yettodawn-lms.conf.template`，
  安装到 `/etc/nginx/sites-available/learn.yettodawn.com`。
- 运行时配置：`/srv/heyvisions-secrets/lms-prod.env`（600，不入 Git）。
  键名见 `scripts/heyvisions/server-install-prod.sh` 的注释；改完 `systemctl restart hv-lms-api`。
- Web 侧的密钥：`/srv/heyvisions-secrets/lms-web.env`（600，不入 Git）。
  由 `hv-lms-web.service` 以 `EnvironmentFile=-` 引入（缺文件不报错），装安装脚本时
  若不存在会自动建一个空骨架。放的是 Web 服务端才需要的凭据：
  `LEARNHOUSE_GOOGLE_CLIENT_ID`、`LEARNHOUSE_GOOGLE_CLIENT_SECRET`、`RESEND_API_KEY` 等。
  与 `lms-prod.env` 分开是为了不给 Web 进程塞数据库连接串与 JWT 密钥。改完
  `systemctl restart hv-lms-web`。

  Google 登录需要**两处**同一个 client id：Web（授权与换 token）与 API
  （校验 token 的 `aud`，见 `apps/api/src/services/auth/utils.py`），所以
  `LEARNHOUSE_GOOGLE_CLIENT_ID` 在 `lms-web.env` 与 `lms-prod.env` 里各写一份，
  client secret 只给 Web。授权重定向 URI 由运行时域名决定，即
  `https://learn.yettodawn.com/auth/callback/google`。
  未配置时登录页不渲染这些入口（`services/auth/authCapabilities.ts`），无需手动关。
- Web 的客户端配置**不在构建里**，而是安装时写进
  `apps/web/.next/standalone/{runtime-config.json,public/runtime-config.js}`。
  因此换域名不需要重新构建，重跑安装脚本即可。

### 部署端源码与仓库的一致性

`server-rebuild-web.sh` 只重建 Web；**API 的 Python 源码是安装时拷一份**，
之后没有人保证它跟仓库一致。曾经因此出过一次线上故障：

- 现象：Google 登录后界面显示 “Authentication Failed”，只给一个「重试」按钮。
- 实际：用户**已经写入数据库**（`signup_method=google`），失败发生在之后发欢迎邮件那一步 ——
  `services/email/branding.py` 比同目录的 `emails.py` 旧一天，
  `from ... import powered_by_url` 抛 `ImportError`。
- 为什么难自查：错误只在服务端日志（`/srv/heyvisions-run/logs/api.log`）；
  且只在 **OAuth 建号**分支触发（密码注册不走这段），常用自测路径发现不了。

所以改动 API 源码后要同步，并跑一次一致性检查：

```bash
# 只读：列出与仓库不一致的已部署文件，不修改任何东西
ssh vultr-sg '/srv/heyvisions-lms/scripts/heyvisions/check-deploy-drift.sh'

# 同步（先确认部署端没有手工热修）
rsync -c -r --exclude='__pycache__' apps/api/src/ vultr-sg:/srv/heyvisions-lms/apps/api/src/
ssh vultr-sg 'find /srv/heyvisions-lms/apps/api/src -name __pycache__ -type d -exec rm -rf {} + ; systemctl restart hv-lms-api'
```

改动 API 源码时**必须清 `__pycache__`**：Python 只按源文件 mtime 判断是否重编，
而 rsync/install 可能保留旧 mtime，导致字节码不刷新、改了像没改。

### 两个容易踩的坑（都在单元文件里写明了原因）

1. **Web 必须绑 `0.0.0.0`，不能绑回环。** Next 处理绝对 URL 的 rewrite 时会把请求当
   真实 HTTP 请求转发给自己，目标主机取自 `HOSTNAME`；绑回环时这台机器的 localhost
   先解析到 `::1`，进程只监听 IPv4，于是每个组织页 500，且路径会被反复叠加
   （`/orgs/default/orgs/default/…`）。端口不对公网开放由 ufw 的 deny 规则兜底。
2. **API 单元不能设 `ProtectHome=true`。** venv 里的解释器是 uv 装在
   `/root/.local/share/uv/` 下的，隐藏 `/root` 会让 ExecStart 直接 `203/EXEC`。
   用 `ProtectHome=read-only`。

## 首次部署 / 重新部署

```bash
# 0. 依赖与构建（幂等）——在这台机器上跑，不在本机
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-setup.sh'

# 1. 安装（生成运行时配置 → 装 systemd 单元 → 装 nginx vhost → 自检）
ssh vultr-sg 'cd /srv/heyvisions-lms && sudo ./scripts/heyvisions/server-install-prod.sh'

# 2. 只改了 Web 代码时：重建产物后再跑一次安装脚本
ssh vultr-sg 'cd /srv/heyvisions-lms && ./scripts/heyvisions/server-rebuild-web.sh'
```

### 证书

`learn.yettodawn.com` 用 Let's Encrypt DNS-01（本机已有
`/root/.secrets/certbot/cloudflare.ini`），到期自动续期：

```bash
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/certbot/cloudflare.ini \
  -d learn.yettodawn.com --non-interactive --agree-tos -m <邮箱>
certbot certificates | grep -A2 learn.yettodawn
```

DNS 由 `cloudflare.ini` 里的 token 管理。**该 token 有全账号的 DNS 写权限**，
只能放在 600 的 root 文件里；若怀疑泄露，在 Cloudflare 重新签发并替换该文件。

## 内容

课程正文的事实源是 website 仓库（`example/src/course-content/units/*.md` 与
`example/src/course/curriculum.js`），服务器上只有一份拷贝 `/srv/heyvisions-content`。

```bash
# 在本机（有 website 仓库那台）执行：同步文件 + 校正平台侧活动 URL
scripts/heyvisions/sync-content.sh
```

活动的 `markdown_url` 必须是**对外可达**的绝对地址
（`https://learn.yettodawn.com/units/<unitKey>.md`）：正文由浏览器直接 fetch
（`components/Objects/Activities/Markdown/MarkdownActivity.tsx`），写成回环地址时
每个课时页都会显示 `Failed to fetch markdown`。导入脚本会在 URL 与当前基址不一致时
就地校正，所以重跑是安全的。

### 单元正文为什么要先「生成」再上传

单元正文的「模板或反例」一节写着“使用本页下方的模板”，但模板文字**不在 `.md` 里**：
它存于 `example/src/course/templates.js`，由站点页面在渲染到该节时注入
（`example/src/course-page.jsx`）。学习平台只渲染裸 Markdown，没有这层注入，
所以直接同步原始 `.md` 会让每个单元都指向一个不存在的模板（6/6 个公开单元）。

`sync-content.sh` 因此先调用 `build-lms-units.py`，把 `templates.js` 里的模板作为围栏
代码块追加到该节末尾，生成平台专用的自包含副本，再上传。两边同源（都来自
`templates.js`），不存在两处维护的模板文字；站点读的是原始 `.md`，不受影响。

```bash
# 生成结果可以先本地看一眼（只写 --out 目录，不动源仓库）
python3 scripts/heyvisions/build-lms-units.py --website ~/projects/website --out /tmp/lms-units
```

## 验证

```bash
# 三个进程 + 四个对外路径
ssh vultr-sg 'for u in https://learn.yettodawn.com/ \
  https://learn.yettodawn.com/login \
  https://learn.yettodawn.com/api/v1/health \
  https://learn.yettodawn.com/units/judge-task-01.md; do
  printf "%-52s " "$u"; curl -s -o /dev/null -w "%{http_code}\n" --max-time 25 "$u"; done'

# 品牌残留（页面 / 产物 / 接口三层，只读）
ssh vultr-sg 'cd /srv/heyvisions-lms && bash scripts/heyvisions/verify-brand-clean.sh'
```

登录与课程链路的验证需要一个真实账号：打开 `https://learn.yettodawn.com/signup`
注册，或使用管理员账号（口令在 `/srv/heyvisions-secrets/lms-prod.env`）。
管理员后台在 `/admin`。

## 当前明确没做的事

| 项 | 状态与影响 |
| --- | --- |
| 站点侧登录 | 静态站的 `/login` 与其 `apps/heyvisions-api` 是**另一套帐号**（不同后端、不同 cookie），与平台不互通。站点现在把学习者入口指向平台（页脚「学习平台」、`/login`、课时页的进度区），但它自己那套登录仍可访问 |
| 发信 | 未配置邮件服务（`config.yaml` 的 `system_email_address` / `resend_api_key` 为空）。**魔法链接登录、邮箱验证、找回密码都发不出信**；密码登录正常。要开需要 Resend（或 SMTP）凭据，并同时设 `LEARNHOUSE_SITE_NAME` 之外的发件人地址 |
| Google 登录 | 未注册 OAuth 应用，登录页不会显示该入口 |
| 注册策略 | 维持平台默认 `open`：任何人可注册。要改成仅邀请，在组织设置的成员策略里切 `inviteOnly`；`/signup` 页会相应变成邀请码表单 |
| 隐私政策 / 服务条款 | 未配置（`NEXT_PUBLIC_BRAND_TERMS_URL` / `_PRIVACY_URL` 为空），页脚不渲染这两条链接 —— 有链接但指向别家条款比没有更糟 |
| 自定义域名保留表 | `apps/api/src/services/orgs/custom_domains.py` 的保留表只挡 `*.learnhouse.io`，未含本站域名；单租户部署下管理员没有该入口，暂不影响 |
| 管理员后台 i18n | 仍有一批 zh 未翻译键（学习者路径已覆盖） |

## 与开发栈的关系

| | 开发栈 | 生产 |
| --- | --- | --- |
| 启动 | `server-up.sh`（pid 文件，前台进程） | systemd（开机自启、崩溃重启） |
| 绑定 | units/api 回环，web `0.0.0.0` | 同左（见上文坑 1） |
| 配置 | 脚本里写死 `127.0.0.1` | `lms-prod.env` |
| 模式 | `LEARNHOUSE_DEVELOPMENT_MODE=true` | `false` |
| 访问 | SSH 隧道 `-L 3011 -L 1349` | nginx + TLS |

两套用同样的端口与同一个数据库，切换前先 `server-up.sh stop`。
