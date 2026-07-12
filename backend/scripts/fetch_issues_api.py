#!/usr/bin/env python
"""按项目拉取问题单（YLS3000 / YLS5000 / YLS8000）+ 数据梳理。

供「问题单管理」的 API 方式调用。后端以 `python fetch_issues_api.py <PROJECT>` 运行，本脚本：
  1) 通过 API 拉取该项目的缺陷原始记录；
  2) 清洗去重、从「缺陷业务编号」提取年/月/日/年月、按「标题」关键词分类；
  3) 把结果以 **JSON 数组** 打印到 stdout，字段＝后端「原始数据」表（英文键）。

────────────────────────────────────────────────────────────────────────────
接入只有三步（其余全部标准化，不用动）：

  第 1 步：把你的 API 调用写进下面的 `fetch_from_api()`（返回 list[dict]，每个
           dict = 平台一条缺陷原始记录）。地址/鉴权/参数就在它上方几行常量里。
  第 2 步：改 `FIELD_MAPPING` 左边的键，对齐你接口返回的**原始字段名**（右边不用动）。
           —— 若你的接口字段名恰好已是中文标准名或英文标准键，这步可跳过（脚本会自动识别）。
  第 3 步：把顶部 `USE_SAMPLE` 改成 False。

改完用 `python fetch_issues_api.py YLS3000` 跑一下，stdout 出现 JSON 数组即接通。
────────────────────────────────────────────────────────────────────────────
"""
import json
import os
import sys

# True：返回示例数据（先把页面/链路跑通）；接入真实 API 后改为 False
USE_SAMPLE = True


# ════════════════════════════════════════════════════════════════════════════
#  ★★★  你只需要改这一段：把已调通的 API 调用写进 fetch_from_api  ★★★
# ════════════════════════════════════════════════════════════════════════════

# 接口地址 & 鉴权：直接写死，或用环境变量（token 建议走环境变量，别提交到库）
API_URL = os.environ.get("ISSUE_API_URL", "https://你的缺陷平台/api/defects")   # TODO 换成真实地址
API_TOKEN = os.environ.get("ISSUE_API_TOKEN", "")                              # TODO 或设环境变量

# 每个项目对应的查询参数（产品/版本/baseline 等，按你的接口填）
PROJECT_PARAMS = {
    "YLS3000": {"product": "YLS3000 V100R001C00"},   # TODO 换成真实参数
    "YLS5000": {"product": "YLS5000 V100R001C00"},   # TODO
    "YLS8000": {"product": "YLS8000 V100R001C00"},   # TODO
}


def fetch_from_api(project: str) -> list:
    """★ 在这里写你的 API 调用，返回 list[dict]（每个 dict = 平台一条缺陷原始记录）。

    只要返回的 dict 的键能在下方 FIELD_MAPPING 左边找到对应（或本身已是中文标准名 /
    英文标准键），剩下的清洗、去重、分类、编码、输出都由本脚本标准化完成。

    下面是一个 requests 版模板——把 3 个 TODO 换成你的接口即可。若你已有调通的代码，
    直接整段替换本函数体、最后 `return 记录数组` 就行；用别的库（httpx/urllib）也没问题。
    """
    try:
        import requests  # 若报「No module named requests」：pip install requests
    except ImportError:
        raise RuntimeError("缺少 requests，请先 `pip install requests`（或改用 urllib/httpx）")

    params = dict(PROJECT_PARAMS.get(project, {}))
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}   # TODO 换成你的鉴权方式

    resp = requests.get(API_URL, headers=headers, params=params, timeout=60)  # TODO 换成你的请求
    resp.raise_for_status()
    body = resp.json()

    # 从返回体里取「记录数组」。按你的返回结构改这一行，常见几种：
    #   records = body                       # 顶层就是数组
    #   records = body["data"]               # 包在 data 里
    #   records = body["result"]["records"]  # 更深的嵌套
    records = body.get("data", body) if isinstance(body, dict) else body
    if not isinstance(records, list):
        raise ValueError(f"未取到记录数组，请检查返回结构（当前为 {type(records).__name__}）")
    return records


# 平台原始字段名 → 中文标准字段名（★ 第 2 步在这里对齐：改**左边**的键为你接口的字段名）
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
    "customer": "客户面",           # 趋势「按客户面」维度
}

# ════════════════════════════════════════════════════════════════════════════
#  ↓↓↓  以下为标准化处理，通常无需改动  ↓↓↓
# ════════════════════════════════════════════════════════════════════════════

# 关键词 → 分类；未命中归入 DEFAULT_CATEGORY
CATEGORIES = {
    "PXW": ["830", "pxw", "pst"],
    "RBPS": ["rbps"],
    "出厂测试": ["出厂测试", "factory_test"],
}
DEFAULT_CATEGORY = "研发"

# 中文标准字段 → 后端「原始数据」表英文键（后端 _RAW_COLS 的键，勿改）
CN_TO_EN = {
    "版本信息": "version", "缺陷业务编号": "issue_id", "标题": "title",
    "当前责任人": "owner", "当前责任人所属小组": "group", "进展": "progress",
    "严重程度": "severity", "严重程度DI值": "severity_di", "根因": "root_cause",
    "解决措施": "solution", "进展记录": "progress_record",
    "预计闭环时间": "estimated_close", "优先级": "priority", "客户面": "customer",
}


def _to_standard(rec: dict) -> dict:
    """把一条记录规整成「中文标准字段」，兼容三种来源键：
      ① 平台原始字段名（走 FIELD_MAPPING 映射）
      ② 记录本身已是中文标准名
      ③ 记录本身已是英文标准键（version/issue_id/...）
    """
    std = {}
    for raw_key, cn in FIELD_MAPPING.items():
        if raw_key in rec and rec[raw_key] is not None:
            std[cn] = rec[raw_key]
    for cn in CN_TO_EN:
        if cn in rec and rec[cn] is not None and cn not in std:
            std[cn] = rec[cn]
    for cn, en in CN_TO_EN.items():
        if en in rec and rec[en] is not None and cn not in std:
            std[cn] = rec[en]
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
