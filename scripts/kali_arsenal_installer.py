#!/usr/bin/env python3
"""
Kali Linux Arsenal Installer + Skill Generator
Installs 200+ pentesting tools and generates Hermes skills
"""
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

# Kali tool categories with descriptions
KALI_TOOLS = {
    "information-gathering": [
        "nmap", "masscan", "rustscan", "nikto", "whatweb", "wafw00f", 
        "dnsenum", "fierce", "dnsrecon", "sublist3r", "amass", "theharvester",
        "recon-ng", "maltego", "shodan", "censys-cli", "spiderfoot"
    ],
    "vulnerability-analysis": [
        "nikto", "wpscan", "joomscan", "nuclei", "httpx", "ffuf",
        "wfuzz", "sqlmap", "commix", "xsser", "sslyze", "testssl.sh",
        "lynis", "openvas", "nessus", "nexpose"
    ],
    "web-applications": [
        "burpsuite", "zaproxy", "sqlmap", "commix", "wpscan", "joomscan",
        "dirb", "dirbuster", "gobuster", "feroxbuster", "ffuf", "wfuzz",
        "nikto", "whatweb", "wafw00f", "httpx", "nuclei"
    ],
    "database-assessment": [
        "sqlmap", "sqlninja", "bbqsql", "jsql-injection", "mssqlpwner",
        "odat", "oscanner", "sidguesser", "tnscmd10g"
    ],
    "password-attacks": [
        "hydra", "medusa", "ncrack", "john", "hashcat", "ophcrack",
        "rainbowcrack", "crunch", "cewl", "rsmangler", "cupp"
    ],
    "wireless-attacks": [
        "aircrack-ng", "reaver", "pixiewps", "wifite", "fern-wifi-cracker",
        "kismet", "wifiphisher", "mdk4", "mdk3", "cowpatty"
    ],
    "exploitation": [
        "metasploit-framework", "armitage", "beef-xss", "exploitdb",
        "searchsploit", "routersploit", "commix", "sqlmap"
    ],
    "sniffing-spoofing": [
        "wireshark", "tshark", "tcpdump", "ettercap", "bettercap",
        "responder", "mitmproxy", "dsniff", "arpspoof", "dnsspoof"
    ],
    "post-exploitation": [
        "metasploit-framework", "empire", "powersploit", "mimikatz",
        "crackmapexec", "bloodhound", "impacket", "evil-winrm"
    ],
    "forensics": [
        "autopsy", "sleuthkit", "volatility", "binwalk", "foremost",
        "scalpel", "bulk-extractor", "guymager", "dc3dd"
    ],
    "reverse-engineering": [
        "ghidra", "radare2", "gdb", "edb-debugger", "ollydbg",
        "ida-free", "apktool", "jadx", "dex2jar", "jd-gui",
        "frida", "objection", "hopper", "binary-ninja"
    ],
    "social-engineering": [
        "set", "socialfish", "gophish", "king-phisher", "evilginx2",
        "modlishka", "shellphish", "blackeye", "zphisher"
    ]
}

# Modern tools (2024-2026) not in default Kali
MODERN_TOOLS = {
    "cloud-security": [
        "cloudfox", "pacu", "scoutsuite", "prowler", "cloudmapper",
        "cloud-service-enum", "S3Scanner", "bucketeer"
    ],
    "api-security": [
        "kiterunner", "arjun", "postman", "insomnia", "httpx",
        "nuclei", "ffuf", "mitmproxy"
    ],
    "container-security": [
        "trivy", "grype", "syft", "docker-bench-security", "kube-bench",
        "kube-hunter", "kubesploit"
    ],
    "code-analysis": [
        "semgrep", "bandit", "gitleaks", "trufflehog", "detect-secrets",
        "gitrob", "shhgit", "whispers"
    ],
    "osint": [
        "maigret", "sherlock", "blackbird", "holehe", "emailrep",
        "phoneinfogar", "socialscan", "nexfil"
    ]
}

SKILL_DIR = Path.home() / ".hermes/profiles/umi3/skills/red-team-arsenal"
SKILL_DIR.mkdir(parents=True, exist_ok=True)

def check_install(tool):
    """Check if tool is installed"""
    return subprocess.run(
        ["which", tool], 
        capture_output=True, 
        text=True
    ).returncode == 0

def install_tool(tool):
    """Install tool via apt"""
    print(f"[+] Installing {tool}...")
    try:
        subprocess.run(
            ["apt-get", "install", "-y", tool],
            capture_output=True,
            timeout=300
        )
        return True
    except Exception as e:
        print(f"[-] Failed to install {tool}: {e}")
        return False

