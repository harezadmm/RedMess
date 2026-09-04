# -*- coding: utf-8 -*-
"""
catalog.py
Pengelolaan katalog negara & paket jumlah.

Semua data diambil dari database, jadi admin bebas menambah
negara sebanyak apa pun tanpa menyentuh kode.
"""

import re
import unicodedata

import config
import database as db
import ui

# Dua huruf regional indicator = bendera negara
FLAG_RE = re.compile("[\U0001F1E6-\U0001F1FF]{2}")
DEFAULT_FLAG = "🌍"


# ==========================================================
# KODE / SLUG
# ==========================================================
def make_code(name: str) -> str:
    """Ubah nama negara menjadi kode file yang aman."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    text = text[:20] or "negara"
    base, i = text, 2
    while db.country_exists(text):
        text = f"{base}{i}"
        i += 1
    return text


def parse_input(raw: str):
    """
    Baca input admin menjadi (nama, bendera).
    Menerima: "🇳🇬 Nigeria", "Nigeria 🇳🇬", atau "Nigeria".
    """
    raw = " ".join((raw or "").split())
    if not raw:
        return None, None
    flags = FLAG_RE.findall(raw)
    flag = flags[0] if flags else DEFAULT_FLAG
    name = FLAG_RE.sub("", raw).strip(" -|·,")
    name = " ".join(w.capitalize() if w.islower() else w for w in name.split())
    name = ui.bersih(name, 30)
    if not name:
        return None, None
    return name, flag


# ==========================================================
# BACA KATALOG
# ==========================================================
def all_countries(active_only: bool = False) -> list:
    return db.countries(active_only=active_only)


def codes(active_only: bool = False) -> list:
    return [r["code"] for r in all_countries(active_only)]


def get(code: str):
    return db.get_country(code)


def exists(code: str) -> bool:
    return db.country_exists(code)


def name(code: str) -> str:
    row = get(code)
    return row["name"] if row else str(code).title()


def flag(code: str) -> str:
    row = get(code)
    return (row["flag"] if row and row["flag"] else DEFAULT_FLAG)


def label(code: str) -> str:
    row = get(code)
    if not row:
        return str(code).title()
    return f"{row['flag']} {row['name']}".strip()


def filename(code: str) -> str:
    row = get(code)
    return row["file"] if row and row["file"] else f"{code}.txt"


def is_active(code: str) -> bool:
    row = get(code)
    return bool(row and row["aktif"])


# ==========================================================
# UBAH KATALOG
# ==========================================================
def add(raw: str):
    """Tambah negara dari teks bebas. Return (code, name, flag) atau None."""
    nama, bendera = parse_input(raw)
    if not nama:
        return None
    for row in all_countries():
        if row["name"].lower() == nama.lower():
            return None  # sudah ada
    code = make_code(nama)
    db.add_country(code, nama, bendera)
    seed_prices(code)
    return code, nama, bendera


def rename(code: str, raw: str) -> bool:
    nama, bendera = parse_input(raw)
    if not nama:
        return False
    db.update_country(code, name=nama, flag=bendera)
    return True


def toggle(code: str) -> bool:
    row = get(code)
    if not row:
        return False
    db.update_country(code, aktif=0 if row["aktif"] else 1)
    return True


def remove(code: str) -> bool:
    if not exists(code):
        return False
    db.delete_country(code)
    return True


# ==========================================================
# PAKET JUMLAH & HARGA
# ==========================================================
def quantities() -> list:
    return db.quantities()


def set_quantities(values: list) -> None:
    db.set_quantities(values)
    for code in codes():
        seed_prices(code)


def rate() -> int:
    try:
        return int(db.get_setting("rate", config.DEFAULT_RATE))
    except (TypeError, ValueError):
        return config.DEFAULT_RATE


def set_rate(value: int) -> None:
    db.set_setting("rate", int(value))


def seed_prices(code: str) -> None:
    """Pastikan setiap paket punya harga (pakai tarif per nomor bila kosong)."""
    r = rate()
    for q in quantities():
        cur = db.get_conn().cursor()
        cur.execute("SELECT harga FROM prices WHERE negara=? AND jumlah=?", (code, q))
        if not cur.fetchone():
            db.set_price(code, q, q * r)


def prices(code: str) -> dict:
    return db.price_map(code)


# ==========================================================
# MENU — tombol bisa disembunyikan / diganti label & ikon
# ==========================================================
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2B00-\u2BFF\uFE0F\u20E3]+"
)


def menus(active_only: bool = False) -> list:
    return db.menus(active_only=active_only)


def menu(key: str):
    return db.get_menu(key)


def menu_on(key: str) -> bool:
    row = menu(key)
    return bool(row and row["aktif"])


def menu_label(key: str, fallback: str = "") -> str:
    row = menu(key)
    return row["label"] if row and row["label"] else fallback


def menu_icon(key: str, fallback: str = "") -> str:
    row = menu(key)
    return row["icon"] if row and row["icon"] else fallback


def menu_style(key: str):
    row = menu(key)
    return row["style"] if row else None


def menu_toggle(key: str) -> bool:
    row = menu(key)
    if not row:
        return False
    db.update_menu(key, aktif=0 if row["aktif"] else 1)
    return True


def menu_set(key: str, raw: str) -> bool:
    """Ubah label & ikon menu dari teks bebas, contoh: '🛒 Order Sekarang'."""
    raw = " ".join((raw or "").split())
    if not raw or not menu(key):
        return False
    found = EMOJI_RE.findall(raw)
    icon = found[0][:2].strip() if found else None
    label = EMOJI_RE.sub("", raw).strip(" -|·,")
    if not label:
        return False
    label = ui.bersih(label, 28)
    if not label:
        return False
    db.update_menu(key, label=label, icon=icon)
    return True


# ==========================================================
# PRODUK PANEL
# ==========================================================
def panels(active_only: bool = False) -> list:
    return db.panels(active_only=active_only)


def panel(code: str):
    return db.get_panel(code)


def panel_add(raw: str):
    """Format: Nama | Spesifikasi | Harga  →  return code atau None."""
    parts = [p.strip() for p in (raw or "").split("|")]
    if len(parts) < 3:
        return None
    name = ui.bersih(parts[0], 40)
    spek = ui.bersih(parts[1], 80)
    harga = parts[2].replace(".", "").replace(",", "")
    if not name or not harga.isdigit():
        return None
    code = _panel_code(name)
    db.add_panel(code, name, spek, int(harga))
    return code


def _panel_code(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()[:20] or "panel"
    base, i = text, 2
    while db.panel_exists(text):
        text = f"{base}{i}"
        i += 1
    return text


def panel_toggle(code: str) -> bool:
    row = panel(code)
    if not row:
        return False
    db.update_panel(code, aktif=0 if row["aktif"] else 1)
    return True


def panel_set_price(code: str, harga: int) -> bool:
    if not panel(code):
        return False
    db.update_panel(code, price=int(harga))
    return True


def panel_edit(code: str, raw: str) -> bool:
    parts = [p.strip() for p in (raw or "").split("|")]
    if not panel(code) or len(parts) < 3:
        return False
    nama = ui.bersih(parts[0], 40)
    spek = ui.bersih(parts[1], 80)
    harga = parts[2].replace(".", "").replace(",", "")
    if not nama or not harga.isdigit():
        return False
    db.update_panel(code, name=nama, spek=spek, price=int(harga))
    return True


def panel_remove(code: str) -> bool:
    if not panel(code):
        return False
    db.delete_panel(code)
    return True


def price(code: str, jumlah: int) -> int:
    return db.get_price(code, jumlah)


def set_price(code: str, jumlah: int, harga: int) -> None:
    db.set_price(code, jumlah, harga)
