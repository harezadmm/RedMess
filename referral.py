# -*- coding: utf-8 -*-
"""
referral.py
Sistem referral dengan reward.
"""

import random
import string
import database as db
import config


REFERRAL_REWARD = 5000  # Rp untuk referrer
REFEREE_REWARD = 3000   # Rp untuk yang didaftar


def generate_code(user_id: int) -> str:
    """Generate unique referral code."""
    # Format: REF + 6 random chars
    while True:
        code = "REF" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE referral_code=?", (code,))
        if not cur.fetchone():
            cur.execute("UPDATE users SET referral_code=? WHERE user_id=?", (code, user_id))
            conn.commit()
            return code


def get_referral_code(user_id: int) -> str:
    """Get or create referral code for user."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT referral_code FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row and row["referral_code"]:
        return row["referral_code"]
    return generate_code(user_id)


def apply_referral(referred_id: int, referral_code: str) -> bool:
    """Apply referral code when user joins. Return success."""
    conn = db.get_conn()
    cur = conn.cursor()
    
    # Find referrer
    cur.execute("SELECT user_id FROM users WHERE referral_code=?", (referral_code.upper(),))
    row = cur.fetchone()
    if not row:
        return False
    
    referrer_id = row["user_id"]
    
    # Can't refer yourself
    if referrer_id == referred_id:
        return False
    
    # Check if already has referrer
    cur.execute("SELECT referred_by FROM users WHERE user_id=?", (referred_id,))
    row = cur.fetchone()
    if row and row["referred_by"]:
        return False
    
    # Apply referral
    cur.execute("UPDATE users SET referred_by=? WHERE user_id=?", (referrer_id, referred_id))
    cur.execute("INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (?,?,?)",
                (referrer_id, referred_id, db.now_str()))
    
    # Give rewards
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (REFERRAL_REWARD, referrer_id))
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (REFEREE_REWARD, referred_id))
    
    conn.commit()
    return True


def get_referral_stats(user_id: int):
    """Get referral stats for user."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM referrals WHERE referrer_id=?", (user_id,))
    total = cur.fetchone()["total"]
    
    cur.execute("""SELECT COUNT(*) as claimed FROM referrals 
                   WHERE referrer_id=? AND reward_claimed=1""", (user_id,))
    claimed = cur.fetchone()["claimed"]
    
    return {"total": total, "claimed": claimed, "earnings": total * REFERRAL_REWARD}