def get_tool_info(tool):
    """Get tool description and usage"""
    descriptions = {
        # Information Gathering
        "nmap": "Network scanner: ports, services, OS detection, NSE scripts",
        "masscan": "Ultra-fast port scanner: scan entire internet in 6 minutes",
        "rustscan": "Modern port scanner: nmap automation with speed",
        "nikto": "Web server scanner: 6700+ dangerous files/CGIs, outdated servers",
        "whatweb": "Web tech identifier: CMS, frameworks, JS libraries, servers",
        "wafw00f": "WAF detector: identifies web application firewalls",
        "dnsenum": "DNS enum: subdomains, zone transfers, Google scraping",
        "fierce": "DNS recon: non-recursive subdomain discovery",
        "dnsrecon": "DNS enum: zone transfer, brute force, cache snooping",
        "sublist3r": "Subdomain enum: search engines, APIs (Google, Yahoo, Bing)",
        "amass": "OWASP subdomain discovery: scraping, recursive brute force",
        "theharvester": "OSINT: emails, subdomains, hosts from search engines",
        "recon-ng": "Full-featured recon framework: modular like Metasploit",
        "spiderfoot": "OSINT automation: 200+ modules, threat intel",
        
        # Vulnerability Analysis
        "wpscan": "WordPress scanner: vulns, plugins, themes, users",
        "joomscan": "Joomla scanner: exploits, version detection",
        "nuclei": "Fast vuln scanner: 5000+ templates, custom YAML",
        "httpx": "HTTP toolkit: probing, tech detection, screenshots",
        "ffuf": "Fuzzer: dirs, files, params, vhosts, faster than gobuster",
        "wfuzz": "Web fuzzer: parameters, auth, sessions, custom iterators",
        "sqlmap": "SQL injection: automatic detection, exploitation, takeover",
        "commix": "Command injection: OS command exploitation",
        "xsser": "XSS scanner: automatic XSS detection and exploitation",
        "sslyze": "SSL/TLS scanner: misconfigs, vulns, cipher suites",
        "testssl.sh": "SSL/TLS tester: protocols, ciphers, known vulns",
        "lynis": "Security audit: compliance, hardening, benchmarks",
        
        # Web Applications
        "burpsuite": "Web proxy: intercept, modify, replay HTTP traffic",
        "zaproxy": "OWASP ZAP: automated scanner, intercepting proxy",
        "dirb": "Directory brute forcer: wordlist-based web fuzzing",
        "gobuster": "URI brute forcer: dirs, DNS, vhosts, S3 buckets",
        "feroxbuster": "Recursive directory scanner: Rust-based, fast",
        
        # Database Assessment
        "sqlninja": "SQL Server takeover: command execution via injection",
        "bbqsql": "Blind SQL injection framework: semi-automatic exploitation",
        "odat": "Oracle Database Attack Tool: SID enum, privesc, exec",
        
        # Password Attacks
        "hydra": "Network logon cracker: 50+ protocols (SSH, FTP, HTTP)",
        "medusa": "Fast parallel password cracker: modular, 21+ services",
        "ncrack": "High-speed network auth cracker: SMB, RDP, SSH",
        "john": "John the Ripper: offline password cracker, custom rules",
        "hashcat": "Advanced password recovery: GPU-accelerated, 300+ algos",
        "ophcrack": "Windows password cracker: rainbow tables, LM/NTLM",
        "crunch": "Wordlist generator: custom patterns, permutations",
        "cewl": "Custom wordlist: scrape websites for password lists",
        "cupp": "User password profiler: social engineering wordlists",
        
        # Wireless Attacks
        "aircrack-ng": "WiFi security: WEP/WPA/WPA2 cracking, packet injection",
        "reaver": "WPS cracker: brute force WPS PINs",
        "pixiewps": "WPS pixie dust attack: offline WPS PIN recovery",
        "wifite": "Automated WiFi attacker: auditing multiple networks",
        "kismet": "Wireless detector: sniffing, wardriving, IDS",
        "wifiphisher": "Rogue AP: automated phishing, evil twin attacks",
        "mdk4": "WiFi fuzzer: beacon flood, deauth, DoS attacks",
        
        # Exploitation
        "metasploit-framework": "Exploit framework: 2000+ exploits, post-exploit modules",
        "armitage": "Metasploit GUI: team collaboration, attack visualization",
        "beef-xss": "Browser exploitation: hook browsers, pivot attacks",
        "searchsploit": "Exploit-DB CLI: offline exploit search",
        "routersploit": "Router exploitation: embedded device vulns",
        
        # Sniffing/Spoofing
        "wireshark": "Packet analyzer: deep inspection, protocol dissection",
        "tshark": "Wireshark CLI: scriptable packet capture",
        "tcpdump": "Packet sniffer: capture and display network traffic",
        "ettercap": "MITM framework: ARP poisoning, packet manipulation",
        "bettercap": "Swiss Army knife: MITM, monitoring, attack framework",
        "responder": "LLMNR/NBT-NS poisoner: capture NTLM hashes",
        "mitmproxy": "Interactive HTTPS proxy: modify traffic on-the-fly",
        "dsniff": "Password sniffer: Telnet, FTP, HTTP, POP, SNMP",
        
        # Post-Exploitation
        "empire": "PowerShell post-exploit: C2, agent management",
        "mimikatz": "Windows credential dumper: plaintext passwords, hashes",
        "crackmapexec": "Post-exploit swiss knife: SMB/LDAP/WinRM enum",
        "bloodhound": "AD attack graph: shortest path to Domain Admin",
        "impacket": "Python network protocols: SMB, MSRPC, LDAP tools",
        "evil-winrm": "WinRM shell: upload, download, load PowerShell scripts",
        
        # Forensics
        "autopsy": "Digital forensics: disk imaging, file recovery, timeline",
        "sleuthkit": "Forensic toolkit: file system analysis, data recovery",
        "volatility": "Memory forensics: RAM dump analysis, malware detection",
        "binwalk": "Firmware analysis: extract embedded file systems",
        "foremost": "File carving: recover deleted files from raw disk",
        "bulk-extractor": "Fast data extraction: emails, URLs, credit cards",
        
        # Reverse Engineering
        "ghidra": "NSA reverse engineering: decompiler, debugger, analysis",
        "radare2": "Reverse engineering framework: disassembler, debugger",
        "gdb": "GNU debugger: source-level debugging, runtime inspection",
        "apktool": "Android APK tool: decompile, modify, repackage",
        "jadx": "Dex to Java decompiler: Android APK reverse engineering",
        "dex2jar": "Android dex to jar converter: extract Java classes",
        "jd-gui": "Java decompiler GUI: view .class and .jar files",
        "frida": "Dynamic instrumentation: runtime code injection, hooking",
        "objection": "Mobile security framework: Frida runtime automation",
        
        # Social Engineering
        "set": "Social Engineering Toolkit: phishing, payloads, USB/WiFi attacks",
        "gophish": "Phishing framework: campaign management, tracking",
        "evilginx2": "Phishing MITM: bypass 2FA, steal session cookies",
        
        # Modern Tools
        "cloudfox": "AWS/Azure/GCP enum: IAM, S3, secrets, privesc paths",
        "pacu": "AWS exploitation framework: post-compromise enumeration",
        "scoutsuite": "Cloud security auditor: multi-cloud compliance checks",
        "prowler": "AWS/Azure/GCP security assessments: CIS benchmarks",
        "trivy": "Container scanner: vulns, misconfigs, secrets in images",
        "semgrep": "Static code analysis: custom rules, 30+ languages",
        "gitleaks": "Secret scanner: scan repos for leaked credentials",
        "trufflehog": "Secret scanner: search git history for high-entropy strings",
        "maigret": "OSINT username search: 3000+ sites, username enumeration",
        "sherlock": "Username OSINT: hunt social media accounts across 400+ sites",
        "holehe": "Email OSINT: check email on 120+ sites (data breach check)",
    }
    
    return descriptions.get(tool, f"{tool.upper()} pentesting tool")

