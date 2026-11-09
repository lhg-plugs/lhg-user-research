<!-- About 简介（推送后填写到仓库 About 栏）：
小白也能做专业用户调研：定目标→设计问卷→写访谈提纲→分析框架→洞察报告，37 条确定性规则防废卷。 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-user-research
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, ux-research, survey, product, interview, chinese -->

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="lhg-user-research — 小白也能做专业用户调研">
</p>

> **一句话介绍**：小白也能做专业用户调研：定目标→设计问卷→写访谈提纲→分析框架→洞察报告，37 条确定性规则防废卷。

**一键安装**：在 Claude Code 里运行

```bash
/plugin marketplace add lhg-plugs/lhg-user-research
/plugin install lhg-user-research@lhg-plugs
```

## 它能帮你做出什么

每条产出先过确定性脚本自查，再交人工复核清单——数字全部数自仓库里的审计脚本，不靠模型"自觉"。

| 自查脚本 | 规则数 | blocker | warning | nit | 覆盖 |
|---|---|---|---|---|---|
| `scripts/audit/research_audit.py` | 37 | 4 | 27 | 6 | 结构、措辞、量表、样本、隐私、逻辑、质量、分析 |
| **合计** | **37** | **4** | **27** | **6** | |

- **零 LLM 成本**：规则是纯 Python 脚本，零第三方依赖，本地运行。
- **坏 / 好对照可验**：`fixtures/` 里备有坏/好用例，冒烟测试断言命中情况。
- **冒烟全绿**：`python3 smoke_test.py` 46 项全部通过（JSON 合法、frontmatter 完整、命令/skill/agent 齐全）。

## 它是什么

`lhg-user-research` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`interview` 访谈提纲工作坊、`research-audit` 调研自查、`survey` 问卷设计工作坊、`user-research` 用户调研全流程
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：lhg-ur-goal, lhg-ur-insight, lhg-ur-interview, lhg-ur-survey
- **2 个专家 agent**：insight-reviewer, research-designer
- **2 个 hooks**（`hooks/`：post_questionnaire_warn.py, pre_commit_research.py），关键操作前自动把关
- **37 条确定性自查规则**：纯 Python 脚本，见上表

## 为什么是它

不是一个 prompt，而是一套互相兜底的机制：

1. **确定性脚本（机器）+ 人工复核清单（人）**：先跑 `scripts/` 下的审计脚本（共 37 条规则），发现分三级：**blocker**（必须修）、**warning**（修或写豁免理由）、**nit**（顺手修）；再按对应 skill 的复核清单过一遍脚本抓不到的（内容真实性、越权、口径一致）。blocker 清零才算做完；为清零改规则算作弊，不许。
2. **硬门，不是提醒**：hooks 在关键操作前自动拦截或警告（见 `hooks/`），而不是只在文档里写一句"请注意"。
3. **方法论沉淀在 skill 里**：流程、检查清单、口径都写在 `skills/` 的方法论里，命令只是入口；换个 agent 平台也能复用同一套做法。
4. **可验，不是可信**：`fixtures/` 备有坏/好对照用例，`smoke_test.py` 一键验证，规则有没有生效、自己跑一遍就知道。

## 快速上手

```bash
# 1. 安装（Claude Code 里运行）
/plugin marketplace add lhg-plugs/lhg-user-research
/plugin install lhg-user-research@lhg-plugs

# 2. 用户调研全流程：研究目标→问卷设计→访谈提纲→分析框架→洞察报告，一条龙输出可执
/lhg-user-research:user-research "新品满意度"
```

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-user-research:interview` | 访谈提纲工作坊：定访谈对象、写 5~8 个核心问题、配追问与时长规划，输出可直接用的提纲。 | `/lhg-user-research:interview "流失深访" "10"` |
| `/lhg-user-research:research-audit` | 调研自查：先跑 37 条确定性规则脚本，再按人工清单评审问卷与提纲… | `/lhg-user-research:research-audit 方案目录` |
| `/lhg-user-research:survey` | 问卷设计工作坊：搭结构、写题目、过措辞检查、定样本计划，输出可直接发放的问卷。 | `/lhg-user-research:survey "流失原因" "300"` |
| `/lhg-user-research:user-research` | 用户调研全流程：研究目标→问卷设计→访谈提纲→分析框架→洞察报告，一条龙输出可执行的调研方案。 | `/lhg-user-research:user-research "新品满意度"` |

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你需要访谈提纲工作坊时 → 用 `/lhg-user-research:interview`
- 你需要调研自查时 → 用 `/lhg-user-research:research-audit`
- 你需要问卷设计工作坊时 → 用 `/lhg-user-research:survey`

**什么时候不用：**

- 你只需要其中一个零散能力时 → 本插件是成套流程，单点需求用更轻量的 skill 更合适
- 你希望 AI 完全自由发挥、不接受任何自查与硬门时 → 它的规则审计与 hooks 会介入（可关，但那就别装它）
- 你的场景不在上面命令表覆盖范围内时 → 先看命令表，没有对应命令就别硬套

## 目录结构

```
lhg-user-research/
├── smoke_test.py          # 一键冒烟测试
├── ATTRIBUTION.md         # 灵感来源与许可声明
├── LICENSE                # MIT
├── README.md              # 本文件
├── .claude-plugin/
├── agents/
├── commands/
├── fixtures/
├── hooks/
├── scripts/
├── skills/
```

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（本次实测 46 项全部通过）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-user-research/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

同门插件见 [lhg-plugs](https://github.com/lhg-plugs)，86 个插件的完整矩阵在 [marketplace](https://github.com/lhg-plugs/marketplace) 维护。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
