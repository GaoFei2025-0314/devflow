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

路由器（`skills/devflow/SKILL.md`）按任务选择最小可用的技能子集：

- 需求梳理与想法成形 → brainstorming
- 规格与任务计划 → spec-workspace / spec-driven-development / planning-and-task-breakdown
- 测试先行的实现 → test-driven-development、incremental-implementation
- 调试与根因分析 → systematic-debugging
- 代码评审与重构 → code-review-and-quality、code-simplification
- 前端、API、安全、性能、可观测性 → 对应领域技能
- CI、发布与上线 → git-workflow-and-versioning、ci-cd-and-automation、shipping-and-launch

依赖宿主能力的技能（子代理派发、浏览器 MCP）统一引用 `skills/using-devflow/SKILL.md` 中的共享降级契约，因此在不具备这些能力的宿主上也能平稳降级。

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

## 使用

在开发任务开始前，让助手使用 Devflow：

```text
使用 devflow 来规划并实现这个功能。
```

路由器会自动挑选相关技能。例如：

- 新功能：brainstorming、规格、计划、TDD、增量实现、评审
- 修 Bug：系统化调试、回归测试、最小修复、验证
- UI 工作：前端设计与 UI 工程，必要时加浏览器测试
- 发布：git 工作流、CI/CD、上线清单、验证

## 维护

- 提交技能改动前运行 `scripts/check-refs.sh`——它校验 frontmatter、交叉引用和文件体积。CI 会在每次 push 时运行它。
- **任何改动技能内容的 PR 都要升级 `.claude-plugin/plugin.json` 里的 `version`。** 已安装的插件只在版本号变化时才会收到更新——内容改了而版本号不动，`/plugin update` 的用户永远拿不到新内容。
