# -*- coding: utf-8 -*-
"""
admin.py
Panel admin AmelBot.

Fitur:
  - Verifikasi order (terima / tolak) + pengiriman file otomatis
  - Kelola negara: tambah, ubah nama & bendera, aktif/nonaktif, hapus
  - Kelola stok: isi berulang tanpa keluar menu, hapus sebagian / semua
  - Kelola harga, paket jumlah, dan tarif per nomor
  - QRIS, statistik, broadcast, emoji premium
"""

import logging
import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

import bantuan
import catalog
import config
import database as db
import premium
import qris
import stock
import ui
import voucher
from order import safe_edit

log = logging.getLogger(__name__)

PER_PAGE = 8


# ==========================================================
# AKSES
# ==========================================================
def admin_only(update: Update) -> bool:
    return config.is_admin(update.effective_user.id)


async def deny(update: Update):
    pesan = "Menu ini hanya untuk admin."
    if update.callback_query:
        await update.callback_query.answer(pesan, show_alert=True)
    else:
        await update.effective_message.reply_text(pesan)


def wait(context, jenis: str, code: str = "", extra=None):
    context.user_data["awaiting"] = {"type": jenis, "code": code, "extra": extra}


def clear_wait(context):
    context.user_data.pop("awaiting", None)


def back_panel(text: str = "Panel Admin"):
    return ui.plain(text, "adm:panel", icon="⬅️")


# ==========================================================
# PANEL UTAMA
# ==========================================================
def panel_kb():
    pend = len(db.pending_orders(limit=50))
    label = "Order Pending" + (f" · {pend}" if pend else "")
    return ui.kb(
        [ui.primary(label, "adm:pending", icon="📊")],
        [ui.plain("Kelola Negara", "adm:neg:0", icon="🌍"),
         ui.plain("Kelola Stok", "adm:stock", icon="📦")],
        [ui.plain("Harga & Paket", "adm:price", icon="💰"),
         ui.plain("Produk Panel", "adm:pnl", icon="🎁")],
        [ui.plain("Kelola Menu", "adm:menu", icon="🎛"),
         ui.plain("Pengaturan Toko", "adm:set", icon="⚙️")],
        [ui.plain("QRIS", "adm:qris", icon="💳"),
         ui.plain("Voucher", "adm:voucher", icon="🎟️")],
        [ui.plain("Emoji Premium", "adm:emoji", icon="🎨"),
         ui.plain("Testimonial", "adm:testi", icon="⭐")],
        [ui.plain("Statistik", "adm:stats", icon="📊"),
         ui.plain("Broadcast", "adm:bc", icon="📣")],
        [ui.home()],
    )


def panel_text() -> str:
    st = db.stats()
    ringkas = "\n".join([
        ui.field("Pending", f"{st['pending'] + st['checking']} order"),
        ui.field("Sukses", f"{st['success']} order"),
        ui.field("Omzet", ui.rupiah(st["omzet"])),
        ui.field("Hari ini", ui.rupiah(st["omzet_hari_ini"])),
        ui.field("Stok", f"{ui.angka(stock.total_all())} nomor"),
        ui.field("Negara", f"{len(catalog.codes())} terdaftar"),
        ui.field("Menu aktif", f"{len(catalog.menus(True))} dari {len(catalog.menus())}"),
        ui.field("Member", f"{st['total_user']} orang"),
    ])
    return (f"{ui.title('Panel Admin')}\n{ui.quote(ringkas)}\n"
            f"Pilih menu di bawah.{bantuan.q('panel')}")


async def cb_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    clear_wait(context)
    await update.callback_query.answer()
    await safe_edit(update.callback_query, panel_text(), panel_kb())


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    clear_wait(context)
    await update.effective_message.reply_text(
        panel_text(), reply_markup=panel_kb(), parse_mode=ParseMode.HTML
    )


# ==========================================================
# ORDER PENDING
# ==========================================================
async def cb_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()

    rows = db.pending_orders(limit=10)
    if not rows:
        await safe_edit(query, f"{ui.title('Order Pending')}\nTidak ada order menunggu."
                        f"{bantuan.q('pending')}", ui.kb([back_panel()]))
        return

    blok, tombol = [], []
    for o in rows:
        dot = config.STATUS_DOT.get(o["status"], "·")
        blok.append(
            f"{dot} <code>{o['invoice']}</code>\n"
            f"   {o['produk']} — {ui.rupiah(o['harga'])}\n"
            f"   {ui.esc(o['username'])} · {config.STATUS_LABEL.get(o['status'], o['status'])}"
        )
        tombol.append([
            ui.success(f"Terima {o['invoice'][-6:]}", f"adm:ok:{o['invoice']}", icon="✅"),
            ui.danger("Tolak", f"adm:no:{o['invoice']}", icon="❌"),
        ])
    tombol.append([back_panel()])
    await safe_edit(query, f"{ui.title('Order Pending')}\n" + "\n\n".join(blok)
                    + bantuan.q("pending"), ui.kb(*tombol))


# ==========================================================
# PENGIRIMAN OTOMATIS
# ==========================================================
async def deliver_order(context: ContextTypes.DEFAULT_TYPE, order) -> tuple:
    """Kirim produk ke pembeli. Return (sukses, pesan)."""
    invoice = order["invoice"]

    if order["kategori"] == "PANEL":
        db.update_status(invoice, "SUCCESS", "Panel dikirim manual")
        detail = "\n".join([
            ui.field("Invoice", f"<code>{invoice}</code>"),
            ui.field("Produk", order["produk"]),
            ui.field("Total", ui.rupiah(order["harga"])),
        ])
        try:
            await context.bot.send_message(
                order["user_id"],
                f"{ui.title('Pembayaran Diterima')}\n{ui.quote(detail)}\n"
                f"Data panel dikirim admin sebentar lagi lewat chat ini.",
                parse_mode=ParseMode.HTML,
                reply_markup=ui.kb([ui.primary("Order Lagi", "menu:order", icon="🛒")],
                                   [ui.home()]),
            )
        except Exception as e:  # noqa: BLE001
            return True, f"Order sukses, tapi notifikasi gagal: {e}"
        return True, "Order panel disetujui. Kirim data panel manual ke pembeli."

    code = order["negara"]
    jumlah = int(order["jumlah"])
    tersedia = stock.count(code)
    if tersedia < jumlah:
        return False, (f"Stok {catalog.name(code)} hanya {ui.angka(tersedia)} nomor, "
                       f"butuh {ui.angka(jumlah)}. Isi stok dulu.")

    numbers = stock.take(code, jumlah)
    if len(numbers) < jumlah:
        stock.give_back(code, numbers)
        return False, "Gagal mengambil stok, coba lagi."

    path = stock.build_delivery_file(invoice, code, numbers)
    detail = "\n".join([
        ui.field("Invoice", f"<code>{invoice}</code>"),
        ui.field("Produk", order["produk"]),
        ui.field("Jumlah", f"{ui.angka(jumlah)} nomor"),
        ui.field("Total", ui.rupiah(order["harga"])),
    ])
    caption = (f"{ui.title('Pesanan Terkirim')}\n{ui.quote(detail)}\n"
               f"Terima kasih sudah order. Simpan file ini dengan aman.")
    try:
        with open(path, "rb") as f:
            await context.bot.send_document(
                chat_id=order["user_id"], document=f,
                filename=os.path.basename(path), caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=ui.kb([ui.primary("Order Lagi", "menu:order", icon="🛒")],
                                   [ui.home()]),
            )
    except Exception as e:  # noqa: BLE001
        stock.give_back(code, numbers)
        return False, f"Gagal mengirim file: {e}"

    db.update_status(invoice, "SUCCESS", f"Terkirim {jumlah} nomor")
    return True, (f"Order {invoice} selesai. "
                  f"Sisa stok {catalog.name(code)}: {ui.angka(stock.count(code))} nomor.")


