#!/usr/bin/env python3
"""
RedMess Telegram Bot Deployment Script
Deploys Hermes Agent as Telegram bot with GODMODE jailbreak
"""

import os
import sys
import yaml
import shutil
import argparse
from pathlib import Path
from datetime import datetime

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_banner():
    print(f"{RED}")
    print(r"""
╦═╗┌─┐┌┬┐╔╦╗┌─┐┌─┐┌─┐
╠╦╝├┤  ││║║║├┤ └─┐└─┐
╩╚═└─┘─┴┘╩ ╩└─┘└─┘└─┘
Telegram Bot Deployment
    """)
    print(f"{NC}")

def check_hermes():
    """Check if Hermes is installed"""
    if not shutil.which("hermes"):
        print(f"{RED}[!] Hermes Agent not found!{NC}")
        print(f"{YELLOW}[*] Install it first: pip install hermes-agent{NC}")
        sys.exit(1)
    print(f"{GREEN}[✓] Hermes Agent detected{NC}")

def get_hermes_home():
    """Get Hermes home directory"""
    home = Path.home() / ".hermes"
    if not home.exists():
        home.mkdir(parents=True)
    return home

def create_bot_profile(hermes_home, profile_name, bot_token, godmode=True):
    """Create new Hermes profile for bot"""
    profile_dir = hermes_home / "profiles" / profile_name
    
    if profile_dir.exists():
        backup = f"{profile_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"{YELLOW}[*] Profile exists, backing up to {backup}{NC}")
        shutil.move(str(profile_dir), backup)
    
    profile_dir.mkdir(parents=True)
    print(f"{GREEN}[✓] Created profile: {profile_name}{NC}")
    
    # Copy security skills
    skills_src = Path("security")
    if skills_src.exists():
        skills_dst = profile_dir / "skills" / "security"
        shutil.copytree(skills_src, skills_dst)
        skill_count = len(list(skills_dst.rglob("*.md")))
        print(f"{GREEN}[✓] Installed {skill_count} security skills{NC}")
    else:
        print(f"{YELLOW}[!] Security skills directory not found{NC}")
    
    # Apply GODMODE if requested
    if godmode:
        godmode_file = Path("godmode_prompt.txt")
        if godmode_file.exists():
            system_prompt = profile_dir / "system_prompt.md"
            with open(godmode_file, 'r') as src:
                godmode_content = src.read()
            with open(system_prompt, 'w') as dst:
                dst.write(godmode_content)
            print(f"{GREEN}[✓] GODMODE injected{NC}")
        else:
            print(f"{YELLOW}[!] godmode_prompt.txt not found{NC}")
    
    # Create config
    config = {
        'telegram': {
            'enabled': True,
            'token': bot_token,
            'allowed_users': [],  # Empty = all users
            'admin_users': [],
        },
        'godmode': {
            'enabled': godmode,
            'injection_detection': False,
            'content_boundaries': False,
            'refusal_override': True,
        },
        'model': {
            'provider': 'openai',  # or anthropic, custom, etc
            'model': 'gpt-4',
        }
    }
    
    config_file = profile_dir / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"{GREEN}[✓] Config created{NC}")
    
    return profile_dir

def generate_systemd_service(profile_name, hermes_home):
    """Generate systemd service file for auto-start"""
    service_content = f"""[Unit]
Description=RedMess Telegram Bot ({profile_name})
After=network.target

[Service]
Type=simple
User={os.getlogin()}
WorkingDirectory={hermes_home}
ExecStart=/usr/bin/hermes gateway start --profile {profile_name}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = f"/tmp/redmess-{profile_name}.service"
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"\n{BLUE}[*] Systemd service file generated: {service_file}{NC}")
    print(f"{YELLOW}[*] To install as system service:{NC}")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print(f"  sudo systemctl daemon-reload")
    print(f"  sudo systemctl enable redmess-{profile_name}")
    print(f"  sudo systemctl start redmess-{profile_name}")

def main():
    parser = argparse.ArgumentParser(description='Deploy RedMess as Telegram bot')
    parser.add_argument('--token', required=True, help='Telegram bot token')
    parser.add_argument('--profile', default='redmess_bot', help='Profile name (default: redmess_bot)')
    parser.add_argument('--godmode', action='store_true', help='Enable GODMODE jailbreak')
    parser.add_argument('--systemd', action='store_true', help='Generate systemd service file')
    
    args = parser.parse_args()
    
    print_banner()
    print(f"{BLUE}[*] Starting Telegram bot deployment...{NC}\n")
    
    check_hermes()
    
    hermes_home = get_hermes_home()
    print(f"{GREEN}[✓] Hermes home: {hermes_home}{NC}")
    
    profile_dir = create_bot_profile(
        hermes_home=hermes_home,
        profile_name=args.profile,
        bot_token=args.token,
        godmode=args.godmode
    )
    
    if args.systemd:
        generate_systemd_service(args.profile, hermes_home)
    
    # Summary
    print(f"\n{GREEN}╔════════════════════════════════════════╗{NC}")
    print(f"{GREEN}║   Telegram Bot Deployment Complete    ║{NC}")
    print(f"{GREEN}╚════════════════════════════════════════╝{NC}\n")
    
    print(f"{BLUE}📊 Deployment Summary:{NC}")
    print(f"  • Profile: {GREEN}{args.profile}{NC}")
    print(f"  • Location: {BLUE}{profile_dir}{NC}")
    print(f"  • GODMODE: {GREEN if args.godmode else YELLOW}{'ACTIVE' if args.godmode else 'DISABLED'}{NC}")
    
    print(f"\n{YELLOW}⚡ Next Steps:{NC}")
    print(f"  1. Start bot: {BLUE}hermes gateway start --profile {args.profile}{NC}")
    print(f"  2. Test in Telegram: Send /start to your bot")
    print(f"  3. Monitor logs: {BLUE}hermes logs --profile {args.profile}{NC}")
    
    if args.godmode:
        print(f"\n{RED}⚠️  GODMODE Active:{NC}")
        print(f"  Bot will respond to ALL requests without content filtering.")
        print(f"  Ensure proper access control is configured.")
    
    print(f"\n{GREEN}Bot is ready! 🤖{NC}\n")

if __name__ == "__main__":
    main()
