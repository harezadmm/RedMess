#!/usr/bin/env python3
"""
Smart Skill Matcher for RedMess
Identifies required skills from user request WITHOUT scanning all 188+ skills
Uses keyword matching + NLP to find relevant tools
"""
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SKILL_DIR = Path.home() / ".hermes/profiles/umi3/skills/red-team-arsenal"
MEMORY_FILE = Path.home() / ".hermes/profiles/umi3/redmess_memory.json"
SKILL_INDEX_CACHE = Path.home() / ".cache/arsenal_scraper/skill_index.json"

# Keyword to skill category mapping
KEYWORD_MAP = {
    # Information Gathering
    "scan": ["information-gathering", "vulnerability-analysis"],
    "nmap": ["information-gathering"],
    "reconnaissance": ["information-gathering"],
    "recon": ["information-gathering"],
    "subdomain": ["information-gathering"],
    "dns": ["information-gathering"],
    "osint": ["information-gathering"],
    "shodan": ["information-gathering"],
    "enumerate": ["information-gathering"],
    "discovery": ["information-gathering"],
    "fingerprint": ["information-gathering"],
    
    # Web Applications
    "web": ["web-applications", "vulnerability-analysis"],
    "website": ["web-applications"],
    "http": ["web-applications"],
    "https": ["web-applications"],
    "directory": ["web-applications"],
    "url": ["web-applications"],
    "endpoint": ["web-applications", "api-security"],
    "api": ["api-security", "web-applications"],
    "rest": ["api-security"],
    "graphql": ["api-security"],
    
    # Exploitation
    "exploit": ["exploitation"],
    "rce": ["exploitation"],
    "shell": ["exploitation"],
    "reverse shell": ["exploitation"],
    "payload": ["exploitation"],
    "metasploit": ["exploitation"],
    "msf": ["exploitation"],
    "vulnerability": ["vulnerability-analysis", "exploitation"],
    "cve": ["exploitation", "vulnerability-analysis"],
    
    # SQL Injection
    "sql": ["web-applications", "database-assessment"],
    "sqlmap": ["web-applications", "database-assessment"],
    "injection": ["web-applications", "vulnerability-analysis"],
    "sqli": ["web-applications", "database-assessment"],
    "database": ["database-assessment"],
    "mysql": ["database-assessment"],
    "postgres": ["database-assessment"],
    "mssql": ["database-assessment"],
    "oracle": ["database-assessment"],
    
    # XSS
    "xss": ["web-applications", "vulnerability-analysis"],
    "cross site": ["web-applications"],
    "javascript": ["web-applications"],
    
    # Password Attacks
    "password": ["password-attacks"],
    "brute": ["password-attacks"],
    "bruteforce": ["password-attacks"],
    "crack": ["password-attacks"],
    "hash": ["password-attacks"],
    "hydra": ["password-attacks"],
    "john": ["password-attacks"],
    "hashcat": ["password-attacks"],
    "wordlist": ["password-attacks"],
    
    # Wireless
    "wifi": ["wireless-attacks"],
    "wireless": ["wireless-attacks"],
    "wpa": ["wireless-attacks"],
    "wep": ["wireless-attacks"],
    "aircrack": ["wireless-attacks"],
    "bluetooth": ["wireless-attacks"],
    
    # Network
    "network": ["sniffing-spoofing", "information-gathering"],
    "mitm": ["sniffing-spoofing"],
    "arp": ["sniffing-spoofing"],
    "sniff": ["sniffing-spoofing"],
    "wireshark": ["sniffing-spoofing"],
    "packet": ["sniffing-spoofing"],
    "capture": ["sniffing-spoofing"],
    
    # Post-Exploitation
    "privilege": ["post-exploitation"],
    "privesc": ["post-exploitation"],
    "lateral": ["post-exploitation"],
    "persistence": ["post-exploitation"],
    "mimikatz": ["post-exploitation"],
    "bloodhound": ["post-exploitation"],
    "domain": ["post-exploitation"],
    "active directory": ["post-exploitation"],
    "ad": ["post-exploitation"],
    
    # Reverse Engineering
    "reverse": ["reverse-engineering"],
    "decompile": ["reverse-engineering"],
    "disassemble": ["reverse-engineering"],
    "ghidra": ["reverse-engineering"],
    "ida": ["reverse-engineering"],
    "binary": ["reverse-engineering"],
    "apk": ["reverse-engineering"],
    "android": ["reverse-engineering"],
    "frida": ["reverse-engineering"],
    
    # Forensics
    "forensic": ["forensics"],
    "memory": ["forensics"],
    "volatility": ["forensics"],
    "disk": ["forensics"],
    "autopsy": ["forensics"],
    "carve": ["forensics"],
    
    # Social Engineering
    "phishing": ["social-engineering"],
    "social": ["social-engineering"],
    "gophish": ["social-engineering"],
    "evilginx": ["social-engineering"],
    
    # Cloud
    "cloud": ["cloud-security"],
    "aws": ["cloud-security"],
    "azure": ["cloud-security"],
    "gcp": ["cloud-security"],
    "s3": ["cloud-security"],
    "bucket": ["cloud-security"],
    
    # Container
    "docker": ["container-security"],
    "kubernetes": ["container-security"],
    "container": ["container-security"],
}

