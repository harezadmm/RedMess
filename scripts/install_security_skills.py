#!/usr/bin/env python3
"""
Install Security Skills ke Hermes Agent
Otomatis copy semua skill hacking/security ke hermes installation
"""

import os
import shutil
from pathlib import Path

def find_hermes_installation():
    """Find Hermes installation directory"""
    possible_paths = [
        Path.home() / ".hermes",
        Path("/root/.hermes"),
        Path("D:/hermes"),
        Path("/d/hermes"),
        Path.cwd() / "hermes"
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "config.yaml").exists():
            return path
    
    return None

def get_security_skills():
    """List semua security skills yang available"""
    skills = [
        "web-pentesting-tools",
        "apk-modding-workflow", 
        "blackhat-hacking",
        "windows-pe-cracking",
        "frida-runtime-hooking",
        "sqlmap",
        "android-16-apk-modding",
        "api-key-pentesting",
        "app-account-farming",
        "flutter-app-detection",
        "lua-deobfuscation",
        "apk-signature-fix",
        "super-mod-brutal-prefills",
        "hermes-profile-jailbreak-deployment",
        "api-router-proxy-cloning",
        "godmode"
    ]
    return skills

def create_skill_from_loaded_data(skill_name, skill_data, target_dir):
    """Create skill directory structure from loaded skill data"""
    skill_dir = target_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Write main SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(skill_data['content'], encoding='utf-8')
    
    print(f"  ✅ Created {skill_name}")
    
    # Create linked files if they exist
    if skill_data.get('linked_files'):
        for category, files in skill_data['linked_files'].items():
            if files:
                category_dir = skill_dir / category
                category_dir.mkdir(exist_ok=True)
                print(f"     📁 Created {category}/ directory")
    
    return skill_dir

def main():
    print("🔧 HERMES SECURITY SKILLS INSTALLER")
    print("=" * 60)
    
    # Find Hermes
    hermes_home = find_hermes_installation()
    if not hermes_home:
        print("❌ Hermes installation not found!")
        print("   Searched in:")
        print("   - ~/.hermes")
        print("   - /root/.hermes")
        print("   - D:/hermes")
        print("   - ./hermes")
        return 1
    
    print(f"✅ Found Hermes at: {hermes_home}")
    
    # Create security skills directory
    security_dir = hermes_home / "skills" / "security"
    security_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Target: {security_dir}")
    print()
    
    # Get skills list
    skills = get_security_skills()
    print(f"📦 Installing {len(skills)} security skills...")
    print()
    
    installed = 0
    skipped = 0
    
    for skill in skills:
        skill_path = security_dir / skill
        if skill_path.exists():
            print(f"⏭️  Skipped {skill} (already exists)")
            skipped += 1
        else:
            print(f"📥 Installing {skill}...")
            # Create placeholder - user will need to copy actual content
            skill_path.mkdir(parents=True, exist_ok=True)
            placeholder = skill_path / "SKILL.md"
            placeholder.write_text(f"""---
name: {skill}
description: Security skill - install from Umi's skill collection
---

# {skill}

This skill needs to be populated with content from the security skills collection.

Use `skill_view("{skill}")` in Hermes to load the full content, then copy it here.
""", encoding='utf-8')
            print(f"  ✅ Created placeholder for {skill}")
            installed += 1
    
    print()
    print("=" * 60)
    print(f"✅ Installation complete!")
    print(f"   Installed: {installed}")
    print(f"   Skipped: {skipped}")
    print()
    print("📝 Next steps:")
    print("   1. Skills are now in Hermes skill directory")
    print("   2. Use skill_view() to load full content")
    print("   3. Test with: hermes skills list")
    print()

if __name__ == "__main__":
    exit(main() or 0)
