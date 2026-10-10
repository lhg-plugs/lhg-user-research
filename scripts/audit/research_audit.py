#!/usr/bin/env python3
"""lhg-user-research 确定性问卷审计：37 条规则，零第三方依赖。

扫描目标目录下的问卷文档（*.md），检查：
  结构完整性（编号/知情同意/人口学/结束语）、题目措辞（引导性/双重否定/
  一题多问）、量表规范、样本量与抽样、隐私合规、逻辑跳转、
  防废卷机制、分析计划。

用法：
    python3 research_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。
规则文案均为本项目原创。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-user-research/research-audit"

SKIP_DIRS = {
    "node_modules", ".next", "dist", "build", ".git", "coverage",
    "__pycache__", "vendor", ".turbo", "out", "fixtures",
}
SCAN_EXTS = {".md", ".markdown", ".txt"}

QUESTION_LINE_RE = re.compile(r"^\s*(Q\d+|\d+[.、])\s*\S")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file",
                 "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def _mk(rule_id, path, line, snippet):
    r = _RULE_BY_ID[rule_id]
    return Finding(r["id"], r["severity"], r["category"], r["title"],
                   path, line, snippet[:160], r["detail"])


def collect_files(target):
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            _, ext = os.path.splitext(f)
            if ext in SCAN_EXTS:
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _q_lines(lines):
    """题目行：编号开头的行，或以？结尾的行。"""
    return [(i + 1, ln.strip()) for i, ln in enumerate(lines)
            if QUESTION_LINE_RE.match(ln) or ln.strip().endswith(("？", "?"))]


def _has_scale_ctx(text):
    return bool(re.search(r"打分|评分|量表|非常同意|非常满意", text))


# ================================================================ 结构规则

@rule("UR-STRUCT-001", "warning", "结构", "题目无编号",
      "题目没有编号。没有编号，数据分析时对不上题，访谈追问也说不清：给每道题编上 Q1、Q2……")
def _s001(lines, text, path, ctx):
    qs = _q_lines(lines)
    if qs and not any(QUESTION_LINE_RE.match(ln) for _, ln in qs):
        return [_mk("UR-STRUCT-001", path, qs[0][0], qs[0][1])]
    return []


@rule("UR-STRUCT-002", "warning", "结构", "缺开场白/知情同意",
      "问卷没有开场白与知情同意说明。用户不知道这是什么调研、数据怎么用，信任度和回收质量都会打折：加上调研目的、保密承诺、预计用时。")
def _s002(lines, text, path, ctx):
    if not re.search(r"知情同意|调研目的|本次调研|本问卷旨在", text):
        return [_mk("UR-STRUCT-002", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-STRUCT-003", "warning", "结构", "缺结束语",
      "问卷没有结束语。用户答完戛然而止，体验差：加一句感谢语，顺便可以放抽奖/结果订阅入口。")
def _s003(lines, text, path, ctx):
    if not re.search(r"感谢.*(参与|填写)|谢谢参与|问卷到此结束", text):
        return [_mk("UR-STRUCT-003", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-STRUCT-004", "warning", "结构", "缺人口学题目",
      "问卷没有人口学题目（性别/年龄/职业/城市等）。没有人口学维度，做不了交叉分析，结论只能是总体平均：至少加上性别、年龄、职业。")
def _s004(lines, text, path, ctx):
    if not re.search(r"性别|年龄|职业|城市|学历", text):
        return [_mk("UR-STRUCT-004", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-STRUCT-005", "warning", "结构", "未声明预计用时",
      "问卷没写预计用时。用户不知道要填多久，中途弃答率会升高：写清预计用时（如\"约 5 分钟\"）。")
def _s005(lines, text, path, ctx):
    if not re.search(r"预计.{0,6}分钟|大约.{0,6}分钟|用时.{0,6}分钟", text):
        return [_mk("UR-STRUCT-005", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-STRUCT-006", "nit", "结构", "无问卷版本标识",
      "问卷没有版本标识。改了两版问卷，数据对不上都不知道是哪版的：加上版本号与日期。")
def _s006(lines, text, path, ctx):
    if not re.search(r"版本|v\d+\.\d+|20\d\d[-年]\d+", text):
        return [_mk("UR-STRUCT-006", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-STRUCT-007", "warning", "结构", "无配额/样本结构说明",
      "问卷没写样本配额或样本结构。回收时不控制结构，样本会偏向某一类人群：写清配额要求（如男女比例、年龄分布）。")
def _s007(lines, text, path, ctx):
    if not re.search(r"配额|样本结构|男女比例", text):
        return [_mk("UR-STRUCT-007", path, 1, lines[0] if lines else "")]
    return []


# ================================================================ 措辞规则

@rule("UR-BIAS-001", "blocker", "措辞", "引导性措辞",
      "题目用了引导性措辞（\"大家都认为\"\"你不觉得吗\"等）。被引导的答案不是真实想法，数据直接作废：改成中性问法。")
def _b001(lines, text, path, ctx):
    pats = [r"大家都认为", r"显而易见", r"众所周知", r"你不觉得",
            r"不得不说", r"想必你也"]
    out = []
    for i, ln in enumerate(lines):
        if any(re.search(p, ln) for p in pats):
            out.append(_mk("UR-BIAS-001", path, i + 1, ln.strip()))
    return out


@rule("UR-BIAS-002", "blocker", "措辞", "双重否定/反问施压",
      "题目用了双重否定或反问施压（\"难道\"\"不得不承认\"）。用户要么看不懂，要么被压着选一边：拆成直接的中性问法。")
def _b002(lines, text, path, ctx):
    pats = [r"难道", r"不得不承认", r"不是.*吗？"]
    out = []
    for i, ln in enumerate(lines):
        if any(re.search(p, ln) for p in pats):
            out.append(_mk("UR-BIAS-002", path, i + 1, ln.strip()))
    return out


@rule("UR-BIAS-003", "warning", "措辞", "一题多问",
      "一道题里问了两个维度的事（如\"性能和外观都满意吗\"）。用户对 A 满意对 B 不满意时没法答：拆成两道题。")
def _b003(lines, text, path, ctx):
    out = []
    for ln_no, ln in _q_lines(lines):
        if re.search(r"\S{2,8}和\S{2,8}(满意|认同|支持|喜欢|重要|方便)", ln):
            out.append(_mk("UR-BIAS-003", path, ln_no, ln))
    return out


@rule("UR-BIAS-004", "warning", "措辞", "情绪化措辞",
      "题目带情绪化措辞（\"糟糕\"\"完美\"\"极致\"）。情绪词会污染用户的判断：换成中性描述。")
def _b004(lines, text, path, ctx):
    out = []
    for ln_no, ln in _q_lines(lines):
        if re.search(r"糟糕|垃圾|完美|极致|超棒|差劲", ln):
            out.append(_mk("UR-BIAS-004", path, ln_no, ln))
    return out


@rule("UR-BIAS-005", "warning", "措辞", "绝对化措辞",
      "题目用了\"总是\"\"从不\"\"所有\"等绝对化措辞。绝对化让用户难以作答，数据失真：改成频率词（\"经常\"\"偶尔\"）。")
def _b005(lines, text, path, ctx):
    out = []
    for ln_no, ln in _q_lines(lines):
        if re.search(r"总是|从不|所有.+都|每个.+都", ln):
            out.append(_mk("UR-BIAS-005", path, ln_no, ln))
    return out


@rule("UR-BIAS-006", "warning", "措辞", "专业术语未解释",
      "题目出现专业术语（NPS/ROI 等）却没解释。用户看不懂就会乱填：要么换成人话，要么在术语后加括号解释。")
def _b006(lines, text, path, ctx):
    terms = ["NPS", "ROI", "CAC", "KPI", "DAU", "UV", "PV"]
    out = []
    for i, ln in enumerate(lines):
        for t in terms:
            m = re.search(t, ln)
            if m and "（" not in ln[m.end():m.end() + 15]:
                out.append(_mk("UR-BIAS-006", path, i + 1, ln.strip()))
                break
    return out


@rule("UR-BIAS-007", "nit", "措辞", "题干过长",
      "题干超过 60 字。题干太长用户读不完：拆成题干+说明，或精简。")
def _b007(lines, text, path, ctx):
    out = []
    for ln_no, ln in _q_lines(lines):
        if len(ln) > 60:
            out.append(_mk("UR-BIAS-007", path, ln_no, ln))
    return out


# ================================================================ 量表规则

@rule("UR-SCALE-001", "warning", "量表", "打分题无刻度说明",
      "有打分/评分题却没说明刻度。用户不知道 5 分是满分还是及格：写清刻度（如\"5分制：1=非常不同意，5=非常同意\"）。")
def _sc001(lines, text, path, ctx):
    if re.search(r"打分|评分", text) and not re.search(
            r"5分制|7分制|10分制|1-5|1~5|非常同意|非常满意", text):
        return [_mk("UR-SCALE-001", path, 1, "打分题无刻度说明")]
    return []


@rule("UR-SCALE-002", "warning", "量表", "量表题少于 3 道",
      "量表题少于 3 道。单题量表信度不够，一个维度至少 3 道题才能做信度检验：补充题项。")
def _sc002(lines, text, path, ctx):
    if not _has_scale_ctx(text):
        return []
    n = sum(1 for i, ln in enumerate(lines)
            if QUESTION_LINE_RE.match(ln)
            and re.search(r"同意|满意|愿意|认同", ln))
    if n < 3:
        return [_mk("UR-SCALE-002", path, 1, "量表题仅 %d 道" % n)]
    return []


# ================================================================ 样本规则

@rule("UR-SAMPLE-001", "blocker", "样本", "样本量不足 30",
      "样本量不足 30。30 以下做任何统计推断都不成立：要么加大回收量，要么改做定性访谈。")
def _sa001(lines, text, path, ctx):
    m = re.search(r"样本量\D{0,6}(\d+)", text)
    if m and int(m.group(1)) < 30:
        return [_mk("UR-SAMPLE-001", path, 1,
                    "样本量 %s < 30" % m.group(1))]
    return []


@rule("UR-SAMPLE-002", "warning", "样本", "样本量不足 100",
      "样本量不足 100。做交叉分析、细分人群对比时，100 以下分组后每格人数太少：尽量回收到 100+。")
def _sa002(lines, text, path, ctx):
    m = re.search(r"样本量\D{0,6}(\d+)", text)
    if m and 30 <= int(m.group(1)) < 100:
        return [_mk("UR-SAMPLE-002", path, 1,
                    "样本量 %s < 100" % m.group(1))]
    return []


@rule("UR-SAMPLE-003", "warning", "样本", "未声明抽样/招募方式",
      "没写抽样或招募方式。不知道样本怎么来的，就不知道结论能推广到谁：写清是随机抽样、配额还是滚雪球。")
def _sa003(lines, text, path, ctx):
    if not re.search(r"抽样|招募|随机|配额|滚雪球|分发渠道", text):
        return [_mk("UR-SAMPLE-003", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-SAMPLE-004", "warning", "样本", "未声明样本量",
      "没写计划样本量。没有目标回收量，回收工作没有锚：写清计划回收多少份。")
def _sa004(lines, text, path, ctx):
    if "样本量" not in text:
        return [_mk("UR-SAMPLE-004", path, 1, lines[0] if lines else "")]
    return []


# ================================================================ 隐私规则

@rule("UR-PRIVACY-001", "blocker", "隐私", "收集联系方式无隐私声明",
      "收集手机号/身份证等个人信息，却没有隐私声明。合规红线：必须写清用途、保密承诺与自愿原则，否则删掉该题。")
def _pr001(lines, text, path, ctx):
    if re.search(r"手机号|手机号码|身份证|微信号", text) and not re.search(
            r"隐私|保密|匿名|仅用于研究|不会泄露|自愿", text):
        ln_no = next((i + 1 for i, ln in enumerate(lines)
                      if re.search(r"手机号|手机号码|身份证|微信号", ln)), 1)
        return [_mk("UR-PRIVACY-001", path, ln_no, "收集个人信息无隐私声明")]
    return []


@rule("UR-PRIVACY-002", "warning", "隐私", "收集收入信息无用途说明",
      "收集收入信息却没说明用途。收入是敏感信息，用户会警惕：注明\"仅用于人群分群分析\"，或改为收入区间选择题。")
def _pr002(lines, text, path, ctx):
    if re.search(r"月收入|年收入|收入水平|收入范围", text) and not re.search(
            r"仅用于|用途|分群分析", text):
        return [_mk("UR-PRIVACY-002", path, 1, "收入题无用途说明")]
    return []


# ================================================================ 逻辑规则

@rule("UR-LOGIC-001", "warning", "逻辑", "筛选题无跳转说明",
      "有筛选题却没写跳转逻辑。不符合条件的用户不知道该继续还是退出：写清\"是→跳至 Qx / 否→结束作答\"。")
def _l001(lines, text, path, ctx):
    if "筛选" in text and not re.search(r"跳转|跳过|结束作答|跳至", text):
        return [_mk("UR-LOGIC-001", path, 1, "筛选题无跳转说明")]
    return []


@rule("UR-LOGIC-002", "warning", "逻辑", "开放题占比过高",
      "开放题占比超过 40%。开放题分析成本高、回收率低：开放题控制在 2~3 道，其余转选择题。")
def _l002(lines, text, path, ctx):
    qs = [ln for _, ln in _q_lines(lines) if QUESTION_LINE_RE.match(ln)]
    if len(qs) >= 5:
        n_open = sum(1 for ln in qs
                     if re.search(r"请说明|请描述|请举例|为什么", ln))
        if n_open / len(qs) > 0.4:
            return [_mk("UR-LOGIC-002", path, 1,
                        "开放题 %d/%d 道" % (n_open, len(qs)))]
    return []


@rule("UR-LOGIC-003", "nit", "逻辑", "选项含\"以上都是\"",
      "选项出现\"以上都是/以上都不是\"。这类选项通常意味着单选多选没想清楚：检查题型，必要时拆题。")
def _l003(lines, text, path, ctx):
    if re.search(r"以上都是|以上都不是", text):
        return [_mk("UR-LOGIC-003", path, 1, "选项含\"以上都是\"")]
    return []


# ================================================================ 质量规则

@rule("UR-QUAL-001", "warning", "质量", "无防废卷机制",
      "没有防废卷机制（注意力检测题/作答时长下限/反向题）。没有质检的回收，废卷会污染结论：至少加一道注意力检测题和最短作答时长。")
def _q001(lines, text, path, ctx):
    if not re.search(r"注意力检测|反向题|作答时长|废卷|最短.*秒", text):
        return [_mk("UR-QUAL-001", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-QUAL-002", "warning", "质量", "必答题未标记",
      "题目没有必答/选答标记。用户不知道哪些必须填，关键题空着交上来：每道题标注（必答/选答）。")
def _q002(lines, text, path, ctx):
    if _q_lines(lines) and not re.search(r"必答|必填|\*", text):
        return [_mk("UR-QUAL-002", path, 1, "题目无必答标记")]
    return []


@rule("UR-QUAL-003", "nit", "质量", "缺问卷编号追踪",
      "没有问卷编号。回收后想追查某份异常问卷时找不到：加上问卷编号。")
def _q003(lines, text, path, ctx):
    if not re.search(r"问卷编号|问卷ID|编号[:：]", text):
        return [_mk("UR-QUAL-003", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-QUAL-004", "warning", "质量", "无逻辑一致性检查",
      "没写逻辑一致性检查。前后矛盾的作答（如 Q3 选\"没用过\"Q7 却打分）识别不出来：加上一致性校验规则。")
def _q004(lines, text, path, ctx):
    if not re.search(r"一致性|逻辑校验|矛盾作答", text):
        return [_mk("UR-QUAL-004", path, 1, lines[0] if lines else "")]
    return []


# ================================================================ 分析规则

@rule("UR-ANALYSIS-001", "warning", "分析", "缺交叉分析维度",
      "分析计划没有交叉/分群维度。只看总体平均，等于把最有价值的差异藏起来了：至少规划 1~2 个交叉维度（性别×满意度等）。")
def _a001(lines, text, path, ctx):
    if not re.search(r"交叉|分群|对比分析|细分人群", text):
        return [_mk("UR-ANALYSIS-001", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-ANALYSIS-002", "warning", "分析", "缺统计方法说明",
      "分析计划没写统计方法。方法不定，回收的数据可能不够用（如想做显著性检验却没留对照组）：写清描述统计/显著性检验等方法。")
def _a002(lines, text, path, ctx):
    if not re.search(r"描述统计|显著性|卡方|t检验|回归分析|相关分析", text):
        return [_mk("UR-ANALYSIS-002", path, 1, lines[0] if lines else "")]
    return []


@rule("UR-ANALYSIS-003", "nit", "分析", "缺信效度说明",
      "有量表题却没提信效度检验。量表不做信度检验，分数可不可信不知道：加上 Cronbach α 等信度说明。")
def _a003(lines, text, path, ctx):
    if _has_scale_ctx(text) and not re.search(r"信度|效度|Cronbach", text):
        return [_mk("UR-ANALYSIS-003", path, 1, "量表无信效度说明")]
    return []


@rule("UR-ANALYSIS-004", "nit", "分析", "开放题无编码方案",
      "有开放题却没写编码/归类方案。开放题不编码就是一堆文本，没法进报告：写清主题编码归类方法。")
def _a004(lines, text, path, ctx):
    if re.search(r"开放题", text) and not re.search(r"编码|归类|主题分析", text):
        return [_mk("UR-ANALYSIS-004", path, 1, "开放题无编码方案")]
    return []


# ================================================================ 访谈规则（仅当含访谈提纲时）

@rule("UR-INTV-001", "warning", "访谈", "访谈问题少于 5 个",
      "访谈提纲问题少于 5 个。问题太少，30 分钟访谈撑不起来：补充到 5~8 个核心问题。")
def _i001(lines, text, path, ctx):
    if "访谈提纲" not in text:
        return []
    n = sum(1 for ln in lines if QUESTION_LINE_RE.match(ln))
    if n < 5:
        return [_mk("UR-INTV-001", path, 1, "访谈问题仅 %d 个" % n)]
    return []


@rule("UR-INTV-002", "warning", "访谈", "访谈无暖场问题",
      "访谈提纲没有暖场问题。一上来就问核心问题，用户放不开：加 1~2 道暖场题（如\"先聊聊您平时怎么用这类产品\"）。")
def _i002(lines, text, path, ctx):
    if "访谈提纲" in text and not re.search(r"暖场|破冰|先聊聊", text):
        return [_mk("UR-INTV-002", path, 1, "访谈无暖场问题")]
    return []


@rule("UR-INTV-003", "warning", "访谈", "访谈无追问提示",
      "访谈提纲没有追问提示。用户只答一句话时，主持人不知道怎么深挖：每个核心问题配 1~2 个追问（如\"能举个例子吗\"\"当时为什么这么选\"）。")
def _i003(lines, text, path, ctx):
    if "访谈提纲" in text and not re.search(r"追问|能举个例子|为什么|展开说说", text):
        return [_mk("UR-INTV-003", path, 1, "访谈无追问提示")]
    return []


@rule("UR-INTV-004", "warning", "访谈", "访谈无时长规划",
      "访谈提纲没写时长规划。没计时，访谈容易前松后紧、核心问题没时间问：标注每部分用时，总时长 30~45 分钟。")
def _i004(lines, text, path, ctx):
    if "访谈提纲" in text and not re.search(r"\d+\s*分钟", text):
        return [_mk("UR-INTV-004", path, 1, "访谈无时长规划")]
    return []


# ================================================================ 主流程

SEVERITY_ORDER = {"blocker": 0, "warning": 1, "nit": 2}


def audit_file(path):
    text = read_text(path)
    lines = text.split("\n")
    ctx = {}
    findings = []
    for r in RULES:
        try:
            findings.extend(r["check"](lines, text, path, ctx) or [])
        except Exception:
            continue  # 单条规则出错不影响整体
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line))
    return findings


def main():
    ap = argparse.ArgumentParser(description="lhg-user-research 问卷确定性审计")
    ap.add_argument("--target", required=True, help="待扫描目录")
    ap.add_argument("--format", default="text", choices=["json", "text"])
    ap.add_argument("--fail-on", default="blocker",
                    choices=["blocker", "warning", "nit"])
    args = ap.parse_args()

    files = collect_files(args.target)
    all_findings = []
    for p in files:
        all_findings.extend(audit_file(p))

    sev_count = {"blocker": 0, "warning": 0, "nit": 0}
    for f in all_findings:
        sev_count[f.severity] += 1

    summary = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "files_scanned": len(files),
        "rules_run": len(RULES),
        "blocker": sev_count["blocker"],
        "warning": sev_count["warning"],
        "nit": sev_count["nit"],
        "total": len(all_findings),
    }

    if args.format == "json":
        print(json.dumps({"summary": summary,
                          "findings": [f.to_dict() for f in all_findings]},
                         ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("lhg-user-research 问卷审计报告  v%s" % VERSION)
        print("=" * 60)
        print("扫描文件: %d  运行规则: %d" % (len(files), len(RULES)))
        print("blocker: %d  warning: %d  nit: %d" %
              (sev_count["blocker"], sev_count["warning"], sev_count["nit"]))
        print("-" * 60)
        cur = None
        for f in all_findings:
            if f.severity != cur:
                cur = f.severity
                print("\n[%s]" % cur.upper())
            print("  %s %s:%d" % (f.rule_id, os.path.basename(f.file), f.line))
            print("    %s" % f.title)
            if f.snippet:
                print("    > %s" % f.snippet)
        if not all_findings:
            print("\n未发现问题，问卷结构完整。")

    threshold = SEVERITY_ORDER[args.fail_on]
    bad = any(SEVERITY_ORDER[f.severity] <= threshold for f in all_findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
