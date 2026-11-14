# ADR-0001：devflow v2.3.0 技术方案

- 状态：**草稿（Draft）**，待 SF-Chief of Staff 审阅、主人确认带“需主人批准”标记的事项
- 任务：SF-20261114-01（Architect 产出）
- 日期：2026-11-14（Asia/Shanghai）
- 最终仓库路径：`docs/factory/ADR-0001-devflow-v2.3.md`（现在只放在盒子 `/workspace/devflow-v2.3/`，没有推送）
- 被审对象：GaoFei2025-0314/devflow，`main` HEAD `63c5b70`（工作区 `/workspace/devflow-src` 只读克隆，`git status` 干净）
- 主人已定（Chief 转述）：①许可证 = Apache-2.0；②先在 `main@63c5b70` 补打 `v2.2.1` tag + GitHub Release，再发 `v2.3.0`。**本 ADR 不执行任何 tag/Release。**

## 0. 事实核对（Chief 给的“事实”逐条对照仓库）

我在盒子上亲自跑了命令，结果如下。“已验证”＝我自己运行或读到了；“未验证”＝仓库里查不到。

| # | Chief 的说法 | 结论 | 证据 |
|---|---|---|---|
| 1 | 本地 254 个维护测试通过 | **已验证** | `python3 -m unittest discover -s tests/maintenance -p 'test_*.py'` → `Ran 254 tests … OK`（Python 3.13.5） |
| 2 | check-refs 通过 | **已验证** | `bash scripts/check-refs.sh` → `ALL CHECKS PASSED` |
| 3 | CI 39/39 success | **已验证** | GitHub API `actions/runs`：`total_count=39`，20 个 push + 19 个 pull_request 全部 `success`；`63c5b70` 的 check-runs：check-refs、maintenance-tests（ubuntu/windows）、behavior-material 都是 success，version-bump 是 skipped（push 事件不跑） |
| 4 | 无 LICENSE | **已验证** | `git ls-files` 只有 `skills/frontend-design/LICENSE.txt`；GitHub API 仓库 `license: null` |
| 5 | tag 只到 v2.2.0、无 Release | **已验证** | `git ls-remote --tags`：v2.0.0、v2.0.1、v2.0.2、v2.1.0、v2.2.0（均为附注 tag）；`/releases` 返回空数组 |
| 6 | validate.yml 不查 CHANGELOG | **部分准确** | `.github/workflows/validate.yml:40-60` 的 `version-bump` job 只比较 PR 前后 `plugin.json` 的 version，**不看 CHANGELOG**；逻辑内联在 YAML 里，没有测试 |
| 7 | 未 setup-python | **已验证** | 全文无 `setup-python`；用的是 runner 自带 Python |
| 8 | actions 未钉 SHA | **已验证** | `validate.yml:19,29,36,44` 共 4 处 `uses: actions/checkout@v4`，这是仓库里唯一用到的 action |
| 9 | host-support.md 宿主多未验证 | **已验证** | `docs/devflow/host-support.md:26-34`：Claude Code 插件安装、Codex CLI、Cursor、Copilot CLI、Gemini CLI 都是 unverified/blocked/仅格式兼容 |
| 10 | 消融显示短任务无增益、T8 残留通用授权提醒 | **已验证，但要纠偏** | 见 §D：T8 的那条回复确实有“发布本身还需要你另行明确授权”（`docs/devflow/experiments/2026-10-ablation/README.md:129`；原文在 `docs/devflow/experiments/2026-10-ablation/data/rerun-2.2.0/results.json`，run `T8-B-3`）。但“不要附带通用授权提醒”这条规则**2.2.0 起已经在文本里**（`skills/using-devflow/references/action-rules.md:63`），所以残留不是“缺规则”，是 1/10 的采样事件 |
| 11 | mandatory load 28696/30000 | **已验证** | `python3 scripts/check-bundle.py --root .` → `MANDATORY LOAD: 28696 bytes across 4 files (budget 30000)`；四个文件分别 8479 + 3838 + 5920 + 10459 |

### 与 Chief 描述有出入或需要补充的地方
1. **“补打 v2.2.1”其实是当前版本没打 tag**：`plugin.json` 的 version 就是 `2.2.1`（`.claude-plugin/plugin.json:4`），`CHANGELOG.md:5` 顶部是 `## 2.2.1 (2026-10-22)`。也就是说 `63c5b70` 上版本号、CHANGELOG 已经一致，只缺 tag 与 Release。
2. **PRD 的 US4 写“check-refs.sh 最低版本与 check-behavior 一致（3.10）”——实测证实真实下限就是 3.10**：见 §B（3.9 和 3.8 各有 21 个测试失败）。
3. **许可证有比 PRD 更大的合规问题**：仓库初始提交（`8973c9a`）把三个第三方集合整体搬了进来：`skills/` 下的 `agent-skills/`（20 个文件）、`superpowers/`（46 个文件）、`openspec/`（1 个文件）；`ea390fb` 的提交说明写明 frontend-design 的 LICENSE.txt 取自 `anthropics/skills`。这些上游许可证我查了：`obra/superpowers`（MIT，Copyright (c) 2025 Jesse Vincent）、`addyosmani/agent-skills`（MIT，Copyright (c) 2025 Addy Osmani）、`Fission-AI/OpenSpec`（MIT，Copyright (c) 2025 FISSION AI INC）、`anthropics/skills` 的 frontend-design（Apache-2.0）。**仓库里目前没有任何署名文件**（README、CHANGELOG 都没提）。MIT 要求保留版权和许可声明，所以 T1 不能只放一个 LICENSE，还得有第三方声明文件。哪些现行文本仍然是这些上游的衍生内容，我无法从仓库判断，保守起见按“可能衍生”处理（见 §E）。
4. **version-bump 触发路径与 T1 的交叉**：`validate.yml:51` 的触发路径是 `skills/ SKILL.md AGENTS.md templates/`。任何改到这些路径的 PR 都必须同时升版本。这直接决定了任务顺序，见 TASKS-revised.md。
5. **Claude 插件已能在无账号条件下做真实安装验证**（盒子实测，见 §T6），这比 Chief 预期的“做不了”要好，但仍不是 `/plugin` 面板和技能调用。

