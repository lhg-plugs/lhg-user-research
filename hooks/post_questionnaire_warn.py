#!/usr/bin/env python3
"""lhg-user-research 硬门②（警告级，不拦截）：写问卷发现引导性措辞时提醒。

触发：PostToolUse / Write|Edit。只检查文件名含 survey/问卷/questionnaire/
访谈 的 markdown 文件；发现引导性措辞（难道/大家都认为/你不觉得吗等）
时给出提醒，永远 exit 0。

逃生方式：LHG_UR_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-user-research 停用整个插件。
零第三方依赖。
"""

import json
import os
import re
import sys

Q_NAME_RE = re.compile(r"survey|问卷|questionnaire|访谈", re.I)
LEADING_RES = [
    re.compile(r"难道"),
    re.compile(r"大家都认为"),
    re.compile(r"你不觉得"),
    re.compile(r"显而易见"),
    re.compile(r"众所周知"),
    re.compile(r"不得不说"),
]


def main() -> int:
    if os.environ.get("LHG_UR_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    _, ext = os.path.splitext(file_path)
    if ext.lower() not in (".md", ".markdown", ".txt"):
        return 0
    if not Q_NAME_RE.search(os.path.basename(file_path)):
        return 0  # 非问卷文件：快速放行

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return 0  # 读不到文件：fail-open

    hits = []
    for i, ln in enumerate(lines):
        if any(r.search(ln) for r in LEADING_RES):
            hits.append((i + 1, ln.strip()[:60]))

    if not hits:
        return 0

    msg_lines = [
        "问卷措辞提醒（lhg-user-research）：%s 发现 %d 处疑似引导性措辞，"
        "被引导的答案不是真实想法：" % (os.path.basename(file_path),
                                      len(hits)),
    ]
    for ln_no, snippet in hits[:5]:
        msg_lines.append("  第 %d 行：%s" % (ln_no, snippet))
    msg_lines += [
        "建议改成中性问法；跑 /lhg-user-research:research-audit 可一键检查"
        "全部 37 条规则。",
        "关闭本提醒：export LHG_UR_HOOKS_OFF=1（当前会话有效）。",
    ]
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(msg_lines),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
