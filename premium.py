# -*- coding: utf-8 -*-
"""
premium.py
Dukungan CUSTOM EMOJI (emoji premium Telegram) untuk AmelBot.

Aturan resmi Bot API:
    "Custom emoji entities can only be used by bots that purchased additional
     usernames on Fragment or in the messages directly sent by the bot to
     private, group and supergroup chats if the owner of the bot has a
     Telegram Premium subscription."

Artinya: selama PEMILIK bot punya Telegram Premium, bot boleh mengirim
emoji premium ke chat pribadi/grup. Tidak perlu beli username Fragment.

Cara kerja modul ini:
  - Semua teks yang dikirim bot dilewatkan `decorate()`.
  - Setiap emoji biasa yang punya padanan custom emoji otomatis dibungkus
    <tg-emoji emoji-id="...">emoji</tg-emoji>.
  - Emoji tanpa padanan tetap tampil normal (fallback aman).
  - Bila penerima bukan Premium, Telegram otomatis menampilkan emoji biasa.
"""

import json
import logging
import os
import re

import config
import database as db

SEP = "─" * 22

log = logging.getLogger(__name__)

MAP_FILE = os.path.join(config.BASE_DIR, "premium_emoji.json")

# Emoji yang TIDAK boleh diubah jadi custom emoji (dipakai sebagai bullet/indikator)
BLACKLIST = set()

# Segmen tag HTML dilewati supaya tidak merusak markup
_TAG_RE = re.compile(r"<[^>]+>")


# ==========================================================
# PEMUATAN PETA EMOJI
# ==========================================================
def _load_file_map() -> dict:
    try:
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _load_db_map() -> dict:
    raw = db.get_setting("premium_emoji_map", "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


_CACHE = {"map": None, "regex": None}


def emoji_map() -> dict:
    """Peta gabungan: bawaan file + hasil belajar admin (DB menang)."""
    if _CACHE["map"] is None:
        merged = _load_file_map()
        merged.update(_load_db_map())
        merged = {k: v for k, v in merged.items() if k and v and k not in BLACKLIST}
        _CACHE["map"] = merged
        if merged:
            # urut dari emoji terpanjang supaya varian ZWJ/VS16 menang duluan
            pattern = "|".join(
                re.escape(k) for k in sorted(merged, key=len, reverse=True)
            )
            _CACHE["regex"] = re.compile(pattern)
        else:
            _CACHE["regex"] = None
    return _CACHE["map"]


def reload_map() -> int:
    """Bersihkan cache setelah admin mengubah peta."""
    _CACHE["map"] = None
    _CACHE["regex"] = None
    return len(emoji_map())


def learn(pairs: dict) -> int:
    """Simpan hasil belajar emoji premium dari pesan admin."""
    current = _load_db_map()
    current.update({k: str(v) for k, v in pairs.items() if k and v})
    db.set_setting("premium_emoji_map", json.dumps(current, ensure_ascii=False))
    reload_map()
    return len(current)


def reset_learned() -> None:
    db.set_setting("premium_emoji_map", "")
    reload_map()


# ==========================================================
# SAKLAR ON / OFF
# ==========================================================
def is_enabled() -> bool:
    return db.get_setting("premium_emoji", "1") == "1"


def set_enabled(value: bool) -> None:
    db.set_setting("premium_emoji", "1" if value else "0")


# ==========================================================
# DEKORASI TEKS
# ==========================================================
def decorate(text: str) -> str:
    """Bungkus emoji biasa menjadi custom emoji premium."""
    if not text or not is_enabled():
        return text
    emoji_map()
    regex = _CACHE["regex"]
    if regex is None:
        return text

    def sub(m: "re.Match") -> str:
        char = m.group(0)
        eid = _CACHE["map"].get(char)
        if not eid:
            return char
        return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>'

    hasil = []
    pos = 0
    # lewati bagian yang merupakan tag HTML
    for tag in _TAG_RE.finditer(text):
        hasil.append(regex.sub(sub, text[pos:tag.start()]))
        hasil.append(tag.group(0))
        pos = tag.end()
    hasil.append(regex.sub(sub, text[pos:]))
    return "".join(hasil)


def strip_custom(text: str) -> str:
    """Kembalikan teks tanpa tag tg-emoji (untuk log / preview)."""
    return re.sub(r"</?tg-emoji[^>]*>", "", text or "")


def icon_id(char: str):
    """ID custom emoji untuk dipakai sebagai ikon tombol."""
    if not char or not is_enabled():
        return None
    return emoji_map().get(char)


def status_text() -> str:
    total = len(emoji_map())
    belajar = len(_load_db_map())
    aktif = "🟢 AKTIF" if is_enabled() else "🔴 NONAKTIF"
    return (
        "🎨 <b>EMOJI PREMIUM</b>\n"
        f"{SEP}\n"
        f"⚙️ Status        : <b>{aktif}</b>\n"
        f"🎭 Total emoji   : <b>{total}</b> terpasang\n"
        f"📚 Hasil belajar : <b>{belajar}</b> emoji\n"
        f"{SEP}\n"
        "Set yang dipakai adalah gaya standar Telegram, bentuknya sama "
        "seperti emoji biasa dan hanya bergerak halus, termasuk seluruh "
        "bendera negara.\n"
        "Pengguna non-Premium tetap melihat emoji biasa, "
        "jadi pesan aman untuk semua orang.\n"
        f"{SEP}\n"
        "💡 <b>TAMBAH EMOJI SENDIRI</b>\n"
        "Tekan tombol <b>PELAJARI EMOJI</b>, lalu kirim satu pesan "
        "berisi emoji premium pilihan Anda. Bot akan menyimpannya otomatis."
    )


# ==========================================================
# BOT WRAPPER
# ==========================================================
def build_bot(token: str, rate_limiter=None):
    """
    Bot khusus yang otomatis mengubah emoji biasa menjadi emoji premium
    pada SEMUA pesan keluar (send_message, send_photo, edit, reply, dll).
    """
    from telegram.ext import ExtBot

    class PremiumBot(ExtBot):
        async def _post(self, endpoint, data=None, *args, **kwargs):
            if isinstance(data, dict):
                parse_mode = data.get("parse_mode")
                if parse_mode and str(parse_mode).upper() == "HTML":
                    for key in ("text", "caption"):
                        value = data.get(key)
                        if isinstance(value, str):
                            data[key] = decorate(value)
            return await super()._post(endpoint, data, *args, **kwargs)

    if rate_limiter is not None:
        return PremiumBot(token, rate_limiter=rate_limiter)
    return PremiumBot(token)
