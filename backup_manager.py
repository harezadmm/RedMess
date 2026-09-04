#!/usr/bin/env python3
"""
RedMess Backup & Restore Manager
Backup configuration, database, and skills
Version: BRUTAL V3.0
"""

import os
import sys
import shutil
import tarfile
import sqlite3
from datetime import datetime
from pathlib import Path

INSTALL_DIR = Path.home() / ".redmess"
BACKUP_DIR = INSTALL_DIR / "backups"

class BackupManager:
    def __init__(self):
        self.install_dir = INSTALL_DIR
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, include_logs=False):
        """Create full backup of RedMess installation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"redmess_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        print(f"🔄 Creating backup: {backup_name}")
        print(f"   Source: {self.install_dir}")
        print(f"   Destination: {backup_path}\n")
        
        items_to_backup = []
        
        # Configuration
        if (self.install_dir / "config").exists():
            print("✓ Including configuration")
            items_to_backup.append("config")
        
        # Database
        if (self.install_dir / "umiagent.db").exists():
            print("✓ Including database")
            items_to_backup.append("umiagent.db")
        
        # Skills
        if (self.install_dir / "skills").exists():
            print("✓ Including skills")
            items_to_backup.append("skills")
        
        # Telegram bot
        if (self.install_dir / "telegram_bot").exists():
            print("✓ Including telegram bot")
            items_to_backup.append("telegram_bot")
        
        # Logs (optional)
        if include_logs and (self.install_dir / "logs").exists():
            print("✓ Including logs")
            items_to_backup.append("logs")
        
        # Launcher scripts
        for script in ["start_hermes.sh", "start_bot.sh", "inject_godmode.sh"]:
            if (self.install_dir / script).exists():
                items_to_backup.append(script)
        
        print(f"\n📦 Compressing...")
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                for item in items_to_backup:
                    item_path = self.install_dir / item
                    if item_path.exists():
                        tar.add(item_path, arcname=item)
            
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            
            print(f"\n✅ Backup created successfully!")
            print(f"   File: {backup_path}")
            print(f"   Size: {backup_size:.2f} MB")
            print(f"   Items: {len(items_to_backup)}")
            
            # Save backup metadata
            self._save_metadata(backup_name, items_to_backup, backup_size)
            
            return backup_path
            
        except Exception as e:
            print(f"\n❌ Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def list_backups(self):
        """List all available backups"""
        backups = sorted(self.backup_dir.glob("redmess_backup_*.tar.gz"))
        
        if not backups:
            print("📦 No backups found")
            return
        
        print(f"\n📦 Available Backups ({len(backups)})\n")
        print(f"{'#':<4} {'Filename':<35} {'Size':<12} {'Date':<20}")
        print("=" * 75)
        
        for idx, backup in enumerate(backups, 1):
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"{idx:<4} {backup.name:<35} {size_mb:>8.2f} MB  {date_str}")
        
        print()
    
    def restore_backup(self, backup_name, force=False):
        """Restore from backup"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_name}")
            return False
        
        print(f"🔄 Restoring from: {backup_name}")
        print(f"   Target: {self.install_dir}\n")
        
        if not force:
            response = input("⚠️  This will overwrite existing files. Continue? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled")
                return False
        
        try:
            # Extract backup
            print("📦 Extracting backup...")
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(self.install_dir)
            
            print("\n✅ Restore completed successfully!")
            print(f"   Restored to: {self.install_dir}")
            
            # Verify critical files
            print("\n🔍 Verifying restoration...")
            if (self.install_dir / "config/redmess.yaml").exists():
                print("   ✓ Configuration")
            if (self.install_dir / "umiagent.db").exists():
                print("   ✓ Database")
            if (self.install_dir / "skills").exists():
                print("   ✓ Skills")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Restore failed: {e}")
            return False
    
    def cleanup_old_backups(self, keep_last=7):
        """Remove old backups, keep only recent ones"""
        backups = sorted(self.backup_dir.glob("redmess_backup_*.tar.gz"))
        
        if len(backups) <= keep_last:
            print(f"📦 {len(backups)} backups found (keeping all)")
            return
        
        to_remove = backups[:-keep_last]
        
        print(f"🧹 Cleaning up old backups")
        print(f"   Total: {len(backups)}")
        print(f"   Keeping: {keep_last}")
        print(f"   Removing: {len(to_remove)}\n")
        
        total_size = 0
        for backup in to_remove:
            size = backup.stat().st_size
            total_size += size
            print(f"   Removing: {backup.name} ({size / (1024*1024):.2f} MB)")
            backup.unlink()
        
        print(f"\n✅ Cleanup complete")
        print(f"   Freed space: {total_size / (1024*1024):.2f} MB")
    
    def export_database(self):
        """Export database to SQL file"""
        db_path = self.install_dir / "umiagent.db"
        
        if not db_path.exists():
            print("❌ Database not found")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = self.backup_dir / f"database_export_{timestamp}.sql"
        
        print(f"📤 Exporting database to SQL...")
        print(f"   Source: {db_path}")
        print(f"   Destination: {export_path}\n")
        
        try:
            conn = sqlite3.connect(db_path)
            
            with open(export_path, 'w') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            
            conn.close()
            
            size_kb = export_path.stat().st_size / 1024
            
            print(f"✅ Database exported successfully!")
            print(f"   File: {export_path}")
            print(f"   Size: {size_kb:.2f} KB")
            
            return export_path
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None
    
    def _save_metadata(self, backup_name, items, size_mb):
        """Save backup metadata"""
        metadata_path = self.backup_dir / f"{backup_name}.meta"
        
        with open(metadata_path, 'w') as f:
            f.write(f"Backup: {backup_name}\n")
            f.write(f"Created: {datetime.now().isoformat()}\n")
            f.write(f"Size: {size_mb:.2f} MB\n")
            f.write(f"Items: {len(items)}\n")
            f.write(f"\nContents:\n")
            for item in items:
                f.write(f"  - {item}\n")

