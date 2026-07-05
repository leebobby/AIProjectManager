"""后台调度：APScheduler 跑定时任务。

当前任务：
- daily_ddl_scan：每天 08:00 扫描 special_tasks / special_risks，
  对未关闭、planned_close_date 落在未来 3 天内/已逾期的，给 owner_user_id 发通知。

设计原则：
- 任何异常吞掉，不能阻塞 FastAPI
- 同一条记录每天最多发一条（用一个简单内存去重，进程重启会重置；够用）
- 调度器作用域是进程内，未来上多 worker 需要换 Redis 锁
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

import models
from database import SessionLocal
from notify import dispatch

logger = logging.getLogger("scheduler")

_DATE_RE = re.compile(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})")

_sent_today: set[tuple[str, int, str]] = set()  # (source_type, id, "soon"|"overdue") for dedupe per process-day


def _parse_date(s: str) -> Optional[date]:
    if not s:
        return None
    m = _DATE_RE.search(s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _scan_specials(db, today: date) -> int:
    soon_threshold = today + timedelta(days=3)
    cnt = 0

    for model, source_type, kind_label in (
        (models.SpecialTask, "special_task", "事务"),
        (models.SpecialRisk, "special_risk", "风险"),
    ):
        rows = db.query(model).filter(model.status == "open").all()
        for r in rows:
            if not r.owner_user_id:
                continue
            d = _parse_date(r.planned_close_date)
            if d is None:
                continue
            link = f"/specials/{r.special_id}"
            preview = (r.content or "").strip().splitlines()[0][:60] if r.content else ""

            if d < today:
                key = (source_type, r.id, "overdue")
                if key in _sent_today:
                    continue
                _sent_today.add(key)
                dispatch(
                    db, kind="overdue",
                    title=f"[已逾期] {kind_label}：{preview}",
                    body=f"计划闭环日期 {r.planned_close_date}，已逾期 {(today - d).days} 天",
                    link=link, source_type=source_type, source_id=r.id,
                    recipient_ids=[r.owner_user_id], extra_subs=True,
                )
                cnt += 1
            elif d <= soon_threshold:
                key = (source_type, r.id, "soon")
                if key in _sent_today:
                    continue
                _sent_today.add(key)
                dispatch(
                    db, kind="due_soon",
                    title=f"[临期提醒] {kind_label}：{preview}",
                    body=f"计划闭环日期 {r.planned_close_date}，剩 {(d - today).days} 天",
                    link=link, source_type=source_type, source_id=r.id,
                    recipient_ids=[r.owner_user_id], extra_subs=True,
                )
                cnt += 1
    return cnt


def daily_ddl_scan() -> None:
    """每天 08:00 跑一次。"""
    global _sent_today
    today = date.today()
    # 每天清空一次去重集合（按日期）
    if not _sent_today or any(
        # 偷个懒：直接清；日期切换交给 scheduler 时间触发即可
        True for _ in [None]
    ):
        _sent_today = set()

    db = SessionLocal()
    try:
        n = _scan_specials(db, today)
        logger.info("daily_ddl_scan: %s 条通知已发", n)
    except Exception as e:
        logger.exception("daily_ddl_scan 失败: %s", e)
    finally:
        db.close()


def daily_issue_snapshot() -> None:
    """每天 07:30 采集各项目问题单快照：维度数字入库、明细落文件。

    未配置 API 脚本或项目列表则跳过；单项目失败不影响其它项目。
    """
    from routers.config import _load as _load_config  # 延迟导入避免循环依赖
    cfg = _load_config()
    projects = cfg.get("issue_api_projects") or []
    if not (cfg.get("issue_api_script_path") or "").strip() or not projects:
        return
    from routers.issues import _take_snapshot  # 延迟导入
    db = SessionLocal()
    try:
        ok = 0
        for p in projects:
            try:
                _take_snapshot(db, p, source="api")
                ok += 1
            except Exception as e:  # noqa: BLE001 — 单项目失败继续
                logger.warning("issue snapshot %s 失败: %s", p, e)
        logger.info("daily_issue_snapshot: %s/%s 个项目已采集", ok, len(projects))
    except Exception as e:
        logger.exception("daily_issue_snapshot 失败: %s", e)
    finally:
        db.close()


_scheduler: Optional[BackgroundScheduler] = None


def start() -> None:
    """在 main.py 启动时调用一次。"""
    global _scheduler
    if _scheduler is not None:
        return
    sched = BackgroundScheduler(timezone="Asia/Shanghai")
    # 每天早上 8:00：临期/逾期扫描
    sched.add_job(daily_ddl_scan, "cron", hour=8, minute=0, id="daily_ddl_scan",
                  replace_existing=True)
    # 每天 7:30：问题单快照采集（数字入库 + 明细落文件）
    sched.add_job(daily_issue_snapshot, "cron", hour=7, minute=30, id="daily_issue_snapshot",
                  replace_existing=True)
    sched.start()
    _scheduler = sched
    logger.info("APScheduler started; daily_ddl_scan@08:00, daily_issue_snapshot@07:30")
