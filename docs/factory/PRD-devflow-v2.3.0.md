# PRD：devflow v2.3.0（可安装、许可清晰、宿主证据对齐）
仓库：GaoFei2025-0314/devflow（默认分支 main，HEAD 63c5b70）
任务编号（建 Issue 前）：SF-20261114-01 起
来源：2026-11-14 只读审查（本地 254 维护测试通过、check-refs 通过、CI 历史 39/39 success）

## 目标
把 devflow 从"代码扎实但发布与宣称不严谨"推进到：许可证清楚、版本/标签/Release 一致、CI 可复现且守住发布约定、跨宿主支持说明有证据、按消融结论减掉残留仪式。

## Non-goals
- 不补完历史全量 V2 行为资格（114×2）。
- 不新增技能、不重写路由架构。
- 不引入第三方 Python 依赖（脚本保持只用标准库）。
- 不改仓库保护/安全设置（如需，单独请主人批准）。

## 用户角色
- 维护者（飞）：发版、维护规则。
- 使用者：在 Claude Code / Cursor / Codex 等宿主安装 devflow 的开发者。

## 用户故事与验收标准
| ID | 故事 | 优先级 | 验收 Given/When/Then |
|---|---|---|---|
| US1 | 作为使用者，我想知道能否合法使用/修改/再分发 devflow | Must | Given 打开仓库，When 看 GitHub 仓库信息，Then `license` 不为 null；根目录有 LICENSE（需要时有 NOTICE）；中英 README 有许可证说明；frontend-design 的 Apache-2.0 署名完整 |
| US2 | 作为使用者，我想按 tag 安装拿到与 main 一致的版本 | Must | Given v2.3.0 发布，When 查看 tags/Releases，Then 存在 v2.3.0 tag 与 Release，且与 plugin.json、CHANGELOG 最新标题一致（v2.2.1 是否补打由主人定） |
| US3 | 作为维护者，我想 CI 自动拦住"改技能却漏改版本或 CHANGELOG" | Must | Given PR 改了 skills/**，When plugin.json version 与 CHANGELOG 最新标题不一致或任一未更新，Then CI 失败；一致时通过（有正反用例测试） |
| US4 | 作为维护者，我想 CI 在固定的 Python 3.10+ 上可复现运行 | Must | Given CI 运行，Then Ubuntu/Windows 用 setup-python 指定 3.10+；actions 钉到 commit SHA；check-refs.sh 最低版本与 check-behavior 一致（3.10）；254 维护测试、check-refs、check-behavior validate 全部通过 |
| US5 | 作为使用者，我想 README 只宣称已验证的宿主 | Must | Given 读 README 安装节，Then 已验证/未验证宿主分开标明；host-support.md 更新日期与证据链接；有 Cursor 安装路径（或明确写未支持） |
| US6 | 作为使用者，我想在 Claude 插件和 Cursor 上看到真实原生验收记录 | Should | Given 原生环境，When 安装并调用 devflow:devflow，Then 记录步骤、版本、结果；做不到的明确标"未执行"及原因 |
| US7 | 作为使用者，我想小任务不被多余流程打扰 | Must | Given 路由器与 action-rules，Then 不再要求未决的通用"发布需另行授权"提醒；README 写明何时可不加载完整包；mandatory load 仍 ≤30000 字节 |
| US8 | 作为维护者，我想有基本协作文档 | Could | CONTRIBUTING.md、SECURITY.md、Issue 模板存在 |

## 非功能需求
- 安全：不引入密钥；CI 权限 `contents: read`；actions 钉 SHA。
- 兼容：Ubuntu + Windows CI 矩阵保留。
- 预算：mandatory load ≤ 30000 字节（当前 28696）。
- 成本：不新增付费服务。

## 待确认问题（问主人）
1. 仓库许可证选哪个？（建议 Apache-2.0，与 frontend-design 一致；或 MIT）
2. 是否补打 v2.2.1 标签/Release，还是直接发 v2.3.0？（打 tag/发 Release 需主人批准）

## 任务拆解（初稿，待 Architect 确认）
| ID | 标题 | 负责人 | 依赖 | 文件范围 | 估时 |
|---|---|---|---|---|---|
| T1 | 仓库级许可证与第三方署名 | SF-Builder | 许可证待主人定 | LICENSE, NOTICE, README.md, README.zh-CN.md, skills/frontend-design/LICENSE.txt | 0.5d |
| T2 | CI：版本/CHANGELOG 一致性检查 + setup-python 3.10 + 钉 SHA | SF-Builder | — | .github/workflows/validate.yml, scripts/check-refs.sh, scripts/(新增检查脚本), tests/maintenance/**, tests/behavior/README.md | 1d |
| T3 | 消融结论落地：去残留授权提醒、写清何时不加载 | SF-Builder | — | skills/devflow/SKILL.md, skills/using-devflow/references/action-rules.md, AGENTS.md | 1d |
| T4 | 宿主支持说明按证据改写 + Cursor 安装路径 | SF-Builder | T6（或先按现有证据） | docs/devflow/host-support.md, docs/devflow/installation.md, README.md, README.zh-CN.md | 0.5d |
| T5 | 发布 v2.3.0：版本号、CHANGELOG、release-checklist 补打 tag 步骤 | SF-Builder → Release Manager | T1–T4 | .claude-plugin/plugin.json, .claude-plugin/marketplace.json, CHANGELOG.md, docs/devflow/release-checklist.md | 0.5d |
| T6 | 原生宿主验收（Claude 插件 + Cursor），可行性待 Architect 评估 | SF-QA Reviewer | — | docs/devflow/(验收记录) | 1–2d |
| T7 | CONTRIBUTING / SECURITY / Issue 模板（Could） | SF-Builder | — | CONTRIBUTING.md, SECURITY.md, .github/ISSUE_TEMPLATE/** | 0.5d |

注意文件重叠：T1 与 T4 都改 README（需串行）；T3 改 SKILL.md 后 T5 需更新版本；T2 与 T5 都可能涉及发布约定。