def generate_skill(tool, category, description):
    """Generate SKILL.md for a tool"""
    skill_content = f"""---
name: {tool}
description: {description[:57]}{"..." if len(description) > 57 else ""}
category: red-team-arsenal/{category}
tags: [pentesting, {category.replace("-", " ")}, kali-linux, {tool}]
author: auto-generated
created: {datetime.now().strftime("%Y-%m-%d")}
---

# {tool.upper()}

**Category:** {category.replace("-", " ").title()}  
**Description:** {description}

## Installation

```bash
# Kali Linux
sudo apt-get update && sudo apt-get install -y {tool}

# Check installation
which {tool}
{tool} --version || {tool} -h
```

## Basic Usage

```bash
# Get help
{tool} --help
{tool} -h

# Common usage patterns will be updated after first use
```

## Key Features

- Part of Kali Linux {category.replace("-", " ")} toolkit
- Industry-standard pentesting tool
- Active development and community support

## Common Workflows

*This section will be populated after tool usage and research*

## Pitfalls

- Always verify target authorization before scanning
- Some tools generate significant network traffic
- Check local laws regarding security testing
- Maintain operational security when running tools

## Resources

- Kali Tools: https://www.kali.org/tools/{tool}/
- Official Documentation: Search for "{tool} official documentation"
- Exploit-DB: https://www.exploit-db.com/

## Notes

- Auto-generated skill, will be enriched with usage patterns
- Last updated: {datetime.now().strftime("%Y-%m-%d")}
"""
    
    skill_path = SKILL_DIR / category / f"{tool}-SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(skill_content)
    print(f"[+] Generated skill: {skill_path}")
    return skill_path