---

## 决策 A：CI 的版本 / CHANGELOG 一致性检查

### 背景
- 现状：`version-bump` job（`validate.yml:40-60`）只在 PR 上跑，用内联 shell + `python3 -c` 比较新旧 `plugin.json` 版本，没有测试，不看 CHANGELOG，不看 tag。
- 仓库约定（`./README.md` Maintenance 一节、`docs/devflow/release-checklist.md:18`）：改技能内容的 PR 必须升 `plugin.json` 的 version，并在同一个 PR 里加 `## X.Y.Z (YYYY-MM-DD)` 的 CHANGELOG 条目，发版后不再开“补记 tag”的 PR。这些约定今天只靠人。
- 仓库里的脚本语言是 Python 标准库（`scripts/*.py`），测试是 `unittest`，目录 `tests/maintenance/`。`.claude-plugin/marketplace.json` 目前没有 `version` 字段（只有 name/description/owner/plugins[].source），版本的唯一来源是 `plugin.json`。
- CHANGELOG 现有 13 个二级标题我用同一个正则逐条验证过，全部匹配：`## 2.2.1 (2026-10-22)`、`## 2.2.0 (2026-10-09 tag)`、`## 2.0.2 (2026-09-30 tag, limited acceptance)`、早期的 `## 2.0.0`/`## 1.3.1` 等无日期标题。

### 选项
1. 继续在 YAML 里内联 shell，往里加 CHANGELOG 判断。
2. 新增 Python 脚本 `scripts/check-version.py`（标准库、与现有脚本同风格），YAML 只负责调用；`unittest` 做 fixture 测试。
3. 用 Node/npm 的现成工具（如 changesets）。
4. 并入 `scripts/check-refs.sh`。

### 决定
选 **2**：新增 `scripts/check-version.py`，测试放 `tests/maintenance/test_version.py`，CI 里新增独立 job `version-consistency`，原 `version-bump` job 改为调用同一个脚本的 `bump` 子命令。

脚本接口（只给契约，不写业务代码）：

```text
python scripts/check-version.py consistency [--root .] [--tag vX.Y.Z]
python scripts/check-version.py bump --base-ref origin/main [--root .]
```

`consistency` 检查（任何一条不满足退出码 1；输入无法解析退出码 2，沿用 `check-bundle.py` 的 0/1/2 约定）：
1. `.claude-plugin/plugin.json` 能解析，`version` 严格匹配 `^\d+\.\d+\.\d+$`。
2. `.claude-plugin/marketplace.json` 的 `plugins[]` 里如果出现 `version` 字段，必须等于 plugin.json 的 version（现在没有这个字段，所以现在恒通过，只是防以后漂移）。
3. `./CHANGELOG.md` 的第一个 `## ` 标题必须匹配 `^## (\d+\.\d+\.\d+)(?: \((\d{4}-\d{2}-\d{2})[^)]*\))?\s*$`，版本号等于 plugin.json 的 version，并且**顶部条目必须带合法日期**（对应 README 的“发版 PR 里就写日期”约定）。
4. 所有标题的版本号严格递减、不重复（防止复制粘贴漏改）。历史上没有日期的老条目（2.0.0 及更早）允许无日期，只有顶部条目强制有日期。
5. 传了 `--tag vX.Y.Z` 时：tag 必须等于 `v` + plugin.json version（用于发版前的人工检查和 Release Manager 的核对）。

`bump` 检查（取代 `validate.yml:47-60` 的内联脚本，语义保持，另加两条）：
1. 触发路径与现在完全一致：`skills/`、`SKILL.md`、`AGENTS.md`、`templates/`（对应 `validate.yml:51`）。这些路径没有变化 → 直接通过。
2. 有变化时：plugin.json version 必须和基线不同（现有行为），**且必须比基线大**（新增：防降级），**且 CHANGELOG 相对基线必须有变化并含新版本标题**（新增：补上“漏改 CHANGELOG”这个缺口，满足 US3）。

### 怎么测（与仓库现有测试方式一致）
`tests/maintenance/test_version.py`，`unittest` + `tempfile`，不引入第三方依赖：
- `consistency` 用 fixture 目录（临时目录写入最小的 plugin.json / marketplace.json / CHANGELOG.md）：
  - 正例：版本一致、顶部有日期、标题递减；
  - 反例：plugin 与 CHANGELOG 不一致；顶部条目无日期；日期不合法（2026-13-40）；标题不递减/重复；version 非 semver；marketplace 出现不同的 version；`--tag` 不匹配；
  - 真实仓库用例：对 `REPOSITORY_ROOT` 本身跑一次必须通过（保证真实 CHANGELOG 格式不被将来的修改破坏）。
