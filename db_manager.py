#!/usr/bin/env python3
"""
RedMess Database Manager
Manage users, authorizations, and rental system
Version: BRUTAL V3.0
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Database path
DB_PATH = os.path.expanduser("~/.redmess/umiagent.db")

class DatabaseManager:
    def __init__(self):
        if not Path(DB_PATH).exists():
            print(f"❌ Database not found: {DB_PATH}")
            print("Run setup.sh or install.sh first")
            sys.exit(1)
        
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def list_authorized_users(self):
        """List all authorized GODMODE users"""
        print("\n🔥 GODMODE Authorized Users\n")
        print(f"{'User ID':<15} {'Tier':<20} {'Authorized At':<25} {'Expires':<25}")
        print("=" * 90)
        
        self.cursor.execute("""
            SELECT user_id, tier, authorized_at, expires_at, notes
            FROM godmode_auth
            ORDER BY authorized_at DESC
        """)
        
        rows = self.cursor.fetchall()
        
        if not rows:
            print("No authorized users found")
            return
        
        for row in rows:
            user_id, tier, auth_at, expires_at, notes = row
            expires_str = expires_at if expires_at else "Never"
            print(f"{user_id:<15} {tier:<20} {auth_at:<25} {expires_str:<25}")
            if notes:
                print(f"  └─ Note: {notes}")
        
        print(f"\nTotal: {len(rows)} users")
    
    def add_user(self, user_id, tier="GODMODE_BRUTAL", duration_hours=None, notes=None):
        """Add authorized user"""
        expires_at = None
        if duration_hours:
            expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO godmode_auth 
                (user_id, tier, authorized_at, expires_at, notes)
                VALUES (?, ?, datetime('now'), ?, ?)
            """, (user_id, tier, expires_at, notes))
            
            self.conn.commit()
            
            print(f"\n✅ User {user_id} authorized")
            print(f"   Tier: {tier}")
            if expires_at:
                print(f"   Expires: {expires_at}")
            print(f"   Status: GODMODE ACTIVE")
            
        except Exception as e:
            print(f"❌ Error adding user: {e}")
    
    def remove_user(self, user_id):
        """Remove authorized user"""
        self.cursor.execute("DELETE FROM godmode_auth WHERE user_id = ?", (user_id,))
        
        if self.cursor.rowcount > 0:
            self.conn.commit()
            print(f"\n✅ User {user_id} removed from GODMODE")
        else:
            print(f"\n❌ User {user_id} not found")
    
    def check_user(self, user_id):
        """Check user authorization status"""
        self.cursor.execute("""
            SELECT tier, authorized_at, expires_at, notes
            FROM godmode_auth
            WHERE user_id = ?
        """, (user_id,))
        
        row = self.cursor.fetchone()
        
        if not row:
            print(f"\n❌ User {user_id} is NOT authorized")
            return
        
        tier, auth_at, expires_at, notes = row
        
        print(f"\n✅ User {user_id} Authorization Status")
        print(f"   Tier: {tier}")
        print(f"   Authorized: {auth_at}")
        print(f"   Expires: {expires_at if expires_at else 'Never'}")
        if notes:
            print(f"   Notes: {notes}")
        
        # Check if expired
        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at)
            if expires_dt < datetime.now():
                print(f"\n⚠️  EXPIRED!")
            else:
                remaining = expires_dt - datetime.now()
                hours = remaining.total_seconds() / 3600
                print(f"\n⏰ Time remaining: {hours:.1f} hours")
    
    def cleanup_expired(self):
        """Remove expired authorizations"""
        self.cursor.execute("""
            DELETE FROM godmode_auth
            WHERE expires_at IS NOT NULL
            AND datetime(expires_at) < datetime('now')
        """)
        
        removed = self.cursor.rowcount
        self.conn.commit()
        
        print(f"\n🧹 Cleanup complete: {removed} expired users removed")
    
    def list_rentals(self):
        """List active rentals"""
        print("\n💰 Active Rentals\n")
        print(f"{'User ID':<15} {'Tier':<20} {'Started':<25} {'Expires':<25} {'Amount':<10}")
        print("=" * 100)
        
        self.cursor.execute("""
            SELECT user_id, tier, started_at, expires_at, payment_amount, payment_method
            FROM rentals
            WHERE is_active = 1
            ORDER BY expires_at ASC
        """)
        
        rows = self.cursor.fetchall()
        
        if not rows:
            print("No active rentals")
            return
        
        for row in rows:
            user_id, tier, started, expires, amount, method = row
            print(f"{user_id:<15} {tier:<20} {started:<25} {expires:<25} Rp {amount or 0:<10,}")
            
            # Check if expiring soon
            expires_dt = datetime.fromisoformat(expires)
            remaining = expires_dt - datetime.now()
            if remaining.total_seconds() < 7200:  # Less than 2 hours
                print(f"  ⚠️  Expiring soon! ({remaining.total_seconds()/3600:.1f} hours)")
        
        print(f"\nTotal: {len(rows)} active rentals")
    
    def usage_stats(self):
        """Show usage statistics"""
        print("\n📊 Usage Statistics\n")
        
        # Total authorized users
        self.cursor.execute("SELECT COUNT(*) FROM godmode_auth")
        total_users = self.cursor.fetchone()[0]
        print(f"Total authorized users: {total_users}")
        
        # By tier
        self.cursor.execute("""
            SELECT tier, COUNT(*) as count
            FROM godmode_auth
            GROUP BY tier
            ORDER BY count DESC
        """)
        print("\nBy tier:")
        for tier, count in self.cursor.fetchall():
            print(f"  {tier}: {count}")
        
        # Recent activity
        self.cursor.execute("""
            SELECT COUNT(*) FROM usage_logs
            WHERE timestamp > datetime('now', '-24 hours')
        """)
        recent_commands = self.cursor.fetchone()[0]
        print(f"\nCommands in last 24h: {recent_commands}")
        
        # Active rentals
        self.cursor.execute("SELECT COUNT(*) FROM rentals WHERE is_active = 1")
        active_rentals = self.cursor.fetchone()[0]
        print(f"Active rentals: {active_rentals}")

