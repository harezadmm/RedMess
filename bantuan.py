# -*- coding: utf-8 -*-
"""
bantuan.py
Penjelasan singkat setiap fitur, KHUSUS ADMIN.

Teks di sini hanya dipakai di layar panel admin, tidak pernah
tampil ke pembeli. Ditampilkan sebagai kutipan yang bisa dilipat
supaya pesan tetap ringkas.
"""

import ui

T = {
    # ---------- panel utama ----------
    "panel": (
        "Semua isi toko diatur dari sini, tanpa mengubah kode.\n"
        "Kelola Negara untuk stok jualan, Harga & Paket untuk tarif, "
        "Kelola Menu untuk memilih tombol mana yang tampil ke pembeli.\n"
        "Angka pada Order Pending adalah pembayaran yang menunggu Anda cek."
    ),

    # ---------- order ----------
    "pending": (
        "Daftar pembeli yang sudah menekan Saya Sudah Bayar.\n"
        "Buka satu order, cocokkan nominal dengan mutasi QRIS Anda, "
        "lalu Terima atau Tolak.\n"
        "Begitu diterima, bot langsung memotong stok dan mengirim "
        "file nomornya ke pembeli."
    ),
    "order": (
        "Periksa nominal dan waktu bayar sebelum memutuskan.\n"
        "Terima : stok dipotong, file dikirim otomatis, status jadi berhasil.\n"
        "Tolak  : stok tidak berkurang, pembeli diberi tahu.\n"
        "Bila stok kurang saat diterima, order dibatalkan dan nomor "
        "dikembalikan utuh."
    ),

    # ---------- negara ----------
    "negara": (
        "Daftar negara yang Anda jual. Jumlahnya bebas.\n"
        "● berarti tampil ke pembeli, ○ berarti disembunyikan sementara "
        "tanpa kehilangan stok maupun harga.\n"
        "Tekan salah satu negara untuk isi stok, atur harga, ubah nama, "
        "atau hapus."
    ),
    "negara_add": (
        "Negara baru otomatis dapat file stok sendiri dan harga awal "
        "dari tarif per nomor.\n"
        "Bendera menentukan ikon premium pada tombolnya, jadi sebaiknya "
        "diisi.\n"
        "Nama yang sudah ada akan dilewati, tidak menimpa data lama."
    ),
    "negara_detail": (
        "Isi Stok bisa dilakukan berulang tanpa membuka menu lagi.\n"
        "Sembunyikan memakai negara ini keluar dari daftar pembeli, "
        "data tetap aman.\n"
        "Hapus Negara menghilangkan negara beserta file stoknya secara "
        "permanen."
    ),
    "negara_rename": (
        "Nama dan bendera boleh diganti kapan saja.\n"
        "Kode dan file stok tidak ikut berubah, jadi stok yang sudah "
        "masuk tetap utuh."
    ),
    "negara_del": (
        "Penghapusan tidak bisa dibatalkan.\n"
        "File stok, harga, dan negara akan hilang. Riwayat order lama "
        "tetap tersimpan.\n"
        "Bila hanya ingin menghentikan penjualan sementara, pakai "
        "Sembunyikan."
    ),

    # ---------- stok ----------
    "stock": (
        "Ringkasan sisa nomor tiap negara.\n"
        "Pembeli tidak bisa memesan negara yang stoknya kurang dari "
        "paket yang dipilih, jadi tidak akan ada order yang gagal kirim."
    ),
    "add_stock": (
        "Kirim file .txt atau tempel nomornya langsung, satu nomor per baris.\n"
        "Nomor kembar otomatis dibuang, termasuk yang sudah ada di stok.\n"
        "Mode ini tetap terbuka sampai Anda tekan Selesai, jadi bisa "
        "kirim berkali-kali."
    ),
    "del_stock": (
        "Menghapus nomor dari baris paling atas, yaitu yang paling lama.\n"
        "Berguna untuk membuang nomor mati. Pastikan jumlahnya benar "
        "karena tidak bisa dikembalikan."
    ),

    # ---------- harga ----------
    "price": (
        "Harga dihitung dari tarif per nomor, lalu boleh ditimpa "
        "per negara.\n"
        "Ubah tarif hanya memengaruhi negara yang harganya belum pernah "
        "Anda atur sendiri.\n"
        "Paket jumlah menentukan pilihan yang dilihat pembeli."
    ),
    "price_set": (
        "Kirim harga sesuai urutan paket, dipisah spasi.\n"
        "Semua paket harus diisi. Harga khusus ini menang atas tarif "
        "per nomor."
    ),
    "qty": (
        "Paket jumlah berlaku untuk semua negara, maksimal delapan pilihan.\n"
        "Paket lama yang tetap dipertahankan tidak kehilangan harga "
        "khususnya.\n"
        "Paket baru langsung dihargai jumlah dikali tarif per nomor."
    ),
    "rate": (
        "Tarif ini dipakai menghitung harga awal negara baru dan paket "
        "baru.\n"
        "Negara yang harganya sudah Anda atur manual tidak ikut berubah."
    ),

    # ---------- menu ----------
    "menu": (
        "Di sini Anda memilih tombol mana yang dilihat pembeli.\n"
        "Tekan tombolnya untuk menyembunyikan atau menampilkan kembali, "
        "tekan Ubah untuk mengganti nama dan ikonnya.\n"
        "Menu yang disembunyikan tidak hilang, hanya tidak tampil, dan "
        "bisa dinyalakan lagi kapan saja."
    ),
    "menu_set": (
        "Kirim ikon lalu nama tombol dalam satu baris, contoh 🛍 Belanja.\n"
        "Bila Anda memakai emoji premium dari keyboard Telegram, bot "
        "menyimpan emoji itu dan memasangnya sebagai ikon tombol.\n"
        "Kirim nama saja bila ikonnya tidak ingin diganti."
    ),

    # ---------- produk panel ----------
    "panelprod": (
        "Daftar paket panel hosting yang dijual.\n"
        "● dijual, ○ disembunyikan. Menyembunyikan lebih aman daripada "
        "menghapus bila hanya kehabisan stok sementara."
    ),
    "panel_detail": (
        "Ubah nama, spesifikasi, dan harga kapan saja.\n"
        "Perubahan langsung terlihat pembeli, tapi tidak memengaruhi "
        "order yang sudah masuk."
    ),
    "panel_add": (
        "Format: Nama | Spesifikasi | Harga.\n"
        "Spesifikasi ditampilkan apa adanya ke pembeli, jadi tulis "
        "ringkas.\n"
        "Beberapa paket sekaligus boleh, satu per baris."
    ),
    "panel_del": (
        "Paket akan hilang dari daftar jual secara permanen.\n"
        "Riwayat order yang memakai paket ini tetap tersimpan."
    ),

    # ---------- pengaturan ----------
    "setting": (
        "Nama toko dan owner dipakai di menu utama, invoice, dan "
        "halaman bantuan.\n"
        "Catatan pembayaran tampil di bawah gambar QRIS, cocok untuk "
        "pesan seperti nominal harus sama persis."
    ),
    "setting_set": (
        "Kirim teks penggantinya. Ketik hapus untuk mengosongkan.\n"
        "Perubahan langsung berlaku tanpa perlu restart bot."
    ),
    "qris": (
        "Kirim foto QRIS Anda. Gambar lama otomatis dicadangkan.\n"
        "Pakai gambar yang tajam dan tidak terpotong agar mudah dipindai.\n"
        "Bila belum ada QRIS, pembeli tetap bisa memesan tapi diminta "
        "menghubungi owner."
    ),

    # ---------- lain-lain ----------
    "stats": (
        "Omzet hanya menghitung order berstatus berhasil.\n"
        "Produk terlaris membantu menentukan stok mana yang perlu "
        "diisi lebih dulu."
    ),
    "broadcast": (
        "Pesan dikirim ke semua member yang pernah menekan /start.\n"
        "Pengiriman diberi jeda agar tidak kena batas Telegram, jadi "
        "harap tunggu sampai laporan selesai muncul.\n"
        "Member yang memblokir bot dilewati otomatis."
    ),
    "emoji": (
        "Ikon tombol dan emoji pada pesan memakai set standar Telegram "
        "yang bergerak halus, bentuknya sama seperti emoji biasa.\n"
        "Pengguna tanpa Premium tetap melihat emoji biasa, jadi tampilan "
        "aman untuk semua orang.\n"
        "Pelajari Emoji dipakai bila Anda ingin menambah emoji sendiri "
        "di luar set bawaan."
    ),
}


def q(key: str) -> str:
    """Kutipan penjelasan untuk layar admin. Kosong bila kunci tak dikenal."""
    teks = T.get(key)
    if not teks:
        return ""
    return ui.panduan(teks)