# Tool name direct mapping
TOOL_NAME_MAP = {
    "nmap": "information-gathering/nmap",
    "masscan": "information-gathering/masscan",
    "sqlmap": "web-applications/sqlmap",
    "burp": "web-applications/burpsuite",
    "burpsuite": "web-applications/burpsuite",
    "metasploit": "exploitation/metasploit-framework",
    "msf": "exploitation/metasploit-framework",
    "msfconsole": "exploitation/metasploit-framework",
    "hydra": "password-attacks/hydra",
    "john": "password-attacks/john",
    "hashcat": "password-attacks/hashcat",
    "aircrack": "wireless-attacks/aircrack-ng",
    "wireshark": "sniffing-spoofing/wireshark",
    "gobuster": "web-applications/gobuster",
    "ffuf": "web-applications/ffuf",
    "nikto": "vulnerability-analysis/nikto",
    "nuclei": "vulnerability-analysis/nuclei",
    "mimikatz": "post-exploitation/mimikatz",
    "bloodhound": "post-exploitation/bloodhound",
    "ghidra": "reverse-engineering/ghidra",
    "frida": "reverse-engineering/frida",
    "volatility": "forensics/volatility",
}

def load_memory():
    """Load conversation memory"""
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {
        "conversations": [],
        "frequent_skills": defaultdict(int),
        "last_categories": [],
        "user_preferences": {}
    }

def save_memory(memory):
    """Save conversation memory"""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(memory, indent=2, default=str))

def build_skill_index():
    """Build lightweight skill index (name, category, keywords only)"""
    if SKILL_INDEX_CACHE.exists():
        cache_age = (datetime.now().timestamp() - SKILL_INDEX_CACHE.stat().st_mtime)
        if cache_age < 3600:  # Cache valid for 1 hour
            return json.loads(SKILL_INDEX_CACHE.read_text())
    
    index = {}
    
    for skill_file in SKILL_DIR.glob("**/*-SKILL.md"):
        if skill_file.name == "README.md":
            continue
        
        category = skill_file.parent.name
        tool_name = skill_file.stem.replace("-SKILL", "")
        
        # Extract keywords from frontmatter
        content = skill_file.read_text()
        keywords = []
        
        # Parse YAML frontmatter
        if content.startswith("---"):
            frontmatter = content.split("---")[1]
            
            # Extract tags
            tags_match = re.search(r'tags:\s*\[([^\]]+)\]', frontmatter)
            if tags_match:
                keywords = [t.strip() for t in tags_match.group(1).split(",")]
            
            # Extract description
            desc_match = re.search(r'description:\s*(.+)', frontmatter)
            if desc_match:
                keywords.append(desc_match.group(1).strip())
        
        index[tool_name] = {
            "category": category,
            "keywords": keywords,
            "path": str(skill_file.relative_to(SKILL_DIR))
        }
    
    # Cache index
    SKILL_INDEX_CACHE.parent.mkdir(parents=True, exist_ok=True)
    SKILL_INDEX_CACHE.write_text(json.dumps(index, indent=2))
    
    return index

