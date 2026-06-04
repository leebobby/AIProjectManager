"""Excel 导出工具：专项/攻关导出为美观的单页表格（华为红风格）。

依赖：openpyxl
"""
import io
import json
import re
from datetime import datetime
from typing import List

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# 华为红主题
_BRAND = "C7000B"
_BRAND_DARK = "9E0009"
_SECTION = "FBEAEA"      # 章节标题底色（浅红）
_ZEBRA = "FBF4F4"        # 斑马底色
_BORDER_RGB = "E3C9CB"

_FONT = "微软雅黑"

_MS_STATUS_LABEL = {
    "planning": "未开始", "in_progress": "进行中", "done": "已完成", "delayed": "已延期",
}
_STATUS_FONT = {
    "已完成": "2E7D32", "进行中": "1565C0", "已延期": "C62828",
    "已变更": "B96A00", "未开始": "909399", "已闭环": "2E7D32",
}

_thin = Side(style="thin", color=_BORDER_RGB)
_BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)


def _strip_html(s: str) -> str:
    if not s:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    text = re.sub(r"</\s*(p|div|h\d|li|tr)\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _kind_label(kind: str) -> str:
    return "攻关" if kind == "assault" else "专项"


def build_special_xlsx(special) -> io.BytesIO:
    """传入 Special ORM（含 content/tasks/risks），返回美观 xlsx 的 BytesIO。"""
    label = _kind_label(special.kind)
    content = special.content
    wb = Workbook()
    ws = wb.active
    ws.title = label
    ws.sheet_view.showGridLines = False

    NCOL = 6
    last_col = get_column_letter(NCOL)
    col_widths = [8, 30, 30, 12, 14, 12]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    row = 1

    def merge_row(r, text, *, fill=None, font_color="262626", bold=False, size=11,
                  align="left", height=None, italic=False):
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NCOL)
        c = ws.cell(row=r, column=1, value=text)
        c.font = Font(name=_FONT, bold=bold, size=size, color=font_color, italic=italic)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
        if fill:
            for col in range(1, NCOL + 1):
                ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor=fill)
        if height:
            ws.row_dimensions[r].height = height

    # ===== 标题条 =====
    merge_row(row, f"【{label}周报】{special.name or ''}", fill=_BRAND_DARK,
              font_color="FFFFFF", bold=True, size=16, height=30)
    row += 1
    merge_row(row, f"责任人：{special.owner or '-'}    导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
              fill=_BRAND, font_color="FFFFFF", size=10, height=20)
    row += 2

    def section(title):
        nonlocal row
        merge_row(row, title, fill=_SECTION, font_color=_BRAND_DARK, bold=True, size=12, height=22)
        row += 1

    def text_block(text):
        nonlocal row
        merge_row(row, text or "—", height=None)
        ws.cell(row=row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = max(20, min(160, 16 * (1 + (text or "").count("\n"))))
        row += 1

    def table(headers, data_rows, status_col=None):
        nonlocal row
        for j, h in enumerate(headers, start=1):
            c = ws.cell(row=row, column=j, value=h)
            c.fill = PatternFill("solid", fgColor=_BRAND)
            c.font = Font(name=_FONT, bold=True, color="FFFFFF", size=10)
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = _BORDER
        ws.row_dimensions[row].height = 20
        row += 1
        for i, dr in enumerate(data_rows):
            zebra = i % 2 == 1
            maxlines = 1
            for j, val in enumerate(dr, start=1):
                sval = "" if val is None else str(val)
                maxlines = max(maxlines, 1 + sval.count("\n"))
                c = ws.cell(row=row, column=j, value=sval)
                fcolor = "262626"
                if status_col is not None and j == status_col and sval.strip() in _STATUS_FONT:
                    fcolor = _STATUS_FONT[sval.strip()]
                c.font = Font(name=_FONT, size=10, color=fcolor,
                              bold=(status_col is not None and j == status_col))
                c.alignment = Alignment(
                    horizontal="center" if (j == 1 or j == status_col) else "left",
                    vertical="center", wrap_text=True)
                c.border = _BORDER
                if zebra:
                    c.fill = PatternFill("solid", fgColor=_ZEBRA)
            ws.row_dimensions[row].height = max(18, min(120, 15 * maxlines))
            row += 1

    # ===== 目标 =====
    section(f"一、{label}目标")
    text_block(_strip_html(content.goal) if content else "")

    # ===== 整体进展 =====
    section("二、整体进展")
    text_block(_strip_html(content.progress_summary) if content else "")

    # ===== 求助 =====
    section("三、求助")
    text_block(_strip_html(content.help_request) if content else "")

    # ===== 里程碑 =====
    milestones = []
    if content and content.milestones_json:
        try:
            milestones = json.loads(content.milestones_json) or []
        except (ValueError, TypeError):
            milestones = []
    section(f"四、{label}计划（里程碑）")
    if milestones:
        rows = [[m.get("name", ""), m.get("date", ""),
                 _MS_STATUS_LABEL.get(m.get("status", "planning"), m.get("status", ""))]
                for m in milestones]
        # 里程碑用前 3 列：单独画一张 3 列表
        _mini_table(ws, row, ["里程碑", "日期", "状态"], rows, status_col=3)
        row += 1 + len(rows)
    else:
        text_block("—")

    # ===== 风险（调整到事务之前）=====
    section("五、风险和问题")
    risks = special.risks or []
    if risks:
        rrows = []
        for idx, r in enumerate(risks, 1):
            st = "已闭环" if (r.status or "open") == "closed" else "进行中"
            rrows.append([idx, _strip_html(r.content), _strip_html(r.progress),
                          r.owner or "", r.planned_close_date or "", st])
        table(["序号", "问题内容", "当前进展", "责任人", "计划闭环", "状态"], rrows, status_col=6)
    else:
        text_block("—")

    # ===== 事务 =====
    section(f"六、{label}事务")
    tasks = sorted(special.tasks or [], key=lambda t: (t.sort_order or 0, t.id))
    if tasks:
        trows = []
        for idx, t in enumerate(tasks, 1):
            st = "已闭环" if (t.status or "open") == "closed" else "进行中"
            trows.append([idx, _strip_html(t.content), _strip_html(t.progress),
                          t.owner or "", t.planned_close_date or "", st])
        table(["序号", "事务内容", "当前进展", "责任人", "计划闭环", "状态"], trows, status_col=6)
    else:
        text_block("—")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _mini_table(ws, start_row, headers, data_rows, status_col=None):
    """在前 len(headers) 列画一张小表（里程碑用）。"""
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=start_row, column=j, value=h)
        c.fill = PatternFill("solid", fgColor=_BRAND)
        c.font = Font(name=_FONT, bold=True, color="FFFFFF", size=10)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = _BORDER
    ws.row_dimensions[start_row].height = 20
    for i, dr in enumerate(data_rows):
        r = start_row + 1 + i
        zebra = i % 2 == 1
        for j, val in enumerate(dr, start=1):
            sval = "" if val is None else str(val)
            c = ws.cell(row=r, column=j, value=sval)
            fcolor = "262626"
            if status_col is not None and j == status_col and sval.strip() in _STATUS_FONT:
                fcolor = _STATUS_FONT[sval.strip()]
            c.font = Font(name=_FONT, size=10, color=fcolor,
                          bold=(status_col is not None and j == status_col))
            c.alignment = Alignment(horizontal="center" if j != 1 else "left",
                                    vertical="center", wrap_text=True)
            c.border = _BORDER
            if zebra:
                c.fill = PatternFill("solid", fgColor=_ZEBRA)