def print_help():
    print("""
🔥 RedMess Backup & Restore Manager - BRUTAL V3.0

Usage: python3 backup_manager.py <command> [options]

Commands:
  backup [--logs]          Create full backup
  list                     List all backups
  restore <backup_name>    Restore from backup
  cleanup [--keep N]       Remove old backups (default: keep 7)
  export-db                Export database to SQL file

Options:
  --logs                   Include logs in backup (default: skip)
  --keep N                 Number of backups to keep (default: 7)
  --force                  Skip confirmation prompts

Examples:
  # Create backup
  python3 backup_manager.py backup

  # Create backup with logs
  python3 backup_manager.py backup --logs

  # List backups
  python3 backup_manager.py list

  # Restore backup
  python3 backup_manager.py restore redmess_backup_20260904_134500.tar.gz

  # Cleanup old backups (keep last 5)
  python3 backup_manager.py cleanup --keep 5

  # Export database
  python3 backup_manager.py export-db

Backup Location:
  ~/.redmess/backups/

What Gets Backed Up:
  ✓ Configuration files (config/)
  ✓ Database (umiagent.db)
  ✓ Security skills (skills/)
  ✓ Telegram bot (telegram_bot/)
  ✓ Launcher scripts
  ✗ Logs (unless --logs specified)
  ✗ Workspace files (too large)
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = BackupManager()
    
    if command == "backup":
        include_logs = "--logs" in sys.argv
        manager.create_backup(include_logs=include_logs)
    
    elif command == "list":
        manager.list_backups()
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Error: backup name required")
            print("Usage: python3 backup_manager.py restore <backup_name>")
            print("\nRun 'python3 backup_manager.py list' to see available backups")
            sys.exit(1)
        
        backup_name = sys.argv[2]
        force = "--force" in sys.argv
        manager.restore_backup(backup_name, force=force)
    
    elif command == "cleanup":
        keep_count = 7
        if "--keep" in sys.argv:
            idx = sys.argv.index("--keep")
            if idx + 1 < len(sys.argv):
                keep_count = int(sys.argv[idx + 1])
        
        manager.cleanup_old_backups(keep_last=keep_count)
    
    elif command == "export-db":
        manager.export_database()
    
    elif command == "help" or command == "--help" or command == "-h":
        print_help()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python3 backup_manager.py help' for usage")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
