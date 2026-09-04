# -*- coding: utf-8 -*-
"""
ui.py
Komponen tampilan AmelBot.

Tombol berwarna memakai fitur Bot API 9.4:
    style = "primary" (biru) | "success" (hijau) | "danger" (merah)
    icon_custom_emoji_id = ikon emoji premium di dalam tombol

Bila akun tidak memenuhi syarat, Telegram otomatis memakai gaya bawaan
sehingga tombol tetap tampil normal.
"""

import html as _html
import re as _re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import premium

SEP = "─" * 22

# Semua tombol dibuat biru (primary).
# Ubah ke False bila ingin warna dibedakan lagi:
# hijau untuk terima, merah untuk hapus.
SEMUA_PRIMARY = True


# ==========================================================
# TOMBOL
# ==========================================================
def btn(text: str, data: str = None, url: str = None,
        style: str = None, icon: str = None) -> InlineKeyboardButton:
    kwargs = {}
    eid = premium.icon_id(icon) if icon else None
    if eid:
        kwargs["icon_custom_emoji_id"] = eid
    if SEMUA_PRIMARY:
        style = "primary"
    if style:
        kwargs["style"] = style
    if url:
        return InlineKeyboardButton(text, url=url, **kwargs)
    return InlineKeyboardButton(text, callback_data=data or "noop", **kwargs)


def primary(text, data=None, url=None, icon=None):
    return btn(text, data, url, "primary", icon)


def success(text, data=None, url=None, icon=None):
    return btn(text, data, url, "success", icon)


def danger(text, data=None, url=None, icon=None):
    return btn(text, data, url, "danger", icon)


def plain(text, data=None, url=None, icon=None):
    return btn(text, data, url, None, icon)


def kb(*rows) -> InlineKeyboardMarkup:
    """Terima baris berupa list tombol atau tombol tunggal."""
    out = []
    for r in rows:
        if r is None:
            continue
        if isinstance(r, InlineKeyboardButton):
            out.append([r])
        elif isinstance(r, (list, tuple)):
            baris = [b for b in r if b is not None]
            if baris:
                out.append(baris)
    return InlineKeyboardMarkup(out)


def back(data: str = "menu:main", text: str = "Kembali"):
    return plain(text, data, icon="⬅️")


def home():
    return plain("Menu Utama", "menu:main", icon="🏠")


# ==========================================================
# TEKS
# ==========================================================
_TAG_KOTOR = _re.compile(r"[<>]")


def esc(text) -> str:
    """
    Amankan teks dari luar (nama Telegram, catatan admin) sebelum masuk
    pesan HTML. Tanpa ini, nama seperti 'Rudi <3' membuat Telegram menolak
    seluruh pesan sehingga bot terlihat mati.
    """
    return _html.escape(str(text if text is not None else ""), quote=False)


def bersih(text, batas: int = 0) -> str:
    """
    Bersihkan teks yang akan disimpan ke database lalu dipakai di teks
    maupun di label tombol. Tanda < dan > dibuang karena tombol tidak
    mengenal HTML, jadi tidak bisa di-escape seperti pesan biasa.
    """
    hasil = _TAG_KOTOR.sub("", str(text if text is not None else "")).strip()
    hasil = " ".join(hasil.split())
    return hasil[:batas] if batas else hasil


def rupiah(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    return "Rp" + f"{n:,}".replace(",", ".")


def angka(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    return f"{n:,}".replace(",", ".")


def title(text: str) -> str:
    return f"<b>{text.upper()}</b>\n{SEP}"


def field(label: str, value, width: int = 11) -> str:
    """Baris data sejajar: 'Label     : nilai'"""
    label = str(label)
    pad = "\u00a0" * max(0, width - len(label))
    return f"{label}{pad}: {value}"


def quote(text: str, expandable: bool = False) -> str:
    tag = "<blockquote expandable>" if expandable else "<blockquote>"
    return f"{tag}{text}</blockquote>"


def panduan(text: str) -> str:
    """Kutipan penjelasan yang bisa dilipat. Hanya dipakai di layar admin."""
    return f"\n<b>Penjelasan</b>\n{quote(text, expandable=True)}"


def bullet(items) -> str:
    return "\n".join(f"• {i}" for i in items)
