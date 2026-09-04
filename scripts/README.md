# RedMess Arsenal Scripts

Scripts untuk manage arsenal, smart skill matching, memory system, dan auto-updates.

## 📁 Scripts Overview

### Core Systems

1. **kali_arsenal_installer.py** (17.5 KB)
   - Install 200+ Kali Linux tools
   - Auto-generate SKILL.md untuk setiap tool
   - Build central README index
   - Usage: `python3 scripts/kali_arsenal_installer.py`

2. **daily_arsenal_scraper.py** (13.8 KB)
   - Scrape GitHub trending + awesome-lists
   - Monitor Exploit-DB updates
   - Auto-generate skills untuk tools baru
   - Usage: `python3 scripts/daily_arsenal_scraper.py`

3. **smart_skill_matcher.py** (13.1 KB)
   - Identify relevant skills from user request
   - Keyword mapping + scoring system
   - Max 5 skills returned (token efficient!)
   - Usage: `python3 scripts/smart_skill_matcher.py "<request>"`

4. **redmess_memory.py** (9.1 KB)
   - Persistent conversation history
   - Skill usage tracking
   - Pattern detection
   - Usage: `python3 scripts/redmess_memory.py summary`

5. **arsenal_cli.py** (6.7 KB)
   - Arsenal management CLI
   - List, search, stats, install commands
   - Usage: `arsenal list|search|stats|install|update`

6. **setup_arsenal_cron.sh** (1.2 KB)
   - Install cron job untuk daily updates
   - Schedule: 3 AM WIB daily
   - Usage: `bash scripts/setup_arsenal_cron.sh`

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Clone RedMess
git clone https://github.com/harezadmm/RedMess.git
cd RedMess

# Install arsenal (takes ~20 minutes)
python3 scripts/kali_arsenal_installer.py

# Setup daily updates
bash scripts/setup_arsenal_cron.sh

# Create CLI symlinks
ln -sf $(pwd)/scripts/arsenal_cli.py /usr/local/bin/arsenal
ln -sf $(pwd)/scripts/redmess_memory.py /usr/local/bin/redmess-memory
ln -sf $(pwd)/scripts/smart_skill_matcher.py /usr/local/bin/skill-matcher
```

### 2. Usage Examples

```bash
# List all tools
arsenal list

# Search for tool
arsenal search nmap
arsenal search "sql injection"

# Show statistics
arsenal stats

# Install specific tool
arsenal install gobuster

# Manual update (run scraper)
arsenal update

# Smart skill matching
skill-matcher "aku mau scan website cari vuln"

# Memory management
redmess-memory summary
redmess-memory frequent
redmess-memory recent
```

## 📊 System Integration

### Hermes Integration

```python
# In Hermes conversation, automatic flow:

# 1. User sends request
user_request = "aku mau test sql injection di website"

# 2. Smart matcher identifies skills
from smart_skill_matcher import identify_skills
matched = identify_skills(user_request)

# 3. Load top 2-3 skills (hemat token!)
for skill in matched[:2]:
    skill_view(name=f"red-team-arsenal/{skill['skill']}")

# 4. Record to memory
from redmess_memory import RedMessMemory
memory = RedMessMemory()
memory.add_conversation(
    user_request=user_request,
    skills_loaded=[s['skill'] for s in matched[:2]]
)

# 5. After execution, suggest next
next_skills = memory.suggest_next_skills([s['skill'] for s in matched])
```

## 🛠️ Script Details

### kali_arsenal_installer.py

**Features:**
- Install via apt-get (Kali metapackages)
- Auto-generate SKILL.md with:
  - Installation commands
  - Basic usage
  - Tool description
  - Category tagging
- Build master README.md index
- Save installation stats

**Categories Installed:**
- information-gathering (17 tools)
- vulnerability-analysis (16 tools)
- web-applications (17 tools)
- exploitation (8 tools)
- password-attacks (11 tools)
- wireless-attacks (10 tools)
- sniffing-spoofing (10 tools)
- post-exploitation (8 tools)
- forensics (9 tools)
- reverse-engineering (14 tools)
- database-assessment (9 tools)
- social-engineering (9 tools)

**Output:**
```
~/.hermes/profiles/umi3/skills/red-team-arsenal/
  ├── information-gathering/
  │   ├── nmap-SKILL.md
  │   ├── masscan-SKILL.md
  │   └── ...
  ├── web-applications/
  │   ├── sqlmap-SKILL.md
  │   ├── burpsuite-SKILL.md
  │   └── ...
  └── README.md
