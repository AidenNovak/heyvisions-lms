# HeyVisions fork 维护流程

上游：[`learnhouse/learnhouse`](https://github.com/learnhouse/learnhouse)（AGPL-3.0）。
本仓库是它的 fork，在上面做 HeyVisions 的深度改造。

## 铁律：先 issue，再 PR

任何一处改动都必须能回答「为什么改了它」。流程固定为五步：

1. **开 issue** — 用 [上游改动](../.github/ISSUE_TEMPLATE/upstream-change.yml) 模板，写清：
   改什么 / 为什么改 / 影响范围 / 与上游的关系 / 怎么验收。
2. **切分支** — 从最新 `dev` 切出，命名 `类型/简短描述`：
   `feat/` `fix/` `chore/` `brand/` `i18n/` `content/`。
3. **提交** — 提交正文写 `Refs #<issue编号>`，让 commit 和 issue 双向可查。
4. **开 PR** — PR 标题带 issue 编号，描述里引用 issue 并写清验收结果。
5. **收尾** — 合并后在 issue 里补一句验收结论，并把该条记入 [CHANGELOG](CHANGELOG.md)。

不允许出现「改了但没 issue」的提交。若改动确实微小（错别字、格式），
仍需在 CHANGELOG 里留一行，并注明无 issue 的原因。

## 控制与上游的冲突面

上游在活跃开发，冲突面越窄越好。约定：

- **优先改**：`apps/web/public/`（品牌资源）、`apps/web/components/`（界面文案）、
  `apps/web/locales/`（语言）、`apps/api/src/db/organization_config.py`（组织配置）。
- **尽量不改**：上游的核心业务逻辑、数据模型、迁移脚本。
  确需改动时，在 issue 里写清楚理由与冲突风险。
- **新增而非改写**：能加新文件、新组件解决的就不要就地改上游文件。
- 每次改了上游文件，记入 CHANGELOG 的「触及上游文件」一栏，便于同步时重点检查。

## 与上游同步

```bash
git fetch upstream
git checkout dev
git merge upstream/dev
```

同步后：

1. 跑构建与既有测试，确认品牌改造没被上游覆盖。
2. 若上游改了本仓库也动过的文件，逐条核对 CHANGELOG 里的相关条目。
3. 同步结果记入 CHANGELOG 的「上游同步」小节（日期 + 上游 commit）。

## 验收要求

每个 PR 至少给出一种可复现的验收方式，优先级从高到低：

1. 一条可执行的命令（构建、测试、脚本）。
2. 本地启动后可直接访问的页面路径 + 预期可见结果。
3. 截图或 DOM 断言。

只写「已测试通过」不算验收。

## 许可

AGPL-3.0。深度改造后对外提供服务时，本仓库即公开源码位置。
不要在仓库中提交密钥、令牌、真实用户数据或未授权素材。
