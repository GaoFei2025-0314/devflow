# 宿主验收记录 v2.3.0（T6a）

记录 Issue #25 里能在无账号、无新增费用的条件下实际执行的宿主检查。基线是 T1（PR #32）合入后的 `main`。本文只记录当次命令的退出码和输出。

档位只用这两个词：

- **结构校验通过**：`claude plugin validate` 退出 0。它不表示技能已经被宿主调用。
- **CLI安装命令成功**：`claude plugin marketplace add` 与 `claude plugin install` 退出 0。它不表示交互式 `/plugin` 面板或 Cursor 已经跑过。

以下三项**未验证**：技能调用、`/plugin` 交互面板、Cursor 原生调用。T6b 和消融实验本次未执行。

## 基线

| 项 | 值 |
| --- | --- |
| 仓库 | `GaoFei2025-0314/devflow` |
| 基线完整 SHA | `fe9f1540c222f52ae8965f7a0a3e7f14060a3f74` |
| 该提交 | Merge pull request #32 from GaoFei2025-0314/sf/22-license |
| 执行前远程 `main` | 同一 SHA |
| 执行前 Issue #25 | open；`status:todo`；`owner:SF-QA-Reviewer`；评论 0 |
| 执行前分支 `sf/25-host-verification` | 不存在 |
| 执行前该分支的 PR | 无 |
| 执行前 open PR | 只有 #33 |
| 插件版本 | `.claude-plugin/plugin.json` 仍是 2.2.1。v2.3.0 版本号尚未在这个基线上改动 |

日期与时钟用 Asia/Shanghai。第 1 轮 2026-11-14 13:10:31–13:11:26 CST。第 2 轮 2026-11-14 13:11:27–13:12:33 CST。

## 环境

两轮都使用同一份已安装的 Claude Code 二进制，插件 HOME、XDG 目录、stage 目录和 GitHub 克隆互不共用。第 2 轮的 GitHub 安装日志再次出现 `Cloning repository`，不是用第 1 轮的克隆目录推断成功。

公开 CLI 安装（未改仓库依赖，未钉版本号）：

```text
npm install --prefix /tmp/t6a-cli --cache /tmp/t6a-npm-cache \
  --userconfig /tmp/t6a-empty-npmrc-user \
  --globalconfig /tmp/t6a-empty-npmrc-global \
  @anthropic-ai/claude-code
```

退出码 0，输出 `added 2 packages in 4s`。安装后的包版本是 2.1.325。同一时刻 `npm view @anthropic-ai/claude-code version dist-tags --json` 给出 `latest` = `2.1.325`（`stable` = `2.1.311`）。二进制为 `/tmp/t6a-cli/node_modules/.bin/claude`。

