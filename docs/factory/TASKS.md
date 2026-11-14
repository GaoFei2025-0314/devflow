# devflow v2.3.0 修订任务表（SF-Architect，草稿）

> **主人已定（2026-11-14，经 SF-Chief of Staff 转达）**
> - `scripts/install-bundle.py` 不动（T1 不改 `install-bundle.py` 与 `tests/maintenance/test_install.py`，不要求安装产物自动带上 LICENSE/NOTICE/THIRD_PARTY_NOTICES.md）。
> - 不开 Dependabot（T2b 不提交 `.github/dependabot.yml`）。
> - SECURITY 漏洞上报走 GitHub Issue（T7 的 SECURITY.md 指向 Issue，不启用私密漏洞报告）。
> - 许可证 Apache-2.0；NOTICE/LICENSE 版权人 `Copyright 2026 Gao Fei`；第三方按「可能衍生」保守署名。

- 对应任务：SF-20261114-01；配套文档：`docs/factory/ADR-0001-devflow-v2.3.md`
- 基线：`GaoFei2025-0314/devflow` `main@63c5b70`
- 角色限定：SF-Builder、SF-QA Reviewer、SF-Release Manager、SF-Architect、SF-Chief of Staff
- 所有任务 ≤1 天、单一负责人。“需主人批准”＝执行前必须在聊天里拿到主人的明确批准。
- **本表不执行任何 tag / Release / 仓库改动。**

## 任务表