- `bump` 用临时 git 仓库（`git init`，两次提交）：无技能改动；改了 skills/ 没升版本；升了版本但没动 CHANGELOG；版本降级；全部正确。没有 `git` 时 `skipUnless`（CI 的 ubuntu/windows runner 都自带 git）。

本地与 CI 的确切命令（均来自仓库现有写法，`./README.md` Maintenance 和 `validate.yml:31`）：

```bash
# 只跑新测试
python -m unittest discover -s tests/maintenance -p 'test_version.py'
# 全量维护测试（现有 CI 命令，T2 之后总数会大于 254，以实际输出为准）
python -m unittest discover -s tests/maintenance -p 'test_*.py'
# 直接检查当前仓库
python scripts/check-version.py consistency
# 发版前核对（T8 用 v2.2.1，T5 用 v2.3.0）
python scripts/check-version.py consistency --tag v2.3.0
```

CI 接线：新增 job `version-consistency`（ubuntu-latest，PR 与 push 都跑 `consistency`）；`version-bump` job 保留（仅 PR），改为 `python scripts/check-version.py bump --base-ref "origin/${{ github.base_ref }}"`，保留 `fetch-depth: 0`。**不并入 `scripts/check-refs.sh`**：`tests/maintenance/test_refs.py` 会把 `scripts/check-refs.sh` 复制进临时夹具目录跑，里面没有 plugin.json，并入会让现有测试失败。

### 理由
- 与现有脚本同语言、同目录、同测试框架，维护者无需新工具；零第三方依赖（符合 PRD Non-goals）。
- 把内联 shell 搬进可测试脚本，是这个需求里最实质的改进：现在的 bump 逻辑没有任何测试。
- `consistency` 与 `bump` 分开：前者是“当前状态自洽”，后者是“相对基线的变更规则”，两种场景的输入不同。

### 后果
- 新增 1 个脚本、1 个测试文件，约 1 个 PR（T2a）。
- README 的 Layout 里要补一行 `check-version.py`（归 T4，见任务表，避免多个任务改 README）。
- 同一发布周期内，**第二个**改到触发路径的 PR 必须再升一次版本（因为基线已经是新版本），这是现有 `version-bump` 的既有性质，不是新引入的。所以 v2.3.0 的任务顺序要求“改技能文本的任务必须是最后一个内容 PR”（见 TASKS-revised.md）。

### 风险
- CHANGELOG 标题格式今后有人写成别的样子会被拦：这是预期行为，错误信息要写明期望格式。
- 中文/英文标题混用：目前全英文，不处理。
- 日期只校验“合法日历日期”，不校验“等于合并日”（合并日在 PR 里不可知）。

### v2.2.1 / v2.3.0 对脚本的影响（主人已定：先补 v2.2.1，再发 v2.3.0）
- `63c5b70` 上 plugin.json=2.2.1、CHANGELOG 顶部=2.2.1、日期有效，`consistency --tag v2.2.1` 在该提交上成立（我用等价的人工核对确认了版本与标题；脚本落地后可复核）。**补打 v2.2.1 不需要改任何文件**，所以不会触发版本检查，也不改 CHANGELOG（仓库约定“发布后不再补记 tag”，`CHANGELOG.md:8` 的说明）。
- v2.3.0 发布时：plugin.json=2.3.0、CHANGELOG 顶部 `## 2.3.0 (YYYY-MM-DD)`，且 2.3.0 严格大于 2.2.1，脚本的递减检查自然覆盖。
- 若主人改主意“不补 v2.2.1”：脚本不受影响（脚本不要求每个版本都有 tag）；只是 GitHub 上会出现 v2.2.0 → v2.3.0 的断层，CHANGELOG 里 2.2.1 条目依然存在。
- **本 ADR 不创建任何 tag/Release。** 实际执行都需要主人在对话里明确批准（任务 T8、T5）。

---

## 决策 B：Python 版本与矩阵

### 背景
- 现状：CI 没有 `setup-python`，用 runner 自带的 Python（版本随镜像变化，不可复现，对应 PRD US4）。
- 仓库自述：`tests/behavior/README.md:7` 写“需要 Python 3.10 或更新”；`scripts/check-refs.sh:23,31` 写 `>= 3.8`；脚本都有 `from __future__ import annotations`。
- **实测真实下限**（`uv run --python X`，同一份代码、同一条测试命令）：

| Python | 254 个维护测试 | `check-bundle.py` |
|---|---|---|
| 3.8 | 失败：21 failures + 3 errors | 通过 |
| 3.9 | 失败：21 failures | 通过 |
| 3.10 | **254 OK** | 通过 |
| 3.13 | **254 OK** | 通过 |

  所以 `scripts/check-refs.sh` 里的“3.8”是**错的下限**：它让脚本在 3.8/3.9 上看似可用，但同仓库的测试已经会失败。

### 选项
1. 只测 3.10（下限）。
2. 3.10 + 3.13（下限 + 当前较新版本），维护测试在 Ubuntu/Windows 上都跑。
3. 3.10–3.13 全矩阵。
4. 继续不钉版本。

### 决定
选 **2，且不全交叉**：
- `maintenance-tests`：`os: [ubuntu-latest, windows-latest]` × `python-version: ['3.10', '3.13']`，共 4 个组合（仍保留 Ubuntu+Windows，满足 PRD 兼容要求）。
- `check-refs`、`behavior-material`、`version-consistency`、`version-bump`：各加 `actions/setup-python`，固定 `'3.10'`（下限；这些 job 只依赖标准库，没必要乘矩阵）。
- `scripts/check-refs.sh:23,31`：下限从 3.8 改为 3.10，提示文字同步（T2b）。
- 统一写法：`python-version` 用带引号的字符串（避免 `3.10` 被 YAML 解析成 `3.1`）。

