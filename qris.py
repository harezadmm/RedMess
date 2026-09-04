# -*- coding: utf-8 -*-
"""
qris.py
Pembayaran manual QRIS: penyimpanan gambar & teks invoice.
Tidak memakai API payment gateway apa pun.
"""

import os
import shutil
from datetime import datetime

import config
import database as db
import ui


def qris_exists() -> bool:
    return os.path.isfile(config.QRIS_PATH)


def qris_path() -> str:
    return config.QRIS_PATH


def backup_current() -> str:
    if not qris_exists():
        return ""
    stamp = config.sekarang().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(config.BASE_DIR, f"qris-lama-{stamp}.jpg")
    try:
        shutil.copy2(config.QRIS_PATH, dest)
        return dest
    except OSError:
        return ""


def save_qris(temp_path: str) -> bool:
    try:
        backup_current()
        shutil.move(temp_path, config.QRIS_PATH)
        return True
    except OSError:
        return False


def payment_caption(order) -> str:
    nama = db.get_setting("qris_name", db.get_setting("store_name", config.STORE_NAME))
    catatan = db.get_setting(
        "qris_note",
        "Scan QRIS di atas, bayar sesuai nominal, lalu tekan Saya Sudah Bayar.",
    )
    detail = "\n".join([
        ui.field("Invoice", f"<code>{order['invoice']}</code>"),
        ui.field("Produk", order["produk"]),
        ui.field("Total", f"<b>{ui.rupiah(order['harga'])}</b>"),
        ui.field("Atas nama", nama),
        ui.field("Status", config.STATUS_LABEL.get(order["status"], order["status"])),
    ])
    langkah = ui.bullet([
        "Scan QRIS dengan aplikasi e-wallet atau m-banking",
        "Bayar tepat sesuai nominal di atas",
        "Tekan tombol <b>Saya Sudah Bayar</b>",
        "Admin verifikasi, pesanan terkirim otomatis",
    ])
    return (
        f"{ui.title('Invoice Pembayaran')}\n"
        f"{ui.quote(detail)}\n"
        f"<b>Cara bayar</b>\n{langkah}\n\n"
        f"{ui.quote(catatan)}"
    )


def no_qris_text() -> str:
    return ui.quote("Gambar QRIS belum diunggah admin. Silakan hubungi owner.")