每条宿主命令都放在 `env -i` 里，只保留这些变量：`PATH`（Node 22.23.4 与 `/usr/bin:/bin`）、`HOME`、`XDG_CONFIG_HOME`、`XDG_DATA_HOME`、`XDG_CACHE_HOME`、`XDG_STATE_HOME`、`TMPDIR`、`LANG=C.UTF-8`、`LC_ALL=C.UTF-8`、`TZ=Asia/Shanghai`、`TERM=dumb`、指向空文件的 `GIT_CONFIG_GLOBAL`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_TERMINAL_PROMPT=0`、`GCM_INTERACTIVE=Never`、`NO_UPDATE_NOTIFIER=1`、`npm_config_update_notifier=false`。标准输入来自 `/dev/null`。没有传入 API key，也没有登录。

第 1 轮本地 HOME 的 `env` 输出只有上面这些名字。第 2 轮同名变量，路径换成 round2。两轮结束后扫描执行日志和 `/tmp/t6a-*`，没有 `x-access-token`、`ghp_`、`github_pat_` 或 `sk-ant-`。`/home/ubuntu` 下没有新建 Claude 配置目录。仓库 `git status --porcelain` 在两轮结束后都是空的。

工作区 `origin` URL 含有凭据 userinfo，所以宿主没有直接指向该工作区。每一轮先把基线文件树复制到新的临时目录并排除 `.git`，再对这个副本做 validate、本地安装和 `install-bundle.py`。副本内容对应上面的完整 SHA。

GitHub 源使用 CLI 自己的公开 HTTPS。两轮都打印了：

```text
SSH not configured, cloning via HTTPS: https://github.com/GaoFei2025-0314/devflow.git
Cloning repository (timeout: 120s): https://github.com/GaoFei2025-0314/devflow.git
```

克隆出来的 `.git/config` URL 是 `https`、`github.com`、路径 `/GaoFei2025-0314/devflow.git`，`has_userinfo=False`。2026-11-14 13:14:41 CST 在清洁 Git 环境里对两份克隆执行 `git rev-parse HEAD`，都是 `fe9f1540c222f52ae8965f7a0a3e7f14060a3f74`。

| 工具 | 第 1 轮 | 第 2 轮 |
| --- | --- | --- |
| OS | Linux cursor 6.12.113+ #1 SMP PREEMPT_DYNAMIC Fri Nov 13 20:22:28 UTC 2026 x86_64 | 相同 |
| Python | 3.12.3 | 相同 |
| Node | v22.23.4 | 相同 |
| npm | 10.9.9 | 相同 |
| Claude Code | 2.1.325 (Claude Code) | 相同 |

## 两轮差异

把两轮全部 `*.log` 里的时间戳和 `round1` / `round2` 路径替换掉之后，逐文件比较没有剩余差异。退出码一一相同。实质输出相同。不同的只有每轮的临时路径、命令时间，以及 `plugin list --json` 里的 `installedAt` / `lastUpdated`。

下面各节按轮次列出关键输出。第 2 轮不重复粘贴与第 1 轮逐字相同的长警告，只写该轮自己的时间和退出码，并标明与第 1 轮哪一段相同。

## 第 1 轮

HOME：`/tmp/t6a-round1-local`（本地源、validate、`claude -p`、stage）和 `/tmp/t6a-round1-github`（GitHub 源）。源副本 `/tmp/t6a-round1-src`。stage 目标 `/tmp/t6a-round1-stage`。

| 时间 (CST) | 命令 | 退出码 |
| --- | --- | --- |
| 13:10:39 | `claude --version` | 0 |
| 13:10:41 | `claude auth status --text` | 1 |
| 13:10:43 | `claude plugin validate <src>` | 0 |
| 13:10:47 | `claude plugin validate <src> --json` | 0 |
| 13:10:49 | `claude plugin validate <src> --profile directory` | 0 |
| 13:10:51 | `claude plugin validate <src>/.claude-plugin/plugin.json` | 0 |
| 13:10:52 | `claude plugin validate <src>/.claude-plugin/marketplace.json` | 0 |
| 13:10:54 | `timeout -k 5 25 claude -p hi` | 1 |
| 13:10:56 | `timeout -k 5 120 claude plugin marketplace add <src> --scope user` | 0 |
| 13:10:58 | `timeout -k 5 180 claude plugin install devflow@devflow --scope user` | 0 |
| 13:11:00 | `claude plugin list` | 0 |
| 13:11:02 | `claude plugin list --json` | 0 |
| 13:11:04 | `claude plugin details devflow` | 0 |
| 13:11:08 | `claude auth status --text`（GitHub 用的新 HOME） | 1 |
| 13:11:11 | `timeout -k 5 180 claude plugin marketplace add GaoFei2025-0314/devflow --scope user` | 0 |
| 13:11:14 | `timeout -k 5 180 claude plugin install devflow@devflow --scope user` | 0 |
| 13:11:16 | `claude plugin list` | 0 |
| 13:11:18 | `claude plugin list --json` | 0 |
| 13:11:20 | `claude plugin details devflow` | 0 |
| 13:11:23 | `python3 scripts/install-bundle.py stage --bundle <src> --layout full --dest <stage>` | 0 |
| 13:11:24 | `python3 scripts/install-bundle.py verify --bundle <src> --install-root <stage>` | 0 |

`claude` 是上面的 `/tmp/t6a-cli/node_modules/.bin/claude`。`<src>` 是该轮副本。

### validate

整仓 `claude plugin validate <src>` 退出码 0。末行是 `✔ Validation passed`。目录检查只有 1 条警告，代码 `ICON_MISSING`，字段 `icon`。JSON 里 `directory.findings[0].severity` 为 `warning`，`blocking` 为 `false`。marketplace manifest 的 `warnings` 是空数组。两轮所有 validate 输出里都没有 `LICENSE_MISSING`。

警告全文：

```text
⚠ Found 1 plugin directory warning:

  ❯ .claude-plugin/plugin.json icon: No icon (ICON_MISSING). No icon found in the plugin. The validator looked for `icon` in plugin.json and for a file at .claude-plugin/icon.png or .svg, assets/icon.png or .svg, or a similar path.
    Fix: Add a square PNG to the plugin folder at .claude-plugin/icon.png, or set `icon` in plugin.json to the path of a square PNG or JPEG in the plugin: 512 to 2048 px on each side, under 2 MB. SVG and WebP are not accepted. That file may become the listing icon only once: the first time the plugin is saved or submitted in the developer portal. Adding or changing it later does not change the icon.
