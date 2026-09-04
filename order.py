# -*- coding: utf-8 -*-
"""
order.py
Handler sisi pembeli: menu utama, order file nomor, order panel,
riwayat, akun, owner, konfirmasi pembayaran.
"""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

import catalog
import config
import database as db
import levels
import qris
import referral
import stock
import ui
import voucher

log = logging.getLogger(__name__)

PER_PAGE = 8


# ==========================================================
# UTIL
# ==========================================================
def uname(user) -> str:
    """Nama tampilan pembeli, sudah aman untuk pesan HTML."""
    if getattr(user, "username", None):
        return "@" + ui.esc(user.username)
    return ui.esc(getattr(user, "first_name", "User") or "User")


async def safe_edit(query, text: str, keyboard=None):
    try:
        if query.message and query.message.photo:
            await query.edit_message_caption(
                caption=text, reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
    except BadRequest as e:
        if "not modified" in str(e).lower():
            return
        try:
            await query.message.reply_text(
                text, reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
        except Exception:  # noqa: BLE001
            log.warning("safe_edit gagal: %s", e)


# ==========================================================
# MENU UTAMA
# ==========================================================
def mbtn(key: str, data: str, fallback: str, ikon: str = "", warna=None):
    """Tombol yang label, ikon, dan warnanya diatur dari Kelola Menu."""
    return ui.btn(
        catalog.menu_label(key, fallback),
        data,
        style=warna if warna is not None else catalog.menu_style(key),
        icon=catalog.menu_icon(key, ikon),
    )


def main_menu_kb(user_id: int):
    rows = []
    if catalog.menu_on("order"):
        rows.append([mbtn("order", "menu:order", "Order Sekarang", "🛒", "primary")])

    kedua = []
    if catalog.menu_on("history"):
        kedua.append(mbtn("history", "menu:history", "Riwayat", "📊"))
    if catalog.menu_on("info"):
        kedua.append(mbtn("info", "menu:info", "Akun Saya", "👤"))
    if kedua:
        rows.append(kedua)
    
    # Add voucher and referral buttons
    rows.append([
        ui.plain("Voucher", "menu:voucher", icon="🎟️"),
        ui.plain("Referral", "menu:referral", icon="🎁"),
    ])

    if catalog.menu_on("owner"):
        rows.append([mbtn("owner", "menu:owner", "Owner & Bantuan", "👑")])

    if config.is_admin(user_id):
        rows.append([ui.plain("Admin Panel", "adm:panel", icon="🎨")])
    if not rows:
        rows.append([ui.plain("Hubungi Admin", "menu:owner", icon="👑")])
    return ui.kb(*rows)


def welcome_text(user) -> str:
    toko = db.get_setting("store_name", config.STORE_NAME)
    st = db.stats()
    
    # Get user level
    user_level = levels.get_user_level(user.id)
    next_lvl, needed = levels.next_level(user_level.get("min", 0))
    
    level_info = f"{user_level['icon']} Level {user_level['name']}"
    if user_level['discount'] > 0:
        level_info += f" • Diskon {user_level['discount']}%"
    
    ringkas = "\n".join([
        ui.field("Status", level_info),
        ui.field("Stok", f"{ui.angka(stock.total_all())} nomor tersedia"),
        ui.field("Negara", f"{len(catalog.codes(True))} pilihan"),
        ui.field("Transaksi", f"{ui.angka(st['success'])} sukses"),
        ui.field("Member", f"{ui.angka(st['total_user'])} terdaftar"),
    ])
    
    greeting = f"Halo, <b>{ui.esc(user.first_name) or 'Kak'}</b> 👋"
    
    return (
        f"<b>🏪 {toko.upper()}</b>\n"
        f"{ui.SEP}\n\n"
        f"{greeting}\n"
        f"Selamat datang di layanan file nomor otomatis.\n"
        f"Aktif 24 jam, pengiriman instan.\n\n"
        f"{ui.quote(ringkas)}\n"
        f"Silakan pilih menu di bawah."
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username or "", user.first_name or "")
    context.user_data.clear()
    await update.effective_message.reply_text(
        welcome_text(user), reply_markup=main_menu_kb(user.id),
        parse_mode=ParseMode.HTML,
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"User ID Anda: <code>{update.effective_user.id}</code>",
        parse_mode=ParseMode.HTML,
    )


async def cb_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("awaiting", None)
    await safe_edit(query, welcome_text(update.effective_user),
                    main_menu_kb(update.effective_user.id))


# ==========================================================
# MENU ORDER
# ==========================================================
async def cb_order_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ada_file = catalog.menu_on("order_file")
    ada_panel = catalog.menu_on("order_panel") and len(catalog.panels(True)) > 0

    # Bila hanya satu kategori aktif, lompat langsung supaya tidak bertele-tele
    if ada_file and not ada_panel:
        return await cb_order_file(update, context)
    if ada_panel and not ada_file:
        return await cb_order_panel(update, context)
    if not ada_file and not ada_panel:
        await safe_edit(query, (
            f"{ui.title('Order')}\n"
            "Belum ada produk yang dibuka.\nSilakan hubungi admin."
        ), ui.kb([ui.back()]))
        return

    keterangan = []
    rows = []
    if ada_file:
        keterangan.append(f"{catalog.menu_label('order_file', 'File Nomor')} — "
                          f"{len(catalog.codes(True))} negara, dikirim sebagai file .txt")
        rows.append([mbtn("order_file", "order:file:0", "File Nomor", "📂", "primary")])
    if ada_panel:
        keterangan.append(f"{catalog.menu_label('order_panel', 'Panel Hosting')} — "
                          f"{len(catalog.panels(True))} paket panel siap pakai")
        rows.append([mbtn("order_panel", "order:panel", "Panel Hosting", "🎁")])
    rows.append([ui.back()])

    await safe_edit(query, f"{ui.title('Pilih Kategori')}\n"
                           f"{ui.quote(chr(10).join(keterangan))}", ui.kb(*rows))


# ---------- DAFTAR NEGARA (dinamis + halaman) ----------
async def cb_order_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not catalog.menu_on("order_file"):
        await safe_edit(query, f"{ui.title('Tidak Tersedia')}\n"
                               "Menu ini sedang ditutup admin.", ui.kb([ui.home()]))
        return

    parts = query.data.split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    negara = [r for r in catalog.all_countries(active_only=True)]
    if not negara:
        await safe_edit(query, (
            f"{ui.title('File Nomor')}\n"
            "Belum ada negara yang tersedia.\n"
            "Silakan hubungi admin."
        ), ui.kb([ui.back("menu:order")]))
        return

    total_page = max(1, (len(negara) + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, total_page - 1))
    chunk = negara[page * PER_PAGE:(page + 1) * PER_PAGE]

    baris = []
    for r in chunk:
        n = stock.count(r["code"])
        tanda = "●" if n > 0 else "○"
        baris.append(f"{tanda} {r['flag']} {r['name']} — {ui.angka(n)} nomor")

    text = (
        f"{ui.title('Pilih Negara')}\n"
        f"{ui.quote(chr(10).join(baris))}\n"
        f"Halaman {page + 1} dari {total_page} · {len(negara)} negara"
    )

    rows, pair = [], []
    for r in chunk:
        n = stock.count(r["code"])
        tombol = ui.plain(r["name"], f"country:{r['code']}", icon=r["flag"]) if n == 0 \
            else ui.primary(r["name"], f"country:{r['code']}", icon=r["flag"])
        pair.append(tombol)
        if len(pair) == 2:
            rows.append(pair); pair = []
    if pair:
        rows.append(pair)

    nav = []
    if page > 0:
        nav.append(ui.plain("‹ Sebelumnya", f"order:file:{page - 1}"))
    if page < total_page - 1:
        nav.append(ui.plain("Berikutnya ›", f"order:file:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([ui.back("menu:order")])

    await safe_edit(query, text, ui.kb(*rows))


# ---------- DETAIL NEGARA ----------
async def cb_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]

    row = catalog.get(code)
    if not row or not row["aktif"]:
        await safe_edit(query, "Produk tidak tersedia.", ui.kb([ui.back("order:file:0")]))
        return

    tersedia = stock.count(code)
    harga = catalog.prices(code)

    info = "\n".join([
        ui.field("Stok", f"{ui.angka(tersedia)} nomor"),
        ui.field("Format", "file .txt"),
        ui.field("Kirim", "otomatis setelah diverifikasi"),
    ])
    daftar = "\n".join(f"• {ui.angka(q)} nomor — {ui.rupiah(h)}" for q, h in harga.items())

    judul = f"{row['flag']} {row['name']}"
    text = (
        f"{ui.title(judul)}\n"
        f"{ui.quote(info)}\n"
        f"<b>Paket tersedia</b>\n{daftar}\n\n"
        + ("Pilih paket di bawah." if tersedia > 0 else "Stok sedang kosong.")
    )

    rows = []
    for q, h in harga.items():
        if tersedia >= q:
            rows.append([ui.success(f"{ui.angka(q)} nomor · {ui.rupiah(h)}",
                                    f"qty:{code}:{q}", icon="💰")])
        else:
            rows.append([ui.plain(f"{ui.angka(q)} nomor · stok kurang", f"qty:{code}:{q}")])
    rows.append([ui.back("order:file:0", "Negara Lain"), ui.home()])

    await safe_edit(query, text, ui.kb(*rows))


# ---------- BUAT INVOICE ----------
async def _kirim_invoice(context, chat_id: int, invoice: str):
    order = db.get_order(invoice)
    keyboard = ui.kb(
        [ui.success("Saya Sudah Bayar", f"pay:{invoice}", icon="✅")],
        [ui.danger("Batalkan", f"cancel:{invoice}", icon="❌")],
        [ui.home()],
    )
    caption = qris.payment_caption(order)
    if qris.qris_exists():
        with open(qris.qris_path(), "rb") as f:
            await context.bot.send_photo(chat_id=chat_id, photo=f, caption=caption,
                                         reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=chat_id,
                                       text=caption + "\n\n" + qris.no_qris_text(),
                                       reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def cb_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, code, qty = query.data.split(":")
    qty = int(qty)
    user = update.effective_user

    row = catalog.get(code)
    if not row:
        await query.answer("Produk tidak tersedia.", show_alert=True)
        return

    tersedia = stock.count(code)
    if tersedia < qty:
        await query.answer(
            f"Stok {row['name']} tinggal {ui.angka(tersedia)} nomor.", show_alert=True
        )
        return

    await query.answer("Membuat invoice")
    db.ensure_user(user.id, user.username or "", user.first_name or "")
    harga = catalog.price(code, qty)
    invoice = db.create_order(
        user_id=user.id, username=uname(user), kategori="FILE",
        produk=f"{ui.angka(qty)} Nomor {row['name']}",
        negara=code, jumlah=qty, harga=harga,
    )
    await _kirim_invoice(context, update.effective_chat.id, invoice)


# ---------- PANEL ----------
async def cb_order_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    items = catalog.panels(active_only=True)
    judul = catalog.menu_label("order_panel", "Panel Hosting")
    if not catalog.menu_on("order_panel") or not items:
        await safe_edit(query, f"{ui.title(judul)}\n"
                               "Belum ada paket yang tersedia.", ui.kb([ui.home()]))
        return

    daftar = "\n".join(
        f"• <b>{p['name']}</b> — {ui.rupiah(p['price'])}\n  {p['spek']}" for p in items
    )
    text = (
        f"{ui.title(judul)}\n{daftar}\n\n"
        f"{ui.quote('Panel dibuat admin setelah pembayaran diverifikasi.')}"
    )
    rows = [[ui.primary(f"{p['name']} · {ui.rupiah(p['price'])}",
                        f"panel:{p['code']}", icon=catalog.menu_icon("order_panel", "🎁"))]
            for p in items]
    rows.append([ui.back("menu:order")])
    await safe_edit(query, text, ui.kb(*rows))


async def cb_panel_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    key = query.data.split(":", 1)[1]
    p = catalog.panel(key)
    if not p or not p["aktif"]:
        await query.answer("Produk tidak tersedia lagi.", show_alert=True)
        return
    user = update.effective_user
    await query.answer("Membuat invoice")
    db.ensure_user(user.id, user.username or "", user.first_name or "")
    invoice = db.create_order(user.id, uname(user), "PANEL", p["name"], "", 1, p["price"])
    await _kirim_invoice(context, update.effective_chat.id, invoice)


# ==========================================================
# PEMBAYARAN
# ==========================================================
async def cb_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    invoice = query.data.split(":", 1)[1]
    user = update.effective_user

    order = db.get_order(invoice)
    if not order:
        await query.answer("Invoice tidak ditemukan.", show_alert=True)
        return
    if order["user_id"] != user.id and not config.is_admin(user.id):
        await query.answer("Ini bukan invoice Anda.", show_alert=True)
        return
    if order["status"] == "CHECKING":
        await query.answer("Sudah dikonfirmasi, mohon tunggu admin.", show_alert=True)
        return
    if order["status"] != "PENDING":
        await query.answer(config.STATUS_LABEL.get(order["status"], "-"), show_alert=True)
        return

    db.update_status(invoice, "CHECKING")
    order = db.get_order(invoice)
    await query.answer("Konfirmasi terkirim")

    detail = "\n".join([
        ui.field("Invoice", f"<code>{invoice}</code>"),
        ui.field("Produk", order["produk"]),
        ui.field("Total", f"<b>{ui.rupiah(order['harga'])}</b>"),
        ui.field("Status", config.STATUS_LABEL["CHECKING"]),
    ])
    await safe_edit(query, (
        f"{ui.title('Menunggu Verifikasi')}\n"
        f"{ui.quote(detail)}\n"
        "Konfirmasi Anda sudah diteruskan ke admin.\n"
        "Pesanan dikirim otomatis setelah pembayaran disetujui."
    ), ui.kb([ui.plain("Riwayat", "menu:history", icon="📊")], [ui.home()]))

    # --- laporan ke admin ---
    stok_baris = ""
    if order["kategori"] == "FILE":
        stok_baris = "\n" + ui.field("Stok", f"{ui.angka(stock.count(order['negara']))} nomor")

    lap = "\n".join([
        ui.field("Invoice", f"<code>{order['invoice']}</code>"),
        ui.field("Pembeli", ui.esc(order["username"])),
        ui.field("User ID", f"<code>{order['user_id']}</code>"),
        ui.field("Produk", order["produk"]),
        ui.field("Harga", f"<b>{ui.rupiah(order['harga'])}</b>"),
        ui.field("Waktu", order["created_at"]),
    ]) + stok_baris

    teks_admin = (
        f"{ui.title('Pembayaran Baru')}\n"
        f"{ui.quote(lap)}\n"
        "Cek mutasi QRIS lalu pilih tindakan."
    )
    keyboard = ui.kb(
        [ui.success("Terima", f"adm:ok:{invoice}", icon="✅"),
         ui.danger("Tolak", f"adm:no:{invoice}", icon="❌")],
        [ui.plain("Order Pending", "adm:pending", icon="📊")],
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, teks_admin, reply_markup=keyboard,
                                           parse_mode=ParseMode.HTML)
        except Exception as e:  # noqa: BLE001
            log.warning("Notif admin %s gagal: %s", admin_id, e)


async def cb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    invoice = query.data.split(":", 1)[1]
    user = update.effective_user
    order = db.get_order(invoice)

    if not order:
        await query.answer("Invoice tidak ditemukan.", show_alert=True)
        return
    if order["user_id"] != user.id and not config.is_admin(user.id):
        await query.answer("Ini bukan invoice Anda.", show_alert=True)
        return
    if order["status"] == "SUCCESS":
        await query.answer("Pesanan sudah selesai.", show_alert=True)
        return

    db.update_status(invoice, "CANCEL", "Dibatalkan pembeli")
    await query.answer("Pesanan dibatalkan")
    await safe_edit(query, (
        f"{ui.title('Pesanan Dibatalkan')}\n"
        f"{ui.quote(ui.field('Invoice', f'<code>{invoice}</code>') + chr(10) + ui.field('Produk', order['produk']))}\n"
        "Silakan order kembali kapan saja."
    ), ui.kb([ui.primary("Order Lagi", "menu:order", icon="🛒")], [ui.home()]))


# ==========================================================
# RIWAYAT
# ==========================================================
async def cb_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not catalog.menu_on("history") and not config.is_admin(update.effective_user.id):
        await safe_edit(query, f"{ui.title('Tidak Tersedia')}\n"
                               "Menu ini sedang ditutup admin.", ui.kb([ui.home()]))
        return
    user = update.effective_user
    rows = db.user_orders(user.id, limit=10)

    if not rows:
        text = (f"{ui.title('Riwayat Order')}\n"
                "Belum ada transaksi.\nMulai order pertama Anda sekarang.")
    else:
        item = []
        for o in rows:
            dot = config.STATUS_DOT.get(o["status"], "·")
            item.append(
                f"{dot} <code>{o['invoice']}</code>\n"
                f"   {o['produk']} — {ui.rupiah(o['harga'])}\n"
                f"   {config.STATUS_LABEL.get(o['status'], o['status'])} · {o['created_at']}"
            )
        ringkas = "\n".join([
            ui.field("Sukses", f"{db.count_user_success(user.id)} order"),
            ui.field("Belanja", ui.rupiah(db.sum_user_spend(user.id))),
        ])
        text = (f"{ui.title('Riwayat Order')}\n"
                + "\n\n".join(item) + f"\n\n{ui.quote(ringkas)}")

    await safe_edit(query, text, ui.kb(
        [mbtn("order", "menu:order", "Order Sekarang", "🛒", "primary")], [ui.home()]
    ))


# ==========================================================
# AKUN
# ==========================================================
async def cb_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    db.ensure_user(user.id, user.username or "", user.first_name or "")
    row = db.get_user(user.id)

    belanja = db.sum_user_spend(user.id)
    level = ("Diamond" if belanja >= 500000 else
             "Gold" if belanja >= 200000 else
             "Silver" if belanja >= 50000 else "Bronze")

    data = "\n".join([
        ui.field("Nama", ui.esc(user.first_name) or "-"),
        ui.field("Username", uname(user)),
        ui.field("User ID", f"<code>{user.id}</code>"),
        ui.field("Status", "Admin" if config.is_admin(user.id) else "Member"),
        ui.field("Level", f"<b>{level}</b>"),
        ui.field("Order", f"{db.count_user_success(user.id)} sukses"),
        ui.field("Belanja", ui.rupiah(belanja)),
        ui.field("Gabung", row["joined_at"] if row else "-"),
    ])
    await safe_edit(query, f"{ui.title('Akun Saya')}\n{ui.quote(data)}",
                    ui.kb([ui.plain("Riwayat", "menu:history", icon="📊")], [ui.home()]))


# ==========================================================
# OWNER
# ==========================================================
async def cb_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_user = db.get_setting("owner_username", config.OWNER_USERNAME)
    owner_name = db.get_setting("owner_name", config.OWNER_NAME)
    toko = db.get_setting("store_name", config.STORE_NAME)

    data = "\n".join([
        ui.field("Toko", toko),
        ui.field("Owner", owner_name),
        ui.field("Kontak", owner_user),
        ui.field("Jam", "24 jam"),
    ])
    aturan = ui.bullet([
        "Bayar sesuai nominal invoice",
        "Produk digital tidak dapat direfund",
        "Komplain maksimal 1x24 jam",
        "Dilarang menyalahgunakan produk",
    ])
    text = (f"{ui.title('Owner & Bantuan')}\n{ui.quote(data)}\n"
            f"<b>Aturan toko</b>\n{aturan}")

    rows = []
    if owner_user.startswith("@"):
        rows.append([ui.primary("Chat Owner", url=f"https://t.me/{owner_user.lstrip('@')}",
                                icon="👑")])
    rows.append([ui.home()])
    await safe_edit(query, text, ui.kb(*rows))


async def cb_noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


# ==========================================================
# VOUCHER MENU
# ==========================================================
async def cb_voucher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    conn = db.get_conn()
    cur = conn.cursor()
    
    # Get active vouchers
    cur.execute("SELECT * FROM vouchers WHERE aktif=1 ORDER BY expires_at")
    vouchers = cur.fetchall()
    
    if not vouchers:
        text = (
            f"{ui.title('Voucher Diskon')}\n"
            "Belum ada voucher tersedia saat ini.\n"
            "Pantau terus untuk promo menarik!"
        )
        await safe_edit(query, text, ui.kb([ui.back()]))
        return
    
    vlist = []
    for v in vouchers:
        if v["discount_type"] == "PERCENT":
            disc = f"{v['discount_value']}%"
        else:
            disc = ui.rupiah(v['discount_value'])
        
        status = "✅ Aktif"
        if v["max_uses"] > 0:
            status += f" • {v['used_count']}/{v['max_uses']} terpakai"
        
        vlist.append(f"<code>{v['code']}</code>\n  Diskon {disc} • {status}")
    
    text = (
        f"{ui.title('Voucher Tersedia')}\n"
        f"{ui.quote(chr(10).join(vlist))}\n\n"
        "Masukkan kode voucher saat checkout untuk mendapat diskon."
    )
    
    await safe_edit(query, text, ui.kb([ui.back()]))


# ==========================================================
# REFERRAL MENU
# ==========================================================
async def cb_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    ref_code = referral.get_referral_code(user_id)
    stats = referral.get_referral_stats(user_id)
    
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = cur.fetchone()["balance"] or 0
    
    info = "\n".join([
        ui.field("Kode Anda", f"<code>{ref_code}</code>"),
        ui.field("Total Referral", f"{stats['total']} orang"),
        ui.field("Penghasilan", ui.rupiah(stats['earnings'])),
        ui.field("Saldo", ui.rupiah(balance)),
    ])
    
    text = (
        f"{ui.title('Program Referral')}\n"
        f"{ui.quote(info)}\n\n"
        f"<b>Cara Kerja:</b>\n"
        f"• Ajak teman pakai kode referral Anda\n"
        f"• Anda dapat {ui.rupiah(referral.REFERRAL_REWARD)}\n"
        f"• Teman dapat {ui.rupiah(referral.REFEREE_REWARD)}\n"
        f"• Saldo bisa dipakai untuk belanja\n\n"
        f"Bagikan kode: <code>{ref_code}</code>"
    )
    
    await safe_edit(query, text, ui.kb([ui.back()]))