### 理由
- 3.10 是实测下限，守住下限最能抓“用了新语法”的回归；3.13 是本次实测通过的较新版本，覆盖“新版本弃用/行为变化”。
- 总 job 数从 6 个增加到约 8 个（每个很短，维护测试 20 余秒），不新增付费服务（公开仓库的 Actions 免费）。
- 不测 3.11/3.12：边际信息少，需要时再加。

### 后果 / 风险
- Windows × 3.10 是新增组合，**我只在 Linux 上验证了 3.10**，Windows 上的 3.10 要靠 T2b 的 PR CI 来验证；如果失败，按失败修，不要放宽下限。
- `test_refs.py` 的 `find_bash()` 会在 Windows 上找 Git 自带的 bash（`tests/maintenance/test_refs.py:12-24`），与 setup-python 无冲突。
- 将来 setup-python 弃用某个 Python 版本（v7.0.0 的发布说明里有 “Remove EOL Python versions”），3.10 已处于 EOL 之后的状态是否仍可用，要看 v7.1.0 的实际行为；**T2b 的 PR 首次运行即是验证**。若 3.10 被拒，备选是回退到 setup-python v6.3.0（SHA 见决策 C）。

---

## 决策 C：actions 钉 SHA

### 背景
- 仓库全部 workflow 只有一个文件 `.github/workflows/validate.yml`，其中 **唯一使用的 action 是 `actions/checkout@v4`，出现 4 次（第 19、29、36、44 行）**；新增 `actions/setup-python` 后共 2 个 action。
- `permissions: contents: read` 已经存在（`validate.yml:8-9`），符合 PRD 的安全要求。
- 对应 PRD 的 US4 与“安全”非功能需求。

### 选项
1. 保持 `@v4` 浮动 tag。
2. 钉到 SHA，并在行尾用注释写明版本（`# v7.0.1`）。
3. 钉 SHA + 启用 Dependabot（github-actions 生态）自动提升级 PR。

### 决定
选 **3**（SHA 必须；Dependabot 为可选项，需主人点头，见下）。

SHA 全部用 `git ls-remote https://github.com/<owner>/<action> refs/tags/<tag>` 实时查得（2026-11-14）。这些 tag 在上游是**轻量 tag**（查询时没有 `^{}` 解引用行），ls-remote 返回的就是 commit SHA：

| Action | 选定版本 | 完整 SHA（40 位） | 备注 |
|---|---|---|---|
| `actions/checkout` | **v7.0.1** | `3d3c42e5aac5ba805825da76410c181273ba90b1` | 2026-07-20 发布；`action.yml` 使用 `node24` |
| `actions/setup-python` | **v7.1.0** | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | 2026-10-22 发布；`action.yml` 使用 `node24` |

备选（如 v7 在 CI 里有兼容问题，整体回退一档，都是我查到的真实值）：
- `actions/checkout` v6.1.0 → `d23441a48e516b6c34aea4fa41551a30e30af803`；v6.0.2 → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `actions/setup-python` v6.3.0 → `ece7cb06caefa5fff74198d8649806c4678c61a1`；v6.2.0 → `a309ff8b426b58ec0e2a45f0f869d46889d02405`
- 当前在用的 `actions/checkout@v4` 最近的具体版本：v4.3.1 → `34e114876b0b11c390a56381ad16ebd13914f8d5`（只作对照，不建议继续用 Node 20 运行时的版本）

写法（T2b 实现，行尾注释必须保留版本号，方便人和 Dependabot 读）：

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  with:
    persist-credentials: false
- uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
  with:
    python-version: '3.10'