| ID | 目标 | 负责人 | 依赖 | Files（文件锁） | 估时 | 串行说明 | 验收 |
|---|---|---|---|---|---|---|---|
| **T8** | 在 `main@63c5b70` 补打附注 tag `v2.2.1` 并建 GitHub Release `v2.2.1`（正文取 `./CHANGELOG.md` 的 2.2.1 条目）。**不改任何代码和文件** | SF-Release Manager | 无（只需主人批准）；**必须先于 T5** | 无仓库文件。只产生 git tag 与 GitHub Release | 0.25d | 与其他任务无文件冲突，可随时执行；唯一硬约束是排在 T5 之前 | `git ls-remote --tags` 出现 `v2.2.1`，其 `^{}` 指向 `63c5b70`；Release 页有 v2.2.1；核对 `63c5b70` 上 plugin.json=2.2.1 且 CHANGELOG 顶部=2.2.1；`validate.yml` 在该提交的 push 运行为 success（已核）。**⚠ 需主人最终批准：建 tag 与建 Release 各一次，必须在聊天里逐项确认；未批准不得执行** |
| **T1** | 许可证与第三方署名：Apache-2.0 的 LICENSE、NOTICE、THIRD_PARTY_NOTICES.md；README 中英 License 小节；让暂存/安装产物带上这些文件 | SF-Builder | 许可证已定（Apache-2.0）。NOTICE 的**版权人姓名/年份需主人确认** | `LICENSE`、`NOTICE`、`./THIRD_PARTY_NOTICES.md`、`./README.md`、`./README.zh-CN.md`、`scripts/install-bundle.py`（仅 `DISTRIBUTION_ROOT_FILES`）、`tests/maintenance/test_install.py`。**不改** `skills/**`（含 frontend-design/LICENSE.txt，避免触发版本检查） | 0.5d | **README 链第 1 位**：T1 → T4 → T3。与 T2a/T2b 无文件重叠，可并行 | `LICENSE` 与 Apache 官方全文 `diff` 一致；THIRD_PARTY_NOTICES.md 列出 superpowers、agent-skills、OpenSpec（MIT，含各自版权行）和 anthropics/skills frontend-design（Apache-2.0）；`claude plugin validate .` 不再报 `LICENSE_MISSING`；全量维护测试 OK；`install-bundle.py stage --layout full` 产物含三个新文件且 `verify` 通过；README 中英同步。**⚠ 需主人批准：NOTICE 版权人姓名与年份；是否采纳“第三方按可能衍生署名”** |
| **T2a** | 新增 `scripts/check-version.py`（`consistency` 与 `bump` 两个子命令）+ fixture 测试；CI 新增 `version-consistency` job，`version-bump` job 改为调用脚本；release-checklist 补“tag 前核对”步骤 | SF-Builder | 无 | `scripts/check-version.py`（新）、`tests/maintenance/test_version.py`（新）、`.github/workflows/validate.yml`（仅新增 job 与改写 version-bump 的 run）、`docs/devflow/release-checklist.md` | 1d | **validate.yml 链第 1 位**：T2a → T2b。与 T1 无重叠，可并行 | `python -m unittest discover -s tests/maintenance -p 'test_version.py'` 全过（含正反例和“真实仓库自检”）；`python scripts/check-version.py consistency` 对 `main` 退出 0；全量测试 OK；PR 上 `version-consistency`、`version-bump` 均为 success；人为构造“改了 skills/ 没改 CHANGELOG”的 PR 能被拦（用临时分支验证，不合并） |
| **T2b** | CI 可复现：setup-python 3.10（维护测试 3.10+3.13 × Ubuntu/Windows）；所有 `uses:` 钉 SHA；`scripts/check-refs.sh` 下限 3.8→3.10；`check-bundle.py` 增加 29000 字节软警告；（可选）Dependabot | SF-Builder | T2a | `.github/workflows/validate.yml`、`scripts/check-refs.sh`、`scripts/check-bundle.py`、`tests/maintenance/test_bundle.py`、`.github/dependabot.yml`（新，**可选**） | 0.5d | **validate.yml 链第 2 位**。检查脚本相关文件只有 T2b 动 | 全部 `uses:` 为 40 位 SHA + 行尾版本注释（`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`、`actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0`；SHA 已用 `git ls-remote` 实查）；CI 全绿（含新增 Windows×3.10 组合）；`permissions: contents: read` 不变；`scripts/check-refs.sh` 报错信息写 3.10；测试覆盖软警告（>29000 打印 WARNING 且不失败，>30000 失败）；当前 `MANDATORY LOAD` 仍 28696 且无警告。**⚠ 需主人批准：是否启用 Dependabot（github-actions，monthly）；不批准则不提交该文件** |
| **T6a** | 宿主验收记录（能做的部分）：Claude 插件 `validate`、CLI 本地源与 GitHub 源安装、`plugin details`、`install-bundle.py stage/verify`；明确列出未执行项与原因 | SF-QA Reviewer | T1（让 `validate` 里 LICENSE 项已消除，记录的是合入后的状态） | docs/devflow/host-verification-v2.3.md（新） | 0.5d | **host-verification 文件链第 1 位**：T6a → T6b。与其他任务无文件冲突 | 文件含每条命令、宿主版本（Claude Code 2.1.325）、日期（Asia/Shanghai）、输出摘要；不使用任何账号/API key（`claude -p` 的 `Not logged in` 如实记录）；明确写“技能调用未验证、`/plugin` 面板未验证、Cursor 未验证”；QA 独立复跑一遍命令结果一致 |
| **T6b** | 原生宿主验收（调用 `devflow:devflow`、Cursor 原生读技能） | SF-QA Reviewer | T6a；**以及主人批准凭据/费用** | 追加到 docs/devflow/host-verification-v2.3.md | 1–2d（获批后） | host-verification 链第 2 位。**不在 v2.3.0 关键路径上** | **当前状态：未执行（BLOCKED，等批准）**。需要 Claude 账号或 `ANTHROPIC_API_KEY`、Cursor 账号与用量，盒子里都没有。v2.3.0 的文档按“未验证”写（见 T4），不等 T6b。**⚠ 需主人批准：新凭据与费用** |
| **T4** | 宿主支持说明按证据改写（三档：已验证 / 结构校验通过 / 未验证）+ Cursor 手动安装路径（明确标“未做原生验证”，不支持 GitHub 一键导入）+ README Layout 补 `check-version.py` | SF-Builder | T1、T2a、T6a（**不依赖 T6b**） | `docs/devflow/host-support.md`、`docs/devflow/installation.md`、`./README.md`、`./README.zh-CN.md` | 0.5d | **README 链第 2 位**：T1 → T4 → T3 | 每个宿主有档位标签，且“已验证”档每行带证据链接；Claude 插件安装行为“结构校验通过”并链接 T6a 记录；Cursor 小节与 Cursor 官方文档一致且标注“未原生验证”；`docs/devflow/host-support.md` 状态日期已更新；中英 README 同步；`bash scripts/check-refs.sh` 与全量维护测试通过（链接解析） |
| **T7** | CONTRIBUTING.md、SECURITY.md、Issue 模板（Could） | SF-Builder | T2a（CONTRIBUTING 要引用 `check-version.py` 的真实命令） | CONTRIBUTING.md、SECURITY.md、`.github/ISSUE_TEMPLATE/**` | 0.5d | 与别的任务无文件重叠；不改 `skills/` 所以不触发版本检查。**优先级最低：来不及就顺延到 v2.3.1，不阻塞 T3** | 三类文件存在；CONTRIBUTING 里的命令都来自仓库现有写法（`./README.md` Maintenance）；SECURITY.md 的联系方式由主人提供。**⚠ 需主人提供：漏洞上报渠道（邮箱或是否启用 GitHub 私密漏洞报告——启用是仓库设置，需另行批准）** |
| **T3** | 消融结论落地 + **承载 v2.3.0 版本号与 CHANGELOG**：微调 `action-rules.md:63` 措辞（字节净增 ≤0）；README 补“何时可不加载完整包”；`plugin.json` 升 2.3.0；CHANGELOG 加 `## 2.3.0 (YYYY-MM-DD)` | SF-Builder | T1、T2b、T4（T7 为软依赖：已合入则写进 CHANGELOG，否则不写） | `skills/using-devflow/references/action-rules.md`（仅第 63 行）、`./README.md`、`./README.zh-CN.md`、`.claude-plugin/plugin.json`、`./CHANGELOG.md`；**条件性**：`AGENTS.md`、`skills/devflow/SKILL.md`、`tests/maintenance/*.py`（仅当入口一致性检查要求镜像时） | 1d | **README 链第 3 位（最后）**；它改 `skills/`，会触发版本检查，所以必须是**最后一个内容 PR**（同一发布周期第二个触发 PR 会因基线已升版而失败）。plugin.json 与 CHANGELOG 只有它改 | `python scripts/check-bundle.py --root .` 的 `MANDATORY LOAD` ≤ 28696（净不增，PR 里贴前后输出）；`check-version.py consistency` 与 `bump` 通过；CHANGELOG 2.3.0 条目含 T1、T2、T4（及已合入的 T7）并注明“措辞微调，未重跑消融”；README 与 `AGENTS.md`/路由摘要一致；全量测试 + check-refs + check-behavior validate 全绿；`action-rules.md:47-56` 授权表与其他行逐字未动（`git diff` 证明）。**如要验证行为效果须重跑消融（模型费用，需主人批准），默认不跑** |
| **T5** | 发布 v2.3.0：在 T3 合并后的 `main` 上建附注 tag `v2.3.0` + GitHub Release（正文取 CHANGELOG 2.3.0 条目）。**不改文件**（版本号、CHANGELOG、release-checklist 的改动已分别在 T3、T2a 完成） | SF-Release Manager | T3（已合并、main CI 全绿）、**T8（v2.2.1 已完成）**、SF-QA Reviewer 对 T3 PR 的独立审查通过 | 无仓库文件。只产生 git tag 与 GitHub Release | 0.25d | 最后一步；不与任何任务争文件 | `python scripts/check-version.py consistency --tag v2.3.0` 退出 0；main 最新提交的 `Validate skill bundle` push 运行 success；tag 附注且指向该提交；Release 页存在 v2.3.0；GitHub 仓库页 license 显示 Apache-2.0。**⚠ 需主人最终批准：建 tag 与建 Release，必须在聊天里明确确认，未批准不得执行** |

