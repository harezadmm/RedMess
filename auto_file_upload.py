#!/usr/bin/env python3
"""
auto_file_upload.py
Auto upload files >50MB ke gofile.io
"""

import httpx
from pathlib import Path

UPLOAD_THRESHOLD_MB = 50

async def should_upload(filepath: Path) -> bool:
    """Check if file should be uploaded"""
    size_mb = filepath.stat().st_size / 1024 / 1024
    return size_mb > UPLOAD_THRESHOLD_MB

async def upload_to_gofile(filepath: Path) -> dict:
    """Upload file to gofile.io"""
    
    # Get best server
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get("https://api.gofile.io/getServer")
        if resp.status_code != 200:
            return {"error": "Failed to get server"}
        
        server = resp.json()["data"]["server"]
        
        # Upload file
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f)}
            upload_resp = await client.post(
                f"https://{server}.gofile.io/uploadFile",
                files=files,
                timeout=300
            )
        
        if upload_resp.status_code != 200:
            return {"error": "Upload failed"}
        
        data = upload_resp.json()
        if data["status"] != "ok":
            return {"error": data.get("status", "Unknown error")}
        
        return {
            "success": True,
            "download_url": data["data"]["downloadPage"],
            "file_id": data["data"]["fileId"],
            "size_mb": round(filepath.stat().st_size / 1024 / 1024, 2)
        }

async def auto_upload_large_files(workspace_path: Path) -> list:
    """Scan workspace and upload large files"""
    results = []
    
    for filepath in workspace_path.rglob("*"):
        if filepath.is_file() and await should_upload(filepath):
            result = await upload_to_gofile(filepath)
            result["filename"] = filepath.name
            result["original_path"] = str(filepath)
            results.append(result)
    
    return results
