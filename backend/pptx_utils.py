"""PPT 导出工具：模板化 16:9 表格输出。

依赖：python-pptx

设计要点：
- 表头采用品牌色 + 白字 + 居中加粗
- 数据行斑马纹（浅灰底）+ 边框 + 左对齐 + 自动换行
- 支持父子分组表头：通过将相邻列的父表头合并并设置同样的填充色实现
- 标题区域含主标题 + 副标题（导出时间）
"""
import io
from datetime import datetime
from typing import Iterable, List, Optional, Sequence

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt


_SLIDE_W = Emu(12192000)  # 16:9 默认 13.333"
_SLIDE_H = Emu(6858000)

_BRAND = RGBColor(0x40, 0x73, 0xBA)
_BRAND_DARK = RGBColor(0x2C, 0x55, 0x8C)
_ZEBRA = RGBColor(0xF5, 0xF7, 0xFA)
_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_TEXT = RGBColor(0x30, 0x31, 0x33)
_BORDER = RGBColor(0xD0, 0xD7, 0xE2)


def _new_pres() -> Presentation:
    pres = Presentation()
    pres.slide_width = _SLIDE_W
    pres.slide_height = _SLIDE_H
    return pres


def _add_banner(slide, title: str, subtitle: str):
    """顶部品牌色横幅：主标题 + 副标题。"""
    banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), _SLIDE_W, Inches(0.8))
    banner.line.fill.background()
    banner.fill.solid()
    banner.fill.fore_color.rgb = _BRAND_DARK
    banner.shadow.inherit = False

    # 主标题
    title_box = slide.shapes.add_textbox(Inches(0.4), Inches(0.1), Inches(10), Inches(0.45))
    tf = title_box.text_frame
    tf.margin_left = tf.margin_right = 0
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.runs[0]
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = _WHITE

    # 副标题
    sub_box = slide.shapes.add_textbox(Inches(0.4), Inches(0.5), Inches(10), Inches(0.3))
    tf2 = sub_box.text_frame
    tf2.margin_left = tf2.margin_right = 0
    tf2.text = subtitle
    p2 = tf2.paragraphs[0]
    run2 = p2.runs[0]
    run2.font.size = Pt(11)
    run2.font.color.rgb = RGBColor(0xCD, 0xDC, 0xEE)


def _fit_font_size(rows_count: int) -> int:
    if rows_count <= 6:
        return 11
    if rows_count <= 12:
        return 10
    if rows_count <= 20:
        return 9
    return 8


def _rgb_to_hex(color: RGBColor) -> str:
    return str(color)  # python-pptx RGBColor 的 __str__ 返回 6 位大写十六进制


def _set_cell_border(cell, color: RGBColor = _BORDER):
    """给单元格四边加细边框。python-pptx 没有现成 API，用 lxml 操作。"""
    tc_pr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        # 先删除已有，避免重复
        existing = tc_pr.findall(qn(tag))
        for e in existing:
            tc_pr.remove(e)
    hex_val = _rgb_to_hex(color)
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = etree.SubElement(tc_pr, qn(tag))
        ln.set("w", "6350")  # 0.5pt
        ln.set("cap", "flat")
        ln.set("cmpd", "sng")
        ln.set("algn", "ctr")
        solid = etree.SubElement(ln, qn("a:solidFill"))
        srgb = etree.SubElement(solid, qn("a:srgbClr"))
        srgb.set("val", hex_val)


def _style_header_cell(cell, text: str, font_size: int):
    cell.text = text
    cell.fill.solid()
    cell.fill.fore_color.rgb = _BRAND
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for para in cell.text_frame.paragraphs:
        para.alignment = PP_ALIGN.CENTER
        for r in para.runs:
            r.font.size = Pt(font_size + 1)
            r.font.bold = True
            r.font.color.rgb = _WHITE
    _set_cell_border(cell, _WHITE)


def _style_data_cell(cell, value, font_size: int, zebra: bool):
    cell.text = "" if value is None else str(value)
    cell.fill.solid()
    cell.fill.fore_color.rgb = _ZEBRA if zebra else _WHITE
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for para in cell.text_frame.paragraphs:
        para.alignment = PP_ALIGN.LEFT
        for r in para.runs:
            r.font.size = Pt(font_size)
            r.font.color.rgb = _TEXT
    _set_cell_border(cell)


def _merge_header_groups(table, header_row: int, groups: Sequence[tuple]):
    """合并某一表头行的相邻列：groups = [(start_col, end_col, label), ...]"""
    for start, end, label in groups:
        if end > start:
            table.cell(header_row, start).merge(table.cell(header_row, end))
        cell = table.cell(header_row, start)
        cell.text = label


