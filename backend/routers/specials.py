"""专项 / 攻关管理：
- 元数据（name/kind/owner/...）：admin 增删改
- 单条目的内容/事务/风险/全景图：任意登录用户可写
- 周报草稿：服务端生成草稿文本 + 美化 HTML，前端下载为 .eml（Outlook 可直接打开为草稿）
"""
import email.utils
import html
import json
import pathlib
import uuid
from datetime import datetime
from email.message import EmailMessage
from typing import List
from urllib.parse import quote as url_quote

from fastapi import APIRouter, Body, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_admin
from database import get_db
from op_log import log_op

router = APIRouter(prefix="/api/specials", tags=["specials"])

UPLOAD_ROOT = pathlib.Path(__file__).resolve().parent.parent / "uploads" / "specials"


def _kind_label(kind: str) -> str:
    return "攻关" if kind == "assault" else "专项"


def _ensure_dir(p: pathlib.Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _get_or_404(db: Session, sid: int) -> models.Special:
    item = db.query(models.Special).filter(models.Special.id == sid).first()
    if not item:
        raise HTTPException(404, "专项不存在")
    return item


def _ensure_content(db: Session, special: models.Special) -> models.SpecialContent:
    if special.content:
        return special.content
    c = models.SpecialContent(special_id=special.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ─── Specials list ─────────────────────────────────────────────────

@router.get("", response_model=List[schemas.SpecialOut])
def list_specials(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(models.Special)
    if not include_inactive:
        q = q.filter(models.Special.is_active.is_(True))
    return q.order_by(models.Special.sort_order, models.Special.id).all()


@router.post("", response_model=schemas.SpecialOut)
def create_special(
    payload: schemas.SpecialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    data = payload.model_dump()
    if data.get("kind") not in ("special", "assault"):
        data["kind"] = "special"
    item = models.Special(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    # 创建对应的空 content
    db.add(models.SpecialContent(special_id=item.id))
    db.commit()
    log_op(db, action="新增", target=_kind_label(item.kind), target_id=item.id,
           detail=f"name={item.name}",
           user=current_admin, request=request)
    return item


@router.put("/{sid}", response_model=schemas.SpecialOut)
def update_special(
    sid: int,
    payload: schemas.SpecialUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    item = _get_or_404(db, sid)
    data = payload.model_dump(exclude_unset=True)
    if "kind" in data and data["kind"] not in ("special", "assault"):
        raise HTTPException(400, "kind 仅支持 special / assault")
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    log_op(db, action="修改", target=_kind_label(item.kind), target_id=item.id,
           detail=f"name={item.name} fields={','.join(data.keys()) or '无'}",
           user=current_admin, request=request)
    return item


@router.delete("/{sid}")
def delete_special(
    sid: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_admin),
):
    item = _get_or_404(db, sid)
    snapshot = f"name={item.name}"
    label = _kind_label(item.kind)
    # 清理全景图文件
    if item.content and item.content.panorama_image_path:
        try:
            p = (UPLOAD_ROOT.parent / item.content.panorama_image_path).resolve()
            if p.exists():
                p.unlink()
        except OSError:
            pass
    db.delete(item)
    db.commit()
    log_op(db, action="删除", target=label, target_id=sid,
           detail=snapshot, user=current_admin, request=request)
    return {"ok": True}


# ─── 详情 ──────────────────────────────────────────────────────────


@router.get("/{sid}", response_model=schemas.SpecialDetailOut)
def get_one(sid: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, sid)
    _ensure_content(db, item)
    return item


@router.put("/{sid}/content", response_model=schemas.SpecialContentOut)
def update_content(
    sid: int,
    payload: schemas.SpecialContentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    special = _get_or_404(db, sid)
    content = _ensure_content(db, special)
    if content.version != payload.version:
        raise HTTPException(409, "数据已被他人修改，请刷新后重试")
    data = payload.model_dump(exclude_unset=True)
    data.pop("version", None)
    for k, v in data.items():
        setattr(content, k, v)
    content.version += 1
    db.commit()
    db.refresh(content)
    log_op(db, action="修改", target=f"{_kind_label(special.kind)}内容", target_id=sid,
           detail=f"name={special.name} fields={','.join(data.keys()) or '无'}",
           user=current_user, request=request)
    return content


# ─── 全景图上传/下载 ────────────────────────────────────────────────

_PANORAMA_OK_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}


@router.post("/{sid}/panorama", response_model=schemas.SpecialContentOut)
def upload_panorama(
    sid: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ct = (file.content_type or "").lower()
    ext = pathlib.Path(file.filename or "").suffix.lower()
    is_image = ct.startswith("image/") or ct == "image/svg+xml"
    if not (is_image or ext in _PANORAMA_OK_EXT):
        raise HTTPException(400, "仅支持图片或 SVG 文件")
    special = _get_or_404(db, sid)
    content = _ensure_content(db, special)

    # 写入新文件
    sub = UPLOAD_ROOT / str(sid)
    _ensure_dir(sub)
    orig_name = file.filename or "panorama.png"
    safe_ext = pathlib.Path(orig_name).suffix[:16] or ".png"
    stored = f"{uuid.uuid4().hex}{safe_ext}"
    full = sub / stored
    with open(full, "wb") as f:
        while True:
            chunk = file.file.read(64 * 1024)
            if not chunk:
                break
            f.write(chunk)

    # 删旧
    if content.panorama_image_path:
        try:
            old = (UPLOAD_ROOT.parent / content.panorama_image_path).resolve()
            if old.exists() and old != full.resolve():
                old.unlink()
        except OSError:
            pass

    content.panorama_image_path = f"specials/{sid}/{stored}"
    content.panorama_image_name = orig_name
    content.version += 1
    db.commit()
    db.refresh(content)
    log_op(db, action="修改", target=f"{_kind_label(special.kind)}全景图", target_id=sid,
           detail=f"name={special.name} file={orig_name}",
           user=current_user, request=request)
    return content


@router.get("/{sid}/panorama")
def get_panorama(sid: int, db: Session = Depends(get_db)):
    special = _get_or_404(db, sid)
    if not special.content or not special.content.panorama_image_path:
        raise HTTPException(404, "全景图未上传")
    p = (UPLOAD_ROOT.parent / special.content.panorama_image_path).resolve()
    if not p.exists():
        raise HTTPException(404, "全景图文件已丢失")
    return FileResponse(str(p))


# ─── 事务 / 风险 (合并实现) ─────────────────────────────────────────

def _item_model(kind: str):
    return models.SpecialTask if kind == "task" else models.SpecialRisk


def _action_target(kind: str) -> str:
    return "专项事务" if kind == "task" else "风险问题"


@router.get("/{sid}/tasks", response_model=List[schemas.SpecialItemOut])
def list_tasks(sid: int, db: Session = Depends(get_db)):
    _get_or_404(db, sid)
    return (
        db.query(models.SpecialTask)
        .filter(models.SpecialTask.special_id == sid)
        .order_by(models.SpecialTask.sort_order, models.SpecialTask.id)
        .all()
    )


@router.get("/{sid}/risks", response_model=List[schemas.SpecialItemOut])
def list_risks(sid: int, db: Session = Depends(get_db)):
    _get_or_404(db, sid)
    return (
        db.query(models.SpecialRisk)
        .filter(models.SpecialRisk.special_id == sid)
        .order_by(models.SpecialRisk.sort_order, models.SpecialRisk.id)
        .all()
    )


def _create_item(
    kind: str,
    sid: int,
    payload: schemas.SpecialItemBase,
    db: Session,
    user: models.User,
    request: Request,
):
    _get_or_404(db, sid)
    Model = _item_model(kind)
    data = payload.model_dump(exclude_unset=True)
    if not data.get("seq"):
        cnt = db.query(Model).filter(Model.special_id == sid).count()
        data["seq"] = cnt + 1
    if not data.get("sort_order"):
        data["sort_order"] = data["seq"]
    item = Model(special_id=sid, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    log_op(db, action="新增", target=_action_target(kind), target_id=item.id,
           detail=f"special_id={sid} content={(item.content or '')[:60]}",
           user=user, request=request)
    return item


def _update_item(
    kind: str,
    item_id: int,
    payload: schemas.SpecialItemUpdate,
    db: Session,
    user: models.User,
    request: Request,
):
    Model = _item_model(kind)
    item = db.query(Model).filter(Model.id == item_id).first()
    if not item:
        raise HTTPException(404, "条目不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    log_op(db, action="修改", target=_action_target(kind), target_id=item.id,
           detail=f"special_id={item.special_id} fields={','.join(data.keys()) or '无'}",
           user=user, request=request)
    return item


def _delete_item(
    kind: str,
    item_id: int,
    db: Session,
    user: models.User,
    request: Request,
):
    Model = _item_model(kind)
    item = db.query(Model).filter(Model.id == item_id).first()
    if not item:
        raise HTTPException(404, "条目不存在")
    snapshot = f"special_id={item.special_id} content={(item.content or '')[:60]}"
    db.delete(item)
    db.commit()
    log_op(db, action="删除", target=_action_target(kind), target_id=item_id,
           detail=snapshot, user=user, request=request)
    return {"ok": True}


@router.post("/{sid}/tasks", response_model=schemas.SpecialItemOut)
def create_task(
    sid: int,
    payload: schemas.SpecialItemBase,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _create_item("task", sid, payload, db, current_user, request)


@router.put("/tasks/{item_id}", response_model=schemas.SpecialItemOut)
def update_task(
    item_id: int,
    payload: schemas.SpecialItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _update_item("task", item_id, payload, db, current_user, request)


@router.delete("/tasks/{item_id}")
def delete_task(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _delete_item("task", item_id, db, current_user, request)


@router.post("/{sid}/risks", response_model=schemas.SpecialItemOut)
def create_risk(
    sid: int,
    payload: schemas.SpecialItemBase,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _create_item("risk", sid, payload, db, current_user, request)


@router.put("/risks/{item_id}", response_model=schemas.SpecialItemOut)
def update_risk(
    item_id: int,
    payload: schemas.SpecialItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _update_item("risk", item_id, payload, db, current_user, request)


@router.delete("/risks/{item_id}")
def delete_risk(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _delete_item("risk", item_id, db, current_user, request)


# ─── 周报草稿 ──────────────────────────────────────────────────────

_MS_STATUS_LABEL = {
    "planning": "未开始", "in_progress": "进行中",
    "done": "已完成", "delayed": "已延期",
}


def _render_report_body(special: models.Special) -> str:
    label = _kind_label(special.kind)
    content = special.content
    parts: List[str] = []

    parts.append(f"[{label}名称] {special.name}")
    parts.append(f"[责任人] {special.owner or '-'}")
    parts.append(f"[报告日期] {datetime.now().strftime('%Y-%m-%d')}")
    parts.append("")

    if content and content.goal:
        parts.append(f"一、{label}目标")
        parts.append(content.goal.strip())
        parts.append("")

    if content and content.progress_summary:
        parts.append("二、一句话进展 & 求助")
        parts.append(content.progress_summary.strip())
        parts.append("")

    # 里程碑
    milestones = []
    if content and content.milestones_json:
        try:
            milestones = json.loads(content.milestones_json) or []
        except (ValueError, TypeError):
            milestones = []
    if milestones:
        parts.append(f"三、{label}计划（里程碑）")
        for m in milestones:
            st = _MS_STATUS_LABEL.get(m.get("status", "planning"), m.get("status", ""))
            parts.append(f"  · {m.get('name','')}  {m.get('date','')}  [{st}]")
        parts.append("")

    # 事务
    open_tasks = [t for t in (special.tasks or []) if (t.status or "open") == "open"]
    closed_tasks = [t for t in (special.tasks or []) if (t.status or "open") == "closed"]
    if open_tasks or closed_tasks:
        parts.append(f"四、{label}事务")
        if open_tasks:
            parts.append(f"  ◇ 进行中（{len(open_tasks)} 项）")
            for i, t in enumerate(open_tasks, 1):
                parts.append(f"    {i}. {(t.content or '').strip()}")
                if t.progress: parts.append(f"       进展：{t.progress.strip()}")
                meta = []
                if t.owner: meta.append(f"责任人：{t.owner}")
                if t.planned_close_date: meta.append(f"计划闭环：{t.planned_close_date}")
                if meta: parts.append(f"       " + " / ".join(meta))
        if closed_tasks:
            parts.append(f"  ◇ 本期已闭环（{len(closed_tasks)} 项）")
            for i, t in enumerate(closed_tasks, 1):
                parts.append(f"    {i}. {(t.content or '').strip()}")
        parts.append("")

    # 风险
    risks = special.risks or []
    if risks:
        parts.append("五、风险和问题")
        for i, r in enumerate(risks, 1):
            parts.append(f"  {i}. {(r.content or '').strip()}")
            if r.progress: parts.append(f"     当前进展：{r.progress.strip()}")
            meta = []
            if r.owner: meta.append(f"责任人：{r.owner}")
            if r.planned_close_date: meta.append(f"计划闭环：{r.planned_close_date}")
            if meta: parts.append(f"     " + " / ".join(meta))
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def _render_subject(special: models.Special) -> str:
    label = _kind_label(special.kind)
    tpl = (special.email_subject_tpl or "").strip()
    today = datetime.now().strftime("%Y-%m-%d")
    if tpl:
        return (tpl
                .replace("{label}", label)
                .replace("{kind_label}", label)
                .replace("{name}", special.name)
                .replace("{owner}", special.owner or "")
                .replace("{date}", today))
    return f"【{label}周报】{special.name} - {today}"


# ─── HTML 美化版本 ─────────────────────────────────────────────────

_HTML_BASE_CSS = (
    "font-family: 'Microsoft YaHei','PingFang SC',Arial,sans-serif; "
    "font-size: 14px; line-height: 1.65; color: #303133;"
)

_HTML_TABLE_CSS = (
    "border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; "
    "font-size: 13px;"
)
_HTML_TH_CSS = (
    "background: #4073BA; color: #fff; text-align: left; "
    "padding: 6px 10px; border: 1px solid #4073BA;"
)
_HTML_TD_CSS = "padding: 6px 10px; border: 1px solid #dcdfe6; vertical-align: top;"
_HTML_TD_ZEBRA = "padding: 6px 10px; border: 1px solid #dcdfe6; vertical-align: top; background: #f9fbfd;"


def _e(s) -> str:
    """HTML 转义 + 把换行变 <br>。"""
    return html.escape(str(s or ""), quote=False).replace("\n", "<br>")


def _row_td(cells, zebra: bool) -> str:
    css = _HTML_TD_ZEBRA if zebra else _HTML_TD_CSS
    return "<tr>" + "".join(f'<td style="{css}">{_e(c)}</td>' for c in cells) + "</tr>"


def _build_table(headers: list, rows: list) -> str:
    head = "<tr>" + "".join(f'<th style="{_HTML_TH_CSS}">{_e(h)}</th>' for h in headers) + "</tr>"
    body = "".join(_row_td(r, i % 2 == 1) for i, r in enumerate(rows))
    return f'<table style="{_HTML_TABLE_CSS}">{head}{body}</table>'


def _render_report_html(special: models.Special) -> str:
    label = _kind_label(special.kind)
    content = special.content
    today = datetime.now().strftime("%Y-%m-%d")

    sections: List[str] = []

    if content and content.goal:
        sections.append(
            f'<h3 style="color:#4073BA;border-left:4px solid #4073BA;padding-left:8px;margin:18px 0 8px;">'
            f'一、{label}目标</h3>'
            f'<div>{_e(content.goal.strip())}</div>'
        )

    if content and content.progress_summary:
        sections.append(
            f'<h3 style="color:#4073BA;border-left:4px solid #4073BA;padding-left:8px;margin:18px 0 8px;">'
            f'二、一句话进展 &amp; 求助</h3>'
            f'<div>{_e(content.progress_summary.strip())}</div>'
        )

    # 里程碑
    milestones = []
    if content and content.milestones_json:
        try:
            milestones = json.loads(content.milestones_json) or []
        except (ValueError, TypeError):
            milestones = []
    if milestones:
        rows = [
            [m.get("name", ""), m.get("date", ""),
             _MS_STATUS_LABEL.get(m.get("status", "planning"), m.get("status", ""))]
            for m in milestones
        ]
        sections.append(
            f'<h3 style="color:#4073BA;border-left:4px solid #4073BA;padding-left:8px;margin:18px 0 8px;">'
            f'三、{label}计划（里程碑）</h3>'
            + _build_table(["里程碑", "日期", "状态"], rows)
        )

    # 事务
    open_tasks = [t for t in (special.tasks or []) if (t.status or "open") == "open"]
    closed_tasks = [t for t in (special.tasks or []) if (t.status or "open") == "closed"]
    if open_tasks or closed_tasks:
        block = [
            f'<h3 style="color:#4073BA;border-left:4px solid #4073BA;padding-left:8px;margin:18px 0 8px;">'
            f'四、{label}事务</h3>'
        ]
        if open_tasks:
            rows = [
                [t.content or "", t.progress or "", t.owner or "",
                 t.planned_close_date or "", "Open"]
                for t in open_tasks
            ]
            block.append(
                f'<div style="font-weight:600;margin:6px 0;color:#E6A23C;">'
                f'◇ 进行中（{len(open_tasks)} 项）</div>'
                + _build_table(["事务内容", "当前进展", "责任人", "计划闭环时间", "状态"], rows)
            )
        if closed_tasks:
            rows = [
                [t.content or "", t.progress or "", t.owner or "",
                 t.planned_close_date or "", "Closed"]
                for t in closed_tasks
            ]
            block.append(
                f'<div style="font-weight:600;margin:6px 0;color:#67C23A;">'
                f'◇ 本期已闭环（{len(closed_tasks)} 项）</div>'
                + _build_table(["事务内容", "当前进展", "责任人", "计划闭环时间", "状态"], rows)
            )
        sections.append("".join(block))

    # 风险
    risks = special.risks or []
    if risks:
        rows = [
            [r.content or "", r.progress or "", r.owner or "",
             r.planned_close_date or "",
             "Open" if (r.status or "open") == "open" else "Closed"]
            for r in risks
        ]
        sections.append(
            f'<h3 style="color:#F56C6C;border-left:4px solid #F56C6C;padding-left:8px;margin:18px 0 8px;">'
            f'五、风险和问题</h3>'
            + _build_table(["问题内容", "当前进展", "责任人", "计划闭环时间", "状态"], rows)
        )

    body_inner = "".join(sections) or '<div style="color:#909399;">（该报告无内容）</div>'

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f'<body style="{_HTML_BASE_CSS} margin:0;padding:0;background:#f5f7fa;">'
        '<div style="max-width:880px;margin:0 auto;background:#fff;'
        'box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
        # 标题条
        f'<div style="background:linear-gradient(135deg,#4073BA 0%,#2D4A6B 100%);'
        f'color:#fff;padding:18px 24px;">'
        f'<div style="font-size:20px;font-weight:600;">【{_e(label)}周报】{_e(special.name)}</div>'
        f'<div style="margin-top:6px;font-size:13px;opacity:.9;">'
        f'责任人：{_e(special.owner or "-")} &nbsp;|&nbsp; '
        f'报告日期：{today}'
        f'</div></div>'
        # 内容
        f'<div style="padding:8px 24px 24px 24px;">{body_inner}</div>'
        '</div></body></html>'
    )


def _build_eml(special: models.Special, subject: str, to: str, cc: str,
               text_body: str, html_body: str) -> bytes:
    msg = EmailMessage()
    msg["Subject"] = subject or _render_subject(special)
    if to:
        msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["MIME-Version"] = "1.0"
    # Outlook 识别此 header，会以"草稿"形式打开并允许发送
    msg["X-Unsent"] = "1"
    msg.set_content(text_body or "", charset="utf-8")
    msg.add_alternative(html_body or "", subtype="html", charset="utf-8")
    return bytes(msg)


@router.get("/{sid}/report-draft", response_model=schemas.SpecialReportDraft)
def get_report_draft(sid: int, db: Session = Depends(get_db)):
    special = _get_or_404(db, sid)
    _ensure_content(db, special)
    db.refresh(special)
    return schemas.SpecialReportDraft(
        subject=_render_subject(special),
        to=special.email_to or "",
        cc=special.email_cc or "",
        body=_render_report_body(special),
    )


@router.post("/{sid}/report.eml")
def export_report_eml(
    sid: int,
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """根据当前数据 + 前端编辑过的字段生成 .eml 文件供下载。

    payload 字段: subject / to / cc / body （body 是用户编辑过的纯文本）。
    HTML 部分用当前数据库内容现场渲染，保证格式美观；
    纯文本 fallback 用 body（用户编辑过的版本）。
    """
    special = _get_or_404(db, sid)
    _ensure_content(db, special)
    db.refresh(special)

    subject = str(payload.get("subject") or _render_subject(special))
    to = str(payload.get("to") or special.email_to or "")
    cc = str(payload.get("cc") or special.email_cc or "")
    text_body = str(payload.get("body") or _render_report_body(special))
    html_body = _render_report_html(special)

    eml = _build_eml(special, subject, to, cc, text_body, html_body)

    fname_base = "".join(
        c for c in (special.name or "report") if c not in '\\/:*?"<>|'
    ).strip() or "report"
    fname = f"{fname_base}_{datetime.now().strftime('%Y%m%d')}.eml"
    log_op(db, action="导出周报", target=_kind_label(special.kind), target_id=sid,
           detail=f"name={special.name}", user=current_user, request=request)
    return Response(
        content=eml,
        media_type="message/rfc822",
        headers={
            "Content-Disposition": (
                # ASCII fallback + RFC 5987 编码（处理中文文件名）
                f'attachment; filename="report_{sid}.eml"; '
                f"filename*=UTF-8''{url_quote(fname)}"
            ),
        },
    )
