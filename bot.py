# -*- coding: utf-8 -*-
"""
bot.py
Entry point AmelBot — Telegram Auto Order Bot (File Nomor + Panel).

Cara jalan:
    pip install -r requirements.txt
    python bot.py

Wajib set Environment Variable (atau edit config.py):
    BOT_TOKEN=1234567:AAxxxxxxxxxxxxxxxxxxxxx
    ADMIN_IDS=123456789,987654321
"""

import asyncio
import logging
import sys

from telegram import BotCommand, Update
from telegram.error import InvalidToken, NetworkError
from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import admin
import config
import database as db
import order
import premium
import stock

# ==========================================================
# LOGGING
# ==========================================================
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("AmelBot")


# ==========================================================
# ERROR HANDLER
# ==========================================================
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Terjadi error saat memproses update", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Terjadi kesalahan sistem. Silakan coba lagi atau ketik /start."
            )
    except Exception:  # noqa: BLE001
        pass


# ==========================================================
# PERINTAH TAMBAHAN
# ==========================================================
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_adm = config.is_admin(update.effective_user.id)
    text = (
        "📖 <b>BANTUAN</b>\n"
        f"{'─' * 22}\n"
        "/start — Membuka menu utama\n"
        "/menu  — Sama dengan /start\n"
        "/id    — Melihat User ID Anda\n"
        "/help  — Menampilkan bantuan\n"
    )
    if is_adm:
        text += (
            f"{'─' * 22}\n"
            "👑 <b>PERINTAH ADMIN</b>\n"
            "/admin      — Membuka Admin Panel\n"
            "/tambahstok — Menambah stok nomor\n"
            "/cekstok    — Melihat jumlah stok\n"
            "/batal      — Membatalkan aksi admin\n"
        )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Buka menu utama"),
        BotCommand("menu", "Buka menu utama"),
        BotCommand("id", "Lihat User ID"),
        BotCommand("help", "Bantuan"),
        BotCommand("admin", "Admin panel (khusus admin)"),
        BotCommand("tambahstok", "Tambah stok (khusus admin)"),
        BotCommand("cekstok", "Cek stok (khusus admin)"),
    ])
    me = await application.bot.get_me()
    log.info("Bot aktif sebagai @%s (id: %s)", me.username, me.id)


