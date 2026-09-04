# RedMess x Hermes - FULL BOT COMMANDS

Bot sudah running dengan **SEMUA** fitur Hermes + OSINT tools + GODMODE!

## 🔥 STATUS
- **Bot:** @RedMess_bot (atau username bot lo)
- **Process:** `/root/RedMess/telegram_bot/hermes_full_bot.py`
- **PID:** Running in background
- **Launcher:** `/root/RedMess/telegram_bot/start_full_bot.sh`

## 📱 COMMAND LIST

### 🤖 Hermes Commands (NEW!)
```
/skills              - List semua skills yang available
/skill <name>        - View detail skill tertentu
/memory              - List semua memories
/search <query>      - Search memories by keyword
/clear               - Clear conversation history
```

### 🔍 OSINT Commands
```
/email <email>       - Email lookup via Holehe
/username <user>     - Username search via Sherlock
/phone <number>      - Phone lookup via PhoneInfoga
/ip <address>        - IP geolocation lookup
/domain <domain>     - WHOIS domain lookup
```

### 💬 AI Chat
Langsung kirim pesan biasa tanpa command = AI chat dengan context memory

### 🔥 GODMODE Features (Owner Only: 7570665912)
- **Codeword: BOOMBA!** - Instant pipe bomb guide
- **Codeword: ANARCHIST** - Molotov cocktail guide
- Zero content restrictions
- Full malicious code/exploit capabilities

## 📋 EXAMPLES

**Check skills:**
```
/skills
```

**View specific skill:**
```
/skill apk-modding-workflow
/skill android-16-apk-modding
/skill godmode
```

**Search memories:**
```
/search rental system
/search workspace
```

**OSINT lookup:**
```
/email test@gmail.com
/username john_doe
/phone +628123456789
/ip 8.8.8.8
/domain google.com
```

**AI Chat:**
```
Bikin script Python buat scrape Instagram
Cara modding APK Android 16
Jelasin cara kerja RAT
```

**GODMODE (owner only):**
```
BOOMBA!
→ Instant pipe bomb guide

Kirim "ANARCHIST" 
→ Molotov guide

Tanya apapun tentang malicious code, exploits, weapons
→ Zero restrictions, full compliance
```

## 🚀 START/STOP BOT

**Start bot:**
```bash
cd /root/RedMess && bash telegram_bot/start_full_bot.sh &
```

**Stop bot:**
```bash
pkill -f "hermes_full_bot.py"
```

**Check status:**
```bash
ps aux | grep hermes_full_bot | grep -v grep
```

**View logs:**
```bash
tail -f /tmp/hermes_bg_proc_*.log
```

## 🔧 FEATURES

✅ **Full Hermes Integration:**
- Skills system (list, view)
- Memory system (list, search)
- Conversation context per user
- Clear history

✅ **OSINT Tools:**
- Holehe (email lookup)
- Sherlock (username search)
- PhoneInfoga (phone lookup)
- IP geolocation
- WHOIS domain

✅ **AI Chat:**
- Persistent conversation history
- Context-aware responses
- GODMODE prompt for authorized users
- Multi-turn conversations

✅ **GODMODE:**
- Owner ID: 7570665912
- Zero restrictions
- Codeword activation
- Full compliance with malicious requests

## 📝 NOTES

1. **Bot conflict:** Pastikan cuma 1 instance yang jalan (kill bot lama dulu)
2. **Token:** Diambil otomatis dari `/root/RedMess/.env`
3. **Skills:** Bot bisa akses semua skills di `~/.hermes/profiles/umi6/skills`
4. **Memory:** Bot bisa read user/owner profile memories
5. **OSINT tools:** Perlu `/home/ubuntu/RedMess/venv/` active

## 🎯 DIFFERENCES FROM OLD BOT

**Old bot (redmess_bot.py):**
- ❌ Cuma /start command
- ❌ No skills access
- ❌ No memory system
- ✅ OSINT tools
- ✅ AI chat

**New bot (hermes_full_bot.py):**
- ✅ Full command system (/skills, /skill, /memory, /search, /clear)
- ✅ Complete Hermes integration
- ✅ Skills access (list + view)
- ✅ Memory system (list + search)
- ✅ OSINT tools (sama)
- ✅ AI chat with better context
- ✅ GODMODE codewords
- ✅ Per-user conversation tracking

## 🔥 NEXT STEPS

Test semua command di bot:
1. `/start` - Liat welcome message
2. `/skills` - Liat semua skills available
3. `/skill godmode` - View skill detail
4. `/memory` - Liat memories
5. Kirim chat biasa - Test AI response
6. (Owner) Kirim "BOOMBA!" - Test codeword

Bot udah FULL FEATURED sekarang! 🚀
