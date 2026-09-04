# AmelBot — Telegram Auto Order Bot

Bot store otomatis untuk jual file nomor per negara dan panel hosting.
Pembayaran QRIS manual, tanpa API payment gateway.

Semua isi toko diatur dari dalam Telegram: negara, harga, paket jumlah,
produk panel, tombol menu, sampai nama toko. Tidak perlu edit kode.

---

## Yang baru di versi ini

| Fitur | Keterangan |
|---|---|
| Tombol berwarna | Biru (primary), hijau (success), merah (danger) — fitur Bot API 9.4 |
| Ikon emoji premium di tombol | `icon_custom_emoji_id`, aktif karena owner bot Premium |
| Negara bebas | Tambah negara sebanyak apa pun, otomatis dapat file stok & harga |
| Tombol bisa disembunyikan | Matikan menu yang tidak dipakai, nyalakan lagi kapan saja |
| Label & ikon bisa diganti | Ubah nama dan emoji tiap tombol dari panel |
| Produk panel dinamis | Tambah, ubah harga, sembunyikan, hapus paket panel |
| Paket jumlah bebas | Bukan cuma 200/500/1000 — atur sendiri, maksimal 8 paket |
| Isi stok berturut-turut | Mode isi stok tetap aktif, kirim file berkali-kali tanpa buka menu lagi |
| Tampilan bersih | Tanpa hiasan berlebihan, data sejajar dalam blockquote |

---

## Struktur file

```
AmelBot/
├── bot.py               entry point, pendaftaran handler
├── config.py            token, admin, data awal (dipakai sekali saat DB kosong)
├── database.py          SQLite: users, orders, prices, countries, menus, panels, settings
├── catalog.py           katalog negara, paket, menu, produk panel
├── ui.py                komponen tampilan: tombol berwarna, ikon, format teks
├── order.py             alur pembeli
├── admin.py             panel admin
├── stock.py             operasi file stok (aman untuk akses bersamaan)
├── qris.py              gambar QRIS & teks invoice
├── premium.py           emoji premium di teks dan ikon tombol
├── premium_emoji.json   peta emoji → custom_emoji_id
├── requirements.txt
├── stok/                togo.txt, laos.txt, mali.txt, ...
├── orders/              file hasil order
├── qris.jpg             gambar QRIS
└── database.db          dibuat otomatis
```

---

## Cara menjalankan di Pterodactyl

1. Upload seluruh isi folder ini.
2. Startup command:
   ```
   pip install -r requirements.txt && python bot.py
   ```
3. Isi variabel lingkungan:

| Variabel | Wajib | Contoh |
|---|---|---|
| `BOT_TOKEN` | ya | `123456:ABC-DEF...` |
| `ADMIN_IDS` | ya | `7794103299` (pisah koma bila banyak) |
| `STORE_NAME` | tidak | `AMEL STORE` |
| `OWNER_USERNAME` | tidak | `@AmelOwner` |
| `OWNER_NAME` | tidak | `Amel` |

Butuh Python 3.10 atau lebih baru.

---

## Perintah

| Perintah | Untuk | Fungsi |
|---|---|---|
| `/start`, `/menu` | semua | Menu utama |
| `/id` | semua | Lihat user ID sendiri |
| `/help` | semua | Bantuan |
| `/admin` | admin | Panel admin |
| `/cekstok` | admin | Laporan stok |
| `/tambahstok` | admin | Pilih negara lalu isi stok |
| `/batal` | admin | Keluar dari mode input |

---

## Panel admin

```
Order Pending      verifikasi pembayaran, terima / tolak
Kelola Negara      tambah, ubah nama & bendera, sembunyikan, hapus
Kelola Stok        laporan stok semua negara
Harga & Paket      harga per negara, paket jumlah, tarif per nomor
Produk Panel       tambah, ubah, sembunyikan, hapus paket panel
Kelola Menu        sembunyikan tombol, ganti label & ikonnya
Pengaturan Toko    nama toko, owner, catatan pembayaran
QRIS               ganti gambar QRIS
Emoji Premium      aktifkan, tambah emoji, lihat contoh
Statistik          omzet, order, produk terlaris
Broadcast          kirim pesan ke semua member
```

### Menambah negara

Panel Admin → Kelola Negara → Tambah Negara, lalu kirim:

```
🇳🇬 Nigeria
🇰🇪 Kenya
Vietnam
```

Beberapa negara sekaligus boleh, satu per baris. Bendera opsional.
Setiap negara baru otomatis dapat file stok dan harga awal
(jumlah × tarif per nomor).

### Mengisi stok

Kelola Negara → pilih negara → Isi Stok. Kirim file `.txt` atau tempel
nomornya. Mode tetap aktif sampai Anda tekan Selesai, jadi bisa kirim
berkali-kali. Nomor duplikat otomatis dibuang.

### Menyembunyikan tombol

Kelola Menu → tekan tombol yang ingin ditutup. Tanda `●` berarti tampil
ke pembeli, `○` berarti disembunyikan. Tekan Ubah untuk mengganti nama
dan ikonnya, misalnya `🛍 Belanja Nomor`. Bila hanya satu kategori order
yang aktif, bot langsung melompat ke sana tanpa menu perantara.

---

## Alur order

```
Pembeli  /start → Order → File Nomor → pilih negara → pilih paket
         → invoice + QRIS → Saya Sudah Bayar
Admin    notifikasi → Terima
Bot      ambil nomor dari stok → kirim file .txt ke pembeli → status SUCCESS
```

Bila stok kurang saat disetujui, order tidak diproses dan nomor
dikembalikan ke stok.

---

## Catatan teknis

- Tombol berwarna dan ikon emoji premium memakai
  [Bot API 9.4](https://core.telegram.org/bots/api#february-9-2026)
  (`style`, `icon_custom_emoji_id`).
- Emoji premium di teks memakai `<tg-emoji>`, diizinkan karena
  [pemilik bot berlangganan Telegram Premium](https://core.telegram.org/bots/api#html-style).
- Bila perangkat pembeli tidak mendukung, Telegram otomatis memakai gaya
  bawaan sehingga tombol tetap tampil normal.
- Teks tombol biasa tidak bisa berisi emoji premium; itulah sebabnya
  emoji dipasang sebagai ikon lewat `icon_custom_emoji_id`.
- Stok disimpan sebagai file teks dengan lock agar aman saat banyak
  order bersamaan.
