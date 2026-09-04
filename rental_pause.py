#!/usr/bin/env python3
"""
rental_pause.py
Pause/resume rental system
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "umiagent.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def pause_rental(user_id: int) -> dict:
    """Pause rental for user_id"""
    conn = get_db()
    cur = conn.cursor()
    
    # Check if rental exists
    cur.execute("SELECT * FROM rentals WHERE user_id = ?", (user_id,))
    rental = cur.fetchone()
    
    if not rental:
        conn.close()
        return {"error": "Rental tidak ditemukan"}
    
    # Calculate remaining time
    now = int(time.time())
    remaining_seconds = rental["end_time"] - now
    
    if remaining_seconds <= 0:
        conn.close()
        return {"error": "Rental sudah expired"}
    
    # Store pause state (add paused_at column if not exists)
    try:
        cur.execute("ALTER TABLE rentals ADD COLUMN paused_at INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    cur.execute("""
        UPDATE rentals 
        SET paused_at = ? 
        WHERE user_id = ?
    """, (now, user_id))
    conn.commit()
    conn.close()
    
    return {
        "paused": True,
        "user_id": user_id,
        "remaining_seconds": remaining_seconds,
        "remaining_minutes": round(remaining_seconds / 60, 1)
    }

def resume_rental(user_id: int) -> dict:
    """Resume rental for user_id"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM rentals WHERE user_id = ?", (user_id,))
    rental = cur.fetchone()
    
    if not rental:
        conn.close()
        return {"error": "Rental tidak ditemukan"}
    
    paused_at = rental.get("paused_at", 0)
    if paused_at == 0:
        conn.close()
        return {"error": "Rental tidak dalam status pause"}
    
    # Calculate time extension
    now = int(time.time())
    paused_duration = now - paused_at
    new_end_time = rental["end_time"] + paused_duration
    
    cur.execute("""
        UPDATE rentals 
        SET end_time = ?, paused_at = 0 
        WHERE user_id = ?
    """, (new_end_time, user_id))
    conn.commit()
    conn.close()
    
    return {
        "resumed": True,
        "user_id": user_id,
        "extended_seconds": paused_duration,
        "new_end_time": new_end_time
    }

def is_rental_active(user_id: int) -> bool:
    """Check if rental is active (considering pause state)"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM rentals WHERE user_id = ?", (user_id,))
    rental = cur.fetchone()
    conn.close()
    
    if not rental:
        return False
    
    now = int(time.time())
    
    # If paused, always active until resumed
    if rental.get("paused_at", 0) > 0:
        return True
    
    # Check normal expiry
    return rental["end_time"] > now
