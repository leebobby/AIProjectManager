"""PPT 导出工具：单页 16:9 表格。

依赖：python-pptx
"""
import io
from datetime import datetime
from typing import Iterable, List, Sequence

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt


_SLIDE_W = Emu(12192000)  # 16:9 默认 13.333"
_SLIDE_H = Emu(6858000)


def _new_pres() -> Presentation:
    pres = Presentation()
    pres.slide_width = _SLIDE_W
    pres.slide_height = _SLIDE_H
    return pres


def _add_title(slide, text: str):
    from pptx.util import Inches
    box = slide.shapes.add_textbox(Inches(0.4), Inches(0.2), Inches(12.5), Inches(0.6))
    tf = box.text_frame
    tf.text = text
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.runs[0]
    run.font.size = Pt(20)
    run.font.bold = True


def _fit_font_size(rows_count: int) -> int:
    if rows_count <= 6:
        return 11
    if rows_count <= 12:
        return 10
    if rows_count <= 20:
        return 9
    return 8


def _add_table(slide, headers: Sequence[str], rows: Sequence[Sequence[str]], col_widths_in: Sequence[float] | None = None):
    from pptx.util import Inches

    n_cols = len(headers)
    n_rows = len(rows) + 1  # +1 表头

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

    # 表头
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        for para in cell.text_frame.paragraphs:
            para.alignment = PP_ALIGN.CENTER
            for r in para.runs:
                r.font.size = Pt(font_size + 1)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x40, 0x73, 0xBA)

    # 数据
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = "" if val is None else str(val)
            for para in cell.text_frame.paragraphs:
                para.alignment = PP_ALIGN.LEFT
                for r in para.runs:
                    r.font.size = Pt(font_size)


def build_customer_status_pptx(rows: Iterable) -> io.BytesIO:
    """传入 CustomerStatus ORM 列表，返回 BytesIO。"""
    headers = [
        "机台编号", "客户", "型号", "当前阶段", "现场版本", "关注度",
        "当前进展", "近期现场关键诉求", "软件类风险和问题",
    ]
    col_widths = [0.9, 1.1, 1.0, 1.0, 1.0, 0.7, 2.2, 2.3, 2.3]

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
        ])

    pres = _new_pres()
    slide = pres.slides.add_slide(pres.slide_layouts[6])  # 空白
    _add_title(slide, f"客户面状态  ·  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    _add_table(slide, headers, data, col_widths)

    buf = io.BytesIO()
    pres.save(buf)
    buf.seek(0)
    return buf


def build_iteration_pptx(iteration, requirements: Iterable) -> io.BytesIO:
    """传入 AnnualIteration + IterationRequirement 列表，返回 BytesIO。"""
    headers = [
        "序号", "需求编号", "需求标题", "责任人", "优先级", "计划版本",
        "需求串讲", "反串讲", "STC设计", "编码", "BBIT", "转测澄清",
    ]
    col_widths = [0.5, 1.1, 2.6, 0.8, 0.6, 1.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]

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
        ])

    pres = _new_pres()
    slide = pres.slides.add_slide(pres.slide_layouts[6])
    title = f"{iteration.year}年{iteration.month}月迭代"
    if iteration.name:
        title += f"  ·  {iteration.name}"
    title += f"  ·  {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    _add_title(slide, title)
    _add_table(slide, headers, data, col_widths)

    buf = io.BytesIO()
    pres.save(buf)
    buf.seek(0)
    return buf
