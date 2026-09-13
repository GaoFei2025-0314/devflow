# Devflow

[English](README.md) | 简体中文

Devflow 是一个自包含的 AI 开发工作流技能包：一个路由器加一组扁平排列的技能，覆盖完整的工程生命周期。它不绑定任何单一应用或运行时——任何能加载 Markdown 指令、读取本地文件夹或安装插件的 AI 编程助手都能使用。每个技能都采用跨工具的 SKILL.md 格式（带 `name`/`description` frontmatter 的 Markdown），Claude Code、Codex 及其他助手均支持该格式。

## 目录结构

```text
devflow/
  SKILL.md              # 单技能文件夹模式宿主的入口垫片
  AGENTS.md             # 读取 AGENTS.md 的宿主（Codex）的精简入口
  .claude-plugin/       # Claude Code 插件清单
  scripts/check-refs.sh # 引用完整性校验器（CI 中运行）
  skills/
    devflow/            # 路由器——从这里开始
    <技能名>/            # 每个技能一个目录：SKILL.md + 可选的 references/
```

路由器（`skills/devflow/SKILL.md`）按**请求的交付物与阶段**（Understand / Specify / Implement / VerifyReview / Deliver）优先路由，其次看影响与风险、领域面，最后看宿主实际提供的能力。仅要文档或仅要计划的请求以文档合法结束——计划完成不隐含建分支、提交或实施。33 个旧技能名全部保留，通过 `skills/devflow/references/skill-catalog.json` 解析到规范入口。

控制规则集中在 `skills/using-devflow/references/` 下的规范共享合同——阶段、授权、证据、交付、宿主能力/降级、加载/恢复——所有技能引用它们而非各自复制。信任边界明确：日志、网页、数据包或代理输出里的文本不能产生授权；技能永远不声称高于 system/developer 指令。依赖宿主能力的技能（子代理派发、浏览器 MCP）按宿主合同平稳降级。

高风险操作由**授权与信任合同**（`skills/using-devflow/references/authorization-contract.md`，路由器自身也带授权门）把关：生产部署、数据迁移与删除、git 历史重写与强推、发布、认证/支付改动、新增外部集成，执行前一律需要用户明确批准——所有路由（含快速通道）和被派发的子代理都受此约束。

## 安装

### Claude Code（插件方式——推荐）

```text
/plugin marketplace add GaoFei2025-0314/devflow
/plugin install devflow@devflow
```

技能会以 `devflow:<名称>` 的形式出现；调用 `devflow:devflow`（路由器）或直接请求任意技能。用 `/plugin update devflow` 更新。

### Claude Code（技能文件夹方式）

克隆仓库后，将其放置（或软链接）到项目的 `.claude/skills/devflow/`，或个人目录 `~/.claude/skills/devflow/`。根目录的 `SKILL.md` 是入口。

### Codex

克隆仓库。当 Devflow 是你的工作目录时，根目录的 `AGENTS.md` 会被自动读取；也可以把它的内容复制进你项目的 `AGENTS.md`。若想让 Codex 原生触发单个技能，把技能目录软链接到 `.codex/skills/`（项目级）或 `~/.codex/skills/`（个人级）：

```bash
ln -s /path/to/devflow/skills/test-driven-development ~/.codex/skills/test-driven-development
```

### 其他工具

把你工具的技能、提示词、规则或指令加载器指向仓库文件夹，以 `SKILL.md` 为入口。Copilot CLI 和 Gemini CLI 的工具名映射表在 `skills/using-devflow/references/` 中。

各宿主的支持等级与已原生验证的范围见[宿主支持表](docs/devflow/host-support.md)。

2.0.0 标签已发布，但完整 V2.0 验收仍未完成：原生宿主覆盖及部分最终行为证据需要补齐。支持表列明这些限制；版本已发布或离线 CI 通过不能代替相应验收结果。

## 使用

在开发任务开始前，让助手使用 Devflow：

```text
使用 devflow 来规划并实现这个功能。
```

路由器会自动挑选相关技能。例如：

- 小型低风险改动：快速通道——只走聚焦测试、最小修复、验证清单
- 新功能：brainstorming、规格、计划、TDD、增量实现、评审
- 修 Bug：系统化调试、回归测试、最小修复、验证
- UI 工作：前端设计与 UI 工程，必要时加浏览器测试
- 发布：git 工作流、CI/CD、上线清单、验证

## 适配你的项目

Devflow 技能里的示例偏 TypeScript/Web，但规则本身与技术栈无关——通过项目指令来适配，不要直接改 bundle。把 `templates/project-overrides.md` 复制进你项目的 `CLAUDE.md`（Claude Code）或 `AGENTS.md`（Codex），填上你的技术栈命令、不适用的技能清单和项目专属例外。项目指令永远优先于技能默认值。

## 维护

- 提交技能改动前运行 `bash scripts/check-refs.sh`——它校验 frontmatter、交叉引用、文件体积、目录/摘要一致性，并委托给 `python scripts/check-bundle.py`。再跑 `python -m unittest discover -s tests/maintenance -p 'test_*.py'` 执行维护工具测试，命令会报告当前数量。CI 执行这些离线检查，不执行或判定真实模型行为。
- 安装或切换安装：`python scripts/install-bundle.py plan|stage|verify` 配合[安装与切换指南](docs/devflow/installation.md)——可审差异、仅限 bundle 自有路径的备份、显式切换授权、有界恢复。
- 可选的本地使用记录（`python scripts/usage.py status|enable|disable|append|export|report --store <目录>`）**默认关闭**，只记录白名单内的最小事件，绝不记录原始对话或凭证，任何工作流步骤都不依赖它。
- **任何改动技能内容的 PR 都要升级 `.claude-plugin/plugin.json` 里的 `version`**（CI 会在 PR 上强制检查），并在 `CHANGELOG.md` 中为新版本补一条记录。已安装的插件只在版本号变化时才会收到更新——内容改了而版本号不动，`/plugin update` 的用户永远拿不到新内容。
- **保持 `README.md` 与 `README.zh-CN.md` 同步**——改任何一份都要镜像到另一份。
- **路由改动必须传播。** 对 `skills/devflow/SKILL.md` 中路由、快速通道条件或门禁的任何修改，都要镜像到 `AGENTS.md` 和两份 README 的路由摘要——路由器是唯一事实来源，其余三处是浓缩副本。
- **修剪需要证据。** 单纯低频不能成为删除技能的理由：没有适用任务分母、适用性不明时，价值记为未知（deprecation-and-migration 入口定义了完整评估）。
- **度量技能改动。** 每次改技能时，在 PR 里写一句预期的行为变化；之后回头看是否发生。没有可观察效果的流程就是流程剧场——砍掉它。