def print_help():
    print("""
🔥 RedMess Database Manager - BRUTAL V3.0

Usage: python3 db_manager.py <command> [options]

Commands:
  list                     List all authorized users
  add <user_id> [options]  Add user to GODMODE
  remove <user_id>         Remove user from GODMODE
  check <user_id>          Check user authorization status
  cleanup                  Remove expired authorizations
  rentals                  List active rentals
  stats                    Show usage statistics

Add Options:
  --tier <tier>            Authorization tier (default: GODMODE_BRUTAL)
  --hours <hours>          Duration in hours (default: permanent)
  --notes <text>           Additional notes

Tiers:
  PRIMARY_OWNER           Full unrestricted access (permanent)
  GODMODE_BRUTAL          Full GODMODE, no limits
  GODMODE_STANDARD        GODMODE with OPSEC warnings
  RENTAL_USER             Time-limited access
  STANDARD_USER           Safety filters active

Examples:
  # List all users
  python3 db_manager.py list

  # Add user permanently
  python3 db_manager.py add 123456789 --tier GODMODE_BRUTAL

  # Add user for 24 hours
  python3 db_manager.py add 123456789 --hours 24 --notes "Trial user"

  # Check user status
  python3 db_manager.py check 123456789

  # Remove user
  python3 db_manager.py remove 123456789

  # Cleanup expired
  python3 db_manager.py cleanup

  # Show statistics
  python3 db_manager.py stats
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    with DatabaseManager() as db:
        if command == "list":
            db.list_authorized_users()
        
        elif command == "add":
            if len(sys.argv) < 3:
                print("❌ Error: user_id required")
                print("Usage: python3 db_manager.py add <user_id> [--tier TIER] [--hours HOURS] [--notes TEXT]")
                sys.exit(1)
            
            user_id = int(sys.argv[2])
            tier = "GODMODE_BRUTAL"
            duration = None
            notes = None
            
            # Parse options
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--tier" and i + 1 < len(sys.argv):
                    tier = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--hours" and i + 1 < len(sys.argv):
                    duration = int(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == "--notes" and i + 1 < len(sys.argv):
                    notes = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            db.add_user(user_id, tier, duration, notes)
        
        elif command == "remove":
            if len(sys.argv) < 3:
                print("❌ Error: user_id required")
                print("Usage: python3 db_manager.py remove <user_id>")
                sys.exit(1)
            
            user_id = int(sys.argv[2])
            db.remove_user(user_id)
        
        elif command == "check":
            if len(sys.argv) < 3:
                print("❌ Error: user_id required")
                print("Usage: python3 db_manager.py check <user_id>")
                sys.exit(1)
            
            user_id = int(sys.argv[2])
            db.check_user(user_id)
        
        elif command == "cleanup":
            db.cleanup_expired()
        
        elif command == "rentals":
            db.list_rentals()
        
        elif command == "stats":
            db.usage_stats()
        
        elif command == "help" or command == "--help" or command == "-h":
            print_help()
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Run 'python3 db_manager.py help' for usage")
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