async def cb_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    invoice = query.data.split(":", 2)[2]
    order = db.get_order(invoice)

    if not order:
        await query.answer("Invoice tidak ditemukan.", show_alert=True)
        return
    if order["status"] == "SUCCESS":
        await query.answer("Order ini sudah selesai.", show_alert=True)
        return

    await query.answer("Memproses")
    ok, msg = await deliver_order(context, order)
    judul = "Order Disetujui" if ok else "Gagal Diproses"
    await safe_edit(query, (
        f"{ui.title(judul)}\n"
        f"{ui.quote(ui.field('Invoice', f'<code>{invoice}</code>') + chr(10) + ui.field('Produk', order['produk']))}\n"
        f"{msg}"
    ), ui.kb([ui.plain("Order Pending", "adm:pending", icon="📊")], [back_panel()]))


async def cb_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    invoice = query.data.split(":", 2)[2]
    order = db.get_order(invoice)

    if not order:
        await query.answer("Invoice tidak ditemukan.", show_alert=True)
        return
    if order["status"] == "SUCCESS":
        await query.answer("Order sudah selesai, tidak bisa ditolak.", show_alert=True)
        return

    db.update_status(invoice, "CANCEL", "Ditolak admin")
    await query.answer("Order ditolak")

    detail = "\n".join([
        ui.field("Invoice", f"<code>{invoice}</code>"),
        ui.field("Produk", order["produk"]),
        ui.field("Total", ui.rupiah(order["harga"])),
    ])
    try:
        await context.bot.send_message(
            order["user_id"],
            f"{ui.title('Pembayaran Ditolak')}\n{ui.quote(detail)}\n"
            f"Pembayaran belum kami terima atau nominal tidak sesuai.\n"
            f"Hubungi {db.get_setting('owner_username', config.OWNER_USERNAME)} bila ini keliru.",
            parse_mode=ParseMode.HTML,
            reply_markup=ui.kb([ui.primary("Order Lagi", "menu:order", icon="🛒")]),
        )
    except Exception as e:  # noqa: BLE001
        log.warning("Notif tolak gagal: %s", e)

    await safe_edit(query, f"{ui.title('Order Ditolak')}\n{ui.quote(detail)}\n"
                           "Pembeli sudah diberi tahu.",
                    ui.kb([ui.plain("Order Pending", "adm:pending", icon="📊")],
                          [back_panel()]))


# ==========================================================
# KELOLA NEGARA
# ==========================================================
def negara_text(page: int, total_page: int, chunk, total: int) -> str:
    if not chunk:
        isi = "Belum ada negara. Tekan Tambah Negara untuk mulai."
    else:
        baris = []
        for r in chunk:
            tanda = "●" if r["aktif"] else "○"
            baris.append(f"{tanda} {r['flag']} {r['name']} — {ui.angka(stock.count(r['code']))} nomor")
        isi = ui.quote("\n".join(baris))
    return (
        f"{ui.title('Kelola Negara')}\n{isi}\n"
        f"Halaman {page + 1} dari {total_page} · {total} negara\n"
        f"{ui.quote('● aktif dan tampil ke pembeli · ○ disembunyikan')}"
        f"{bantuan.q('negara')}"
    )


