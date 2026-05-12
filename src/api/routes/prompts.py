"""
Prompt 管理路由 — 按 workspace 隔离的 criteria .txt 文件 CRUD.

共享模板 (base_prompt.txt, macbook_criteria.txt) 由上游提供, 不在列表里显示,
但允许直接 GET (read-only, 用于参考). PUT 禁止改它们。
"""
import os
import aiofiles
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.multitenant import (
    SHARED_PROMPT_FILES,
    current_workspace_id,
    is_prompt_in_workspace,
    strip_prompt_workspace_prefix,
)


router = APIRouter(prefix="/api/prompts", tags=["prompts"])

PROMPTS_DIR = "prompts"


class PromptUpdate(BaseModel):
    """Prompt 更新模型"""
    content: str


def _require_workspace() -> int:
    ws = current_workspace_id()
    if ws is None:
        raise HTTPException(status_code=401, detail="工作区未识别")
    return ws


def _validate_basename(filename: str) -> None:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")


@router.get("")
async def list_prompts():
    """列出当前 workspace 拥有的 prompt 文件 (返回用户可见的去前缀名)。"""
    ws = _require_workspace()
    if not os.path.isdir(PROMPTS_DIR):
        return []
    return sorted(
        strip_prompt_workspace_prefix(f)
        for f in os.listdir(PROMPTS_DIR)
        if is_prompt_in_workspace(ws, f)
    )


@router.get("/{filename}")
async def get_prompt(filename: str):
    """读 prompt 文件内容。

    用户传去前缀的名字 (e.g. "macbook_criteria")。函数自动按 workspace 拼前缀。
    共享模板 (base_prompt.txt / macbook_criteria.txt) 允许直接读, 不要前缀。
    """
    _validate_basename(filename)
    ws = _require_workspace()

    # 共享模板分支 — 任何 workspace 都可读。
    if filename in SHARED_PROMPT_FILES:
        filepath = os.path.join(PROMPTS_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Prompt 文件未找到")
        async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
            content = await f.read()
        return {"filename": filename, "content": content, "shared": True}

    # workspace 路径分支
    scoped = f"ws{ws}__{filename}.txt" if not filename.endswith(".txt") else f"ws{ws}__{filename}"
    filepath = os.path.join(PROMPTS_DIR, scoped)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Prompt 文件未找到")
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()
    return {"filename": filename, "content": content, "shared": False}


@router.put("/{filename}")
async def update_prompt(filename: str, prompt_update: PromptUpdate):
    """改 prompt 文件内容。共享模板拒绝写。"""
    _validate_basename(filename)
    ws = _require_workspace()

    if filename in SHARED_PROMPT_FILES:
        raise HTTPException(status_code=403, detail="共享模板只读, 复制到工作区后编辑")

    scoped = f"ws{ws}__{filename}.txt" if not filename.endswith(".txt") else f"ws{ws}__{filename}"
    filepath = os.path.join(PROMPTS_DIR, scoped)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Prompt 文件未找到")
    try:
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(prompt_update.content)
        return {"message": f"Prompt 文件 '{filename}' 更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入文件时出错: {e}")
