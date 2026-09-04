# -*- coding: utf-8 -*-
"""
database.py
Semua operasi SQLite untuk AmelBot.
"""

import os
import random
import sqlite3
import string
from datetime import datetime

import config

_CONN = None


# ==========================================================
# KONEKSI
# ==========================================================
def get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        _CONN = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _CONN.row_factory = sqlite3.Row
        _CONN.execute("PRAGMA journal_mode=WAL;")
    return _CONN


def now_str() -> str:
    return config.sekarang().strftime("%d-%m-%Y %H:%M:%S")


# ==========================================================
# INIT
# ==========================================================
def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            balance     INTEGER DEFAULT 0,
            banned      INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            total_orders INTEGER DEFAULT 0,
            referral_code TEXT,
            referred_by INTEGER,
            joined_at   TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice     TEXT UNIQUE,
            user_id     INTEGER,
            username    TEXT,
            kategori    TEXT,
            produk      TEXT,
            negara      TEXT,
            jumlah      INTEGER,
            harga       INTEGER,
            status      TEXT,
            created_at  TEXT,
            updated_at  TEXT,
            catatan     TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            negara  TEXT,
            jumlah  INTEGER,
            harga   INTEGER,
            PRIMARY KEY (negara, jumlah)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            code    TEXT PRIMARY KEY,
            name    TEXT,
            flag    TEXT,
            file    TEXT,
            aktif   INTEGER DEFAULT 1,
            urutan  INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            key     TEXT PRIMARY KEY,
            label   TEXT,
            icon    TEXT,
            aktif   INTEGER DEFAULT 1,
            urutan  INTEGER DEFAULT 0,
            style   TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS vouchers (
            code TEXT PRIMARY KEY,
            discount_type TEXT,
            discount_value INTEGER,
            min_purchase INTEGER DEFAULT 0,
            max_uses INTEGER DEFAULT 0,
            used_count INTEGER DEFAULT 0,
            expires_at TEXT,
            aktif INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS voucher_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            voucher_code TEXT,
            order_invoice TEXT,
            used_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            referred_id INTEGER,
            reward_claimed INTEGER DEFAULT 0,
            created_at TEXT,
            PRIMARY KEY (referrer_id, referred_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            rating INTEGER,
            message TEXT,
            approved INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            urutan INTEGER DEFAULT 0,
            aktif INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS panels (
            code    TEXT PRIMARY KEY,
            name    TEXT,
            spek    TEXT,
            price   INTEGER DEFAULT 0,
            aktif   INTEGER DEFAULT 1,
            urutan  INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key    TEXT PRIMARY KEY,
            value  TEXT
        )
    """)

    conn.commit()
    seed_countries()
    seed_menus()
    seed_panels()
    seed_settings()


def seed_countries() -> None:
    """Isi daftar negara awal hanya bila tabel masih kosong."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM countries")
    if cur.fetchone()["c"] == 0:
        for i, (code, name, flag) in enumerate(config.SEED_COUNTRIES):
            cur.execute(
                "INSERT OR IGNORE INTO countries (code, name, flag, file, aktif, urutan) "
                "VALUES (?,?,?,?,1,?)",
                (code, name, flag, f"{code}.txt", i),
            )
        conn.commit()


def seed_menus() -> None:
    """Isi daftar menu bawaan bila tabel masih kosong."""
    conn = get_conn()
    cur = conn.cursor()
    for i, (key, label, icon, style) in enumerate(config.SEED_MENUS):
        cur.execute("SELECT 1 FROM menus WHERE key=?", (key,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO menus (key, label, icon, aktif, urutan, style) "
                "VALUES (?,?,?,1,?,?)",
                (key, label, icon, i, style),
            )
    conn.commit()


def seed_panels() -> None:
    """Isi produk panel awal bila tabel masih kosong."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM panels")
    if cur.fetchone()["c"] == 0:
        for i, (code, name, spek, price) in enumerate(config.SEED_PANELS):
            cur.execute(
                "INSERT OR IGNORE INTO panels (code, name, spek, price, aktif, urutan) "
                "VALUES (?,?,?,?,1,?)",
                (code, name, spek, price, i),
            )
        conn.commit()


def seed_settings() -> None:
    defaults = {
        "store_name": config.STORE_NAME,
        "owner_username": config.OWNER_USERNAME,
        "owner_name": config.OWNER_NAME,
        "welcome_note": "Silakan pilih menu di bawah ini.",
        "quantities": ",".join(str(q) for q in config.SEED_QUANTITIES),
        "rate": str(config.DEFAULT_RATE),
    }
    for k, v in defaults.items():
        if get_setting(k) is None:
            set_setting(k, v)


# ==========================================================
# SETTINGS
# ==========================================================
def get_setting(key: str, default=None):
    cur = get_conn().cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row["value"] if row else default


def set_setting(key: str, value) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()


# ==========================================================
# USERS
# ==========================================================
def ensure_user(user_id: int, username: str = "", first_name: str = "") -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cur.fetchone():
        cur.execute(
            "UPDATE users SET username=?, first_name=? WHERE user_id=?",
            (username or "", first_name or "", user_id),
        )
    else:
        cur.execute(
            "INSERT INTO users (user_id, username, first_name, balance, banned, joined_at) "
            "VALUES (?,?,?,0,0,?)",
            (user_id, username or "", first_name or "", now_str()),
        )
    conn.commit()


def get_user(user_id: int):
    cur = get_conn().cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()


def all_user_ids() -> list:
    cur = get_conn().cursor()
    cur.execute("SELECT user_id FROM users WHERE banned=0")
    return [r["user_id"] for r in cur.fetchall()]


def count_users() -> int:
    cur = get_conn().cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    return cur.fetchone()["c"]


# ==========================================================
# PRICES
# ==========================================================
def get_price(negara: str, jumlah: int) -> int:
    cur = get_conn().cursor()
    cur.execute("SELECT harga FROM prices WHERE negara=? AND jumlah=?", (negara, int(jumlah)))
    row = cur.fetchone()
    if row:
        return int(row["harga"])
    try:
        rate = int(get_setting("rate", config.DEFAULT_RATE))
    except (TypeError, ValueError):
        rate = config.DEFAULT_RATE
    return int(jumlah) * rate


def set_price(negara: str, jumlah: int, harga: int) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO prices (negara, jumlah, harga) VALUES (?,?,?) "
        "ON CONFLICT(negara, jumlah) DO UPDATE SET harga=excluded.harga",
        (negara, int(jumlah), int(harga)),
    )
    conn.commit()


def quantities() -> list:
    raw = get_setting("quantities", ",".join(str(q) for q in config.SEED_QUANTITIES))
    out = []
    for p in str(raw).replace(" ", "").split(","):
        if p.isdigit() and int(p) > 0:
            out.append(int(p))
    return sorted(set(out)) or list(config.SEED_QUANTITIES)


def set_quantities(values: list) -> None:
    clean = sorted({int(v) for v in values if int(v) > 0})
    set_setting("quantities", ",".join(str(v) for v in clean))


def price_map(negara: str) -> dict:
    return {q: get_price(negara, q) for q in quantities()}


def delete_prices(negara: str) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM prices WHERE negara=?", (negara,))
    conn.commit()


# ==========================================================
# COUNTRIES
# ==========================================================
def countries(active_only: bool = False) -> list:
    cur = get_conn().cursor()
    if active_only:
        cur.execute("SELECT * FROM countries WHERE aktif=1 ORDER BY urutan, name")
    else:
        cur.execute("SELECT * FROM countries ORDER BY urutan, name")
    return cur.fetchall()


def get_country(code: str):
    cur = get_conn().cursor()
    cur.execute("SELECT * FROM countries WHERE code=?", (code,))
    return cur.fetchone()


def add_country(code: str, name: str, flag: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(urutan), -1) AS m FROM countries")
    urut = cur.fetchone()["m"] + 1
    conn.execute(
        "INSERT INTO countries (code, name, flag, file, aktif, urutan) VALUES (?,?,?,?,1,?)",
        (code, name, flag, f"{code}.txt", urut),
    )
    conn.commit()


def update_country(code: str, name: str = None, flag: str = None,
                   aktif: int = None) -> None:
    row = get_country(code)
    if not row:
        return
    conn = get_conn()
    conn.execute(
        "UPDATE countries SET name=?, flag=?, aktif=? WHERE code=?",
        (
            name if name is not None else row["name"],
            flag if flag is not None else row["flag"],
            row["aktif"] if aktif is None else int(aktif),
            code,
        ),
    )
    conn.commit()


def delete_country(code: str) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM countries WHERE code=?", (code,))
    conn.commit()
    delete_prices(code)


def country_exists(code: str) -> bool:
    return get_country(code) is not None


# ==========================================================
# MENU (tombol bisa disembunyikan / diubah)
# ==========================================================
def menus(active_only: bool = False) -> list:
    cur = get_conn().cursor()
    if active_only:
        cur.execute("SELECT * FROM menus WHERE aktif=1 ORDER BY urutan")
    else:
        cur.execute("SELECT * FROM menus ORDER BY urutan")
    return cur.fetchall()


def get_menu(key: str):
    cur = get_conn().cursor()
    cur.execute("SELECT * FROM menus WHERE key=?", (key,))
    return cur.fetchone()


def update_menu(key: str, label: str = None, icon: str = None,
                aktif: int = None) -> None:
    row = get_menu(key)
    if not row:
        return
    conn = get_conn()
    conn.execute(
        "UPDATE menus SET label=?, icon=?, aktif=? WHERE key=?",
        (
            label if label else row["label"],
            icon if icon else row["icon"],
            row["aktif"] if aktif is None else int(aktif),
            key,
        ),
    )
    conn.commit()


# ==========================================================
# PRODUK PANEL
# ==========================================================
def panels(active_only: bool = False) -> list:
    cur = get_conn().cursor()
    if active_only:
        cur.execute("SELECT * FROM panels WHERE aktif=1 ORDER BY urutan, price")
    else:
        cur.execute("SELECT * FROM panels ORDER BY urutan, price")
    return cur.fetchall()


def get_panel(code: str):
    cur = get_conn().cursor()
    cur.execute("SELECT * FROM panels WHERE code=?", (code,))
    return cur.fetchone()


def add_panel(code: str, name: str, spek: str, price: int) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(urutan), -1) AS m FROM panels")
    urut = cur.fetchone()["m"] + 1
    conn.execute(
        "INSERT INTO panels (code, name, spek, price, aktif, urutan) VALUES (?,?,?,?,1,?)",
        (code, name, spek, int(price), urut),
    )
    conn.commit()


def update_panel(code: str, name: str = None, spek: str = None,
                 price: int = None, aktif: int = None) -> None:
    row = get_panel(code)
    if not row:
        return
    conn = get_conn()
    conn.execute(
        "UPDATE panels SET name=?, spek=?, price=?, aktif=? WHERE code=?",
        (
            name if name is not None else row["name"],
            spek if spek is not None else row["spek"],
            row["price"] if price is None else int(price),
            row["aktif"] if aktif is None else int(aktif),
            code,
        ),
    )
    conn.commit()


def delete_panel(code: str) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM panels WHERE code=?", (code,))
    conn.commit()


def panel_exists(code: str) -> bool:
    return get_panel(code) is not None


# ==========================================================
# ORDERS
# ==========================================================
def generate_invoice() -> str:
    charset = string.ascii_uppercase + string.digits
    while True:
        code = "AMEL-" + "".join(random.choice(charset) for _ in range(6))
        cur = get_conn().cursor()
        cur.execute("SELECT id FROM orders WHERE invoice=?", (code,))
        if not cur.fetchone():
            return code


def create_order(user_id: int, username: str, kategori: str, produk: str,
                 negara: str, jumlah: int, harga: int) -> str:
    invoice = generate_invoice()
    conn = get_conn()
    conn.execute(
        "INSERT INTO orders (invoice, user_id, username, kategori, produk, negara, "
        "jumlah, harga, status, created_at, updated_at, catatan) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (invoice, user_id, username or "", kategori, produk, negara or "",
         int(jumlah), int(harga), "PENDING", now_str(), now_str(), ""),
    )
    conn.commit()
    return invoice


def get_order(invoice: str):
    cur = get_conn().cursor()
    cur.execute("SELECT * FROM orders WHERE invoice=?", (invoice,))
    return cur.fetchone()


def update_status(invoice: str, status: str, catatan: str = None) -> None:
    conn = get_conn()
    if catatan is None:
        conn.execute(
            "UPDATE orders SET status=?, updated_at=? WHERE invoice=?",
            (status, now_str(), invoice),
        )
    else:
        conn.execute(
            "UPDATE orders SET status=?, updated_at=?, catatan=? WHERE invoice=?",
            (status, now_str(), catatan, invoice),
        )
    conn.commit()


def user_orders(user_id: int, limit: int = 10) -> list:
    cur = get_conn().cursor()
    cur.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    return cur.fetchall()


def pending_orders(limit: int = 20) -> list:
    cur = get_conn().cursor()
    cur.execute(
        "SELECT * FROM orders WHERE status IN ('PENDING','CHECKING') "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    return cur.fetchall()


def count_user_success(user_id: int) -> int:
    cur = get_conn().cursor()
    cur.execute(
        "SELECT COUNT(*) AS c FROM orders WHERE user_id=? AND status='SUCCESS'",
        (user_id,),
    )
    return cur.fetchone()["c"]


def sum_user_spend(user_id: int) -> int:
    cur = get_conn().cursor()
    cur.execute(
        "SELECT COALESCE(SUM(harga),0) AS s FROM orders WHERE user_id=? AND status='SUCCESS'",
        (user_id,),
    )
    return int(cur.fetchone()["s"])


def stats() -> dict:
    cur = get_conn().cursor()
    data = {}
    cur.execute("SELECT COUNT(*) AS c FROM orders")
    data["total_order"] = cur.fetchone()["c"]
    for st in ("SUCCESS", "PENDING", "CHECKING", "CANCEL"):
        cur.execute("SELECT COUNT(*) AS c FROM orders WHERE status=?", (st,))
        data[st.lower()] = cur.fetchone()["c"]
    cur.execute("SELECT COALESCE(SUM(harga),0) AS s FROM orders WHERE status='SUCCESS'")
    data["omzet"] = int(cur.fetchone()["s"])
    cur.execute(
        "SELECT COALESCE(SUM(jumlah),0) AS s FROM orders "
        "WHERE status='SUCCESS' AND kategori='FILE'"
    )
    data["nomor_terjual"] = int(cur.fetchone()["s"])
    data["total_user"] = count_users()
    today = config.sekarang().strftime("%d-%m-%Y")
    cur.execute(
        "SELECT COALESCE(SUM(harga),0) AS s FROM orders "
        "WHERE status='SUCCESS' AND created_at LIKE ?",
        (today + "%",),
    )
    data["omzet_hari_ini"] = int(cur.fetchone()["s"])
    return data


def top_products(limit: int = 5) -> list:
    cur = get_conn().cursor()
    cur.execute(
        "SELECT produk, COUNT(*) AS total FROM orders WHERE status='SUCCESS' "
        "GROUP BY produk ORDER BY total DESC LIMIT ?",
        (limit,),
    )
    return cur.fetchall()


if __name__ == "__main__":
    init_db()
    print("Database siap:", config.DB_PATH, "| ukuran:",
          os.path.getsize(config.DB_PATH), "bytes")