async def cb_negara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)

    parts = query.data.split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    semua = catalog.all_countries()
    total_page = max(1, (len(semua) + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, total_page - 1))
    chunk = semua[page * PER_PAGE:(page + 1) * PER_PAGE]

    rows, pair = [], []
    for r in chunk:
        tanda = "●" if r["aktif"] else "○"
        pair.append(ui.plain(f"{tanda} {r['name']}", f"adm:ndet:{r['code']}",
                             icon=r["flag"]))
        if len(pair) == 2:
            rows.append(pair); pair = []
    if pair:
        rows.append(pair)

    nav = []
    if page > 0:
        nav.append(ui.plain("‹ Sebelumnya", f"adm:neg:{page - 1}"))
    if page < total_page - 1:
        nav.append(ui.plain("Berikutnya ›", f"adm:neg:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([ui.primary("Tambah Negara", "adm:nadd", icon="➕")])
    rows.append([back_panel()])

    await safe_edit(query, negara_text(page, total_page, chunk, len(semua)), ui.kb(*rows))


async def cb_negara_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    wait(context, "negara_add")
    await safe_edit(query, (
        f"{ui.title('Tambah Negara')}\n"
        "Kirim nama negara beserta benderanya dalam satu pesan.\n\n"
        f"{ui.quote('🇳🇬 Nigeria' + chr(10) + 'Kenya 🇰🇪' + chr(10) + 'Vietnam')}\n"
        "Bendera boleh dilewat, nanti dipakai ikon dunia.\n"
        "Bisa kirim beberapa negara sekaligus, satu per baris.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('negara_add')}"
    ), ui.kb([ui.plain("Batal", "adm:neg:0", icon="❌")]))


def negara_detail_text(code: str) -> str:
    row = catalog.get(code)
    if not row:
        return f"{ui.title('Negara')}\nNegara tidak ditemukan."
    hm = catalog.prices(code)
    data = "\n".join([
        ui.field("Nama", row["name"]),
        ui.field("Bendera", row["flag"]),
        ui.field("Kode", f"<code>{row['code']}</code>"),
        ui.field("File", f"<code>{row['file']}</code>"),
        ui.field("Stok", f"{ui.angka(stock.count(code))} nomor"),
        ui.field("Status", "Aktif" if row["aktif"] else "Disembunyikan"),
    ])
    harga = "\n".join(f"• {ui.angka(q)} nomor — {ui.rupiah(h)}" for q, h in hm.items())
    judul = f"{row['flag']} {row['name']}"
    return (f"{ui.title(judul)}\n{ui.quote(data)}\n<b>Harga</b>\n{harga}"
            f"{bantuan.q('negara_detail')}")


def negara_detail_kb(code: str):
    row = catalog.get(code)
    aktif = bool(row and row["aktif"])
    return ui.kb(
        [ui.primary("Isi Stok", f"adm:add:{code}", icon="➕")],
        [ui.plain("Atur Harga", f"adm:pset:{code}", icon="💰"),
         ui.plain("Ubah Nama", f"adm:nren:{code}", icon="✏️")],
        [ui.plain("Sembunyikan" if aktif else "Tampilkan", f"adm:ntog:{code}", icon="🔒"),
         ui.plain("Kurangi Stok", f"adm:del:{code}", icon="🗑")],
        [ui.danger("Hapus Negara", f"adm:ndel:{code}", icon="⚠️")],
        [ui.plain("Daftar Negara", "adm:neg:0", icon="🌍"), back_panel("Panel")],
    )


async def cb_negara_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await safe_edit(query, "Negara tidak ditemukan.", ui.kb([ui.plain("Daftar Negara", "adm:neg:0")]))
        return
    await safe_edit(query, negara_detail_text(code), negara_detail_kb(code))


async def cb_negara_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    wait(context, "negara_rename", code)
    await safe_edit(query, (
        f"{ui.title('Ubah Nama Negara')}\n"
        f"{ui.quote(ui.field('Sekarang', catalog.label(code)))}\n"
        "Kirim nama baru beserta benderanya.\n\n"
        f"{ui.quote('🇹🇭 Thailand')}\n"
        f"Ketik /batal untuk keluar.{bantuan.q('negara_rename')}"
    ), ui.kb([ui.plain("Batal", f"adm:ndet:{code}", icon="❌")]))


async def cb_negara_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    code = query.data.split(":", 2)[2]
    if not catalog.toggle(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    await query.answer("Aktif" if catalog.is_active(code) else "Disembunyikan")
    await safe_edit(query, negara_detail_text(code), negara_detail_kb(code))


async def cb_negara_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    data = "\n".join([
        ui.field("Negara", catalog.label(code)),
        ui.field("Stok", f"{ui.angka(stock.count(code))} nomor"),
    ])
    await safe_edit(query, (
        f"{ui.title('Hapus Negara')}\n{ui.quote(data)}\n"
        "Negara, harga, dan file stoknya akan dihapus permanen.\n"
        f"Riwayat order lama tetap tersimpan.{bantuan.q('negara_del')}"
    ), ui.kb(
        [ui.danger("Ya, Hapus Sekarang", f"adm:ndelok:{code}", icon="⚠️")],
        [ui.plain("Batal", f"adm:ndet:{code}", icon="❌")],
    ))


async def cb_negara_del_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    code = query.data.split(":", 2)[2]
    label = catalog.label(code)
    if not catalog.remove(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    stock.delete_file(code)
    await query.answer("Negara dihapus")
    await safe_edit(query, (
        f"{ui.title('Negara Dihapus')}\n"
        f"{ui.quote(ui.field('Negara', label))}\n"
        f"Sisa {len(catalog.codes())} negara terdaftar."
    ), ui.kb([ui.plain("Daftar Negara", "adm:neg:0", icon="🌍")], [back_panel()]))


# ==========================================================
# STOK
# ==========================================================
def stock_report() -> str:
    rows = catalog.all_countries()
    if not rows:
        return f"{ui.title('Kelola Stok')}\nBelum ada negara terdaftar."
    baris = []
    for r in rows:
        n = stock.count(r["code"])
        tanda = "●" if n >= 1000 else ("◐" if n > 0 else "○")
        baris.append(f"{tanda} {r['flag']} {r['name']} — {ui.angka(n)} nomor")
    return (f"{ui.title('Kelola Stok')}\n{ui.quote(chr(10).join(baris))}\n"
            f"{ui.field('Total', f'{ui.angka(stock.total_all())} nomor')}\n\n"
            f"Pilih negara untuk mengisi atau mengurangi stok.{bantuan.q('stock')}")


def country_pick_kb(prefix: str, back_data: str = "adm:panel"):
    rows, pair = [], []
    for r in catalog.all_countries():
        pair.append(ui.plain(r["name"], f"{prefix}{r['code']}", icon=r["flag"]))
        if len(pair) == 2:
            rows.append(pair); pair = []
    if pair:
        rows.append(pair)
    rows.append([ui.plain("Kembali", back_data, icon="⬅️")])
    return ui.kb(*rows)


async def cb_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    await safe_edit(query, stock_report(), country_pick_kb("adm:ndet:"))


async def cmd_cekstok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    await update.effective_message.reply_text(stock_report(), parse_mode=ParseMode.HTML)


def add_stock_text(code: str, hasil: str = "") -> str:
    data = "\n".join([
        ui.field("Negara", catalog.label(code)),
        ui.field("Stok kini", f"{ui.angka(stock.count(code))} nomor"),
    ])
    return (
        f"{ui.title('Isi Stok')}\n{ui.quote(data)}\n"
        + (hasil + "\n\n" if hasil else "")
        + "Kirim nomor ke chat ini. Bisa berupa:\n"
        + ui.bullet(["file .txt", "teks banyak baris", "satu nomor per pesan"])
        + "\n\nMode isi stok tetap aktif, jadi Anda bisa mengirim berkali-kali.\n"
          "Nomor duplikat otomatis dibuang."
        + bantuan.q("add_stock")
    )


def add_stock_kb(code: str):
    return ui.kb(
        [ui.success("Selesai", f"adm:ndet:{code}", icon="✅")],
        [ui.plain("Negara Lain", "adm:stock", icon="📦"), back_panel("Panel")],
    )


async def cb_addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    wait(context, "stok", code)
    await safe_edit(query, add_stock_text(code), add_stock_kb(code))


async def cmd_tambahstok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    await update.effective_message.reply_text(
        stock_report(), reply_markup=country_pick_kb("adm:add:"), parse_mode=ParseMode.HTML
    )


async def cb_delstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    wait(context, "hapus_stok", code)
    data = "\n".join([
        ui.field("Negara", catalog.label(code)),
        ui.field("Stok kini", f"{ui.angka(stock.count(code))} nomor"),
    ])
    await safe_edit(query, (
        f"{ui.title('Kurangi Stok')}\n{ui.quote(data)}\n"
        "Kirim jumlah nomor yang ingin dihapus dari baris paling atas.\n"
        f"{ui.quote('Contoh: 500')}\n"
        f"Atau kosongkan seluruh stok dengan tombol di bawah.{bantuan.q('del_stock')}"
    ), ui.kb(
        [ui.danger("Kosongkan Semua", f"adm:delall:{code}", icon="⚠️")],
        [ui.plain("Batal", f"adm:ndet:{code}", icon="❌")],
    ))


async def cb_delstock_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    hapus = stock.clear(code)
    clear_wait(context)
    await query.answer("Stok dikosongkan")
    await safe_edit(query, (
        f"{ui.title('Stok Dikosongkan')}\n"
        f"{ui.quote(ui.field('Negara', catalog.label(code)) + chr(10) + ui.field('Dihapus', f'{ui.angka(hapus)} nomor'))}"
    ), negara_detail_kb(code))


# ==========================================================
# HARGA & PAKET
# ==========================================================
async def cb_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)

    qs = catalog.quantities()
    info = "\n".join([
        ui.field("Paket", " · ".join(ui.angka(q) for q in qs)),
        ui.field("Tarif", f"{ui.rupiah(catalog.rate())} / nomor"),
        ui.field("Negara", f"{len(catalog.codes())} terdaftar"),
    ])
    await safe_edit(query, (
        f"{ui.title('Harga & Paket')}\n{ui.quote(info)}\n"
        "Tarif dipakai menghitung harga awal setiap paket baru.\n"
        f"Pilih negara untuk mengatur harga satu per satu.{bantuan.q('price')}"
    ), ui.kb(
        [ui.primary("Atur Paket Jumlah", "adm:qty", icon="🎁")],
        [ui.plain("Atur Tarif per Nomor", "adm:rate", icon="💰")],
        *[r for r in country_pick_kb("adm:pset:", "adm:panel").inline_keyboard],
    ))


async def cb_price_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    if not catalog.exists(code):
        await query.answer("Negara tidak ditemukan.", show_alert=True)
        return
    hm = catalog.prices(code)
    wait(context, "harga", code)
    contoh = " ".join(str(h) for h in hm.values())
    urutan = " / ".join(ui.angka(q) for q in hm)
    await safe_edit(query, (
        f"{ui.title('Atur Harga')}\n"
        f"{ui.quote(ui.field('Negara', catalog.label(code)) + chr(10) + chr(10).join(f'{ui.angka(q)} nomor : {ui.rupiah(h)}' for q, h in hm.items()))}\n"
        f"Kirim {len(hm)} angka dipisah spasi, urut untuk {urutan} nomor.\n"
        f"{ui.quote('Contoh: ' + contoh)}\n"
        f"Ketik /batal untuk keluar.{bantuan.q('price_set')}"
    ), ui.kb([ui.plain("Batal", f"adm:ndet:{code}", icon="❌")]))


async def cb_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    qs = catalog.quantities()
    wait(context, "paket")
    await safe_edit(query, (
        f"{ui.title('Atur Paket Jumlah')}\n"
        f"{ui.quote(ui.field('Sekarang', ' · '.join(ui.angka(q) for q in qs)))}\n"
        "Kirim daftar jumlah baru dipisah spasi atau koma.\n"
        f"{ui.quote('Contoh: 100 250 500 1000 2000')}\n"
        "Berlaku untuk semua negara. Harga paket baru dihitung dari tarif per nomor, "
        "harga lama tidak berubah.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('qty')}"
    ), ui.kb([ui.plain("Batal", "adm:price", icon="❌")]))


async def cb_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    wait(context, "tarif")
    await safe_edit(query, (
        f"{ui.title('Tarif per Nomor')}\n"
        f"{ui.quote(ui.field('Sekarang', f'{ui.rupiah(catalog.rate())} / nomor'))}\n"
        "Kirim angka baru tanpa titik.\n"
        f"{ui.quote('Contoh: 45')}\n"
        "Dipakai untuk menghitung harga awal negara atau paket baru.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('rate')}"
    ), ui.kb([ui.plain("Batal", "adm:price", icon="❌")]))


# ==========================================================
# KELOLA MENU (sembunyikan / ubah label & ikon tombol)
# ==========================================================
def menu_text() -> str:
    rows = catalog.menus()
    baris = []
    for r in rows:
        tanda = "●" if r["aktif"] else "○"
        ikon = r["icon"] or "·"
        baris.append(f"{tanda} {ikon} {r['label']}")
    keterangan = "\n".join(
        f"• {r['icon'] or ''} {r['label']} — {config.MENU_INFO.get(r['key'], '')}".strip()
        for r in rows
    )
    return (
        f"{ui.title('Kelola Menu')}\n{ui.quote(chr(10).join(baris))}\n"
        f"Tekan tombol untuk membuka atau menutupnya.\n"
        f"{ui.quote('● tampil ke pembeli · ○ disembunyikan')}\n"
        f"<b>Keterangan</b>\n{ui.quote(keterangan, expandable=True)}"
        f"{bantuan.q('menu')}"
    )


def menu_kb():
    rows = []
    for r in catalog.menus():
        tanda = "●" if r["aktif"] else "○"
        ikon = r["icon"] or ""
        rows.append([
            ui.success(f"{tanda} {ikon} {r['label']}", f"adm:mtog:{r['key']}")
            if r["aktif"] else
            ui.plain(f"{tanda} {ikon} {r['label']}", f"adm:mtog:{r['key']}"),
            ui.plain("Ubah", f"adm:mset:{r['key']}", icon="✏️"),
        ])
    rows.append([back_panel()])
    return ui.kb(*rows)


async def cb_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    await safe_edit(query, menu_text(), menu_kb())


async def cb_menu_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    key = query.data.split(":", 2)[2]
    if not catalog.menu_toggle(key):
        await query.answer("Menu tidak ditemukan.", show_alert=True)
        return
    await query.answer("Dibuka" if catalog.menu_on(key) else "Disembunyikan")
    await safe_edit(query, menu_text(), menu_kb())


async def cb_menu_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 2)[2]
    row = catalog.menu(key)
    if not row:
        await query.answer("Menu tidak ditemukan.", show_alert=True)
        return
    wait(context, "menu_set", key)
    sekarang = "{} {}".format(row["icon"] or "", row["label"]).strip()
    ket = ui.quote(ui.field("Sekarang", sekarang) + chr(10)
                   + ui.field("Fungsi", config.MENU_INFO.get(key, "-")))
    await safe_edit(query, (
        f"{ui.title('Ubah Tombol')}\n"
        f"{ket}\n"
        "Kirim ikon dan nama baru dalam satu pesan.\n"
        f"{ui.quote('🛍 Belanja Nomor' + chr(10) + '📦 Stok Nomor')}\n"
        "Emoji premium juga bisa dipakai — kirim saja emoji premium Anda "
        "di depan nama, ID-nya otomatis disimpan dan dipasang di tombol.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('menu_set')}"
    ), ui.kb([ui.plain("Batal", "adm:menu", icon="❌")]))


# ==========================================================
# PRODUK PANEL
# ==========================================================
def panel_prod_text() -> str:
    items = catalog.panels()
    if not items:
        isi = "Belum ada paket panel. Tekan Tambah Paket untuk mulai."
    else:
        isi = ui.quote("\n".join(
            f"{'●' if p['aktif'] else '○'} {p['name']} — {ui.rupiah(p['price'])}\n"
            f"   {p['spek']}" for p in items
        ))
    return (f"{ui.title('Produk Panel')}\n{isi}\n"
            f"{ui.quote('● dijual · ○ disembunyikan')}\n"
            f"Pilih paket untuk mengubahnya.{bantuan.q('panelprod')}")


def panel_prod_kb():
    rows = []
    for p in catalog.panels():
        tanda = "●" if p["aktif"] else "○"
        rows.append([ui.plain(f"{tanda} {p['name']} · {ui.rupiah(p['price'])}",
                              f"adm:pdet:{p['code']}")])
    rows.append([ui.primary("Tambah Paket", "adm:padd", icon="➕")])
    rows.append([back_panel()])
    return ui.kb(*rows)


async def cb_panelprod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    await safe_edit(query, panel_prod_text(), panel_prod_kb())


def panel_detail_text(code: str) -> str:
    p = catalog.panel(code)
    if not p:
        return f"{ui.title('Paket Panel')}\nPaket tidak ditemukan."
    data = "\n".join([
        ui.field("Nama", p["name"]),
        ui.field("Spek", p["spek"]),
        ui.field("Harga", ui.rupiah(p["price"])),
        ui.field("Status", "Dijual" if p["aktif"] else "Disembunyikan"),
    ])
    return f"{ui.title(p['name'])}\n{ui.quote(data)}{bantuan.q('panel_detail')}"


def panel_detail_kb(code: str):
    p = catalog.panel(code)
    aktif = bool(p and p["aktif"])
    return ui.kb(
        [ui.primary("Ubah Paket", f"adm:pedit:{code}", icon="✏️")],
        [ui.plain("Sembunyikan" if aktif else "Tampilkan", f"adm:ptog:{code}", icon="🔒"),
         ui.danger("Hapus", f"adm:pdel:{code}", icon="🗑")],
        [ui.plain("Daftar Paket", "adm:pnl", icon="🎁"), back_panel("Panel")],
    )


async def cb_panel_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    code = query.data.split(":", 2)[2]
    await safe_edit(query, panel_detail_text(code), panel_detail_kb(code))


async def cb_panel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    wait(context, "panel_add")
    await safe_edit(query, (
        f"{ui.title('Tambah Paket Panel')}\n"
        "Kirim data paket dengan format:\n"
        f"{ui.quote('Nama | Spesifikasi | Harga')}\n"
        "Contoh:\n"
        f"{ui.quote('Panel 4 GB | RAM 4 GB · Disk 20 GB · CPU 120% | 9000')}\n"
        "Bisa beberapa paket sekaligus, satu per baris.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('panel_add')}"
    ), ui.kb([ui.plain("Batal", "adm:pnl", icon="❌")]))


async def cb_panel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    p = catalog.panel(code)
    if not p:
        await query.answer("Paket tidak ditemukan.", show_alert=True)
        return
    wait(context, "panel_edit", code)
    sekarang = "{} | {} | {}".format(p["name"], p["spek"], p["price"])
    await safe_edit(query, (
        f"{ui.title('Ubah Paket')}\n"
        f"{ui.quote(sekarang)}\n"
        "Kirim data baru dengan format sama:\n"
        f"{ui.quote('Nama | Spesifikasi | Harga')}\n"
        f"Ketik /batal untuk keluar.{bantuan.q('panel_add')}"
    ), ui.kb([ui.plain("Batal", f"adm:pdet:{code}", icon="❌")]))


async def cb_panel_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    code = query.data.split(":", 2)[2]
    if not catalog.panel_toggle(code):
        await query.answer("Paket tidak ditemukan.", show_alert=True)
        return
    await query.answer("Dijual" if catalog.panel(code)["aktif"] else "Disembunyikan")
    await safe_edit(query, panel_detail_text(code), panel_detail_kb(code))


async def cb_panel_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 2)[2]
    p = catalog.panel(code)
    if not p:
        await query.answer("Paket tidak ditemukan.", show_alert=True)
        return
    await safe_edit(query, (
        f"{ui.title('Hapus Paket')}\n"
        f"{ui.quote(ui.field('Paket', p['name']) + chr(10) + ui.field('Harga', ui.rupiah(p['price'])))}\n"
        "Paket akan dihapus permanen. Riwayat order lama tetap tersimpan.\n"
        f"Bila hanya ingin menutup sementara, pakai Sembunyikan.{bantuan.q('panel_del')}"
    ), ui.kb(
        [ui.danger("Ya, Hapus", f"adm:pdelok:{code}", icon="⚠️")],
        [ui.plain("Batal", f"adm:pdet:{code}", icon="❌")],
    ))


async def cb_panel_del_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    code = query.data.split(":", 2)[2]
    nama = catalog.panel(code)["name"] if catalog.panel(code) else code
    catalog.panel_remove(code)
    await query.answer("Paket dihapus")
    await safe_edit(query, f"{ui.title('Paket Dihapus')}\n"
                           f"{ui.quote(ui.field('Paket', nama))}", panel_prod_kb())


# ==========================================================
# PENGATURAN TOKO
# ==========================================================
SETTINGS_FIELD = [
    ("store_name", "Nama toko", "AMEL STORE"),
    ("owner_name", "Nama owner", "Amel"),
    ("owner_username", "Username owner", "@AmelOwner"),
    ("qris_name", "Nama di QRIS", "AMEL STORE"),
    ("qris_note", "Catatan pembayaran", "-"),
    ("welcome_note", "Catatan menu utama", "-"),
]


def setting_text() -> str:
    baris = []
    for key, label, default in SETTINGS_FIELD:
        nilai = str(db.get_setting(key, default) or "-")
        if len(nilai) > 40:
            nilai = nilai[:37] + "..."
        baris.append(ui.field(label, nilai, width=18))
    return (f"{ui.title('Pengaturan Toko')}\n{ui.quote(chr(10).join(baris))}\n"
            f"Tekan salah satu untuk mengubahnya.{bantuan.q('setting')}")


def setting_kb():
    rows = [[ui.plain(label, f"adm:sset:{key}", icon="✏️")]
            for key, label, _ in SETTINGS_FIELD]
    rows.append([back_panel()])
    return ui.kb(*rows)


async def cb_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    await safe_edit(query, setting_text(), setting_kb())


async def cb_setting_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 2)[2]
    label = next((l for k, l, _ in SETTINGS_FIELD if k == key), None)
    if not label:
        await query.answer("Pengaturan tidak dikenal.", show_alert=True)
        return
    wait(context, "setting", key)
    judul = "Ubah " + label
    await safe_edit(query, (
        f"{ui.title(judul)}\n"
        f"{ui.quote(ui.field('Sekarang', str(db.get_setting(key, '-') or '-')))}\n"
        f"Kirim nilai baru untuk <b>{label}</b>.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('setting_set')}"
    ), ui.kb([ui.plain("Batal", "adm:set", icon="❌")]))