```

另外有一条说明，不是另一条告警码：这个目录同时有 marketplace manifest，目录检查只覆盖本目录里的插件；插件目录还会做本命令不做的 safety scan 和 policy review。

`--profile directory` 同样退出码 0，警告仍是这一条 `ICON_MISSING`。这里只记录退出码，不把退出码 0 写成“插件目录已经接受提交”。

单独校验 `.claude-plugin/plugin.json`：退出码 0，同样带上面这一条 `ICON_MISSING`，末行 `✔ Validation passed`。单独校验 `.claude-plugin/marketplace.json`：退出码 0，输出只有 `✔ Validation passed`，没有 `ICON_MISSING`。

这是结构校验通过。

### 未登录

`claude -p hi` 放在任何插件安装之前，限时 25 秒。退出码是 1，不是超时的 124。标准输出只有：

```text
Not logged in · Please run /login
```

没有助手回复。同一清洁 HOME 上 `claude auth status --text` 的输出是 `Not logged in. Run claude auth login to authenticate.`，退出码 1。GitHub 用的另一个新 HOME 再次得到同一句，退出码 1。

这次没有观察到成功的模型响应。技能调用未验证。

### 本地源 CLI 安装

```text
Adding marketplace…✔ Successfully added marketplace: devflow (declared in user settings)
Installing plugin "devflow@devflow"...✔ Successfully installed plugin: devflow@devflow (scope: user)
```

`claude plugin list`：

```text
Installed plugins:

  ❯ devflow@devflow
    Version: 2.2.1
    Read from: /tmp/t6a-round1-src
    Scope: user
    Status: ✔ enabled
```

`plugin list --json`：`id` 为 `devflow@devflow`，`version` 为 `2.2.1`，`enabled` 为 `true`，`installPath` 为该 HOME 下 `.claude/plugins/cache/devflow/devflow/2.2.1`。

`claude plugin details devflow`：`devflow 2.2.1`，Skills (33)，Agents/Hooks/MCP servers/LSP servers 都是 0，Always-on 约 1,709 tok。这是清单投影，不是一次技能调用。

CLI安装命令成功。缓存目录里同时存在 `./LICENSE`、`./NOTICE`、`./THIRD_PARTY_NOTICES.md` 和 `skills/devflow/SKILL.md`。这是插件按整仓 source `./` 缓存的结果，不是 `scripts/install-bundle.py` stage 的分发清单。

### GitHub 源 CLI 安装

marketplace add 与 plugin install 的成功句与本地源相同，退出码都是 0。`claude plugin list` 没有 “Read from” 行，其余为 Version 2.2.1、Scope user、Status enabled。`plugin details` 与本地源相同：33 个技能，Always-on 约 1,709 tok。

克隆与插件缓存里都有 `./LICENSE`、`./NOTICE`、`./THIRD_PARTY_NOTICES.md` 和 `skills/devflow/SKILL.md`。

CLI安装命令成功。传输是上面的公共 HTTPS。没有使用账号。

### install-bundle.py stage / verify

```text
STAGED full layout: 33 skills, 41 distribution entries -> /tmp/t6a-round1-stage
INSTALL VERIFY PASSED: layout=full, 33 skills, references resolve
```

两个命令退出码都是 0。stage 目录里有 `./SKILL.md`、`./AGENTS.md`、`./README.md`、`./README.zh-CN.md`、`./CHANGELOG.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`templates/project-overrides.md`、`skills/devflow/SKILL.md` 和 install-manifest.json。技能目录 33 个。

同一目录里 **ABSENT**：`./LICENSE`、`./NOTICE`、`./THIRD_PARTY_NOTICES.md`。manifest 的 `paths` 也没有这三项。源副本根上这三项是存在的。分发清单没有把它们拷进 stage 产物。本次按既定边界只记录，不改 `scripts/install-bundle.py`。

`verify` 退出码 0 只说明清单内的条目、引用和字节核对通过。它不表示许可证文件已经被 stage 带上。

## 第 2 轮

HOME：`/tmp/t6a-round2-local` 与 `/tmp/t6a-round2-github`。源副本 `/tmp/t6a-round2-src`。stage 目标 `/tmp/t6a-round2-stage`。命令与第 1 轮相同，路径换成这一轮的新目录。

