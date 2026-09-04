# -*- coding: utf-8 -*-
"""
levels.py
Sistem level/rank user berdasarkan total pembelian.
"""

import database as db

LEVELS = [
    {"name": "Bronze", "min": 0, "icon": "🥉", "discount": 0},
    {"name": "Silver", "min": 100000, "icon": "🥈", "discount": 2},
    {"name": "Gold", "min": 500000, "icon": "🥇", "discount": 5},
    {"name": "Platinum", "min": 2000000, "icon": "💎", "discount": 10},
    {"name": "Diamond", "min": 5000000, "icon": "💠", "discount": 15},
]


def get_level(total_spent: int):
    """Get user level based on total spent."""
    for i in range(len(LEVELS) - 1, -1, -1):
        if total_spent >= LEVELS[i]["min"]:
            return LEVELS[i]
    return LEVELS[0]


def get_user_level(user_id: int):
    """Get level for user."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT total_spent FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        return LEVELS[0]
    return get_level(row["total_spent"] or 0)


def next_level(total_spent: int):
    """Get next level info."""
    current = get_level(total_spent)
    for lvl in LEVELS:
        if lvl["min"] > total_spent:
            return lvl, lvl["min"] - total_spent
    return None, 0


def update_user_stats(user_id: int, amount: int):
    """Update user total spent and order count."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("""UPDATE users 
                   SET total_spent=total_spent+?, total_orders=total_orders+1
                   WHERE user_id=?""", (amount, user_id))
    conn.commit()


def apply_level_discount(user_id: int, amount: int) -> int:
    """Apply level discount to amount, return discount."""
    level = get_user_level(user_id)
    if level["discount"] > 0:
        return int(amount * level["discount"] / 100)
    return 0
