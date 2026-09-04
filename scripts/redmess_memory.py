#!/usr/bin/env python3
"""
RedMess Memory System - Anti-Pikun
Ingat conversation history, skill usage patterns, dan user preferences
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

MEMORY_FILE = Path.home() / ".hermes/profiles/umi3/redmess_memory.json"
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

class RedMessMemory:
    def __init__(self):
        self.load()
    
    def load(self):
        """Load memory from disk"""
        if MEMORY_FILE.exists():
            self.data = json.loads(MEMORY_FILE.read_text())
        else:
            self.data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "conversations": [],
                "skill_usage": {},
                "user_patterns": {
                    "common_tasks": [],
                    "favorite_tools": [],
                    "typical_targets": [],
                    "preferred_categories": []
                },
                "context": {
                    "current_target": None,
                    "active_skills": [],
                    "session_notes": []
                }
            }
    
    def save(self):
        """Save memory to disk"""
        self.data["last_updated"] = datetime.now().isoformat()
        MEMORY_FILE.write_text(json.dumps(self.data, indent=2, default=str))
    
    def add_conversation(self, user_request, skills_loaded, outcome=None):
        """Record conversation"""
        conv = {
            "timestamp": datetime.now().isoformat(),
            "request": user_request[:300],  # First 300 chars
            "skills_loaded": skills_loaded,
            "outcome": outcome
        }
        
        self.data["conversations"].append(conv)
        
        # Keep last 100 conversations
        self.data["conversations"] = self.data["conversations"][-100:]
        
        # Update skill usage stats
        for skill in skills_loaded:
            skill_name = skill if isinstance(skill, str) else skill.get("skill", "")
            self.data["skill_usage"][skill_name] = self.data["skill_usage"].get(skill_name, 0) + 1
        
        self.save()
    
    def get_frequent_skills(self, limit=5):
        """Get most frequently used skills"""
        sorted_skills = sorted(
            self.data["skill_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_skills[:limit]
    
    def get_recent_context(self, hours=24):
        """Get recent conversation context"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for conv in reversed(self.data["conversations"]):
            conv_time = datetime.fromisoformat(conv["timestamp"])
            if conv_time > cutoff:
                recent.append(conv)
            else:
                break
        
        return list(reversed(recent))
    
    def detect_patterns(self):
        """Analyze usage patterns"""
        if len(self.data["conversations"]) < 5:
            return None
        
        # Analyze last 20 conversations
        recent = self.data["conversations"][-20:]
        
        # Extract keywords from requests
        all_words = []
        for conv in recent:
            words = conv["request"].lower().split()
            all_words.extend([w for w in words if len(w) > 4])  # Words > 4 chars
        
        # Most common words = user interests
        word_freq = Counter(all_words)
        common_keywords = [w for w, c in word_freq.most_common(10)]
        
        # Most used categories
        categories = []
        for conv in recent:
            for skill in conv.get("skills_loaded", []):
                skill_path = skill if isinstance(skill, str) else skill.get("skill", "")
                if "/" in skill_path:
                    cat = skill_path.split("/")[0]
                    categories.append(cat)
        
        cat_freq = Counter(categories)
        common_cats = [c for c, _ in cat_freq.most_common(5)]
        
        return {
            "common_keywords": common_keywords,
            "preferred_categories": common_cats,
            "total_sessions": len(self.data["conversations"]),
            "skills_tried": len(self.data["skill_usage"])
        }
    
    def set_context(self, target=None, notes=None):
        """Set current session context"""
        if target:
            self.data["context"]["current_target"] = target
        
        if notes:
            self.data["context"]["session_notes"].append({
                "timestamp": datetime.now().isoformat(),
                "note": notes
            })
            # Keep last 20 notes
            self.data["context"]["session_notes"] = self.data["context"]["session_notes"][-20:]
        
        self.save()
    
    def get_context(self):
        """Get current session context"""
        return self.data["context"]
    
    def suggest_next_skills(self, current_skills):
        """Suggest next skills based on patterns"""
        # Find conversations with similar skills
        similar_convs = []
        
        for conv in self.data["conversations"]:
            conv_skills = [s if isinstance(s, str) else s.get("skill", "") 
                          for s in conv.get("skills_loaded", [])]
            
            # Check overlap
            overlap = set(current_skills) & set(conv_skills)
            if overlap:
                similar_convs.append(conv)
        
        # What did user do next in those conversations?
        next_skills = []
        for i, conv in enumerate(self.data["conversations"]):
            if conv in similar_convs and i + 1 < len(self.data["conversations"]):
                next_conv = self.data["conversations"][i + 1]
                next_skills.extend(next_conv.get("skills_loaded", []))
        
        # Count frequency
        skill_names = [s if isinstance(s, str) else s.get("skill", "") for s in next_skills]
        freq = Counter(skill_names)
        
        return [skill for skill, _ in freq.most_common(3)]
    
    def summarize(self):
        """Generate memory summary"""
        patterns = self.detect_patterns()
        freq_skills = self.get_frequent_skills(5)
        recent = self.get_recent_context(24)
        
        summary = f"""
RedMess Memory Summary
{'='*60}

Total Conversations: {len(self.data['conversations'])}
Skills Tracked: {len(self.data['skill_usage'])}
Last 24h Activity: {len(recent)} conversations

Most Used Skills:
"""
        for skill, count in freq_skills:
            summary += f"  • {skill} ({count}x)\n"
        
        if patterns:
            summary += f"""
User Patterns Detected:
  • Common Keywords: {', '.join(patterns['common_keywords'][:5])}
  • Preferred Categories: {', '.join(patterns['preferred_categories'][:3])}
"""
        
        ctx = self.get_context()
        if ctx.get("current_target"):
            summary += f"\nCurrent Target: {ctx['current_target']}\n"
        
        if ctx.get("session_notes"):
            summary += f"\nRecent Notes:\n"
            for note in ctx["session_notes"][-3:]:
                summary += f"  • [{note['timestamp'][:10]}] {note['note'][:80]}\n"
        
        summary += f"\n{'='*60}\n"
        
        return summary

def main():
    import sys
    
    memory = RedMessMemory()
    
    if len(sys.argv) < 2:
        print(memory.summarize())
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "summary":
        print(memory.summarize())
    
    elif command == "patterns":
        patterns = memory.detect_patterns()
        if patterns:
            print(json.dumps(patterns, indent=2))
        else:
            print("Not enough data to detect patterns (need 5+ conversations)")
    
    elif command == "frequent":
        skills = memory.get_frequent_skills(10)
        print("Most Frequently Used Skills:\n")
        for skill, count in skills:
            print(f"  {count:3d}x  {skill}")
    
    elif command == "context":
        ctx = memory.get_context()
        print(json.dumps(ctx, indent=2))
    
    elif command == "recent":
        recent = memory.get_recent_context(24)
        print(f"Last 24h Activity ({len(recent)} conversations):\n")
        for conv in recent:
            print(f"[{conv['timestamp'][:16]}] {conv['request'][:80]}")
            if conv.get("skills_loaded"):
                print(f"  Skills: {', '.join([s if isinstance(s, str) else s.get('skill', '') for s in conv['skills_loaded'][:3]])}")
            print()
    
    elif command == "reset":
        memory.data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "conversations": [],
            "skill_usage": {},
            "user_patterns": {},
            "context": {}
        }
        memory.save()
        print("[+] Memory reset")
    
    else:
        print(f"Unknown command: {command}")
        print("Usage: redmess-memory [summary|patterns|frequent|context|recent|reset]")

if __name__ == "__main__":
    main()
