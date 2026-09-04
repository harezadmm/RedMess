#!/usr/bin/env python3
"""
workspace_manager.py
Dynamic workspace router per user_id
Path: D:/hermes/workspace/{user_id}/
"""

import os
from pathlib import Path

WORKSPACE_BASE = Path("D:/hermes/workspace")

def get_user_workspace(user_id: int) -> Path:
    """Get workspace directory for user_id"""
    workspace = WORKSPACE_BASE / str(user_id)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace

def list_user_files(user_id: int) -> list:
    """List all files in user workspace"""
    workspace = get_user_workspace(user_id)
    files = []
    for root, dirs, filenames in os.walk(workspace):
        for filename in filenames:
            filepath = Path(root) / filename
            size = filepath.stat().st_size
            files.append({
                "name": filename,
                "path": str(filepath.relative_to(workspace)),
                "size": size,
                "size_mb": round(size / 1024 / 1024, 2)
            })
    return files

def get_workspace_stats(user_id: int) -> dict:
    """Get workspace statistics"""
    workspace = get_user_workspace(user_id)
    files = list_user_files(user_id)
    total_size = sum(f["size"] for f in files)
    
    return {
        "path": str(workspace),
        "file_count": len(files),
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "files": files
    }

def clear_workspace(user_id: int) -> dict:
    """Clear all files in workspace"""
    import shutil
    workspace = get_user_workspace(user_id)
    
    stats_before = get_workspace_stats(user_id)
    
    for item in workspace.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    
    return {
        "cleared": True,
        "files_deleted": stats_before["file_count"],
        "space_freed_mb": stats_before["total_size_mb"]
    }
