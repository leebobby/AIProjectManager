#!/usr/bin/env python
"""按项目拉取问题单（YLS3000 / YLS5000 / YLS8000）+ 数据梳理。

供「问题单管理」的 API 方式调用。后端以 `python fetch_issues_api.py <PROJECT>` 运行，本脚本：
  1) 通过 API 拉取该项目的缺陷原始记录；
  2) 清洗去重、从「缺陷业务编号」提取年/月/日/年月、按「标题」关键词分类；
  3) 把结果以 **JSON 数组** 打印到 stdout，字段＝后端「原始数据」表（英文键）。

────────────────────────────────────────────────────────────────────────────
DTS(queryList) 接口已接好（POST，pbiName 走 query，分页走 body，自动翻页）。你通常只需两件事：

  ① 更新凭证：顶部 API_HEADERS 里的 Cookie（会话会过期）/ X-HW-APPKEY。
     建议设环境变量 ISSUE_API_COOKIE / ISSUE_API_APPKEY / ISSUE_API_HWID，就不必改代码。
  ② 对齐字段：先跑 `python fetch_issues_api.py YLS3000 --peek` 看 DTS 真实字段名，
     再把 FIELD_MAPPING 左边的键改成对应字段名。
     （若 DTS 字段名本身已是中文标准名/英文标准键，会被自动识别，这步可跳过。）

自测：`python fetch_issues_api.py YLS3000` —— stdout 打出 JSON 数组即接通。
想先用示例数据跑通页面链路，把顶部 USE_SAMPLE 改回 True。
────────────────────────────────────────────────────────────────────────────
"""
import json
import os
import sys

# 已接入真实 DTS API。若想先用示例数据跑通页面/链路，把这里改回 True
USE_SAMPLE = False


# ════════════════════════════════════════════════════════════════════════════
#  ★★★  API 接入配置（已按 DTS queryList 接口接好）：改地址/凭证/参数即可  ★★★
# ════════════════════════════════════════════════════════════════════════════

# 接口地址（POST）；pbiName 走 query，分页 pageSize/pageNo 走 body
API_URL = os.environ.get(
    "ISSUE_API_URL",
    "https://apig.sicarrier.com/api/dtsService/apig/dts/queryList",
)

# ⚠️ 认证头是**明文凭证，仅供调试**：切勿提交到库；Cookie(会话)会过期，失效后更新；
#    上线请改为从环境变量读（下方已留 env 回退，设了环境变量就不用改代码）。
API_HEADERS = {
    "X-HW-ID":      os.environ.get("ISSUE_API_HWID",   "acc90a5778b04aad90a1509c66220042"),
    "X-HW-APPKEY":  os.environ.get("ISSUE_API_APPKEY", "yLF1HruQhOqFoBtmuwAWfw=="),
    "x-app-id":     os.environ.get("ISSUE_API_HWID",   "acc90a5778b04aad90a1509c66220042"),
    "Content-Type": "application/json",
    "Cookie":       os.environ.get("ISSUE_API_COOKIE", "prod_J_SESSION_ID=3bf42a272adba85f3f09f85aa17911bda5b678ddd5a3500e"),
}

PAGE_SIZE = 200   # 每页条数；超过一页自动翻页拉全

# 每个项目 → pbiName（产品基线名）。新增项目照葫芦画瓢加一行
PROJECT_PARAMS = {
    "YLS3000": {"pbiName": "YLS3000 V100R001C00"},
    "YLS5000": {"pbiName": "YLS5000 V100R001C00"},
    "YLS8000": {"pbiName": "YLS8000 V100R001C00"},
}


def _extract_records(body) -> list:
    """从返回体里稳妥地取出「记录数组」，兼容多种常见分页结构。
    若 DTS 的返回结构这里没兜住，跑 `python fetch_issues_api.py YLS3000 --peek` 看结构后改本函数。
    """
    if isinstance(body, list):
        return body
    if not isinstance(body, dict):
        return []
    for path in (("data", "list"), ("data", "records"), ("data", "rows"), ("data", "result"),
                 ("result", "records"), ("result", "list"), ("result", "data"), ("result", "rows"),
                 ("data",), ("rows",), ("list",), ("records",), ("result",)):
        cur = body
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if isinstance(cur, list):
            return cur
    return []


def fetch_from_api(project: str) -> list:
    """调 DTS queryList 拉该项目全部缺陷（自动翻页），返回 list[dict]（平台原始记录）。"""
    try:
        import requests  # 若报「No module named requests」：pip install requests
    except ImportError:
        raise RuntimeError("缺少 requests，请先 `pip install requests`")

    pbi = PROJECT_PARAMS.get(project, {}).get("pbiName") or f"{project} V100R001C00"
    all_rows, page_no = [], 1
    while True:
        resp = requests.post(
            API_URL,
            params={"pbiName": pbi},
            headers=API_HEADERS,
            data=json.dumps({"pageSize": str(PAGE_SIZE), "pageNo": str(page_no)}),
            timeout=60,
            # 若报 SSL 证书错误（内网自签），临时加上：verify=False
        )
        resp.raise_for_status()
        rows = _extract_records(resp.json())
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE or page_no >= 100:   # 末页 or 安全上限（防死循环）
            break
        page_no += 1
    return all_rows


# 平台原始字段名 → 中文标准字段名（★ 用 `--peek` 看到 DTS 真实字段名后，改**左边**的键对齐）
#   例：若接口返回的编号字段叫 "problemNumber"，就把下面 "defect_id" 改成 "problemNumber"。
#   —— 若接口字段名本身已是中文标准名/英文标准键，会被自动识别，无需改。
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


def _write(obj, indent=None):
    # 直接写 UTF-8 字节，避免 Windows 控制台/管道按 GBK 编码导致后端读到乱码
    sys.stdout.buffer.write(json.dumps(obj, ensure_ascii=False, indent=indent).encode("utf-8"))


def main():
    args = sys.argv[1:]
    peek = "--peek" in args
    positional = [a for a in args if not a.startswith("--")]
    project = positional[0] if positional else ""

    records = _sample(project) if USE_SAMPLE else fetch_from_api(project)

    # 调试用：`python fetch_issues_api.py YLS3000 --peek` 打印拉到的条数 + 第一条原始记录，
    # 用它看清 DTS 真实字段名，再回填 FIELD_MAPPING 左边的键。
    if peek:
        first = records[0] if records else {}
        _write({"project": project, "fetched": len(records),
                "first_record_keys": sorted(first.keys()) if isinstance(first, dict) else None,
                "first_record": first}, indent=2)
        return

    _write(_process(records))


if __name__ == "__main__":
    main()