# ==========================================================
# REGISTRASI HANDLER
# ==========================================================
def register(app: Application) -> None:
    # ---------- COMMAND ----------
    app.add_handler(CommandHandler("start", order.cmd_start))
    app.add_handler(CommandHandler("menu", order.cmd_menu))
    app.add_handler(CommandHandler("id", order.cmd_id))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("admin", admin.cmd_admin))
    app.add_handler(CommandHandler("tambahstok", admin.cmd_tambahstok))
    app.add_handler(CommandHandler("cekstok", admin.cmd_cekstok))
    app.add_handler(CommandHandler("batal", admin.cmd_batal))

    # ---------- CALLBACK USER ----------
    app.add_handler(CallbackQueryHandler(order.cb_main, pattern=r"^menu:main$"))
    app.add_handler(CallbackQueryHandler(order.cb_order_menu, pattern=r"^menu:order$"))
    app.add_handler(CallbackQueryHandler(order.cb_history, pattern=r"^menu:history$"))
    app.add_handler(CallbackQueryHandler(order.cb_info, pattern=r"^menu:info$"))
    app.add_handler(CallbackQueryHandler(order.cb_owner, pattern=r"^menu:owner$"))
    app.add_handler(CallbackQueryHandler(order.cb_voucher, pattern=r"^menu:voucher$"))
    app.add_handler(CallbackQueryHandler(order.cb_referral, pattern=r"^menu:referral$"))

    app.add_handler(CallbackQueryHandler(order.cb_order_file, pattern=r"^order:file"))
    app.add_handler(CallbackQueryHandler(order.cb_order_panel, pattern=r"^order:panel$"))
    app.add_handler(CallbackQueryHandler(order.cb_country, pattern=r"^country:"))
    app.add_handler(CallbackQueryHandler(order.cb_qty, pattern=r"^qty:"))
    app.add_handler(CallbackQueryHandler(order.cb_panel_pick, pattern=r"^panel:"))
    app.add_handler(CallbackQueryHandler(order.cb_pay, pattern=r"^pay:"))
    app.add_handler(CallbackQueryHandler(order.cb_cancel, pattern=r"^cancel:"))

    # --- admin: order ---
    app.add_handler(CallbackQueryHandler(admin.cb_panel, pattern=r"^adm:panel$"))
    app.add_handler(CallbackQueryHandler(admin.cb_pending, pattern=r"^adm:pending$"))
    app.add_handler(CallbackQueryHandler(admin.cb_accept, pattern=r"^adm:ok:"))
    app.add_handler(CallbackQueryHandler(admin.cb_reject, pattern=r"^adm:no:"))

    # --- admin: negara ---
    app.add_handler(CallbackQueryHandler(admin.cb_negara, pattern=r"^adm:neg"))
    app.add_handler(CallbackQueryHandler(admin.cb_negara_add, pattern=r"^adm:nadd$"))
    app.add_handler(CallbackQueryHandler(admin.cb_negara_detail, pattern=r"^adm:ndet:"))
    app.add_handler(CallbackQueryHandler(admin.cb_negara_rename, pattern=r"^adm:nren:"))
    app.add_handler(CallbackQueryHandler(admin.cb_negara_toggle, pattern=r"^adm:ntog:"))
    app.add_handler(CallbackQueryHandler(admin.cb_negara_del_ok, pattern=r"^adm:ndelok:"))
    app.add_handler(CallbackQueryHandler(admin.cb_negara_del, pattern=r"^adm:ndel:"))

    # --- admin: stok ---
    app.add_handler(CallbackQueryHandler(admin.cb_stock, pattern=r"^adm:stock$"))
    app.add_handler(CallbackQueryHandler(admin.cb_addstock, pattern=r"^adm:add:"))
    app.add_handler(CallbackQueryHandler(admin.cb_delstock_all, pattern=r"^adm:delall:"))
    app.add_handler(CallbackQueryHandler(admin.cb_delstock, pattern=r"^adm:del:"))

    # --- admin: harga & paket ---
    app.add_handler(CallbackQueryHandler(admin.cb_price, pattern=r"^adm:price$"))
    app.add_handler(CallbackQueryHandler(admin.cb_price_set, pattern=r"^adm:pset:"))
    app.add_handler(CallbackQueryHandler(admin.cb_qty, pattern=r"^adm:qty$"))
    app.add_handler(CallbackQueryHandler(admin.cb_rate, pattern=r"^adm:rate$"))

    # --- admin: kelola menu ---
    app.add_handler(CallbackQueryHandler(admin.cb_menu, pattern=r"^adm:menu$"))
    app.add_handler(CallbackQueryHandler(admin.cb_menu_toggle, pattern=r"^adm:mtog:"))
    app.add_handler(CallbackQueryHandler(admin.cb_menu_set, pattern=r"^adm:mset:"))

    # --- admin: produk panel ---
    app.add_handler(CallbackQueryHandler(admin.cb_panelprod, pattern=r"^adm:pnl$"))
    app.add_handler(CallbackQueryHandler(admin.cb_panel_add, pattern=r"^adm:padd$"))
    app.add_handler(CallbackQueryHandler(admin.cb_panel_detail, pattern=r"^adm:pdet:"))
    app.add_handler(CallbackQueryHandler(admin.cb_panel_edit, pattern=r"^adm:pedit:"))
    app.add_handler(CallbackQueryHandler(admin.cb_panel_toggle, pattern=r"^adm:ptog:"))
    app.add_handler(CallbackQueryHandler(admin.cb_panel_del_ok, pattern=r"^adm:pdelok:"))
    app.add_handler(CallbackQueryHandler(admin.cb_panel_del, pattern=r"^adm:pdel:"))

    # --- admin: pengaturan toko ---
    app.add_handler(CallbackQueryHandler(admin.cb_setting, pattern=r"^adm:set$"))
    app.add_handler(CallbackQueryHandler(admin.cb_setting_set, pattern=r"^adm:sset:"))

    # --- admin: lain-lain ---
    app.add_handler(CallbackQueryHandler(admin.cb_qris, pattern=r"^adm:qris$"))
    app.add_handler(CallbackQueryHandler(admin.cb_stats, pattern=r"^adm:stats$"))
    app.add_handler(CallbackQueryHandler(admin.cb_broadcast, pattern=r"^adm:bc$"))
    app.add_handler(CallbackQueryHandler(admin.cb_emoji, pattern=r"^adm:emoji$"))
    app.add_handler(CallbackQueryHandler(admin.cb_emoji_toggle, pattern=r"^adm:emojitoggle$"))
    app.add_handler(CallbackQueryHandler(admin.cb_emoji_learn, pattern=r"^adm:emojilearn$"))
    app.add_handler(CallbackQueryHandler(admin.cb_emoji_reset, pattern=r"^adm:emojireset$"))
    app.add_handler(CallbackQueryHandler(admin.cb_emoji_preview, pattern=r"^adm:emojipreview$"))
    
    # --- admin: voucher ---
    app.add_handler(CallbackQueryHandler(admin.cb_voucher, pattern=r"^adm:voucher$"))
    app.add_handler(CallbackQueryHandler(admin.cb_voucher_add, pattern=r"^adm:vadd$"))
    app.add_handler(CallbackQueryHandler(admin.cb_voucher_del, pattern=r"^adm:vdel:"))
    
    # --- admin: testimonial ---
    app.add_handler(CallbackQueryHandler(admin.cb_testi, pattern=r"^adm:testi$"))
    app.add_handler(CallbackQueryHandler(admin.cb_testi_approve, pattern=r"^adm:tapp:"))
    app.add_handler(CallbackQueryHandler(admin.cb_testi_del, pattern=r"^adm:tdel:"))

    app.add_handler(MessageHandler(filters.Document.ALL, admin.handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, admin.handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin.handle_text))

    # ---------- FALLBACK ----------
    app.add_handler(CallbackQueryHandler(order.cb_noop))

    app.add_error_handler(on_error)


