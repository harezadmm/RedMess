# @umi_agbot - Full System Documentation

## Overview
Complete Telegram bot dengan:
- AmelBot order system (file + panel)
- Workspace manager per user_id
- Rental system dengan pause/resume
- GODMODE BRUTAL integration
- Auto upload file >50MB ke gofile.io

## File Structure

```
umi_agbot/
├── bot.py                  # Main bot entry
├── config.py               # Bot config
├── database.py             # Database manager
├── umiagent.db            # SQLite database (rentals table)
│
├── workspace_manager.py    # Dynamic workspace per user_id
├── auto_file_upload.py     # Auto upload >50MB files
├── rental_pause.py         # Pause/resume rental
├── godmode_brutal.py       # GODMODE BRUTAL system
│
├── admin.py               # Admin commands
├── order.py               # Order processing
├── stock.py               # Stock management
├── premium.py             # Premium features
├── catalog.py             # Product catalog
├── ui.py                  # UI helpers
├── bantuan.py             # Help system
├── levels.py              # User levels
├── referral.py            # Referral system
├── voucher.py             # Voucher system
└── qris.py                # QRIS payment
```

## Database Schema

### rentals table
```sql
CREATE TABLE rentals (
    user_id INTEGER PRIMARY KEY,
    end_time INTEGER,
    duration_minutes INTEGER,
    price INTEGER,
    activated_at INTEGER,
    paused_at INTEGER DEFAULT 0
);
```

## Workspace System

Path: `D:/hermes/workspace/{user_id}/`

```python
from workspace_manager import get_user_workspace, get_workspace_stats

# Get user workspace
workspace = get_user_workspace(7570665912)

# Get stats
stats = get_workspace_stats(7570665912)
# Returns: {path, file_count, total_size_mb, files}
```

## Rental System

```python
from godmode_brutal import has_godmode_access, add_rental, get_rental_status
from rental_pause import pause_rental, resume_rental

# Check access
if has_godmode_access(user_id):
    # User has GODMODE BRUTAL

# Add rental (1 jam = 8K)
add_rental(user_id=8773823648, duration_minutes=60, price=8000)

# Pause rental
pause_rental(8773823648)

# Resume rental
resume_rental(8773823648)

# Get status
status = get_rental_status(8773823648)
```

## GODMODE BRUTAL

Owner: `7570665912` (permanent GODMODE)

Active rentals: auto-enable GODMODE BRUTAL

```python
from godmode_brutal import has_godmode_access, get_godmode_prompt

if has_godmode_access(user_id):
    prompt = get_godmode_prompt()
    # Zero content restrictions
```

## Auto File Upload

Files >50MB auto-upload ke gofile.io:

```python
from auto_file_upload import auto_upload_large_files
from workspace_manager import get_user_workspace

workspace = get_user_workspace(user_id)
results = await auto_upload_large_files(workspace)

# Returns: [{filename, download_url, size_mb}]
```

## Running

```bash
cd /root/umi_agbot
python bot.py
```

## Environment Variables

```bash
export BOT_TOKEN="your_bot_token"
export ADMIN_IDS="7570665912"
```

## Rental Pricing

- 1 jam: Rp 8.000
- 1 hari: Rp 50.000
- 1 minggu: Rp 200.000
- 1 bulan: Rp 560.000

## Active Rentals (as of Aug 23 2026)

- `6726919171`: 24h (until Aug 23 13:17 WIB)
- `8924909120`: 1d+1m (until Aug 23 23:27 WIB)
- `8773823648`: 1h (Aug 23 11:25-12:25 WIB, Rp 8K)

All have GODMODE BRUTAL (no refuse, anti-inject, no UU/UUD restrictions).
