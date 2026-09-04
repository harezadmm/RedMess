# -*- coding: utf-8 -*-
"""
config.py
Konfigurasi dasar AmelBot.

Negara, harga, dan jumlah paket TIDAK lagi dikunci di sini —
semuanya dikelola lewat Admin Panel dan disimpan di database.
Nilai di bawah hanya dipakai sekali saat database pertama kali dibuat.
"""

import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


# ==========================================================
# TOKEN & ADMIN
# ==========================================================
BOT_TOKEN = _env("BOT_TOKEN", "ISI_TOKEN_BOT_ANDA_DISINI")

_admin_raw = _env("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(p) for p in _admin_raw.replace(" ", "").split(",") if p.isdigit()]
if not ADMIN_IDS:
    ADMIN_IDS = [123456789]

OWNER_ID = ADMIN_IDS[0]


# ==========================================================
# ZONA WAKTU
# ==========================================================
# Server panel umumnya memakai UTC, sehingga jam transaksi bisa tertulis
# tujuh jam lebih awal. Semua waktu di bot mengikuti zona di bawah ini.
TZ_NAME = _env("TZ_NAME", "Asia/Jakarta")

try:
    from zoneinfo import ZoneInfo

    TZ = ZoneInfo(TZ_NAME)
except Exception:  # noqa: BLE001
    TZ = None


def sekarang() -> datetime:
    """Waktu sekarang menurut zona toko, bukan zona server."""
    return datetime.now(TZ) if TZ is not None else datetime.now()


# ==========================================================
# IDENTITAS TOKO
# ==========================================================
STORE_NAME = _env("STORE_NAME", "AMEL STORE")
OWNER_USERNAME = _env("OWNER_USERNAME", "@AmelOwner")
OWNER_NAME = _env("OWNER_NAME", "Amel")

# ==========================================================
# PATH
# ==========================================================
DB_PATH = os.path.join(BASE_DIR, "database.db")
STOK_DIR = os.path.join(BASE_DIR, "stok")
ORDER_DIR = os.path.join(BASE_DIR, "orders")
QRIS_PATH = os.path.join(BASE_DIR, "qris.jpg")

os.makedirs(STOK_DIR, exist_ok=True)
os.makedirs(ORDER_DIR, exist_ok=True)

# ==========================================================
# DATA AWAL (hanya dipakai saat database masih kosong)
# ==========================================================
SEED_COUNTRIES = [
    ("togo", "Togo", "🇹🇬"),
    ("laos", "Laos", "🇱🇦"),
    ("mali", "Mali", "🇲🇱"),
]

SEED_QUANTITIES = [200, 500, 1000]

# Harga default per nomor (Rp). Dipakai untuk menghitung harga awal
# setiap kali negara atau paket baru dibuat: harga = jumlah x tarif.
DEFAULT_RATE = 40

# ==========================================================
# PRODUK PANEL AWAL (bisa diubah / dihapus dari Admin Panel)
# ==========================================================
SEED_PANELS = [
    ("p1gb", "Panel 1 GB", "RAM 1 GB · Disk 5 GB · CPU 50%", 3000),
    ("p2gb", "Panel 2 GB", "RAM 2 GB · Disk 10 GB · CPU 70%", 5000),
    ("p3gb", "Panel 3 GB", "RAM 3 GB · Disk 15 GB · CPU 100%", 7000),
    ("punli", "Panel Unlimited", "RAM · Disk · CPU tanpa batas", 15000),
]

# ==========================================================
# MENU AWAL — key, label, ikon emoji, warna tombol
# Semua bisa disembunyikan, diganti nama, dan diganti ikon
# lewat Admin Panel → Kelola Menu.
# ==========================================================
SEED_MENUS = [
    ("order",       "Order Sekarang",    "🛒", "primary"),
    ("order_file",  "File Nomor",        "📂", "primary"),
    ("order_panel", "Panel Hosting",     "🎁", None),
    ("history",     "Riwayat",           "📊", None),
    ("info",        "Akun Saya",         "👤", None),
    ("owner",       "Owner & Bantuan",   "👑", None),
]

MENU_INFO = {
    "order":       "Tombol utama di menu awal",
    "order_file":  "Kategori file nomor per negara",
    "order_panel": "Kategori panel hosting",
    "history":     "Riwayat transaksi pembeli",
    "info":        "Data akun & level pembeli",
    "owner":       "Kontak owner & aturan toko",
}

# ==========================================================
# STATUS
# ==========================================================
STATUS_LABEL = {
    "PENDING": "Menunggu pembayaran",
    "CHECKING": "Menunggu verifikasi",
    "SUCCESS": "Berhasil",
    "CANCEL": "Dibatalkan",
}

STATUS_DOT = {
    "PENDING": "○",
    "CHECKING": "◐",
    "SUCCESS": "●",
    "CANCEL": "×",
}


def is_admin(user_id: int) -> bool:
    return int(user_id) in ADMIN_IDS
