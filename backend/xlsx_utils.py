"""Excel 导出工具：专项/攻关导出为美观、整洁、可直接使用的单页表格（华为红风格）。

依赖：openpyxl

设计要点（解决"导出很乱"）：
- 全表统一 6 列（A–F）网格，列宽固定且合理；
- 标题 / 章节 / 叙述段落统一横跨 A–F 合并，表格按"逻辑列→物理列合并"对齐；
- 里程碑这种窄表通过合并映射到 6 列，避免落在过窄的列里串味；
- 单元格统一自动换行 + 按内容估算行高，长文本不再溢出/挤压。
"""
import io
import json
import math
import re
from datetime import datetime

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

# 6 列网格列宽（字符单位）
_COL_WIDTHS = [6, 36, 30, 12, 14, 10]
_NCOL = len(_COL_WIDTHS)

_MS_STATUS_LABEL = {
    "planning": "未开始", "in_progress": "进行中", "done": "已完成", "delayed": "已延期",
}
_STATUS_FONT = {
    "已完成": "2E7D32", "进行中": "1565C0", "已延期": "C62828",
    "已变更": "B96A00", "未开始": "909399", "已闭环": "2E7D32",
}
_STATUS_FILL = {
    "已闭环": "EAF6EA", "已完成": "EAF6EA",
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


def _disp_w(s: str) -> int:
    """显示宽度：CJK 记 2，其余记 1。"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)


def _cell_lines(text: str, capacity: int) -> int:
    cap = max(capacity, 4)
    lines = 0
    for seg in str(text or "").split("\n"):
        lines += max(1, math.ceil(_disp_w(seg) / cap))
    return max(1, lines)


def build_special_xlsx(special) -> io.BytesIO:
    """传入 Special ORM（含 content/tasks/risks），返回美观 xlsx 的 BytesIO。"""
    label = _kind_label(special.kind)
    content = special.content
    wb = Workbook()
    ws = wb.active
    ws.title = label
    ws.sheet_view.showGridLines = False

    for i, w in enumerate(_COL_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    state = {"row": 1}

    def _fill(r, c1, c2, color):
        for c in range(c1, c2 + 1):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=color)

    def band(text, *, fill=None, font_color="262626", bold=False, size=11,
             align="left", height=20, italic=False, wrap=True):
        r = state["row"]
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=_NCOL)
        c = ws.cell(row=r, column=1, value=text)
        c.font = Font(name=_FONT, bold=bold, size=size, color=font_color, italic=italic)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
        if fill:
            _fill(r, 1, _NCOL, fill)
        ws.row_dimensions[r].height = height
        state["row"] += 1

    def section(title):
        band(title, fill=_SECTION, font_color=_BRAND_DARK, bold=True, size=12, height=22)

    def narrative(text):
        r = state["row"]
        text = text or "—"
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=_NCOL)
        c = ws.cell(row=r, column=1, value=text)
        c.font = Font(name=_FONT, size=11, color="262626")
        c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        c.border = _BORDER
        cap = sum(_COL_WIDTHS) - 2
        ws.row_dimensions[r].height = max(20, min(260, _cell_lines(text, cap) * 16 + 4))
        state["row"] += 1

    def gap():
        state["row"] += 1

    def table(col_specs, headers, rows, status_col=None, center_cols=None):
        """col_specs: [(c1,c2), ...] 每个逻辑列在 6 列网格中的物理列区间。
        status_col: 逻辑列下标（从 0 起），该列文字按状态着色 + 整行变浅绿。
        center_cols: 需要居中的逻辑列下标集合（默认 status / 第 0 列居中）。"""
        center = set(center_cols or [])
        # 列容量（字符单位）
        caps = [sum(_COL_WIDTHS[c1 - 1:c2]) for (c1, c2) in col_specs]

        # 表头
        r = state["row"]
        for j, (c1, c2) in enumerate(col_specs):
            if c2 > c1:
                ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
            for cc in range(c1, c2 + 1):
                cell = ws.cell(row=r, column=cc, value=headers[j] if cc == c1 else None)
                cell.fill = PatternFill("solid", fgColor=_BRAND)
                cell.font = Font(name=_FONT, bold=True, color="FFFFFF", size=10)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = _BORDER
        ws.row_dimensions[r].height = 20
        state["row"] += 1

        # 数据行
        for i, dr in enumerate(rows):
            r = state["row"]
            status_txt = ""
            if status_col is not None and status_col < len(dr):
                status_txt = str(dr[status_col] or "").strip()
            zebra = (i % 2 == 1)
            row_fill = _STATUS_FILL.get(status_txt) or (_ZEBRA if zebra else None)
            max_lines = 1
            for j, (c1, c2) in enumerate(col_specs):
                if c2 > c1:
                    ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
                val = "" if j >= len(dr) or dr[j] is None else str(dr[j])
                max_lines = max(max_lines, _cell_lines(val, caps[j]))
                is_status = (status_col is not None and j == status_col)
                fcolor = _STATUS_FONT.get(val.strip(), "262626") if is_status else "262626"
                halign = "center" if (j in center or is_status) else "left"
                for cc in range(c1, c2 + 1):
                    cell = ws.cell(row=r, column=cc, value=val if cc == c1 else None)
                    cell.font = Font(name=_FONT, size=10, color=fcolor, bold=is_status)
                    cell.alignment = Alignment(horizontal=halign, vertical="center", wrap_text=True)
                    cell.border = _BORDER
                    if row_fill:
                        cell.fill = PatternFill("solid", fgColor=row_fill)
            ws.row_dimensions[r].height = max(18, min(160, max_lines * 15 + 3))
            state["row"] += 1

    # ===== 标题条 =====
    band(f"【{label}周报】{special.name or ''}", fill=_BRAND_DARK,
         font_color="FFFFFF", bold=True, size=16, align="center", height=30)
    band(f"责任人：{special.owner or '-'}      导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
         fill=_BRAND, font_color="FFFFFF", size=10, align="center", height=20)
    gap()

    # ===== 目标 =====
    section(f"一、{label}目标")
    narrative(_strip_html(content.goal) if content else "")
    gap()

    # ===== 整体进展 =====
    section("二、整体进展")
    narrative(_strip_html(content.progress_summary) if content else "")
    gap()

    # ===== 求助 =====
    section("三、求助")
    narrative(_strip_html(content.help_request) if content else "")
    gap()

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
        # 里程碑→A:C，日期→D，状态→E:F
        table([(1, 3), (4, 4), (5, 6)], ["里程碑", "日期", "状态"], rows,
              status_col=2, center_cols={1, 2})
    else:
        narrative("—")
    gap()

    # 6 列等分映射（序号/内容/进展/责任人/闭环/状态）
    six = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)]

    # ===== 风险（调整到事务之前）=====
    section("五、风险和问题")
    risks = special.risks or []
    if risks:
        rrows = []
        for idx, rk in enumerate(risks, 1):
            st = "已闭环" if (rk.status or "open") == "closed" else "进行中"
            rrows.append([idx, _strip_html(rk.content), _strip_html(rk.progress),
                          rk.owner or "", rk.planned_close_date or "", st])
        table(six, ["序号", "问题内容", "当前进展", "责任人", "计划闭环", "状态"],
              rrows, status_col=5, center_cols={0, 3, 4})
    else:
        narrative("—")
    gap()

    # ===== 事务 =====
    section(f"六、{label}事务")
    tasks = sorted(special.tasks or [], key=lambda t: (t.sort_order or 0, t.id))
    if tasks:
        trows = []
        for idx, t in enumerate(tasks, 1):
            st = "已闭环" if (t.status or "open") == "closed" else "进行中"
            trows.append([idx, _strip_html(t.content), _strip_html(t.progress),
                          t.owner or "", t.planned_close_date or "", st])
        table(six, ["序号", "事务内容", "当前进展", "责任人", "计划闭环", "状态"],
              trows, status_col=5, center_cols={0, 3, 4})
    else:
        narrative("—")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