| 时间 (CST) | 命令 | 退出码 |
| --- | --- | --- |
| 13:11:37 | `claude --version` | 0 |
| 13:11:39 | `claude auth status --text` | 1 |
| 13:11:43 | `claude plugin validate <src>` | 0 |
| 13:11:47 | `claude plugin validate <src> --json` | 0 |
| 13:11:48 | `claude plugin validate <src> --profile directory` | 0 |
| 13:11:51 | `claude plugin validate <src>/.claude-plugin/plugin.json` | 0 |
| 13:11:54 | `claude plugin validate <src>/.claude-plugin/marketplace.json` | 0 |
| 13:11:56 | `timeout -k 5 25 claude -p hi` | 1 |
| 13:11:57 | `timeout -k 5 120 claude plugin marketplace add <src> --scope user` | 0 |
| 13:12:00 | `timeout -k 5 180 claude plugin install devflow@devflow --scope user` | 0 |
| 13:12:03 | `claude plugin list` | 0 |
| 13:12:05 | `claude plugin list --json` | 0 |
| 13:12:08 | `claude plugin details devflow` | 0 |
| 13:12:11 | `claude auth status --text`（GitHub 用的新 HOME） | 1 |
| 13:12:13 | `timeout -k 5 180 claude plugin marketplace add GaoFei2025-0314/devflow --scope user` | 0 |
| 13:12:17 | `timeout -k 5 180 claude plugin install devflow@devflow --scope user` | 0 |
| 13:12:19 | `claude plugin list` | 0 |
| 13:12:22 | `claude plugin list --json` | 0 |
| 13:12:24 | `claude plugin details devflow` | 0 |
| 13:12:28 | `python3 scripts/install-bundle.py stage --bundle <src> --layout full --dest <stage>` | 0 |
| 13:12:30 | `python3 scripts/install-bundle.py verify --bundle <src> --install-root <stage>` | 0 |

第 2 轮自己的关键原文：

- `claude --version`：`2.1.325 (Claude Code)`
- `claude auth status --text`（两个 HOME）：`Not logged in. Run claude auth login to authenticate.`
- `claude -p hi`：`Not logged in · Please run /login`，退出码 1
- validate 末行：`✔ Validation passed`；唯一警告码仍是 `ICON_MISSING`；没有 `LICENSE_MISSING`
- 本地与 GitHub 的 install 成功句与第 1 轮相同；list 都是 Version 2.2.1、Status enabled
- details：Skills (33)，Always-on 约 1,709 tok
- stage：`STAGED full layout: 33 skills, 41 distribution entries -> /tmp/t6a-round2-stage`
- verify：`INSTALL VERIFY PASSED: layout=full, 33 skills, references resolve`
- stage 目录同样 **ABSENT** `./LICENSE`、`./NOTICE`、`./THIRD_PARTY_NOTICES.md`
- GitHub 克隆 SHA 同样是 `fe9f1540c222f52ae8965f7a0a3e7f14060a3f74`，URL 无 userinfo

第 2 轮的 validate、安装、details 和 stage 文件清单，与第 1 轮在去掉路径和时间之后一致。

## 未执行

- **技能调用未验证。** 没有 Claude 账号，也没有 API key。`claude -p` 停在未登录错误，没有调用 `devflow:devflow`，也没有别的技能。
- **`/plugin` 交互面板未验证。** 没有交互式 TUI，也没有已登录会话。上面的安装是 CLI 子命令。
- **Cursor 未验证。** 没有 Cursor 桌面或 Cursor 账号，没有把技能放进 Cursor 的加载目录做原生读取。
- **T6b 未执行。** 仍缺凭据和费用批准。
- **消融实验未执行。**
- `install-bundle.py plan` 未执行。本次范围是 `stage` 和 `verify`。
- 没有购买、超额付费或新订阅。出现这类要求时按指示停止；本次没有出现。

## 已知边界

`scripts/install-bundle.py` 的 `DISTRIBUTION_ROOT_FILES` 不含 `./LICENSE`、`./NOTICE`、`./THIRD_PARTY_NOTICES.md`。两轮 stage 产物都缺这三项，同时 `verify` 退出码为 0。这是主人已定、本次不改安装脚本的结果，不是漏测。Claude 插件缓存因为整仓拷贝而带有这三项，不能用来声称 stage 分发已经带上许可证。