# ==========================================================
# MAIN
# ==========================================================
def ensure_event_loop() -> None:
    """
    Python 3.12+ / 3.14 tidak lagi membuat event loop otomatis di main thread,
    sedangkan run_polling masih memanggil asyncio.get_event_loop().
    Fungsi ini memastikan event loop selalu tersedia.
    """
    try:
        asyncio.get_event_loop()
    except (RuntimeError, DeprecationWarning):
        asyncio.set_event_loop(asyncio.new_event_loop())


def main() -> None:
    ensure_event_loop()
    print("=" * 46)
    print("        🏪  AMELBOT — AUTO ORDER STORE")
    print("=" * 46)

    if not config.BOT_TOKEN or "ISI_TOKEN" in config.BOT_TOKEN:
        print("❌ BOT_TOKEN belum diisi.")
        print("   Set environment variable BOT_TOKEN atau edit config.py")
        sys.exit(1)

    db.init_db()
    stock.ensure_files()
    log.info("Database siap : %s", config.DB_PATH)
    log.info("Admin ID      : %s", config.ADMIN_IDS)
    log.info("Stok saat ini : %s", stock.count_all())

    limiter = None
    try:
        limiter = AIORateLimiter()
    except Exception:  # noqa: BLE001  (butuh extra [rate-limiter])
        log.warning("AIORateLimiter tidak aktif, lanjut tanpa rate limiter.")

    tg_bot = premium.build_bot(config.BOT_TOKEN, rate_limiter=limiter)
    log.info(
        "Emoji premium : %s (%d emoji)",
        "AKTIF" if premium.is_enabled() else "NONAKTIF",
        len(premium.emoji_map()),
    )

    app = ApplicationBuilder().bot(tg_bot).post_init(post_init).build()
    register(app)

    log.info("Bot mulai polling...")
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except InvalidToken:
        print("\n❌ BOT_TOKEN tidak valid. Cek kembali token dari @BotFather.")
        sys.exit(1)
    except NetworkError as e:
        print(f"\n❌ Gagal terhubung ke Telegram: {e}")
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Bot dihentikan.")


if __name__ == "__main__":
    main()