# ==========================================================
# QRIS
# ==========================================================
async def cb_qris(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    wait(context, "qris")
    data = "\n".join([
        ui.field("Gambar", "sudah ada" if qris.qris_exists() else "belum ada"),
        ui.field("Atas nama", db.get_setting("qris_name", config.STORE_NAME)),
    ])
    await safe_edit(query, (
        f"{ui.title('QRIS Pembayaran')}\n{ui.quote(data)}\n"
        "Kirim foto QRIS baru ke chat ini untuk menggantinya.\n"
        "Gambar lama otomatis dibuat salinan cadangan.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('qris')}"
    ), ui.kb([back_panel()]))


# ==========================================================
# STATISTIK
# ==========================================================
async def cb_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    st = db.stats()
    ringkas = "\n".join([
        ui.field("Total order", st["total_order"]),
        ui.field("Sukses", st["success"]),
        ui.field("Pending", st["pending"]),
        ui.field("Verifikasi", st["checking"]),
        ui.field("Batal", st["cancel"]),
        ui.field("Omzet", ui.rupiah(st["omzet"])),
        ui.field("Hari ini", ui.rupiah(st["omzet_hari_ini"])),
        ui.field("Nomor jual", f"{ui.angka(st['nomor_terjual'])} nomor"),
        ui.field("Member", st["total_user"]),
    ])
    top = db.top_products(limit=5)
    laris = "\n".join(f"{i}. {r['produk']} — {r['total']}x"
                      for i, r in enumerate(top, 1)) or "Belum ada data."
    stok = "\n".join(f"• {catalog.label(c)} — {ui.angka(n)} nomor"
                     for c, n in stock.count_all().items()) or "Belum ada negara."
    await safe_edit(query, (
        f"{ui.title('Statistik Toko')}\n{ui.quote(ringkas)}\n"
        f"<b>Produk terlaris</b>\n{laris}\n\n"
        f"<b>Stok saat ini</b>\n{ui.quote(stok, expandable=True)}"
        f"{bantuan.q('stats')}"
    ), ui.kb([ui.plain("Muat Ulang", "adm:stats", icon="🔄")], [back_panel()]))


# ==========================================================
# BROADCAST
# ==========================================================
async def cb_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    wait(context, "broadcast")
    await safe_edit(query, (
        f"{ui.title('Broadcast')}\n"
        f"{ui.quote(ui.field('Penerima', f'{db.count_users()} member'))}\n"
        "Kirim pesan yang ingin disebar ke semua member.\n"
        "Format HTML didukung: <b>tebal</b>, <i>miring</i>, <code>kode</code>.\n\n"
        f"Ketik /batal untuk keluar.{bantuan.q('broadcast')}"
    ), ui.kb([back_panel()]))


async def do_broadcast(context: ContextTypes.DEFAULT_TYPE, text: str) -> tuple:
    """
    Kirim pengumuman ke semua member.

    Teks admin dikirim apa adanya supaya <b> dan <i> tetap berfungsi. Namun
    bila tanda < dipakai bukan sebagai tag (misalnya "diskon <3 hari"),
    Telegram menolak seluruh pesan. Karena itu teks diuji lebih dahulu; bila
    tidak sah, seluruh pengiriman otomatis memakai versi tanpa format.
    """
    ids = db.all_user_ids()
    ok = gagal = 0
    isi = f"{ui.title('Pengumuman')}\n{text}"
    aman = f"{ui.title('Pengumuman')}\n{ui.esc(text)}"
    mode = ParseMode.HTML

    for uid in ids:
        try:
            await context.bot.send_message(uid, isi, parse_mode=mode)
            ok += 1
        except BadRequest as e:
            if "parse entities" in str(e).lower() and isi != aman:
                isi = aman  # format tidak sah, lanjutkan tanpa format
                try:
                    await context.bot.send_message(uid, isi, parse_mode=mode)
                    ok += 1
                    continue
                except Exception:  # noqa: BLE001
                    pass
            gagal += 1
        except Exception:  # noqa: BLE001
            gagal += 1
    return ok, gagal


# ==========================================================
# EMOJI PREMIUM
# ==========================================================
def emoji_kb():
    aktif = premium.is_enabled()
    return ui.kb(
        [ui.success("Nonaktifkan", "adm:emojitoggle", icon="✅") if aktif
         else ui.primary("Aktifkan", "adm:emojitoggle", icon="🎨")],
        [ui.plain("Contoh Tampilan", "adm:emojipreview", icon="👀"),
         ui.plain("Tambah Emoji", "adm:emojilearn", icon="➕")],
        [ui.danger("Reset Tambahan", "adm:emojireset", icon="🗑")],
        [back_panel()],
    )


async def cb_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    clear_wait(context)
    await safe_edit(query, premium.status_text() + bantuan.q("emoji"), emoji_kb())


async def cb_emoji_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    premium.set_enabled(not premium.is_enabled())
    await query.answer("Aktif" if premium.is_enabled() else "Nonaktif")
    await safe_edit(query, premium.status_text() + bantuan.q("emoji"), emoji_kb())


async def cb_emoji_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    contoh = "\n".join([
        ui.field("Stok", "1.200 nomor"),
        ui.field("Harga", "Rp40.000"),
        ui.field("Status", "Berhasil"),
    ])
    await safe_edit(query, (
        f"{ui.title('Contoh Tampilan')}\n{ui.quote(contoh)}\n"
        "Tombol di bawah memakai warna dan ikon emoji premium."
    ), ui.kb(
        [ui.primary("Tombol Biru", "adm:emojipreview", icon="🛒")],
        [ui.success("Tombol Hijau", "adm:emojipreview", icon="✅"),
         ui.danger("Tombol Merah", "adm:emojipreview", icon="❌")],
        [ui.plain("Emoji Premium", "adm:emoji", icon="🎨")],
    ))


async def cb_emoji_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    wait(context, "emoji")
    await safe_edit(query, (
        f"{ui.title('Tambah Emoji Premium')}\n"
        "Kirim satu pesan berisi emoji premium yang Anda punya.\n"
        "Bot menyimpan ID-nya dan memakainya di teks serta ikon tombol.\n\n"
        f"{ui.quote('Pakai keyboard emoji premium Telegram, lalu kirim.')}\n"
        "Ketik /batal untuk keluar."
    ), ui.kb([ui.plain("Batal", "adm:emoji", icon="❌")]))


async def cb_emoji_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    premium.reset_learned()
    await query.answer("Emoji tambahan dihapus")
    await safe_edit(query, premium.status_text(), emoji_kb())


# ==========================================================
# BATAL
# ==========================================================
async def cmd_batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_wait(context)
    await update.effective_message.reply_text("Mode input dibatalkan.")


# ==========================================================
# INPUT: DOKUMEN
# ==========================================================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return
    st = context.user_data.get("awaiting")
    if not st or st["type"] != "stok":
        await update.effective_message.reply_text(
            "Buka Panel Admin lalu pilih negara dan tekan Isi Stok sebelum mengirim file."
        )
        return

    code = st["code"]
    doc = update.effective_message.document
    if doc.file_size and doc.file_size > 20 * 1024 * 1024:
        await update.effective_message.reply_text("File terlalu besar, maksimal 20 MB.")
        return

    msg = await update.effective_message.reply_text("Memproses file...")
    try:
        f = await doc.get_file()
        raw = await f.download_as_bytearray()
        text = bytes(raw).decode("utf-8", errors="ignore")
    except Exception as e:  # noqa: BLE001
        await msg.edit_text(f"Gagal mengunduh file: {e}")
        return

    hasil = stock.add_from_text(code, text)
    ringkas = "\n".join([
        ui.field("Berkas", doc.file_name or "-"),
        ui.field("Masuk", f"{ui.angka(hasil['added'])} nomor"),
        ui.field("Duplikat", f"{ui.angka(hasil['duplicate'])} dibuang"),
        ui.field("Tidak valid", f"{ui.angka(hasil['invalid'])} baris"),
        ui.field("Stok kini", f"{ui.angka(hasil['total'])} nomor"),
    ])
    await msg.delete()
    await update.effective_message.reply_text(
        add_stock_text(code, ui.quote(ringkas)),
        reply_markup=add_stock_kb(code), parse_mode=ParseMode.HTML
    )


# ==========================================================
# INPUT: FOTO
# ==========================================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return
    st = context.user_data.get("awaiting")
    if not st or st["type"] != "qris":
        return

    photo = update.effective_message.photo[-1]
    temp = os.path.join(config.BASE_DIR, "qris-temp.jpg")
    try:
        f = await photo.get_file()
        await f.download_to_drive(temp)
    except Exception as e:  # noqa: BLE001
        await update.effective_message.reply_text(f"Gagal mengunduh foto: {e}")
        return

    ok = qris.save_qris(temp)
    clear_wait(context)
    await update.effective_message.reply_text(
        f"{ui.title('QRIS Diperbarui' if ok else 'Gagal')}\n"
        + ("Gambar QRIS baru sudah dipakai untuk semua invoice."
           if ok else "Gambar gagal disimpan, coba lagi."),
        reply_markup=ui.kb([back_panel()]), parse_mode=ParseMode.HTML
    )


# ==========================================================
# INPUT: TEKS
# ==========================================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = context.user_data.get("awaiting")
    if not st:
        return
    if not admin_only(update):
        clear_wait(context)
        return

    jenis = st["type"]
    code = st.get("code", "")
    text = update.effective_message.text or ""
    reply = update.effective_message.reply_text

    # ---------- VOUCHER ADD ----------
    if jenis == "voucher_add":
        parts = [p.strip() for p in text.split("|")]
        
        if len(parts) < 5:
            await reply("Format salah. Contoh:\nPROMO10 | PERCENT | 10 | 50000 | 100")
            return
        
        code_v = parts[0].upper()
        dtype = parts[1].upper()
        value = int(parts[2])
        min_purchase = int(parts[3])
        max_uses = int(parts[4])
        
        if dtype not in ["PERCENT", "FIXED"]:
            await reply("Tipe harus PERCENT atau FIXED")
            return
        
        voucher.create_voucher(code_v, dtype, value, min_purchase, max_uses)
        clear_wait(context)
        await reply(f"✅ Voucher {code_v} berhasil dibuat!")
        return

    # ---------- ISI STOK ----------
    if jenis == "stok":
        hasil = stock.add_from_text(code, text)
        ringkas = "\n".join([
            ui.field("Masuk", f"{ui.angka(hasil['added'])} nomor"),
            ui.field("Duplikat", f"{ui.angka(hasil['duplicate'])} dibuang"),
            ui.field("Tidak valid", f"{ui.angka(hasil['invalid'])} baris"),
            ui.field("Stok kini", f"{ui.angka(hasil['total'])} nomor"),
        ])
        await reply(add_stock_text(code, ui.quote(ringkas)),
                    reply_markup=add_stock_kb(code), parse_mode=ParseMode.HTML)
        return

    # ---------- TAMBAH NEGARA ----------
    if jenis == "negara_add":
        baris = [b for b in text.splitlines() if b.strip()]
        masuk, gagal = [], []
        for b in baris[:20]:
            hasil = catalog.add(b)
            if hasil:
                stock.ensure_files()
                masuk.append(f"{hasil[2]} {hasil[1]}")
            else:
                gagal.append(b.strip())
        clear_wait(context)
        blok = []
        if masuk:
            blok.append(ui.quote(ui.field("Ditambah", f"{len(masuk)} negara") + "\n"
                                 + "\n".join(f"• {m}" for m in masuk)))
        if gagal:
            blok.append(ui.quote(ui.field("Dilewati", f"{len(gagal)} baris") + "\n"
                                 + "\n".join(f"• {g}" for g in gagal)
                                 + "\nNama kosong atau sudah terdaftar."))
        if not masuk and not gagal:
            blok.append("Tidak ada nama negara yang terbaca.")
        judul = "Negara Ditambahkan" if masuk else "Tidak Ada Perubahan"
        rows = []
        if len(masuk) == 1:
            satu = catalog.codes()[-1]
            rows.append([ui.primary("Isi Stok Sekarang", f"adm:add:{satu}", icon="➕")])
        rows.append([ui.plain("Daftar Negara", "adm:neg:0", icon="🌍")])
        rows.append([back_panel()])
        await reply(f"{ui.title(judul)}\n" + "\n".join(blok),
                    reply_markup=ui.kb(*rows), parse_mode=ParseMode.HTML)
        return

    # ---------- UBAH NAMA NEGARA ----------
    if jenis == "negara_rename":
        if not catalog.rename(code, text):
            await reply("Nama tidak terbaca. Kirim ulang, contoh: 🇹🇭 Thailand")
            return
        clear_wait(context)
        await reply(negara_detail_text(code), reply_markup=negara_detail_kb(code),
                    parse_mode=ParseMode.HTML)
        return

    # ---------- UBAH TOMBOL MENU ----------
    if jenis == "menu_set":
        # Bila admin memakai emoji premium, ID-nya sekalian disimpan
        pairs = {}
        for e in (update.effective_message.entities or []):
            if e.type == "custom_emoji" and e.custom_emoji_id:
                pairs[text[e.offset:e.offset + e.length]] = e.custom_emoji_id
        if pairs:
            premium.learn(pairs)
        if not catalog.menu_set(code, text):
            await reply("Nama tidak terbaca. Kirim ulang, contoh: 🛍 Belanja Nomor")
            return
        clear_wait(context)
        tambahan = (f"\n{ui.quote(ui.field('Emoji baru', f'{len(pairs)} disimpan'))}"
                    if pairs else "")
        hasil = "{} {}".format(catalog.menu_icon(code), catalog.menu_label(code)).strip()
        await reply(f"{ui.title('Tombol Diperbarui')}\n"
                    f"{ui.quote(ui.field('Sekarang', hasil))}"
                    f"{tambahan}",
                    reply_markup=menu_kb(), parse_mode=ParseMode.HTML)
        return

    # ---------- TAMBAH PAKET PANEL ----------
    if jenis == "panel_add":
        masuk, gagal = [], []
        for b in [x for x in text.splitlines() if x.strip()][:20]:
            kode = catalog.panel_add(b)
            if kode:
                masuk.append(catalog.panel(kode)["name"])
            else:
                gagal.append(b.strip())
        clear_wait(context)
        blok = []
        if masuk:
            blok.append(ui.quote(ui.field("Ditambah", f"{len(masuk)} paket") + "\n"
                                 + "\n".join(f"• {m}" for m in masuk)))
        if gagal:
            blok.append(ui.quote(ui.field("Dilewati", f"{len(gagal)} baris") + "\n"
                                 + "\n".join(f"• {g}" for g in gagal)
                                 + "\nFormat harus: Nama | Spesifikasi | Harga"))
        judul = "Paket Ditambahkan" if masuk else "Tidak Ada Perubahan"
        await reply(f"{ui.title(judul)}\n" + "\n".join(blok or ["Data tidak terbaca."]),
                    reply_markup=panel_prod_kb(), parse_mode=ParseMode.HTML)
        return

    # ---------- UBAH PAKET PANEL ----------
    if jenis == "panel_edit":
        if not catalog.panel_edit(code, text):
            await reply("Format salah. Kirim: Nama | Spesifikasi | Harga")
            return
        clear_wait(context)
        await reply(panel_detail_text(code), reply_markup=panel_detail_kb(code),
                    parse_mode=ParseMode.HTML)
        return

    # ---------- PENGATURAN TOKO ----------
    if jenis == "setting":
        nilai = ui.bersih(text, 200)
        if not nilai:
            await reply("Nilai tidak boleh kosong.")
            return
        if code == "owner_username" and not nilai.startswith("@"):
            nilai = "@" + nilai.lstrip("@")
        db.set_setting(code, nilai)
        clear_wait(context)
        label = next((l for k, l, _ in SETTINGS_FIELD if k == code), code)
        await reply(f"{ui.title('Pengaturan Disimpan')}\n"
                    f"{ui.quote(ui.field(label, nilai[:60], width=18))}",
                    reply_markup=setting_kb(), parse_mode=ParseMode.HTML)
        return

    # ---------- KURANGI STOK ----------
    if jenis == "hapus_stok":
        angka = text.strip().replace(".", "").replace(",", "")
        if not angka.isdigit() or int(angka) <= 0:
            await reply("Kirim angka saja, contoh: 500")
            return
        hapus = stock.delete_top(code, int(angka))
        clear_wait(context)
        ringkas = "\n".join([
            ui.field("Negara", catalog.label(code)),
            ui.field("Dihapus", f"{ui.angka(hapus)} nomor"),
            ui.field("Stok kini", f"{ui.angka(stock.count(code))} nomor"),
        ])
        await reply(f"{ui.title('Stok Dikurangi')}\n{ui.quote(ringkas)}",
                    reply_markup=negara_detail_kb(code), parse_mode=ParseMode.HTML)
        return

    # ---------- HARGA ----------
    if jenis == "harga":
        qs = list(catalog.prices(code).keys())
        parts = text.replace(",", " ").replace(".", "").split()
        if len(parts) != len(qs) or not all(p.isdigit() for p in parts):
            await reply(f"Format salah. Kirim {len(qs)} angka dipisah spasi, "
                        f"urut untuk {' / '.join(ui.angka(q) for q in qs)} nomor.")
            return
        for q, p in zip(qs, parts):
            catalog.set_price(code, q, int(p))
        clear_wait(context)
        await reply(negara_detail_text(code), reply_markup=negara_detail_kb(code),
                    parse_mode=ParseMode.HTML)
        return

    # ---------- PAKET JUMLAH ----------
    if jenis == "paket":
        parts = [p for p in text.replace(",", " ").replace(".", "").split() if p.isdigit()]
        nilai = sorted({int(p) for p in parts if int(p) > 0})
        if not nilai:
            await reply("Kirim angka dipisah spasi, contoh: 100 250 500 1000")
            return
        if len(nilai) > 8:
            await reply("Maksimal 8 paket agar tombol tetap rapi.")
            return
        catalog.set_quantities(nilai)
        clear_wait(context)
        ringkas = "\n".join([
            ui.field("Paket baru", " · ".join(ui.angka(q) for q in nilai)),
            ui.field("Berlaku", f"{len(catalog.codes())} negara"),
        ])
        await reply(f"{ui.title('Paket Diperbarui')}\n{ui.quote(ringkas)}\n"
                    "Harga paket baru dihitung otomatis dari tarif per nomor. "
                    "Sesuaikan lewat menu Atur Harga bila perlu.",
                    reply_markup=ui.kb([ui.plain("Harga & Paket", "adm:price", icon="💰")],
                                       [back_panel()]), parse_mode=ParseMode.HTML)
        return

    # ---------- TARIF ----------
    if jenis == "tarif":
        angka = text.strip().replace(".", "").replace(",", "")
        if not angka.isdigit() or int(angka) <= 0:
            await reply("Kirim angka saja, contoh: 45")
            return
        catalog.set_rate(int(angka))
        clear_wait(context)
        await reply(f"{ui.title('Tarif Diperbarui')}\n"
                    f"{ui.quote(ui.field('Tarif', f'{ui.rupiah(catalog.rate())} / nomor'))}\n"
                    "Harga negara dan paket yang sudah ada tidak berubah.",
                    reply_markup=ui.kb([ui.plain("Harga & Paket", "adm:price", icon="💰")],
                                       [back_panel()]), parse_mode=ParseMode.HTML)
        return

    # ---------- BROADCAST ----------
    if jenis == "broadcast":
        clear_wait(context)
        msg = await reply("Mengirim broadcast...")
        ok, gagal = await do_broadcast(context, text)
        ringkas = "\n".join([
            ui.field("Terkirim", f"{ok} member"),
            ui.field("Gagal", f"{gagal} member"),
        ])
        await msg.edit_text(f"{ui.title('Broadcast Selesai')}\n{ui.quote(ringkas)}",
                            reply_markup=ui.kb([back_panel()]), parse_mode=ParseMode.HTML)
        return

    # ---------- EMOJI ----------
    if jenis == "emoji":
        ents = (update.effective_message.entities or [])
        pairs = {}
        for e in ents:
            if e.type == "custom_emoji" and e.custom_emoji_id:
                char = text[e.offset:e.offset + e.length]
                pairs[char] = e.custom_emoji_id
        if not pairs:
            await reply("Tidak ada emoji premium terdeteksi. "
                        "Pakai keyboard emoji premium lalu kirim ulang.")
            return
        jumlah = premium.learn(pairs)
        clear_wait(context)
        await reply(f"{ui.title('Emoji Disimpan')}\n"
                    f"{ui.quote(ui.field('Baru', f'{jumlah} emoji') + chr(10) + ui.field('Total', f'{len(premium.emoji_map())} emoji'))}",
                    reply_markup=emoji_kb(), parse_mode=ParseMode.HTML)
        return


# ==========================================================
# VOUCHER MANAGEMENT
# ==========================================================
async def cb_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    
    vouchers = voucher.list_vouchers()
    
    if not vouchers:
        text = f"{ui.title('Kelola Voucher')}\nBelum ada voucher.\n\nTekan Tambah untuk membuat voucher baru."
        kb = ui.kb(
            [ui.success("Tambah Voucher", "adm:vadd", icon="➕")],
            [back_panel()]
        )
        await safe_edit(query, text, kb)
        return
    
    vlist = []
    buttons = []
    for v in vouchers:
        status = "●" if v["aktif"] else "○"
        if v["discount_type"] == "PERCENT":
            disc = f"{v['discount_value']}%"
        else:
            disc = ui.rupiah(v['discount_value'])
        
        vlist.append(f"{status} <code>{v['code']}</code> • Diskon {disc}")
        buttons.append([
            ui.plain(v['code'], f"adm:vdet:{v['code']}"),
            ui.plain("Hapus", f"adm:vdel:{v['code']}", icon="🗑️")
        ])
    
    text = f"{ui.title('Kelola Voucher')}\n{ui.quote(chr(10).join(vlist))}"
    buttons.append([ui.success("Tambah Voucher", "adm:vadd", icon="➕")])
    buttons.append([back_panel()])
    
    await safe_edit(query, text, ui.kb(*buttons))


async def cb_voucher_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    
    wait(context, "voucher_add")
    
    text = (
        f"{ui.title('Tambah Voucher')}\n\n"
        "Format: KODE | TIPE | NILAI | MIN_BELI | MAX_USE\n\n"
        "Contoh:\n"
        "<code>PROMO10 | PERCENT | 10 | 50000 | 100</code>\n"
        "<code>DISKON5K | FIXED | 5000 | 0 | 0</code>\n\n"
        "TIPE: PERCENT atau FIXED\n"
        "MIN_BELI: minimal pembelian (0 = tidak ada min)\n"
        "MAX_USE: maksimal penggunaan (0 = unlimited)"
    )
    
    await safe_edit(query, text, ui.kb([ui.plain("Batal", "adm:voucher")]))


async def cb_voucher_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    
    code = query.data.split(":", 2)[2]
    voucher.delete_voucher(code)
    
    await query.answer(f"Voucher {code} dihapus", show_alert=True)
    await cb_voucher(update, context)


# ==========================================================
# TESTIMONIAL MANAGEMENT
# ==========================================================
async def cb_testi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    await query.answer()
    
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM testimonials ORDER BY approved DESC, created_at DESC LIMIT 20")
    testimonials = cur.fetchall()
    
    if not testimonials:
        text = f"{ui.title('Testimonial')}\nBelum ada testimonial."
        await safe_edit(query, text, ui.kb([back_panel()]))
        return
    
    tlist = []
    buttons = []
    for t in testimonials:
        status = "✅" if t["approved"] else "⏳"
        stars = "⭐" * t["rating"]
        tlist.append(f"{status} {stars} @{t['username']}: {t['message'][:50]}...")
        
        if not t["approved"]:
            buttons.append([
                ui.success("Setujui", f"adm:tapp:{t['id']}", icon="✅"),
                ui.danger("Tolak", f"adm:tdel:{t['id']}", icon="❌")
            ])
    
    text = f"{ui.title('Kelola Testimonial')}\n{chr(10).join(tlist)}"
    buttons.append([back_panel()])
    
    await safe_edit(query, text, ui.kb(*buttons))


async def cb_testi_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    
    testi_id = int(query.data.split(":", 2)[2])
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE testimonials SET approved=1 WHERE id=?", (testi_id,))
    conn.commit()
    
    await query.answer("Testimonial disetujui", show_alert=True)
    await cb_testi(update, context)


async def cb_testi_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return await deny(update)
    query = update.callback_query
    
    testi_id = int(query.data.split(":", 2)[2])
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM testimonials WHERE id=?", (testi_id,))
    conn.commit()
    
    await query.answer("Testimonial dihapus", show_alert=True)
    await cb_testi(update, context)