def _add_grouped_table(
    slide,
    parent_headers: Sequence[Optional[tuple]],  # list aligned with cols: (group_id, label) or None
    leaf_headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    col_widths_in: Optional[Sequence[float]] = None,
):
    """支持「父表头 + 子表头」两行表头的表格。

    parent_headers: 长度与 leaf_headers 相同。每个元素是 (group_id, label) 或 None。
        相邻同 group_id 会被合并；None 表示该列没有父分组，会与子表头单元格垂直合并显示。
    """
    n_cols = len(leaf_headers)
    n_rows = 2 + len(rows)  # 2 行表头

    left = Inches(0.4)
    top = Inches(0.95)
    width = Inches(12.5)
    height = Inches(5.7)

    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = table_shape.table

    if col_widths_in and len(col_widths_in) == n_cols:
        for i, w in enumerate(col_widths_in):
            table.columns[i].width = Inches(w)

    font_size = _fit_font_size(len(rows))

    # ===== 父表头行 =====
    # 先填默认 label（空），稍后合并
    for j in range(n_cols):
        _style_header_cell(table.cell(0, j), "", font_size)

    # 计算分组
    groups: List[tuple] = []  # (start, end, label, group_id)
    j = 0
    while j < n_cols:
        ph = parent_headers[j]
        if ph is None:
            # 此列父行将与子行做垂直合并
            j += 1
            continue
        gid, label = ph
        end = j
        while end + 1 < n_cols and parent_headers[end + 1] is not None and parent_headers[end + 1][0] == gid:
            end += 1
        groups.append((j, end, label, gid))
        j = end + 1

    _merge_header_groups(table, 0, [(s, e, lab) for s, e, lab, _ in groups])

    # 重新设置合并后的父单元格样式（merge 之后需要再次设置文本/样式）
    for s, e, lab, _ in groups:
        _style_header_cell(table.cell(0, s), lab, font_size)

    # ===== 子表头行 =====
    for j, h in enumerate(leaf_headers):
        _style_header_cell(table.cell(1, j), h, font_size)

    # 把「没有父分组」的列做垂直合并（父行 + 子行 -> 同一格显示子标题）
    for j in range(n_cols):
        if parent_headers[j] is None:
            top_cell = table.cell(0, j)
            bot_cell = table.cell(1, j)
            top_cell.merge(bot_cell)
            _style_header_cell(table.cell(0, j), leaf_headers[j], font_size)

    # ===== 数据行 =====
    for i, row in enumerate(rows, start=2):
        zebra = (i - 2) % 2 == 1
        for j, val in enumerate(row):
            _style_data_cell(table.cell(i, j), val, font_size, zebra)


def build_customer_status_pptx(rows: Iterable) -> io.BytesIO:
    """传入 CustomerStatus ORM 列表，返回 BytesIO。"""
    leaf_headers = [
        "机台编号", "客户", "型号", "当前阶段", "现场版本", "关注度",
        "当前进展", "近期现场关键诉求", "软件类风险和问题", "问题单",
    ]
    parent_headers: List[Optional[tuple]] = [None] * len(leaf_headers)
    col_widths = [0.85, 1.0, 0.9, 0.95, 0.95, 0.7, 2.0, 2.0, 2.0, 1.15]

    data: List[List[str]] = []
    for r in rows:
        data.append([
            r.machine_id or "",
            r.battlefield or "",
            r.model or "",
            r.current_stage or "",
            r.field_version or "",
            ("★" * (r.attention_level or 0)) or "-",
            r.customer_status or "",
            r.recent_focus or "",
            r.key_issues or "",
            getattr(r, "issue_url", "") or "—",
        ])

    pres = _new_pres()
    slide = pres.slides.add_slide(pres.slide_layouts[6])  # 空白
    _add_banner(
        slide,
        "客户面状态总览",
        f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}   ·   共 {len(data)} 条",
    )
    _add_grouped_table(slide, parent_headers, leaf_headers, data, col_widths)

    buf = io.BytesIO()
    pres.save(buf)
    buf.seek(0)
    return buf


def build_iteration_pptx(iteration, requirements: Iterable) -> io.BytesIO:
    """传入 AnnualIteration + IterationRequirement 列表，返回 BytesIO。

    表头改成两行：基础列 + 「交付进展跟踪」分组下的 6 个子列 + 备注。
    """
    # leaf 列
    leaf_headers = [
        "序号", "需求编号", "需求标题", "责任人", "优先级", "计划版本",
        "需求串讲", "反串讲", "STC设计", "编码", "BBIT", "转测澄清",
        "备注",
    ]
    # 父表头：6 个进展列归到「交付进展跟踪」组
    parent_headers: List[Optional[tuple]] = [None] * 6 + [("progress", "交付进展跟踪")] * 6 + [None]
    col_widths = [0.45, 1.0, 2.2, 0.8, 0.6, 0.95, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 1.5]

    data: List[List[str]] = []
    for r in requirements:
        data.append([
            str(r.seq or 0),
            r.req_no or "",
            r.title or "",
            r.owner or "",
            r.priority or "",
            r.planned_version or "",
            r.progress_walkthrough or "",
            r.progress_reverse or "",
            r.progress_stc or "",
            r.progress_coding or "",
            r.progress_bbit or "",
            r.progress_clarify or "",
            getattr(r, "remark", "") or "",
        ])

    pres = _new_pres()
    slide = pres.slides.add_slide(pres.slide_layouts[6])
    title = f"{iteration.year}年{iteration.month}月迭代"
    if iteration.name:
        title += f"  ·  {iteration.name}"
    subtitle = f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}   ·   共 {len(data)} 条需求"
    if iteration.owner:
        subtitle += f"   ·   负责人：{iteration.owner}"
    _add_banner(slide, title, subtitle)
    _add_grouped_table(slide, parent_headers, leaf_headers, data, col_widths)

    buf = io.BytesIO()
    pres.save(buf)
    buf.seek(0)
    return buf
