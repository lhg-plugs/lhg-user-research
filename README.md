<!-- About 简介（推送后填写到仓库 About 栏）：
小白也能做专业用户调研：目标→问卷→访谈→分析→洞察报告一条龙 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-user-research
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, ux-research, survey, product -->

# lhg-user-research：用户调研专家

> **一句话介绍**：给 AI 助手装上"用户调研全流程"——定研究目标、设计问卷、写访谈提纲、搭分析框架、出洞察报告，小白也能做出专业水准的用户调研。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-user-research
> /plugin install lhg-user-research@lhg-plugs
> ```

## 它是什么

`lhg-user-research` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`user-research` 五步全流程一条龙，`survey` 问卷设计工作坊，`interview` 访谈提纲工作坊，`research-audit` 调研自查
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：研究目标与抽样、问卷设计、用户访谈、数据分析与洞察报告
- **2 个专家 agent**：调研设计专家、独立审查专家
- **2 个硬门 hooks**：commit 前问卷审计拦截、写问卷发现引导性措辞提醒（均可一键豁免）
- **37 条确定性审计规则**：纯 Python、零第三方依赖，查措辞引导、量表规范、样本量、隐私合规、逻辑跳转、防废卷、分析计划

差异化：**先定分析计划再写题**（题目→分析映射表，"顺便问问"的题直接拦下）、**措辞七戒机器检查**（引导性/双重否定/一题多问，脚本直接报警）、**洞察三要素**（发现+证据+行动，每条洞察标注证据强度，反例必须写进局限）。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-user-research:user-research` | 目标→问卷→访谈→分析→洞察报告，一条龙输出完整调研方案 | `/lhg-user-research:user-research "新品满意度"` |
| `/lhg-user-research:survey` | 问卷设计工作坊：搭结构、写题目、措辞检查、定样本计划 | `/lhg-user-research:survey "流失原因" "300"` |
| `/lhg-user-research:interview` | 访谈提纲工作坊：五段式提纲+追问话术库+时长规划 | `/lhg-user-research:interview "流失深访" "10"` |
| `/lhg-user-research:research-audit` | 37 条规则审计 + 人工评审清单（含认知走查） | `/lhg-user-research:research-audit 方案目录` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审（人）：

1. 先跑 `scripts/audit/research_audit.py`（37 条规则），零 LLM 成本；
2. 发现分三级：**blocker**（数据作废级：引导性措辞、样本量<30、无隐私声明，commit 前 hook 会拦截）、**warning**（大概率是坑）、**nit**（洁癖项）；
3. 再按人工清单过一遍脚本抓不到的（认知走查：找 3 个真实用户读一遍问卷、跳转逻辑实测、访谈提纲试讲）。

blocker 清零才算做完；为清零改规则算作弊，不许。

## 目录结构

```
lhg-user-research/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：user-research / survey / interview / research-audit
├── skills/                  # 4 个平台中立 skill（goal/survey/interview/insight）
├── agents/                  # 2 个专家 agent（research-designer / insight-reviewer）
├── hooks/                   # 2 个硬门（commit 前审计拦截 / 引导性措辞提醒）+ 豁免说明
├── scripts/audit/           # 37 条确定性审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你想做一次用户调研（满意度/流失原因/新功能验证），但不知道从哪下手时 → 用 `/lhg-user-research:user-research` 一条龙
- 问卷草稿写完了，怕有引导性措辞、样本量不够这类硬伤时 → 跑 `/lhg-user-research:research-audit`
- 你只想做几场用户深访，挖"为什么"时 → 用 `/lhg-user-research:interview`（含追问话术库）
- 你是产品/运营，想给团队立一套"问卷发放前必须检查"的纪律时 → 它的 hooks 硬门开箱即用

**什么时候不用：**

- 你只是想在群里随手发个投票（"今晚吃啥"）→ 杀鸡不用牛刀，本插件是正式调研的全流程
- 你的研究不需要问卷/访谈（如只做数据分析）→ 问卷与访谈 skill 用不上，但抽样设计与洞察报告方法论仍可参考
- 你希望 AI 无条件按你的问法出问卷、不接受"这题有引导性"的打回 → 它的措辞零容忍会让你烦（这是设计，不是 bug）

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-user-research](https://github.com/lhg-plugs/lhg-user-research) | 用户调研专家：目标→问卷→访谈→分析→洞察报告，小白也能做专业调研 | `/plugin install lhg-user-research@lhg-plugs` |
| *（后续插件在此追加，保持表格格式一致）* | | |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、37 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-user-research/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
