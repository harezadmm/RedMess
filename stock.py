# -*- coding: utf-8 -*-
"""
stock.py
Manajemen file stok nomor (folder /stok).
Semua operasi baca/tulis dilindungi Lock supaya aman dari race condition.
"""

import os
import re
import threading
from datetime import datetime

import catalog
import config

_LOCK = threading.Lock()

# Karakter yang dianggap valid untuk sebuah "nomor"
_CLEAN_RE = re.compile(r"[^\d+]")


def stock_path(code: str) -> str:
    return os.path.join(config.STOK_DIR, catalog.filename(code))


def ensure_files() -> None:
    """Pastikan semua file stok ada."""
    for code in catalog.codes():
        path = stock_path(code)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("")


def _read_lines(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [ln.strip() for ln in f if ln.strip()]


def _write_lines(path: str, lines: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")


def normalize(raw: str) -> str:
    """Bersihkan satu baris nomor."""
    value = _CLEAN_RE.sub("", raw.strip())
    return value


def count(code: str) -> int:
    with _LOCK:
        return len(_read_lines(stock_path(code)))


def count_all(active_only: bool = False) -> dict:
    return {code: count(code) for code in catalog.codes(active_only)}


def total_all() -> int:
    return sum(count_all().values())


def add_from_text(code: str, text: str) -> dict:
    """
    Tambah stok dari teks mentah (isi file txt yang diupload admin).
    Return: {"added": n, "duplicate": n, "invalid": n, "total": n}
    """
    with _LOCK:
        path = stock_path(code)
        current = _read_lines(path)
        existing = set(current)

        added, duplicate, invalid = 0, 0, 0
        for raw in text.replace("\r", "\n").split("\n"):
            raw = raw.strip()
            if not raw:
                continue
            num = normalize(raw)
            if len(num) < 6:
                invalid += 1
                continue
            if num in existing:
                duplicate += 1
                continue
            existing.add(num)
            current.append(num)
            added += 1

        _write_lines(path, current)
        return {
            "added": added,
            "duplicate": duplicate,
            "invalid": invalid,
            "total": len(current),
        }


def take(code: str, jumlah: int) -> list:
    """
    Ambil `jumlah` nomor paling atas dan HAPUS dari file stok.
    Return list kosong bila stok kurang.
    """
    jumlah = int(jumlah)
    with _LOCK:
        path = stock_path(code)
        lines = _read_lines(path)
        if len(lines) < jumlah:
            return []
        taken = lines[:jumlah]
        sisa = lines[jumlah:]
        _write_lines(path, sisa)
        return taken


def give_back(code: str, numbers: list) -> None:
    """Kembalikan nomor ke stok (dipakai bila pengiriman gagal)."""
    if not numbers:
        return
    with _LOCK:
        path = stock_path(code)
        lines = _read_lines(path)
        _write_lines(path, list(numbers) + lines)


def clear(code: str) -> int:
    """Kosongkan stok satu negara. Return jumlah yang dihapus."""
    with _LOCK:
        path = stock_path(code)
        n = len(_read_lines(path))
        _write_lines(path, [])
        return n


def delete_top(code: str, jumlah: int) -> int:
    """Hapus sejumlah nomor teratas tanpa dikirim."""
    with _LOCK:
        path = stock_path(code)
        lines = _read_lines(path)
        jumlah = min(int(jumlah), len(lines))
        _write_lines(path, lines[jumlah:])
        return jumlah


def build_delivery_file(invoice: str, code: str, numbers: list) -> str:
    """Buat file txt hasil order, return path filenya."""
    name = catalog.name(code)
    filename = f"{invoice}_{name}_{len(numbers)}.txt"
    path = os.path.join(config.ORDER_DIR, filename)
    header = [
        f"# {config.STORE_NAME}",
        f"# Invoice : {invoice}",
        f"# Produk  : {len(numbers)} Nomor {name}",
        f"# Tanggal : {config.sekarang().strftime('%d-%m-%Y %H:%M:%S')}",
        "#" + "-" * 40,
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        f.write("\n".join(numbers) + "\n")
    return path


def delete_file(code: str) -> None:
    """Hapus file stok saat negara dibuang."""
    try:
        os.remove(stock_path(code))
    except OSError:
        pass
