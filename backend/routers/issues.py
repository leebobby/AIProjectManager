"""问题单报表接口：读取服务器侧 Excel，解析后返回给前端。

权限：
- GET  /api/issues/data              —— 所有登录用户（加载最新单张报表）
- GET  /api/issues/trend             —— 所有登录用户（扫描全目录按天聚合趋势）
- GET  /api/issues/run-script/status —— 所有登录用户（查询脚本是否正在运行）
- POST /api/issues/run-script        —— 仅管理员（执行外部刷新脚本）
- GET  /api/issues/export.pptx       —— 所有登录用户（导出 PPT）

配置项（via PUT /api/config）：
  issue_report_path  —— Excel 目录或文件路径
  issue_script_path  —— 刷新脚本路径（.py / .bat / .exe）
"""
import io
import pathlib
import re
import subprocess
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

import models
from auth import get_current_user, require_admin
from routers.config import _load as _load_config

router = APIRouter(prefix="/api/issues", tags=["issues"])

# 全局锁：防止脚本并发执行
_script_lock: threading.Lock = threading.Lock()
_script_started_at: Optional[datetime] = None

_RAW_COLS = [
    "version", "issue_id", "title", "owner", "group",
    "severity", "feature", "module", "is_sdts",
    "year", "month", "date", "year_month", "category",
]

_DATE_PAT = re.compile(r"_(\d{8})\.", re.IGNORECASE)

COLORS = ["#4073ba", "#67C23A", "#E6A23C", "#F56C6C", "#909399", "#8E7AD8", "#26C9C3"]


# ─── helpers ────────────────────────────────────────────────────────────────

def _cell(ws, row: int, col: int) -> str:
    v = ws.cell(row, col).value
    return str(v).strip() if v is not None else ""