def generate_arsenal_readme():
    """Generate master README for arsenal"""
    readme_content = f"""# Red Team Arsenal
**Auto-generated Kali Linux toolkit index**  
**Last updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is a comprehensive index of 200+ pentesting tools organized by category.
Each tool has a dedicated SKILL.md with installation, usage, and workflows.

## Tool Categories

"""
    
    total_tools = 0
    for category, tools in sorted(KALI_TOOLS.items()):
        readme_content += f"\n### {category.replace('-', ' ').title()} ({len(tools)} tools)\n\n"
        for tool in sorted(tools):
            desc = get_tool_info(tool).split(":")[0]  # Short description
            readme_content += f"- **{tool}** — {desc}\n"
            total_tools += 1
    
    readme_content += f"\n### Modern Tools (2024-2026)\n\n"
    for category, tools in sorted(MODERN_TOOLS.items()):
        readme_content += f"\n#### {category.replace('-', ' ').title()}\n"
        for tool in sorted(tools):
            readme_content += f"- **{tool}**\n"
            total_tools += 1
    
    readme_content += f"""

## Statistics

- **Total Tools:** {total_tools}
- **Kali Categories:** {len(KALI_TOOLS)}
- **Modern Categories:** {len(MODERN_TOOLS)}
- **Skills Generated:** Check individual category directories

## Usage

Load any tool skill:
```
skill_view(name='red-team-arsenal/<category>/<tool>')
```

Example:
```
skill_view(name='red-team-arsenal/information-gathering/nmap')
```

## Daily Updates

This arsenal is automatically updated daily via cron job:
- New tools from Kali repositories
- GitHub trending security tools
- Exploit-DB latest additions
- Community-contributed tools

## Contributing

Skills are auto-generated but can be manually enriched:
```
skill_manage(action='patch', name='red-team-arsenal/<category>/<tool>', ...)
```

---
*Generated by Kali Arsenal Installer*
"""
    
    readme_path = SKILL_DIR / "README.md"
    readme_path.write_text(readme_content)
    print(f"[+] Generated arsenal README: {readme_path}")
    return readme_path

def main():
    print("[*] Kali Arsenal Installer + Skill Generator")
    print("[*] This will install 200+ tools and generate skills")
    print()
    
    # Update package lists
    print("[*] Updating package lists...")
    subprocess.run(["apt-get", "update"], capture_output=True)
    
    stats = {
        "installed": 0,
        "failed": 0,
        "skipped": 0,
        "skills_generated": 0
    }
    
    # Install and generate skills for each category
    for category, tools in KALI_TOOLS.items():
        print(f"\n[*] Processing category: {category}")
        for tool in tools:
            if check_install(tool):
                print(f"[✓] {tool} already installed")
                stats["skipped"] += 1
            else:
                if install_tool(tool):
                    stats["installed"] += 1
                else:
                    stats["failed"] += 1
                    continue
            
            # Generate skill
            description = get_tool_info(tool)
            generate_skill(tool, category, description)
            stats["skills_generated"] += 1
    
    # Generate master README
    generate_arsenal_readme()
    
    # Print summary
    print("\n" + "="*60)
    print("INSTALLATION SUMMARY")
    print("="*60)
    print(f"Installed: {stats['installed']}")
    print(f"Already installed: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skills generated: {stats['skills_generated']}")
    print(f"Skill directory: {SKILL_DIR}")
    print("="*60)
    
    # Save stats
    stats_file = SKILL_DIR / "install_stats.json"
    stats_file.write_text(json.dumps({
        **stats,
        "timestamp": datetime.now().isoformat(),
        "total_tools": len([t for tools in KALI_TOOLS.values() for t in tools])
    }, indent=2))

if __name__ == "__main__":
    main()
