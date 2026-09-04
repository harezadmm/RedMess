#!/usr/bin/env python3
"""
Enhanced Daily Arsenal Scraper with GitHub API Token Support
Avoids rate limits and scrapes multiple sources
"""
import subprocess
import json
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import time

SKILL_DIR = Path.home() / ".hermes/profiles/umi3/skills/red-team-arsenal"
CACHE_DIR = Path.home() / ".cache/arsenal_scraper"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# GitHub API token (optional, set via env var to avoid rate limits)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Alternative sources when GitHub rate limits
ALTERNATIVE_SOURCES = [
    "https://github.com/topics/pentesting",
    "https://github.com/topics/security-tools",
    "https://github.com/topics/hacking-tools",
]

# Awesome lists to scrape
AWESOME_LISTS = [
    "https://raw.githubusercontent.com/enaqx/awesome-pentest/master/README.md",
    "https://raw.githubusercontent.com/Hack-with-Github/Awesome-Hacking/master/README.md",
    "https://raw.githubusercontent.com/carpedm20/awesome-hacking/master/README.md",
]

def fetch_awesome_list(url):
    """Fetch and parse awesome-list markdown"""
    print(f"[*] Fetching awesome list: {url.split('/')[-2]}")
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Hermes-Arsenal-Scraper/2.0")
        
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            
        # Extract GitHub repo links
        pattern = r'\[([^\]]+)\]\((https://github\.com/[^)]+)\)'
        matches = re.findall(pattern, content)
        
        repos = []
        for name, repo_url in matches:
            # Skip non-repo links
            if "/topics/" in repo_url or "/search" in repo_url:
                continue
            
            # Extract owner/repo
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2:
                repos.append({
                    "name": parts[1],
                    "description": name,
                    "html_url": repo_url,
                    "stargazers_count": 0,  # Will be unknown
                    "language": "Unknown",
                    "topics": []
                })
        
        print(f"[+] Found {len(repos)} repos from awesome list")
        return repos
        
    except Exception as e:
        print(f"[-] Failed to fetch awesome list: {e}")
        return []