```

### daily_arsenal_scraper.py

**Sources:**
1. **Awesome Lists** (no rate limit):
   - enaqx/awesome-pentest
   - Hack-with-Github/Awesome-Hacking
   - carpedm20/awesome-hacking

2. **Exploit-DB:**
   - Via searchsploit --update
   - Recent exploits (last 7 days)

3. **Kali Repos:**
   - apt-cache search for new packages

4. **GitHub API** (optional with token):
   - Trending repos by security topics
   - Set GITHUB_TOKEN env var

**Output:**
- New SKILL.md files for discovered tools
- Updated README.md with "Recently Added" section
- Scrape log: `/root/.cache/arsenal_scraper/scrape_YYYYMMDD.json`

**Filters:**
- Minimum 10 GitHub stars
- Deduplicate by repo URL
- Category auto-detection via keywords
- Max 50 tools per day

### smart_skill_matcher.py

**Algorithm:**
1. **Direct Tool Name Match** (+HIGH confidence)
   - Word boundary matching
   - Regex: `\b(nmap|sqlmap|metasploit)\b`

2. **Keyword Mapping** (+MEDIUM/HIGH)
   - "scan" → information-gathering, vulnerability-analysis
   - "sql injection" → web-applications, database-assessment
   - "wifi crack" → wireless-attacks

3. **Tool Name Scoring:**
   - Tool name contains keyword: +5 points
   - Category match: +3 points
   - Keyword in description: +1 point

4. **Memory Integration** (+LOW)
   - Frequently used skills from history
   - Last 3 categories used

5. **Ranking:**
   - Sort by confidence + score
   - Return top 5 skills max

**Keyword Coverage:**
- 80+ keywords mapped
- 15+ categories covered
- 30+ direct tool names

### redmess_memory.py

**Data Structure:**
```json
{
  "version": "1.0",
  "created": "2026-09-04T...",
  "conversations": [
    {
      "timestamp": "...",
      "request": "aku mau scan...",
      "skills_loaded": ["information-gathering/nmap"],
      "outcome": "Found 22 ports"
    }
  ],
  "skill_usage": {
    "web-applications/sqlmap": 15,
    "information-gathering/nmap": 12
  },
  "user_patterns": {
    "common_keywords": ["scan", "web", "sql"],
    "preferred_categories": ["web-applications"]
  },
  "context": {
    "current_target": "192.168.1.100",
    "session_notes": [...]
  }
}
```

**Methods:**
- `add_conversation()` - Record interaction
- `get_frequent_skills()` - Most used tools
- `detect_patterns()` - Analyze user behavior
- `suggest_next_skills()` - Recommend next steps
- `set_context()` - Save session info
- `summarize()` - Generate report

**Retention:**
- Keep last 100 conversations
- Keep last 20 session notes
- No expiration on skill usage stats

### arsenal_cli.py

**Commands:**

```bash
# List all tools
arsenal list

# List by category
arsenal list web-applications
arsenal list exploitation

# Search tools
arsenal search "sql injection"
arsenal search nmap

# Show stats
arsenal stats
# Output:
#   Total Tools: 188
#   Categories: 15
#   Tools Added Today: 50

# Install tool
arsenal install gobuster

# Run scraper manually
arsenal update

# Initial setup
arsenal setup
```

**Features:**
- Color-coded output
- Category filtering
- Fuzzy search
- Integration with apt-get
- Stats from memory system

### setup_arsenal_cron.sh

**What it does:**
1. Create wrapper script with logging
2. Add cron entry: `0 20 * * *` (3 AM WIB)
3. Setup log rotation (keep 30 days)
4. Install cron package if missing

**Logs:**
```
/root/.cache/arsenal_scraper/logs/scraper_YYYYMMDD_HHMMSS.log
```

**Crontab Entry:**
```cron
0 20 * * * /root/arsenal_scraper_wrapper.sh
```

## 🔧 Configuration

### Environment Variables

```bash
# GitHub token (optional, avoid rate limits)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# Skill directory (default: ~/.hermes/profiles/umi3/skills/red-team-arsenal)
export REDMESS_SKILL_DIR="/path/to/skills"

# Memory file location
export REDMESS_MEMORY_FILE="/path/to/memory.json"
```

### Customize Keywords

Edit `smart_skill_matcher.py`:

```python
KEYWORD_MAP = {
    "custom_keyword": ["category1", "category2"],
    # Add your mappings...
}

TOOL_NAME_MAP = {
    "mytool": "category/mytool",
    # Add direct tool mappings...
}
```

### Customize Scraper Sources

Edit `daily_arsenal_scraper.py`:

```python
AWESOME_LISTS = [
    "https://raw.githubusercontent.com/user/repo/master/README.md",
    # Add more awesome lists...
]

GITHUB_TOPICS = [
    "custom-topic",
    # Add topics to monitor...
]
```

## 📈 Performance

### Token Savings
- **Before:** Load all 188 skills = ~500K tokens
- **After:** Smart matcher + load top 2 = ~15K tokens
- **Savings:** 97%

### Scraper Performance
- **Awesome Lists:** ~400 repos in 3 seconds
- **GitHub API:** ~20 repos/sec (with token)
- **Exploit-DB:** ~100 exploits/sec
- **Skill Generation:** ~1 skill/sec

### Memory Overhead
- **File Size:** ~50-100 KB for 100 conversations
- **Load Time:** <100ms
- **Pattern Detection:** <50ms for 100 conversations

## 🐛 Troubleshooting

### Cron Not Running
```bash
# Check cron service
service cron status

# View logs
tail -f /root/.cache/arsenal_scraper/logs/scraper_*.log

# Test manually
bash /root/arsenal_scraper_wrapper.sh
```

### GitHub Rate Limit
```bash
# Set token
export GITHUB_TOKEN="your_token"
echo 'export GITHUB_TOKEN="..."' >> ~/.bashrc

# Verify
python3 scripts/daily_arsenal_scraper.py
```

### Skills Not Found
```bash
# Rebuild index
rm ~/.cache/arsenal_scraper/skill_index.json
python3 scripts/smart_skill_matcher.py "test query"

# Check skill directory
ls ~/.hermes/profiles/umi3/skills/red-team-arsenal/
```

### Memory Reset
```bash
# Clear all memory
redmess-memory reset

# Or manually
rm ~/.hermes/profiles/umi3/redmess_memory.json
```

## 📚 Documentation

- **Main README:** `/tmp/RedMess/README.md`
- **Arsenal Docs:** `/root/ARSENAL_DOCUMENTATION.md`
- **Smart Systems:** `/tmp/RedMess/SMART_SYSTEMS.md`
- **Skills Index:** `~/.hermes/profiles/umi3/skills/red-team-arsenal/README.md`

---

**Last Updated:** 2026-09-04 03:27 WIB  
**Author:** harezadmm  
**License:** MIT
