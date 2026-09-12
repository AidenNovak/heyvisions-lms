# 改动记录

本仓库相对上游 [`learnhouse/learnhouse`](https://github.com/learnhouse/learnhouse) 的所有改动。
每条对应一个 issue 和一个 PR，用来快速回答「我们和上游差在哪」。

基线：fork 于 `upstream/dev` @ `2841620b`。

## 汇总

| # | 改动 | Issue | PR | 触及上游文件 |
| --- | --- | --- | --- | --- |
| 1 | fork 维护流程与改动记录 | [#1](https://github.com/AidenNovak/heyvisions-lms/issues/1) | [#2](https://github.com/AidenNovak/heyvisions-lms/pull/2) | `README.md`（仅顶部加 fork 声明） |

## 1. fork 维护流程与改动记录

- **改什么**：建立本 fork 的改动留痕机制——issue 模板、维护流程文档、本改动记录。
- **为什么**：fork 会持续偏离上游，需要能逐条追溯每处改动的原因与范围，
  也便于日后 `git merge upstream/dev` 时判断冲突该保留哪一边。
- **影响范围**：新增 `.github/ISSUE_TEMPLATE/upstream-change.yml`、
  `docs/heyvisions/CONTRIBUTING-FORK.md`、`docs/heyvisions/CHANGELOG.md`；
  `README.md` 顶部加 fork 声明。
- **与上游的关系**：纯本地维护文档，不回馈上游。`README.md` 顶部声明会在同步时产生小冲突，
  固定保留本仓库版本即可。

## 上游同步

| 日期 | 上游 commit | 结果 |
| --- | --- | --- |
| — | （尚未同步） | 基线 `2841620b` |