## 依赖图（无环）

```text
T8 ─────────────────────────────────────────────┐
T1 ──┬──► T6a ──┐                               │
     │          ├──► T4 ──┐                     │
     └──────────┘         │                     ▼
T2a ──┬──► T2b ───────────┼──► T3 ──► (QA 审查) ──► T5
      ├──► T4 (见上)      │
      └──► T7 ····(软依赖)┘
T6a ──► T6b（等主人批准，不在关键路径）
```

拓扑顺序之一：T8、T1、T2a 可并行起步 → T2b、T6a → T4（、T7）→ T3 → T5。没有任务依赖自己的后继，无环。

## 文件重叠检查与串行链

| 文件 | 涉及任务 | 处理 |
|---|---|---|
| `./README.md`、`./README.zh-CN.md` | T1、T4、T3 | **串行：T1 → T4 → T3**（T2a 不改 README，Layout 里的新脚本行放到 T4；原 PRD 里 T2 的 `tests/behavior/README.md` 无需改动，已核对它本来就写 3.10） |
| `.github/workflows/validate.yml` | T2a、T2b | **串行：T2a → T2b** |
| docs/devflow/host-verification-v2.3.md | T6a、T6b | **串行：T6a → T6b** |
| `.claude-plugin/plugin.json`、`./CHANGELOG.md` | 只有 T3 | 无冲突（原 PRD 把它们放在 T5，现收口到 T3，见下） |
| `docs/devflow/release-checklist.md` | 只有 T2a | 无冲突 |
| `docs/devflow/host-support.md`、`docs/devflow/installation.md` | 只有 T4 | 无冲突 |
| `scripts/check-bundle.py`、`scripts/check-refs.sh`、`tests/maintenance/test_bundle.py` | 只有 T2b | 无冲突 |
| `scripts/install-bundle.py`、`tests/maintenance/test_install.py` | 只有 T1 | 无冲突 |
| `tests/maintenance/*.py`（条件性） | T3 | 仅在 T3 需要时动，T3 排在最后，不与 T1/T2a/T2b 并行 |