def _count_by(rows: List[Dict], field: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for r in rows:
        k = r.get(field, "")
        if k:
            result[k] = result.get(k, 0) + 1
    return result


def _file_sort_key(f: pathlib.Path):
    m = _DATE_PAT.search(f.name)
    if m:
        try:
            return (1, datetime.strptime(m.group(1), "%Y%m%d").timestamp())
        except ValueError:
            pass
    return (0, f.stat().st_mtime)


def _resolve_target(path_str: str) -> pathlib.Path:
    p = pathlib.Path(path_str)
    if not p.exists():
        raise HTTPException(404, f"路径不存在：{path_str}")
    if p.is_file():
        if p.suffix.lower() != ".xlsx":
            raise HTTPException(400, "指定文件不是 .xlsx 格式")
        return p
    if p.is_dir():
        candidates = sorted(p.glob("*.xlsx"), key=_file_sort_key, reverse=True)
        if not candidates:
            raise HTTPException(404, f"目录 {path_str} 中未找到 .xlsx 文件")
        return candidates[0]
    raise HTTPException(400, f"无法识别路径：{path_str}")


def _parse_cross_table(ws) -> Dict[str, Any]:
    max_col = ws.max_column
    columns = [_cell(ws, 1, c) for c in range(2, max_col + 1)]
    while columns and not columns[-1]:
        columns.pop()
    rows: List[Dict] = []
    for r in range(2, ws.max_row + 1):
        label = _cell(ws, r, 1)
        if not label:
            break
        row: Dict[str, Any] = {"label": label}
        for i, col in enumerate(columns):
            raw_val = ws.cell(r, i + 2).value
            if raw_val is None:
                row[col] = 0
            else:
                try:
                    row[col] = int(raw_val)
                except (ValueError, TypeError):
                    row[col] = str(raw_val)
        rows.append(row)
    return {"columns": columns, "rows": rows}


def _parse_excel(path: str) -> Dict[str, Any]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
    except FileNotFoundError:
        raise HTTPException(404, "报表文件不存在，请检查路径配置")
    except Exception as exc:
        raise HTTPException(500, f"读取报表文件失败: {exc}")

    raw: List[Dict] = []
    try:
        ws_raw = wb["原始数据"]
        for r in range(2, ws_raw.max_row + 1):
            row = {col: _cell(ws_raw, r, i + 1) for i, col in enumerate(_RAW_COLS)}
            if any(row.values()):
                raw.append(row)
    except KeyError:
        pass

    def _sheet(name):
        try:
            return _parse_cross_table(wb[name])
        except KeyError:
            return {"columns": [], "rows": []}

    try:
        mtime = datetime.fromtimestamp(
            pathlib.Path(path).stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        mtime = None

    return {
        "file_mtime": mtime,
        "raw": raw,
        "monthly_by_group":   _sheet("按小组月度统计"),
        "annual_by_group":    _sheet("按小组年度统计"),
        "by_customer":        _sheet("按客户统计"),
        "feature_by_group":   _sheet("特性×小组统计"),
        "feature_by_customer":_sheet("特性×客户统计"),
    }


def _parse_raw_from_wb(wb) -> List[Dict]:
    raw: List[Dict] = []
    try:
        ws = wb["原始数据"]
        for r in range(2, ws.max_row + 1):
            row = {col: _cell(ws, r, i + 1) for i, col in enumerate(_RAW_COLS)}
            if any(row.values()):
                raw.append(row)
    except KeyError:
        pass
    return raw


# ─── PPT builder ────────────────────────────────────────────────────────────

def _build_pptx(data: dict) -> io.BytesIO:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    C_BLUE   = RGBColor(0x40, 0x73, 0xBA)
    C_RED    = RGBColor(0xF5, 0x6C, 0x6C)
    C_ORANGE = RGBColor(0xE6, 0xA2, 0x3C)
    C_GRAY   = RGBColor(0x90, 0x93, 0x99)
    C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
    C_DARK   = RGBColor(0x30, 0x31, 0x33)
    C_LIGHT  = RGBColor(0xF5, 0xF7, 0xFA)

    raw = data.get("raw", [])

    def _txt(slide, text, x, y, w, h, size=12, bold=False, color=C_DARK, align=PP_ALIGN.LEFT):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color

    def _cell_run(cell, text: str, size: int, bold: bool, color: RGBColor,
                  align=PP_ALIGN.LEFT, bg: RGBColor = None):
        """Set cell text via a run (avoids paragraph.font issues)."""
        if bg is not None:
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
        p = cell.text_frame.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color

    def _table_slide(title: str, columns: List[str], rows_data: List[List[str]]):
        slide = prs.slides.add_slide(blank)
        _txt(slide, title, 0.4, 0.15, 12.5, 0.6, size=20, bold=True, color=C_BLUE)

        n_rows = len(rows_data) + 1
        n_cols = len(columns)
        cell_h = min(0.38, 5.8 / n_rows)
        total_h = cell_h * n_rows
        tbl = slide.shapes.add_table(
            n_rows, n_cols,
            Inches(0.4), Inches(0.9), Inches(12.5), Inches(total_h)
        ).table

        col_w = [2.0] + [10.5 / max(n_cols - 1, 1)] * (n_cols - 1)

        for c, h in enumerate(columns):
            _cell_run(tbl.cell(0, c), h, 10, True, C_WHITE,
                      align=PP_ALIGN.CENTER, bg=C_BLUE)

        for r, row_vals in enumerate(rows_data):
            is_total = bool(row_vals) and row_vals[0] == "合计"
            for c, val in enumerate(row_vals):
                _cell_run(tbl.cell(r + 1, c), str(val), 10, is_total, C_DARK,
                          align=PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT,
                          bg=C_LIGHT if is_total else None)

        for c, w in enumerate(col_w):
            tbl.columns[c].width = Inches(w)

    # ── Slide 1: Title ────────────────────────────────────────────
    slide1 = prs.slides.add_slide(blank)
    _txt(slide1, "缺陷统计报表", 1, 1.8, 11, 1.4, size=48, bold=True, color=C_BLUE, align=PP_ALIGN.CENTER)
    _txt(slide1, f"{data.get('actual_file', '')}   {data.get('file_mtime', '')}",
         1, 3.4, 11, 0.5, size=13, color=C_GRAY, align=PP_ALIGN.CENTER)

    total  = len(raw)
    cnts   = {s: sum(1 for r in raw if r.get("severity") == s) for s in ["严重", "一般", "提示"]}
    cards  = [("合计", total, C_BLUE), ("严重", cnts["严重"], C_RED),
              ("一般", cnts["一般"], C_ORANGE), ("提示", cnts["提示"], C_GRAY)]
    cx = 0.7
    for label, val, clr in cards:
        shp = slide1.shapes.add_shape(1, Inches(cx), Inches(4.4), Inches(2.8), Inches(1.7))
        shp.fill.solid()
        shp.fill.fore_color.rgb = clr
        shp.line.color.rgb = clr
        tf = shp.text_frame
        tf.word_wrap = False
        p1 = tf.paragraphs[0]
        p1.alignment = PP_ALIGN.CENTER
        r1 = p1.add_run()
        r1.text = str(val)
        r1.font.size = Pt(40)
        r1.font.bold = True
        r1.font.color.rgb = C_WHITE
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = label
        r2.font.size = Pt(14)
        r2.font.color.rgb = C_WHITE
        cx += 3.0

    # ── Slide 2: Monthly by group ─────────────────────────────────
    m = data.get("monthly_by_group", {})
    if m.get("rows"):
        cols  = ["小组"] + m["columns"]
        rdata = [[r["label"]] + [str(r.get(c, 0)) for c in m["columns"]] for r in m["rows"]]
        _table_slide("按小组月度统计", cols, rdata)

    # ── Slide 3: By customer ─────────────────────────────────────
    c = data.get("by_customer", {})
    if c.get("rows"):
        cols  = ["小组"] + c["columns"]
        rdata = [[r["label"]] + [str(r.get(col, 0)) for col in c["columns"]] for r in c["rows"]]
        _table_slide("按客户分布", cols, rdata)

    # ── Slide 4: Feature by group ─────────────────────────────────
    f = data.get("feature_by_group", {})
    if f.get("rows"):
        cols  = ["小组"] + f["columns"]
        rdata = [[r["label"]] + [str(r.get(col, 0)) for col in f["columns"]] for r in f["rows"]]
        _table_slide("特性 × 小组分布", cols, rdata)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ─── endpoints ──────────────────────────────────────────────────────────────

@router.get("/data")
def get_data(_: models.User = Depends(get_current_user)):
    """加载最新单张报表（按文件名日期优先）。"""
    cfg = _load_config()
    path_str = cfg.get("issue_report_path", "").strip()
    if not path_str:
        return {"configured": False}
    target = _resolve_target(path_str)
    result = _parse_excel(str(target))
    result["actual_file"] = target.name
    return {"configured": True, **result}


@router.get("/trend")
def get_trend(_: models.User = Depends(get_current_user)):
    """扫描目录内全部带日期的 xlsx，按天聚合趋势数据。"""
    import openpyxl

    cfg = _load_config()
    path_str = cfg.get("issue_report_path", "").strip()
    if not path_str:
        raise HTTPException(400, "未配置报表路径")

    p = pathlib.Path(path_str)
    if p.is_file():
        p = p.parent
    if not p.is_dir():
        raise HTTPException(404, f"目录不存在：{path_str}")

    candidates = sorted(
        (f for f in p.glob("*.xlsx") if _DATE_PAT.search(f.name)),
        key=_file_sort_key,
    )
    if not candidates:
        raise HTTPException(404, "目录中无含日期后缀的报表文件（期望格式 _YYYYMMDD）")

    daily: List[Dict] = []
    all_groups:     set = set()
    all_severities: set = set()

    for f in candidates:
        m = _DATE_PAT.search(f.name)
        ds = m.group(1)
        date_fmt = f"{ds[:4]}-{ds[4:6]}-{ds[6:]}"
        try:
            wb  = openpyxl.load_workbook(str(f), data_only=True)
            raw = _parse_raw_from_wb(wb)
            wb.close()
        except Exception:
            continue

        bg = _count_by(raw, "group")
        bs = _count_by(raw, "severity")
        all_groups.update(bg.keys())
        all_severities.update(bs.keys())

        daily.append({
            "date":        date_fmt,
            "file":        f.name,
            "total":       len(raw),
            "by_group":    bg,
            "by_severity": bs,
        })

    sev_order = ["严重", "一般", "提示"]
    return {
        "daily":          daily,
        "all_groups":     sorted(all_groups),
        "all_severities": sorted(all_severities, key=lambda s: sev_order.index(s) if s in sev_order else 99),
    }


@router.get("/run-script/status")
def run_script_status(_: models.User = Depends(get_current_user)):
    """查询刷新脚本是否正在执行（所有登录用户可查）。"""
    return {
        "running":    _script_lock.locked(),
        "started_at": _script_started_at.isoformat() if _script_started_at else None,
    }


@router.post("/run-script")
def run_script(_: models.User = Depends(require_admin)):
    """执行管理员配置的外部刷新脚本（全局互斥，同时只能有一个实例）。"""
    global _script_started_at

    if not _script_lock.acquire(blocking=False):
        raise HTTPException(423, "脚本正在执行中，请等待完成后再试")

    _script_started_at = datetime.utcnow()
    try:
        cfg = _load_config()
        script = cfg.get("issue_script_path", "").strip()
        if not script:
            raise HTTPException(400, "未配置刷新脚本路径（issue_script_path）")

        sp = pathlib.Path(script)
        if not sp.exists():
            raise HTTPException(404, f"脚本不存在：{script}")

        cmd = [sys.executable, str(sp)] if sp.suffix.lower() == ".py" else [str(sp)]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=300, cwd=str(sp.parent),
        )
        return {
            "ok":        result.returncode == 0,
            "exit_code": result.returncode,
            "stdout":    result.stdout[-3000:] if result.stdout else "",
            "stderr":    result.stderr[-1000:] if result.stderr else "",
        }
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "脚本执行超时（>5分钟）")
    except Exception as exc:
        raise HTTPException(500, f"脚本启动失败：{exc}")
    finally:
        _script_started_at = None
        _script_lock.release()


@router.get("/export.pptx")
def export_pptx(_: models.User = Depends(get_current_user)):
    """将当前最新报表导出为 PPT。"""
    cfg = _load_config()
    path_str = cfg.get("issue_report_path", "").strip()
    if not path_str:
        raise HTTPException(400, "未配置报表路径")

    target = _resolve_target(path_str)
    data   = _parse_excel(str(target))
    data["actual_file"] = target.name

    try:
        buf = _build_pptx(data)
    except Exception as exc:
        raise HTTPException(500, f"PPT 生成失败：{exc}")
    filename = f"缺陷统计报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
