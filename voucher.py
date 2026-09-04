# -*- coding: utf-8 -*-
"""
voucher.py
Sistem voucher diskon untuk AmelBot.
"""

from datetime import datetime
import database as db
import config


def validate_voucher(code: str, user_id: int, total: int):
    """
    Validasi voucher. Return (valid, discount_amount, message).
    """
    conn = db.get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM vouchers WHERE code=? AND aktif=1", (code.upper(),))
    row = cur.fetchone()
    
    if not row:
        return False, 0, "Kode voucher tidak valid"
    
    # Check expiry
    if row["expires_at"]:
        try:
            exp = datetime.strptime(row["expires_at"], "%d-%m-%Y %H:%M:%S")
            if datetime.now() > exp:
                return False, 0, "Voucher sudah kadaluarsa"
        except:
            pass
    
    # Check usage limit
    if row["max_uses"] > 0 and row["used_count"] >= row["max_uses"]:
        return False, 0, "Voucher sudah habis digunakan"
    
    # Check user usage
    cur.execute("SELECT COUNT(*) as cnt FROM voucher_usage WHERE user_id=? AND voucher_code=?",
                (user_id, code.upper()))
    if cur.fetchone()["cnt"] > 0:
        return False, 0, "Anda sudah menggunakan voucher ini"
    
    # Check minimum purchase
    if total < row["min_purchase"]:
        from ui import rupiah
        return False, 0, f"Minimal pembelian {rupiah(row['min_purchase'])}"
    
    # Calculate discount
    if row["discount_type"] == "PERCENT":
        discount = int(total * row["discount_value"] / 100)
    else:  # FIXED
        discount = row["discount_value"]
    
    discount = min(discount, total)  # Can't exceed total
    
    return True, discount, "Voucher valid"


def use_voucher(code: str, user_id: int, invoice: str):
    """Mark voucher as used."""
    conn = db.get_conn()
    cur = conn.cursor()
    
    cur.execute("UPDATE vouchers SET used_count=used_count+1 WHERE code=?", (code.upper(),))
    cur.execute("INSERT INTO voucher_usage (user_id, voucher_code, order_invoice, used_at) VALUES (?,?,?,?)",
                (user_id, code.upper(), invoice, db.now_str()))
    conn.commit()


def create_voucher(code: str, discount_type: str, discount_value: int, 
                   min_purchase: int = 0, max_uses: int = 0, expires_at: str = ""):
    """Create new voucher."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT OR REPLACE INTO vouchers 
                   (code, discount_type, discount_value, min_purchase, max_uses, expires_at, aktif)
                   VALUES (?,?,?,?,?,?,1)""",
                (code.upper(), discount_type, discount_value, min_purchase, max_uses, expires_at))
    conn.commit()


def list_vouchers():
    """Get all vouchers."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vouchers ORDER BY aktif DESC, code")
    return cur.fetchall()


def toggle_voucher(code: str):
    """Toggle voucher active status."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE vouchers SET aktif=1-aktif WHERE code=?", (code.upper(),))
    conn.commit()


def delete_voucher(code: str):
    """Delete voucher."""
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM vouchers WHERE code=?", (code.upper(),))
    conn.commit()