```

`version-bump` 的 checkout 需要 `fetch-depth: 0`（`validate.yml:45-46`），与 `persist-credentials: false` 不冲突（它只在本地 `git fetch` 公开仓库）。

**Dependabot（可选，需主人批准是否启用）**：在 `.github/dependabot.yml` 里配 `package-ecosystem: github-actions`、`directory: "/"`、`schedule.interval: monthly`。免费，会自动给钉了 SHA 的 action 发升级 PR（只改 `.github/workflows/`，不触发版本号检查，因为不在 bump 触发路径内）。代价是每月可能多几个 PR。它是仓库文件而不是仓库设置，但“开启后会自动产生 PR”属于对仓库行为的改变，所以列为需批准项。我的建议：启用，monthly。

### 理由
- 浮动 tag 可被上游移动；SHA 不可变，满足 PRD 的“actions 钉 SHA”。
- 选 v7 系：当前 v4 的运行时 Node 版本已较旧，v7 两个 action 都是 node24；v7 发布已有数月（checkout v7.0.1 为 2026-07-20，setup-python v7.1.0 为 2026-10-22），我读了 v7.0.0/7.1.0/7.0.1 的发布说明，没有看到会影响本仓库用法的破坏性变更（setup-python v7.0.0 移除了 `pip-install` 输入和 EOL 的 Python 版本；本仓库没用 `pip-install`）。**但这是读说明得出的判断，不是实跑**，T2b 的 PR CI 是第一次实测。

### 后果 / 风险
- 将来升级要么靠 Dependabot，要么手动换 SHA；脚本无法替你检查 SHA 与注释版本是否匹配（可由 Dependabot 维护）。
- 风险：v7 若在 `windows-latest` 上对 3.10 有问题 → 用上面的备选行整体回退并在 PR 里记录。

---

## 决策 D：减负（残留仪式）的边界与 mandatory load 守门

### 背景（先纠偏）
- “mandatory load”的测量**已经存在并且已经在 CI 里强制**：`scripts/check-bundle.py:29-35` 定义 `MANDATORY_LOAD` 为 4 个文件，`MANDATORY_LOAD_BUDGET = 30_000`；`:373-377` 超过就记错误、退出码 1；`scripts/check-refs.sh:117` 调用它，CI 的 `check-refs` job 每次 push/PR 都会跑。CHANGELOG 2.1.0 也写了这个预算（`CHANGELOG.md:22`）。
- **当前实测值：28696 字节**（8479 + 3838 + 5920 + 10459），余量 1304 字节（约 4.3%）。另外：全部 33 个技能入口合计 317987 字节，最大的 `subagent-driven-development` 16566 字节（预算 18000）；`claude plugin details devflow`（Claude Code 2.1.325 实测）给出常驻开销约 1,709 token（技能描述）。
- “不要附带通用授权提醒”**已经是现行规则**：`skills/using-devflow/references/action-rules.md:63`：“…and the next decision the user needs to make, when one is genuinely pending. Do not append generic reminders that later actions need authorization.”（2.2.0 加入，`CHANGELOG.md:13`）。
- 残留样本：`docs/devflow/experiments/2026-10-ablation/data/rerun-2.2.0/results.json` 的 run `T8-B-3` 在 2.2.0 文本下仍写了“发布本身还需要你另行明确授权”。样本量是 10 次里 1 次（实验记录 `docs/devflow/experiments/2026-10-ablation/README.md` 第 7 节自己也声明样本很小）。
- 所以 **PRD 的 US7 第一条（“不再要求未决的通用授权提醒”）在文本层面已经满足**；没有任何规则文字“要求”这种提醒。剩下的只是模型行为偶发，原因不明。可能的诱因文本（只是假设，没证据）：`skills/using-devflow/references/core-rules.md:20`（“waits only for its authorization”）、`action-rules.md:54`（Deploy/release 行）、`AGENTS.md:18`（“A route or completed document does not grant a later action”），这些都是必须保留的安全边界。

### 选项
1. 不改规则文字，只在 README 补“何时可不加载完整包”，并在 CHANGELOG 如实写“残留 1/10，未再修”。
2. 微调 `action-rules.md:63` 的措辞（由“禁止加提醒”改为“只在确有待决授权时才提”这种正向判据），字节数不增加；README 补说明。
3. 再删一批规则文字大幅减负（比如砍 `skills/using-devflow/references/action-rules.md` 的授权表）。
4. 重跑消融实验验证效果（需要调用模型，产生费用）。

### 决定
选 **2**，**不做 3**，**4 只列为可选（需主人批准）**。

**改什么（T3 的 Files，不多不少）：**
1. `skills/using-devflow/references/action-rules.md`：只改第 63 行（Delivery summary 一句）。把“Do not append generic reminders that later actions need authorization.”改写为正向判据：只有当用户的下一步确实需要一个**尚未取得**的授权，并且这是一个待决事项时，才在“next decision”里点名；否则不写授权相关的话。要求**净字节数 ≤ 0**。
2. `./README.md` 与 `./README.zh-CN.md`：Usage 一节补 3–5 行“何时不必加载完整包”，内容只引用仓库已有表述：`skills/using-devflow/SKILL.md:12`（“a question or a small, clear change usually needs none”）、`AGENTS.md:14`（“do not … load all 33 skills by default”）、`CHANGELOG.md:20`（只读路线约 14,552 字节、实现路线约 28.7 KB）。两份 README 必须同步（`./README.md` Maintenance 要求）。
3. `AGENTS.md`、`skills/devflow/SKILL.md`：**只在 `skills/using-devflow/references/action-rules.md` 的改动需要镜像时才动**（README 的 Maintenance 规定路由变更要镜像）。这次只改措辞不改路由，预期不动；如果测试 `tests/maintenance` 里的入口一致性检查要求镜像，再改。

**绝对不能改：**
- `action-rules.md:47-56` 的授权表（各动作需要的授权）和“Keep separate”（`action-rules.md:37`）；
- 不可信内容不能产生授权的规则（`AGENTS.md:18` 等）；
- `check-bundle.py:29-35` 的 `MANDATORY_LOAD` 清单和 30000 预算（**不放宽**）；
- 33 个技能的名称与 `skills/devflow/references/skill-catalog.json`；
- 消融实验记录的数据文件（`docs/devflow/experiments/**`）。

**mandatory load ≤ 30000 怎么保证（复用现有测量，不另造）：**
1. 硬门：保持现有 `MANDATORY_LOAD_BUDGET = 30_000`，超过 CI 失败（已存在，T3 不动）。
2. 软警告（T2b 新增，`scripts/check-bundle.py` + `tests/maintenance/test_bundle.py`）：超过 **29,000** 字节时在输出里打印 `WARNING: mandatory load … exceeds the 29000-byte warning line`，**不失败**。
   - 为什么不用 Chief 建议的 28,500：当前就是 28,696，已经高于 28,500，上线即常驻警告，没信息量；29,000 给出约 1,000 字节（3.3%）的预警余量，且现在不触发。
3. T3 的增量约束（验收项）：T3 合并后 `MANDATORY LOAD` 必须 **≤ 28696**（净不增），目标但不强制 ≤ 28,500。
4. 验收取证：PR 描述里贴 `python scripts/check-bundle.py --root .` 的前后输出（repo 的 README 也要求“每次改技能写一行预期行为变化”）。

**效果验证的诚实说明**：这次文本改动是否会让残留提醒消失，**我无法在不调用模型的情况下证明**；N=1 的残留本来就不足以给出因果。CHANGELOG 里必须写“措辞微调，未重新跑消融”，与 2.2.0 条目（`CHANGELOG.md:15` 末句）一致。想验证需要重跑 `docs/devflow/experiments/2026-10-ablation/harness/` 的 T8（该实验用 Sonnet 级子代理，有模型费用，**需主人批准**），样本至少每个版本 10 次才有一点信息量。

### 理由
- 规则已经写了“不要附带”，再往里加更多禁止性文字会增加 mandatory load 而没有证据有效；把它写成正向判据、字节不增，是风险最小的做法。
- “减负”真正有数据支持的是 2.2.0 已做的三条（路线宣布、推送前测试、授权提醒），本次不扩大战果，避免没有证据的删减（`./README.md` Maintenance：“Pruning needs evidence”）。

### 后果 / 风险
- 风险：措辞微调可能被测试认为破坏入口一致性 → T3 须跑全量维护测试。
- 风险：效果无法证伪 → 在 CHANGELOG 和 PR 里明说，避免过度宣称。
- 因 T3 会改 `skills/`、`AGENTS.md`，它必然触发版本检查；所以 **T3 同时承载 v2.3.0 的版本号和 CHANGELOG**（见 TASKS-revised.md 的串行说明）。

---

## 决策 E：许可证（主人已定 Apache-2.0）

### 背景
- 根目录没有 LICENSE/NOTICE；GitHub 仓库 `license: null`。
- `skills/frontend-design/LICENSE.txt` 是完整的 Apache-2.0 文本（177 行，以 “END OF TERMS AND CONDITIONS” 结尾，没有附录里的版权行）；`skills/frontend-design/SKILL.md:4` 写 `license: Complete terms in LICENSE.txt`。
- 第三方来源见 §0 第 3 条：agent-skills（MIT）、superpowers（MIT）、OpenSpec（MIT）、anthropics/skills frontend-design（Apache-2.0）。
- `scripts/install-bundle.py:31-40` 的 `DISTRIBUTION_ROOT_FILES` 决定“暂存/安装”时拷贝哪些根文件：现在**不含** LICENSE，所以通过 `install-bundle.py stage` 得到的安装目录会缺许可证（Apache-2.0 §4(a) 要求再分发时附带许可证副本）。
- Claude 插件按 `source: "./"` 整仓缓存（我在盒子上实测安装后缓存目录里是整个仓库内容），根目录 LICENSE 会随插件一起分发。
- `claude plugin validate .`（2.1.325）已报 `LICENSE_MISSING`：“plugin.json 没有 license 且没有 LICENSE 文件”，这是插件目录的提交条件之一；根目录加 LICENSE 即可消除。

### 选项
1. **Apache-2.0**（主人已定）。
2. MIT（作为被否决的备选）。
3. 不加许可证（现状，别人没有任何使用权）。

### 决定
选 **1：Apache-2.0**。落地内容（T1）：
1. `LICENSE`：Apache-2.0 官方全文（可直接用 frontend-design 那份逐字复制的文本，**推荐从 apache.org 官方文本取**，两者应逐字一致，用 `diff` 核对）。
2. `NOTICE`：短文件，格式如 `devflow\nCopyright 2026 <版权人>\n\nThis product includes software developed by …`。**版权人姓名和年份需要主人确认**（GitHub 账号是 GaoFei2025-0314；仓库首个提交是 2026-07-04，`git log --reverse` 的第一行）。
3. `./THIRD_PARTY_NOTICES.md`（或并入 NOTICE，二选一，我倾向单独文件）：列出 4 个上游、各自许可证与版权行，并**原文附上 MIT 许可证文本**三份中的各自版权行（MIT 的唯一条件就是保留版权声明和许可声明）：
   - obra/superpowers — MIT — Copyright (c) 2025 Jesse Vincent
   - addyosmani/agent-skills — MIT — Copyright (c) 2025 Addy Osmani
   - Fission-AI/OpenSpec — MIT — Copyright (c) 2025 FISSION AI INC
   - anthropics/skills（frontend-design）— Apache-2.0 — 许可证文本已在 `skills/frontend-design/LICENSE.txt`
4. `./README.md` / `./README.zh-CN.md` 增加“License”小节（指向 LICENSE、NOTICE、THIRD_PARTY_NOTICES.md；中英同步）。
5. `scripts/install-bundle.py:31-40` 的 `DISTRIBUTION_ROOT_FILES` 增加 `LICENSE`、`NOTICE`、`./THIRD_PARTY_NOTICES.md`，`tests/maintenance/test_install.py` 同步（让暂存/安装产物带许可证）。该元组按 `is_file()` 过滤（`install-bundle.py:126`），缺文件不会报错，所以不会破坏现有流程。**这一条是我的建议，不在 PRD 范围内，需 Chief 同意；不做也不阻塞 US1。**
6. **不修改 `skills/frontend-design/LICENSE.txt` 和任何 `skills/**`**——原因：版本检查的触发路径含 `skills/`，改了就会强制 T1 升版本号；保持该文件逐字不变也更符合 Apache-2.0 对上游文件的要求。
7. `plugin.json` 加 `"license": "Apache-2.0"` 字段属于可选；有根目录 LICENSE 已经够 `claude plugin validate` 过关。不加，避免 T1 与 T3 争用 plugin.json。

**被否决的 MIT**：MIT 更短，但没有专利授权条款、没有 NOTICE 机制；项目里已经有 Apache-2.0 的 frontend-design，统一成 Apache-2.0 更一致。

两种许可证的差异（写给主人确认用，主人已选 Apache-2.0）：

| 项目 | Apache-2.0 | MIT |
|---|---|---|
| 专利授权 | 有明确专利许可（§3），贡献者起诉即终止 | 无明确条款 |
| NOTICE 文件 | 衍生作品要保留 NOTICE（§4(d)） | 无此机制 |
| 修改声明 | 修改过的文件要有显著变更声明（§4(b)） | 无 |
| 文件头 | 可选的版权头（附录），不强制 | 无要求 |
| 商标 | 明确不授予商标权（§6） | 未提 |
| 兼容性 | 可以包含 MIT 代码（保留其声明）| 同左 |

### 理由
- 与既有 frontend-design 一致；有专利条款；NOTICE 机制天然适合放第三方署名。
- MIT 上游内容可以放进 Apache-2.0 项目，只要保留 MIT 声明——这就是 `./THIRD_PARTY_NOTICES.md` 必须有的原因。

### 后果 / 风险
- **主人要确认的事**：版权人姓名/年份；是否接受把初始导入的第三方内容按“可能衍生”署名（我无法判断每个技能今天还有多少上游原文，保守处理成本很低）。
- 风险：上游的版权行我是从各自仓库 `main` 分支的 LICENSE 首行读到的；如果上游将来改了版权行，以 T1 提交当天的上游文件为准，T1 里重新核一次。
- 法律意见不在我的范围，本节是工程层面的合规清单，不是法律建议。
- 添加 LICENSE 之后 GitHub 仓库页的 `license` 才会显示为 Apache-2.0（GitHub 自动识别 LICENSE 文本）；这不需要改仓库设置。

---

## 决策 F（补充）：v2.2.1 补打 tag/Release 与 v2.3.0 的发布步骤

### 背景
`main@63c5b70` 的 plugin.json 与 CHANGELOG 都是 2.2.1（见 §0）。既有 tag 是**附注 tag**（`git ls-remote` 都有 `^{}` 行），且指向 PR 合并提交（如 v2.2.0 → `0fc9e9e`，`CHANGELOG.md:16`）。`63c5b70` 同样是 PR #20 的合并提交，符合这一惯例。

### 决定（只是方案，**不执行**）
- T8（SF-Release Manager，无代码改动）：对 `63c5b70` 建附注 tag `v2.2.1`，然后建 GitHub Release `v2.2.1`，说明正文取 `CHANGELOG.md:5-9` 的 2.2.1 条目。
- T5（SF-Release Manager）：T3 合并后，在最新 `main` 上建附注 tag `v2.3.0` 与 Release，正文取 CHANGELOG 的 2.3.0 条目。
- 两者执行前都跑 `python scripts/check-version.py consistency --tag vX.Y.Z`（T2a 落地后；对 v2.2.1 要在 `63c5b70` 的检出里用旧版脚本之外的方式核对，见 TASKS 的 T8 验收）。
- **实际建 tag / Release 必须主人在聊天里逐项明确批准**（建 tag 与建 Release 各算一次）。本任务已确认：我没有执行。
- 历史版本 v2.0.0–v2.2.0 有 tag 无 Release，是否补 Release 不在本次范围。

### 风险
- 如果在 T8 之前 `main` 前进了，tag 仍然应指向 `63c5b70`（已核对该提交就是 2.2.1 的合并提交），用提交 SHA 而不是分支名建 tag。
- 版本脚本检查的是“工作区”，对已落到别的提交上的 tag 不适用，所以 T8 的核对是对 `63c5b70` 检出后人工比对 + 脚本复核两步。

---

## 附：T6 原生宿主验收评估（结论）

> 完整结论也写入任务表的 T6a/T6b。这里是依据。

### 我在盒子里实际做了什么（全部在临时 HOME、临时目录里，用后删除；没有登录任何账号、没有 API key、没有改仓库）
1. `npm install @anthropic-ai/claude-code` 到 `/tmp/cc`（公开 npm 包，版本 **2.1.325**，不需要账号）。
2. `claude plugin validate .`（对 `63c5b70` 的副本）→ **`✔ Validation passed`**；marketplace.json 与 plugin.json 单独校验也 passed；只提示两个“插件目录提交”项：`LICENSE_MISSING`（会被 T1 消除）和 `ICON_MISSING`（警告）。
3. `claude plugin marketplace add <本地路径>` → `claude plugin install devflow@devflow` → `claude plugin list`：**Version: 2.2.1，Status: enabled**；缓存里存在 `skills/devflow/SKILL.md`。
4. 同样的流程换成 GitHub 源 `claude plugin marketplace add GaoFei2025-0314/devflow`：安装成功，Version 2.2.1，enabled。
5. `claude plugin details devflow`：识别出 33 个技能，常驻开销约 1,709 token。
6. `claude -p "hi"` → `Not logged in · Please run /login`：**调用技能需要登录或 API key**。
7. `python3 scripts/install-bundle.py stage … --layout full` + `verify` → `INSTALL VERIFY PASSED: layout=full, 33 skills`。

### 能验证 / 不能验证
| 项目 | 能否在我们的条件下做 | 说明 |
|---|---|---|
| Claude 插件清单结构校验（`claude plugin validate`） | **能，已做** | 无需账号，免费 |
| Claude 通过 CLI 子命令安装插件（本地源 + GitHub 源） | **能，已做** | 这是 CLI 的 `plugin install`，不是交互式 `/plugin` 面板，但走的是同一套安装与缓存机制（我据此推断，没有逐行核对两者代码） |
| 技能被宿主发现、`devflow:devflow` 被调用并路由 | **不能** | 需要模型调用 → 需要 Claude 账号登录或 `ANTHROPIC_API_KEY`（新凭据 + 新费用）。**需主人批准** |
| 交互式 `/plugin` 面板操作 | **不能** | 需要交互式 TUI 与已登录会话 |
| Cursor：结构层面 | **部分能** | Cursor 官方文档说明技能从 `.cursor/skills/`、`.agents/skills/` 加载，也兼容 `.claude/skills/`（<https://cursor.com/docs/skills>）；devflow 的 `SKILL.md` frontmatter 符合该格式。我能校验目录结构与 frontmatter，不能证明 Cursor 真的加载 |
| Cursor：“从 GitHub 仓库导入”插件 | **目前不支持** | 官方文档要求仓库根有 .cursor-plugin/marketplace.json（<https://cursor.com/docs/skills>，<https://cursor.com/docs/reference/plugins>）；devflow 仓库没有。要支持得新增清单，属于新功能且无法在无 GUI 条件下验证，**本次不做**（写进“后续”） |
| Cursor：原生读技能 / 局部返回恢复 | **不能** | 需要 Cursor 桌面端或 CLI 并登录账号；盒子里没有 Cursor，也没有主人的账号。Cursor Cloud Agent 不会自动带用户级技能（上面链接的文档原话），要验证只能把技能放进目标仓库，这仍需要主人的 Cursor 账号与用量 |

**结论（T6）**：
- “原生宿主验收”在我们的条件下**只能完成到“结构校验通过 + CLI 安装成功”这一层**，不能完成“技能被调用的真实验收”，更不能做 Cursor 的原生验收。**不要在 README/host-support.md 里把这两项写成“已验证”。**
- 拆成两个任务：T6a（QA，能做，无费用）把上述盒子证据整理成验收记录；T6b（调用技能的原生验收）**标为“未执行”**，除非主人批准提供凭据/费用，才能做。

### README / host-support.md 改写方案（T4）
用三档标签，且每一行必须带证据链接（相对路径或固定 commit 链接）：

| 档位 | 含义 | 当前归入 |
|---|---|---|
| **已验证** | 有真实宿主运行记录，写明版本、来源、操作 | Claude Code 子代理宿主 2.1.263 的文件读取/路由/命令（`host-support.md:28`，证据在 `docs/devflow/v2-evaluation-summary.md`）；Codex 桌面端（`host-support.md:30,36-57`，范围限于记录的任务与来源）|
| **结构校验通过** | 清单/目录/安装流程通过自动化检查，但没有技能调用记录 | **Claude Code 插件安装**：`claude plugin validate` 通过 + CLI 安装成功（新证据，T6a 产出，写明版本 2.1.325 和日期）；全部宿主的 SKILL.md 格式兼容 |
| **未验证** | 没有任何运行记录 | Codex CLI（`host-support.md:31` 是 blocked）、Cursor（`:32`，用户 2026-09-13 明确推迟）、Copilot CLI、Gemini CLI（`:33-34`） |

具体改动：
1. `docs/devflow/host-support.md`：顶部状态日期改为实际更新日；把“Claude Code plugin installation”那一行从“unverified”升为“结构校验通过”，**其余列仍写 unverified**，并链接 T6a 的记录；新增档位说明小节；保留历史表，不删旧证据。
2. `./README.md`/`./README.zh-CN.md`（T4）：安装节每个宿主标明档位；Cursor 增加一小节，写“支持：把 `skills/` 目录整体放到 `.cursor/skills/` 或 `.agents/skills/`（依据 Cursor 官方文档，**devflow 未做原生验证**）；不支持：从 GitHub 一键导入（缺 .cursor-plugin/marketplace.json）”。注意必须整目录拷贝，因为技能间用 `../<skill>/SKILL.md` 相对链接（`skills/devflow/SKILL.md:23` 等）。
3. `docs/devflow/installation.md`：补一小节 Cursor 手动安装步骤，用仓库已有的 `python scripts/install-bundle.py stage --bundle <repo> --layout full --dest <dir>` 与 `verify`（我实测通过）。
4. docs/devflow/host-verification-v2.3.md（新文件，T6a 写）：记录上面 7 项的命令、版本、输出摘要、日期、未执行项与原因。

### 需要主人批准的事项（T6）
- 为 `claude -p`/技能调用提供 Claude 账号或 `ANTHROPIC_API_KEY`（新凭据、新费用）。
- 任何 Cursor 账号/用量。
- 重跑消融实验（模型费用）。

---

## 决策汇总（需主人批准项）
1. **建 tag/Release**：v2.2.1（T8）、v2.3.0（T5）——每一次执行都要主人在聊天里明确批准。
2. **版权人姓名与年份**（NOTICE）；是否接受第三方“可能衍生”署名处理。
3. **Dependabot（github-actions，monthly）**是否启用。
4. **任何新凭据/费用**：Claude 账号或 API key、Cursor 账号、消融重跑。
5. （建议项，需 Chief 同意）`install-bundle.py` 的 `DISTRIBUTION_ROOT_FILES` 加入 LICENSE/NOTICE/THIRD_PARTY_NOTICES.md。