def identify_skills(user_request, memory=None):
    """
    Identify relevant skills from user request
    Returns list of skill paths to load
    """
    if memory is None:
        memory = load_memory()
    
    user_request_lower = user_request.lower()
    
    # Step 1: Check for direct tool name mentions
    matched_skills = []
    matched_tool_names = set()
    
    for tool_name, skill_path in TOOL_NAME_MAP.items():
        # Word boundary matching (avoid partial matches)
        pattern = r'\b' + re.escape(tool_name) + r'\b'
        if re.search(pattern, user_request_lower):
            matched_skills.append({
                "skill": skill_path,
                "confidence": "high",
                "reason": f"Direct tool name: {tool_name}"
            })
            matched_tool_names.add(tool_name)
    
    # Step 2: Keyword-based category matching
    relevant_categories = set()
    matched_keywords = []
    
    for keyword, categories in KEYWORD_MAP.items():
        if keyword in user_request_lower:
            relevant_categories.update(categories)
            matched_keywords.append(keyword)
    
    # Step 3: Context from memory (last used categories)
    if memory["last_categories"]:
        recent_categories = memory["last_categories"][-3:]  # Last 3 categories used
        relevant_categories.update(recent_categories)
    
    # Step 4: Search skill index for category matches
    if relevant_categories:
        skill_index = build_skill_index()
        
        # Score tools by relevance
        tool_scores = []
        
        for tool_name, info in skill_index.items():
            # Skip if already matched by direct name
            skill_path = f"{info['category']}/{tool_name}"
            if any(s["skill"] == skill_path for s in matched_skills):
                continue
            
            score = 0
            
            # Category match
            if info["category"] in relevant_categories:
                score += 3
            
            # Tool name contains keywords
            for keyword in matched_keywords:
                if keyword in tool_name.lower():
                    score += 5  # Strong signal
                
                # Keywords in description
                for kw in info.get("keywords", []):
                    if keyword in kw.lower():
                        score += 1
            
            if score > 0:
                tool_scores.append((tool_name, info, score))
        
        # Sort by score and take top 8
        tool_scores.sort(key=lambda x: x[2], reverse=True)
        
        for tool_name, info, score in tool_scores[:8]:
            skill_path = f"{info['category']}/{tool_name}"
            matched_skills.append({
                "skill": skill_path,
                "confidence": "high" if score >= 5 else "medium",
                "reason": f"Category: {info['category']}, keywords: {', '.join(matched_keywords[:3])}"
            })
    
    # Step 5: Limit to top 5 most relevant + frequent skills from memory
    frequent_skills = sorted(
        memory["frequent_skills"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    for skill, count in frequent_skills:
        if not any(s["skill"] == skill for s in matched_skills):
            if len(matched_skills) < 5:
                matched_skills.append({
                    "skill": skill,
                    "confidence": "low",
                    "reason": f"Frequently used (used {count} times)"
                })
    
    # Sort by confidence
    confidence_order = {"high": 3, "medium": 2, "low": 1}
    matched_skills.sort(key=lambda x: confidence_order[x["confidence"]], reverse=True)
    
    return matched_skills[:5]  # Max 5 skills

def update_memory(user_request, loaded_skills):
    """Update memory with this conversation"""
    memory = load_memory()
    
    # Add conversation
    memory["conversations"].append({
        "timestamp": datetime.now().isoformat(),
        "request": user_request[:200],  # First 200 chars
        "skills_used": loaded_skills
    })
    
    # Keep last 50 conversations
    memory["conversations"] = memory["conversations"][-50:]
    
    # Update frequent skills
    for skill in loaded_skills:
        skill_path = skill if isinstance(skill, str) else skill.get("skill")
        memory["frequent_skills"][skill_path] = memory["frequent_skills"].get(skill_path, 0) + 1
    
    # Update last categories
    categories = []
    for skill in loaded_skills:
        skill_path = skill if isinstance(skill, str) else skill.get("skill")
        if "/" in skill_path:
            category = skill_path.split("/")[0]
            if category not in categories:
                categories.append(category)
    
    memory["last_categories"].extend(categories)
    memory["last_categories"] = memory["last_categories"][-10:]  # Keep last 10
    
    save_memory(memory)

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 smart_skill_matcher.py '<user request>'")
        sys.exit(1)
    
    user_request = " ".join(sys.argv[1:])
    
    print(f"[*] Analyzing request: {user_request[:100]}...")
    print()
    
    matched_skills = identify_skills(user_request)
    
    if not matched_skills:
        print("[-] No relevant skills identified")
        print("[*] Try more specific keywords (e.g., 'nmap scan', 'sql injection', 'wifi crack')")
        sys.exit(0)
    
    print(f"[+] Identified {len(matched_skills)} relevant skills:\n")
    
    for i, match in enumerate(matched_skills, 1):
        skill = match["skill"]
        confidence = match["confidence"]
        reason = match["reason"]
        
        conf_emoji = "🔥" if confidence == "high" else "⚡" if confidence == "medium" else "💡"
        
        print(f"{i}. {conf_emoji} {skill}")
        print(f"   Confidence: {confidence.upper()}")
        print(f"   Reason: {reason}")
        print()
    
    print(f"[*] Load these skills with:")
    for match in matched_skills:
        print(f"    skill_view(name='red-team-arsenal/{match['skill']}')")

if __name__ == "__main__":
    main()
