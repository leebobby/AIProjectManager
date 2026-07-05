#!/usr/bin/env python
"""按项目拉取问题单（YLS3000 / YLS5000 / YLS8000）+ 数据梳理。

供「问题单管理」的 API 方式调用。后端以 `python fetch_issues_api.py <PROJECT>` 运行，本脚本：
  1) 通过 API 拉取该项目的缺陷原始记录（你已调通的接口 —— 填到 fetch_from_api 即可）；
  2) 复用原 defect_auto_report/processor.py 的处理方式：清洗去重、从「缺陷业务编号」提取
     年/月/日/年月、按「标题」关键词分类；
  3) 把结果以 **JSON 数组** 打印到 stdout，字段＝后端「原始数据」表（英文键）。

接入步骤：
  1) 把已调通的 API 访问代码粘到 fetch_from_api()，返回 list[dict]（键＝平台原始字段名）；
  2) 按你的接口改 PROJECT_PARAMS / FIELD_MAPPING / CATEGORIES；
  3) 把 USE_SAMPLE 改为 False。
"""
import json
import sys

# True：返回示例数据（先把页面/链路跑通）；接入真实 API 后改为 False
USE_SAMPLE = True

# 每个项目对应的 API 参数（按你的接口填，例如产品/版本/baseline）
PROJECT_PARAMS = {
    "YLS3000": {"product": "YLS3000 V100R001C00"},   # TODO: 换成真实参数
    "YLS5000": {"product": "YLS5000 V100R001C00"},   # TODO
    "YLS8000": {"product": "YLS8000 V100R001C00"},   # TODO
}

# 平台返回字段名 → 标准中文字段名（同 config.yaml 的 field_mapping；按实际接口改左边）
FIELD_MAPPING = {
    "version": "版本信息",
    "defect_id": "缺陷业务编号",
    "title": "标题",
    "assignee": "当前责任人",
    "team": "当前责任人所属小组",
    "progress": "进展",
    "severity": "严重程度",
    "severity_di": "严重程度DI值",
    "priority": "优先级",
    "root_cause": "根因",
    "solution": "解决措施",
    "progress_record": "进展记录",
    "estimated_close": "预计闭环时间",
    "customer": "客户面",           # 趋势「按客户面」维度；按实际接口字段改左边
}

# 关键词 → 分类（同 config.yaml 的 categories）；未命中归入 DEFAULT_CATEGORY
CATEGORIES = {
    "PXW": ["830", "pxw", "pst"],
    "RBPS": ["rbps"],
    "出厂测试": ["出厂测试", "factory_test"],
}
DEFAULT_CATEGORY = "研发"

# 标准中文字段 → 后端「原始数据」表英文键
CN_TO_EN = {
    "版本信息": "version", "缺陷业务编号": "issue_id", "标题": "title",
    "当前责任人": "owner", "当前责任人所属小组": "group", "进展": "progress",
    "严重程度": "severity", "严重程度DI值": "severity_di", "根因": "root_cause",
    "解决措施": "solution", "进展记录": "progress_record",
    "预计闭环时间": "estimated_close", "优先级": "priority", "客户面": "customer",
}


def fetch_from_api(project: str) -> list:
    """TODO: 把已调通的 API 访问代码粘到这里，返回 list[dict]（键＝平台原始字段名）。

    示例（伪代码，按你的实际接口替换）：
        import requests
        params = PROJECT_PARAMS[project]
        token = get_token(...)                       # 你的鉴权方式
        resp = requests.get(API_URL,
                            headers={"Authorization": f"Bearer {token}"},
                            params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()["data"]                   # list[dict]
    """
    raise NotImplementedError(
        "请把 API 访问代码填到 fetch_from_api()，并把脚本顶部的 USE_SAMPLE 改为 False"
    )


# ─── 数据梳理（移植自 defect_auto_report/processor.py，纯 Python 版）──────────────
def _to_standard(rec: dict) -> dict:
    """平台原始字段 → 中文标准字段；也兼容已是中文键的记录。"""
    std = {}
    for raw_key, cn in FIELD_MAPPING.items():
        if raw_key in rec and rec[raw_key] is not None:
            std[cn] = rec[raw_key]
    for cn in CN_TO_EN:
        if cn in rec and rec[cn] is not None and cn not in std:
            std[cn] = rec[cn]
    return std


def _classify(title: str) -> str:
    t = (title or "").lower()
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw.lower() in t:
                return cat
    return DEFAULT_CATEGORY


def _process(records: list) -> list:
    """清洗去重 + 提取日期维度 + 标题分类。"""
    out, seen = [], set()
    for rec in records:
        if not isinstance(rec, dict):
            continue
        std = _to_standard(rec)
        did = str(std.get("缺陷业务编号", "") or "").strip()
        if not did or did in seen:           # 去空 + 按编号去重
            continue
        seen.add(did)

        is_sdts = did.startswith("SDTS")     # 编号格式 SDTS+年(4)+月(2)+日(2)+序号
        year = did[4:8] if is_sdts else ""
        month = did[8:10] if is_sdts else ""
        day = did[10:12] if is_sdts else ""

        row = {en: str(std.get(cn, "") or "").strip() for cn, en in CN_TO_EN.items()}
        row["is_sdts"] = "是" if is_sdts else ""
        row["year"] = year
        row["month"] = month
        row["date"] = day
        row["year_month"] = f"{year}-{month}" if is_sdts else ""
        row["category"] = _classify(row.get("title", ""))
        out.append(row)
    return out


def _sample(project: str) -> list:
    """示例数据：SDTS 编号 + 含关键词标题 + 客户面，便于看到分组/客户面/趋势生效。

    数量随「当天」小幅波动（按日期取模），这样连续几天采集能看到趋势折线有变化。
    """
    import datetime as _dt
    sev = ["严重", "一般", "提示"]
    teams = ["AFK", "SE", "TFO"]
    customers = ["华东-A厂", "华南-B厂", "华北-C厂"]
    titles = ["[示例]PXW 830 偶发停机", "[示例]RBPS 流程异常",
              "[示例]出厂测试 用例失败", "[示例]在线分析卡顿"]
    n = 15 + (_dt.date.today().day % 6)   # 15~20 条，随日变化
    out = []
    for i in range(1, n + 1):
        did = f"SDTS2026{((i % 6) + 1):02d}{((i % 27) + 1):02d}{i:03d}"
        out.append({
            "版本信息": project, "缺陷业务编号": did, "标题": titles[i % len(titles)],
            "当前责任人": "张三", "当前责任人所属小组": teams[i % 3],
            "客户面": customers[i % len(customers)],
            "进展": "处理中", "严重程度": sev[i % 3],
        })
    return out


def main():
    project = sys.argv[1] if len(sys.argv) > 1 else ""
    records = _sample(project) if USE_SAMPLE else fetch_from_api(project)
    rows = _process(records)
    # 直接写 UTF-8 字节，避免 Windows 控制台/管道按 GBK 编码导致后端读到乱码
    sys.stdout.buffer.write(json.dumps(rows, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
