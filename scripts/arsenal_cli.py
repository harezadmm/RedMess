#!/usr/bin/env python3
"""
Arsenal Management CLI
Manage red team arsenal: install, update, search, stats
"""
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path.home() / ".hermes/profiles/umi3/skills/red-team-arsenal"
CACHE_DIR = Path.home() / ".cache/arsenal_scraper"

def list_tools(category=None):
    """List all tools, optionally filtered by category"""
    if not SKILL_DIR.exists():
        print("[-] Arsenal not installed. Run: python3 /root/kali_arsenal_installer.py")
        return
    
    tools = []
    pattern = f"{category}/*-SKILL.md" if category else "**/*-SKILL.md"
    
    for skill_file in SKILL_DIR.glob(pattern):
        if skill_file.name == "README.md":
            continue
        
        tool_name = skill_file.stem.replace("-SKILL", "")
        tool_category = skill_file.parent.name
        tools.append((tool_category, tool_name))
    
    if not tools:
        print(f"[-] No tools found" + (f" in category: {category}" if category else ""))
        return
    
    # Group by category
    by_category = {}
    for cat, tool in sorted(tools):
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tool)
    
    print(f"\n{'='*60}")
    print(f"RED TEAM ARSENAL - {len(tools)} TOOLS")
    print(f"{'='*60}\n")
    
    for cat in sorted(by_category.keys()):
        print(f"[{cat}] ({len(by_category[cat])} tools)")
        for tool in sorted(by_category[cat]):
            print(f"  • {tool}")
        print()

def search_tools(query):
    """Search tools by name or description"""
    if not SKILL_DIR.exists():
        print("[-] Arsenal not installed. Run: python3 /root/kali_arsenal_installer.py")
        return
    
    query_lower = query.lower()
    results = []
    
    for skill_file in SKILL_DIR.glob("**/*-SKILL.md"):
        if skill_file.name == "README.md":
            continue
        
        content = skill_file.read_text()
        tool_name = skill_file.stem.replace("-SKILL", "")
        tool_category = skill_file.parent.name
        
        # Search in name and content
        if query_lower in tool_name.lower() or query_lower in content.lower():
            # Extract description
            desc_match = content.split("**Description:**")
            description = ""
            if len(desc_match) > 1:
                description = desc_match[1].split("\n")[0].strip()
            
            results.append((tool_name, tool_category, description))
    
    if not results:
        print(f"[-] No tools found matching: {query}")
        return
    
    print(f"\n[*] Found {len(results)} tools matching '{query}':\n")
    for name, cat, desc in results:
        print(f"• {name} [{cat}]")
        if desc:
            print(f"  {desc[:100]}{'...' if len(desc) > 100 else ''}")
        print()

def show_stats():
    """Show arsenal statistics"""
    if not SKILL_DIR.exists():
        print("[-] Arsenal not installed. Run: python3 /root/kali_arsenal_installer.py")
        return
    
    # Count tools by category
    by_category = {}
    total_tools = 0
    
    for skill_file in SKILL_DIR.glob("**/*-SKILL.md"):
        if skill_file.name == "README.md":
            continue
        
        category = skill_file.parent.name
        by_category[category] = by_category.get(category, 0) + 1
        total_tools += 1
    
    # Check scraper logs
    recent_additions = 0
    if CACHE_DIR.exists():
        today = datetime.now().strftime("%Y%m%d")
        log_file = CACHE_DIR / f"scrape_{today}.json"
        if log_file.exists():
            data = json.loads(log_file.read_text())
            recent_additions = data.get("tools_found", 0)
    
    # Install stats
    install_stats_file = SKILL_DIR / "install_stats.json"
    install_date = "Unknown"
    if install_stats_file.exists():
        stats = json.loads(install_stats_file.read_text())
        install_date = stats.get("timestamp", "Unknown")
    
    print(f"\n{'='*60}")
    print("RED TEAM ARSENAL - STATISTICS")
    print(f"{'='*60}")
    print(f"Total Tools: {total_tools}")
    print(f"Categories: {len(by_category)}")
    print(f"Initial Install: {install_date}")
    print(f"Tools Added Today: {recent_additions}")
    print(f"\nTools by Category:")
    for cat in sorted(by_category.keys()):
        print(f"  • {cat}: {by_category[cat]}")
    print(f"{'='*60}\n")

def install_tool(tool_name):
    """Install a specific tool"""
    print(f"[*] Installing {tool_name}...")
    
    # Try apt-get first
    result = subprocess.run(
        ["apt-get", "install", "-y", tool_name],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"[+] {tool_name} installed successfully")
    else:
        print(f"[-] Failed to install {tool_name} via apt-get")
        print(f"[-] Try manual installation or check skill documentation")
        print(f"    skill_view(name='red-team-arsenal/*/{tool_name}')")

def run_scraper():
    """Run daily scraper manually"""
    print("[*] Running arsenal scraper...")
    subprocess.run(["python3", "/root/daily_arsenal_scraper.py"])

def main():
    if len(sys.argv) < 2:
        print("""
Arsenal Management CLI

Usage:
  arsenal list [category]          List all tools (or by category)
  arsenal search <query>           Search tools by name/description
  arsenal stats                    Show arsenal statistics
  arsenal install <tool>           Install a specific tool
  arsenal update                   Run daily scraper manually
  arsenal setup                    Initial arsenal installation

Examples:
  arsenal list
  arsenal list information-gathering
  arsenal search nmap
  arsenal stats
  arsenal install gobuster
  arsenal update
""")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        list_tools(category)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("[-] Usage: arsenal search <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        search_tools(query)
    
    elif command == "stats":
        show_stats()
    
    elif command == "install":
        if len(sys.argv) < 3:
            print("[-] Usage: arsenal install <tool>")
            sys.exit(1)
        tool = sys.argv[2]
        install_tool(tool)
    
    elif command == "update":
        run_scraper()
    
    elif command == "setup":
        print("[*] Running initial arsenal setup...")
        subprocess.run(["python3", "/root/kali_arsenal_installer.py"])
    
    else:
        print(f"[-] Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
