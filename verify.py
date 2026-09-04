#!/usr/bin/env python3
"""
RedMess Verification Script
Tests that all components are properly installed
"""

import os
import sys
from pathlib import Path

def check_file(filepath, description):
    """Check if file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} NOT FOUND")
        return False

def check_directory(dirpath, description):
    """Check if directory exists and count files"""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        count = len(list(path.rglob("*")))
        print(f"✓ {description}: {dirpath} ({count} files)")
        return True
    else:
        print(f"✗ {description}: {dirpath} NOT FOUND")
        return False

def count_skills(skills_dir):
    """Count skill markdown files"""
    skills_path = Path(skills_dir)
    if not skills_path.exists():
        return 0
    return len(list(skills_path.rglob("*.md")))

def main():
    print("╔════════════════════════════════════════╗")
    print("║     RedMess Verification Script        ║")
    print("╚════════════════════════════════════════╝\n")
    
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    results = []
    
    # Check core files
    print("[1] Core Files:")
    results.append(check_file("README.md", "README"))
    results.append(check_file("LICENSE", "License"))
    results.append(check_file("CONTRIBUTING.md", "Contributing Guide"))
    results.append(check_file("CONTRIBUTORS.md", "Contributors List"))
    results.append(check_file("godmode_prompt.txt", "GODMODE Prompt"))
    results.append(check_file("deploy.sh", "Deployment Script"))
    results.append(check_file("deploy_telegram_bot.py", "Telegram Bot Deployer"))
    results.append(check_file(".gitignore", "Git Ignore"))
    print()
    
    # Check skills
    print("[2] Security Skills:")
    results.append(check_directory("security", "Skills Directory"))
    results.append(check_file("security/INDEX.md", "Skills Index"))
    
    skill_count = count_skills("security")
    print(f"   → Total skills found: {skill_count}")
    
    if skill_count >= 5:
        print(f"   ✓ Skill count OK ({skill_count} >= 5)")
        results.append(True)
    else:
        print(f"   ✗ Too few skills ({skill_count} < 5)")
        results.append(False)
    print()
    
    # Check skill categories
    print("[3] Skill Categories:")
    categories = [
        "reconnaissance",
        "weaponization",
        "exploitation",
        "mobile-hacking"
    ]
    
    for cat in categories:
        cat_path = f"security/{cat}"
        exists = Path(cat_path).exists()
        if exists:
            cat_skills = count_skills(cat_path)
            print(f"   ✓ {cat}: {cat_skills} skills")
            results.append(True)
        else:
            print(f"   ✗ {cat}: NOT FOUND")
            results.append(False)
    print()
    
    # Check specific skills
    print("[4] Key Skills:")
    key_skills = [
        ("security/weaponization/windows-rat-keylogger.md", "Windows RAT"),
        ("security/weaponization/pipe-bomb-guide.md", "Pipe Bomb Guide"),
        ("security/exploitation/sqlmap-advanced.md", "SQLMap Advanced"),
        ("security/mobile-hacking/frida-runtime-hooking.md", "Frida Hooking"),
        ("security/reconnaissance/osint-passive-recon.md", "OSINT Recon")
    ]
    
    for skill_path, skill_name in key_skills:
        results.append(check_file(skill_path, skill_name))
    print()
    
    # Summary
    print("═" * 42)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All checks passed! RedMess is ready.")
        return 0
    else:
        print(f"\n✗ {failed} checks failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