def fetch_github_api_with_auth(url):
    """Fetch from GitHub API with optional auth"""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Hermes-Arsenal-Scraper/2.0")
    
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"[-] Rate limit exceeded (use GITHUB_TOKEN env var)")
        else:
            print(f"[-] HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"[-] Error: {e}")
        return None

def fetch_exploit_db_recent():
    """Scrape recent exploits from Exploit-DB"""
    print("[*] Checking Exploit-DB recent additions...")
    
    try:
        # Use searchsploit if available
        result = subprocess.run(
            ["searchsploit", "--update"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("[+] Exploit-DB database updated")
            
            # Get recent exploits (last 7 days)
            result = subprocess.run(
                ["searchsploit", "--json", "remote"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                exploits = data.get("RESULTS_EXPLOIT", [])
                recent = [e for e in exploits if e.get("Date", "2000-01-01") > (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]
                print(f"[+] Found {len(recent)} recent exploits")
                return recent
        
    except FileNotFoundError:
        print("[-] searchsploit not found, install exploit-db package")
    except Exception as e:
        print(f"[-] Failed to fetch Exploit-DB: {e}")
    
    return []

def fetch_kali_updates():
    """Check Kali package repository for new tools"""
    print("[*] Checking Kali repository updates...")
    
    try:
        # Update package cache
        subprocess.run(["apt-get", "update"], capture_output=True, timeout=60)
        
        # Search for new security tools
        result = subprocess.run(
            ["apt-cache", "search", "pentesting", "security", "exploit"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            tools = []
            for line in lines:
                if " - " in line:
                    tool_name, description = line.split(" - ", 1)
                    tools.append({
                        "name": tool_name.strip(),
                        "description": description.strip(),
                        "source": "kali-repo"
                    })
            
            print(f"[+] Found {len(tools)} tools in Kali repos")
            return tools
        
    except Exception as e:
        print(f"[-] Failed to check Kali updates: {e}")
    
    return []

def parse_tool_from_repo(repo):
    """Extract tool info from GitHub repo"""
    name = repo["name"].lower().replace("-", "_")
    description = repo.get("description", "") or f"Security tool: {name}"
    stars = repo.get("stargazers_count", 0)
    url = repo["html_url"]
    language = repo.get("language", "Unknown")
    topics = repo.get("topics", [])
    
    # Determine category from topics and name
    category = "miscellaneous"
    keywords = name.lower() + " " + description.lower() + " " + " ".join(topics)
    
    if any(k in keywords for k in ["recon", "osint", "enum", "scan", "discover"]):
        category = "information-gathering"
    elif any(k in keywords for k in ["vuln", "scanner", "audit", "finder"]):
        category = "vulnerability-analysis"
    elif any(k in keywords for k in ["exploit", "rce", "shell", "payload"]):
        category = "exploitation"
    elif any(k in keywords for k in ["post", "lateral", "privesc", "persistence"]):
        category = "post-exploitation"
    elif any(k in keywords for k in ["web", "webapp", "xss", "sqli", "injection"]):
        category = "web-applications"
    elif any(k in keywords for k in ["password", "crack", "brute", "hash"]):
        category = "password-attacks"
    elif any(k in keywords for k in ["wireless", "wifi", "bluetooth", "802.11"]):
        category = "wireless-attacks"
    elif any(k in keywords for k in ["forensic", "memory", "disk", "carve"]):
        category = "forensics"
    elif any(k in keywords for k in ["reverse", "disassem", "decompil", "debug"]):
        category = "reverse-engineering"
    elif any(k in keywords for k in ["cloud", "aws", "azure", "gcp", "s3"]):
        category = "cloud-security"
    elif any(k in keywords for k in ["api", "rest", "graphql", "endpoint"]):
        category = "api-security"
    elif any(k in keywords for k in ["container", "docker", "kubernetes", "k8s"]):
        category = "container-security"
    
    return {
        "name": name,
        "description": description,
        "category": category,
        "stars": stars,
        "url": url,
        "language": language,
        "topics": topics,
        "source": "github",
        "discovered": datetime.now().isoformat()
    }

def check_tool_exists(tool_name, category):
    """Check if skill already exists"""
    skill_path = SKILL_DIR / category / f"{tool_name}-SKILL.md"
    return skill_path.exists()

def generate_new_tool_skill(tool):
    """Generate SKILL.md for newly discovered tool"""
    name = tool["name"]
    desc = tool["description"] or f"Security tool: {name}"
    category = tool["category"]
    url = tool.get("url", "")
    language = tool.get("language", "Unknown")
    stars = tool.get("stars", 0)
    
    short_desc = desc[:57] + "..." if len(desc) > 57 else desc
    
    install_section = f"""## Installation

```bash
# Clone repository
git clone {url} /opt/{name}
cd /opt/{name}

# Follow installation instructions in the repo
cat README.md | grep -A 20 -i "install"
```""" if url else """## Installation

```bash
# Check Kali/Debian repositories
apt-cache search {name}
apt-get install -y {name}
```"""
    
    skill_content = f"""---
name: {name}
description: {short_desc}
category: red-team-arsenal/{category}
tags: [pentesting, {category.replace("-", " ")}, auto-discovered, {language.lower() if language else "tool"}]
author: daily-scraper
created: {datetime.now().strftime("%Y-%m-%d")}
---

# {name.upper()}

**Category:** {category.replace("-", " ").title()}  
**Description:** {desc}  
**Language:** {language}  
{"**GitHub Stars:** " + str(stars) if stars > 0 else ""}
{"**Repository:** " + url if url else ""}

## Discovery Info

- **Source:** {tool.get('source', 'unknown')}
- **Discovered:** {datetime.now().strftime("%Y-%m-%d")}
- **Auto-generated:** Daily arsenal scraper

{install_section}

## Usage

*Check official documentation for usage patterns*

## Resources

{"- **GitHub:** " + url if url else ""}
- **Category:** {category.replace("-", " ").title()}

## Notes

- Newly discovered tool
- Requires manual verification and testing
- Will be enriched after first use
"""
    
    skill_path = SKILL_DIR / category / f"{name}-SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(skill_content)
    print(f"[+] Generated skill: {name} ({category})")
    return skill_path

def update_arsenal_readme(new_tools):
    """Update master README with new tools"""
    readme_path = SKILL_DIR / "README.md"
    
    if not readme_path.exists():
        return
    
    content = readme_path.read_text()
    
    if new_tools:
        today = datetime.now().strftime("%Y-%m-%d")
        new_section = f"\n## Recently Added ({today})\n\n"
        
        for tool in new_tools[:20]:  # Limit to 20 latest
            url = tool.get('url', '')
            name_display = f"[{tool['name']}]({url})" if url else f"**{tool['name']}**"
            new_section += f"- {name_display} — {tool['description'][:80]}{'...' if len(tool['description']) > 80 else ''}\n"
        
        lines = content.split("\n")
        insert_pos = 3
        lines.insert(insert_pos, new_section)
        content = "\n".join(lines)
    
    content = re.sub(
        r"\*\*Last updated:\*\* \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
        f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        content
    )
    
    readme_path.write_text(content)

def main():
    print("[*] Enhanced Arsenal Scraper - Starting...")
    print(f"[*] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_repos = []
    new_tools = []
    
    # Method 1: Fetch from awesome lists (no rate limit)
    for url in AWESOME_LISTS:
        repos = fetch_awesome_list(url)
        all_repos.extend(repos)
        time.sleep(1)  # Be nice
    
    # Method 2: Check Exploit-DB updates
    exploits = fetch_exploit_db_recent()
    
    # Method 3: Check Kali repo updates
    kali_tools = fetch_kali_updates()
    
    # Deduplicate
    seen = set()
    unique_repos = []
    for repo in all_repos:
        key = repo["html_url"] if "html_url" in repo else repo["name"]
        if key not in seen:
            seen.add(key)
            unique_repos.append(repo)
    
    print(f"\n[*] Total unique repos: {len(unique_repos)}")
    print(f"[*] Recent exploits: {len(exploits)}")
    print(f"[*] Kali tools found: {len(kali_tools)}")
    
    # Process repos
    for repo in unique_repos[:50]:  # Limit to 50 per day
        tool = parse_tool_from_repo(repo)
        
        if check_tool_exists(tool["name"], tool["category"]):
            continue
        
        generate_new_tool_skill(tool)
        new_tools.append(tool)
    
    # Process Kali tools
    for kt in kali_tools[:20]:
        if not check_tool_exists(kt["name"], "miscellaneous"):
            tool = {
                "name": kt["name"],
                "description": kt["description"],
                "category": "miscellaneous",
                "source": "kali-repo",
                "stars": 0,
                "url": "",
                "language": "Unknown",
                "topics": []
            }
            generate_new_tool_skill(tool)
            new_tools.append(tool)
    
    if new_tools:
        update_arsenal_readme(new_tools)
    
    # Save log
    log_file = CACHE_DIR / f"scrape_{datetime.now().strftime('%Y%m%d')}.json"
    log_file.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "tools_found": len(new_tools),
        "tools": new_tools
    }, indent=2))
    
    print("\n" + "="*60)
    print("DAILY SCRAPE SUMMARY")
    print("="*60)
    print(f"Sources checked: awesome-lists, exploit-db, kali-repo")
    print(f"New tools added: {len(new_tools)}")
    print(f"Skill directory: {SKILL_DIR}")
    print("="*60)
    
    if new_tools:
        print(f"\nNew tools ({len(new_tools)}):")
        for tool in new_tools[:10]:
            print(f"  • {tool['name']} ({tool['category']})")

if __name__ == "__main__":
    main()