## 相对 PRD 初稿的主要修订（给 Chief）
1. **T2 拆成 T2a/T2b**：原 T2 含脚本+测试+setup-python+钉 SHA+检查脚本改动，超过 1 天；两者都改 `validate.yml`，所以串行。
2. **T5 由“改版本号/CHANGELOG/清单 + 发布”改为“只打 tag + Release”**：原因是 CI 的 `version-bump` 规则让任何改了 `skills/`、`AGENTS.md` 的 PR 都必须升版本；T3 会改 `skills/using-devflow/references/action-rules.md`，所以 T3 必须自带 2.3.0 版本号和 CHANGELOG，并且必须是最后一个内容 PR。release-checklist 的 tag 步骤挪到 T2a。
3. **T6 拆成 T6a（能做、无费用）与 T6b（未执行，等主人批准）**；T4 只依赖 T6a。
4. **新增 T8（v2.2.1 补打 tag + Release）**，先于 T5，无代码改动，执行需主人最终批准。
5. T1 的 Files 去掉了 `skills/frontend-design/LICENSE.txt`（不改它，避免触发版本检查），增加了 `./THIRD_PARTY_NOTICES.md` 和 `install-bundle.py` 的分发清单（原因见 ADR 决策 E）。
6. T3 的 Files 比 PRD 多了 README 中英（“何时可不加载完整包”要写在 README，PRD 的 US7 要求）、plugin.json、CHANGELOG。

## 需要主人批准的事项汇总
1. **T8**：建 `v2.2.1` tag 与 Release（执行前逐项确认）。
2. **T5**：建 `v2.3.0` tag 与 Release（执行前逐项确认）。
3. **T1**：NOTICE 的版权人姓名/年份；第三方署名处理方式。
4. **T2b**：是否启用 Dependabot。
5. **T6b**：Claude 账号或 API key、Cursor 账号（新凭据 + 新费用）。
6. **T3 可选**：重跑消融实验验证（模型费用）。
7. **T7**：SECURITY.md 的上报渠道；若要启用 GitHub 私密漏洞报告属仓库设置，需另行批准。
8. （需 Chief 同意）T1 中改 `install-bundle.py` 分发清单。

## 关键路径与估时
T1(0.5) → T6a(0.5) → T4(0.5) → T3(1) → 独立审查 → T5(0.25)，约 2.75 个工作日；T2a(1) → T2b(0.5) 与之并行，不拖慢关键路径；T8、T7、T6b 不在关键路径。
