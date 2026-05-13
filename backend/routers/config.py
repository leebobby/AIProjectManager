import json
import pathlib

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/config", tags=["config"])

CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config.json"


def _load() -> dict:
    if not CONFIG_PATH.exists():
        return {"current_stages": []}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


@router.get("")
def get_config():
    """读取项目级配置，前端启动时拉取一次即可。"""
    try:
        return _load()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"配置文件解析失败: {exc}")
