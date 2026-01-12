#!/usr/bin/env python3
"""
Agent Initialization Script
===========================
This script MUST be run at the start of every Claude session.
It consolidates all required context into a single briefing file.

Usage:
    ./venv/bin/python scripts/agent/init_agent.py

Output:
    AGENT_BRIEFING.md - Contains all context needed for the session
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
os.chdir(PROJECT_ROOT)

# Required files in order of priority
REQUIRED_FILES = [
    ("AGENT_CONTEXT_STATE.md", "Current state, last actions, TODO queue"),
    ("docs/AGENT_ONBOARDING.md", "Core rules and architecture"),
    ("docs/FOUNDER_QUOTES.md", "Philosophical foundation"),
]

OPTIONAL_FILES = [
    ("docs/ULTRATHINK_SYNTHESIS.md", "22 Masters framework"),
    ("docs/MASTERS_VERIFIED_SOURCES.md", "Verified quotes database"),
    ("dataland_proposal/WHATSAPP_LOG.md", "WhatsApp TODO/RESEARCH queue"),
]

def read_file_content(filepath):
    """Read file content, return None if not found"""
    full_path = PROJECT_ROOT / filepath
    if full_path.exists():
        try:
            return full_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"[ERROR READING FILE: {e}]"
    return None

def extract_section(content, section_name):
    """Extract a specific section from markdown content"""
    if not content:
        return None

    lines = content.split('\n')
    in_section = False
    section_lines = []

    for line in lines:
        if line.startswith('#') and section_name.lower() in line.lower():
            in_section = True
            section_lines.append(line)
        elif in_section:
            if line.startswith('#') and not line.startswith('###'):
                break
            section_lines.append(line)

    return '\n'.join(section_lines) if section_lines else None

def get_todo_queue(content):
    """Extract TODO items from AGENT_CONTEXT_STATE.md"""
    if not content:
        return []

    todos = []
    lines = content.split('\n')
    in_todo = False

    for line in lines:
        if 'TODO QUEUE' in line.upper():
            in_todo = True
        elif in_todo:
            if line.startswith('## ') and 'TODO' not in line.upper():
                break
            if '- [ ]' in line:
                todos.append(line.strip())

    return todos

def get_last_action(content):
    """Extract last action from AGENT_CONTEXT_STATE.md"""
    if not content:
        return None

    section = extract_section(content, "Last Action")
    return section

def get_founders_intent(content):
    """Extract founder intent captures"""
    if not content:
        return None

    section = extract_section(content, "Founder Intent")
    return section

def generate_briefing():
    """Generate consolidated agent briefing"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    briefing = f"""# AGENT BRIEFING
> **Generated**: {timestamp}
> **Session Start**: Read this file completely before doing ANY work.

---

## INITIALIZATION CHECKLIST

Before proceeding, confirm you understand:

- [ ] What was the last action completed?
- [ ] What is in the TODO queue?
- [ ] What are the current priorities?
- [ ] What founder intent should guide this session?

---

"""

    # Read AGENT_CONTEXT_STATE.md for current state
    context_state = read_file_content("AGENT_CONTEXT_STATE.md")

    if context_state:
        # Extract key sections
        last_action = get_last_action(context_state)
        todos = get_todo_queue(context_state)
        founders_intent = get_founders_intent(context_state)

        briefing += "## CURRENT STATE\n\n"

        if last_action:
            briefing += "### Last Action\n"
            briefing += last_action + "\n\n"

        if todos:
            briefing += "### TODO Queue\n"
            for todo in todos[:10]:  # Top 10 todos
                briefing += f"{todo}\n"
            briefing += "\n"

        if founders_intent:
            briefing += "### Founder Intent (This Session)\n"
            briefing += founders_intent + "\n\n"
    else:
        briefing += "## CURRENT STATE\n\n"
        briefing += "**WARNING**: AGENT_CONTEXT_STATE.md not found. Create it.\n\n"

    # Add architecture reminder
    briefing += """---

## ARCHITECTURE REMINDER

```
ARCHIV-IT (Umbrella)
├── DOC-8   - DATABASE & ARCHIVE (Foundation - current focus)
├── IT-R8   - CREATE & RATE (spatial design tool)
└── SOCI-8  - SHARE & CONNECT (future)
```

### 22 NORTHSTAR Masters
**Feminine (9)**: Hildegard, Gisel, Rand, Starhawk, Tori, Bjork, Swan, Hicks, Byrne
**Masculine (13)**: da Vinci, Tesla, Fuller, Jung, Suleyman, Grant, Prince, Coltrane, Bowie, Koe, Jobs, Cherny, Rene

### Physics Constants (SACRED)
```javascript
PHI = 1.618033988749895
GOLDEN_ANGLE = 137.5077640500378
SCHUMANN = 7.83
TESLA_PATTERN = [3, 6, 9]
```

---

## CRITICAL RULES

1. **Honor the Founder's Voice** - Preserve exact wording
2. **ultrathink = Deep comprehensive analysis**
3. **Local-first, cloud-optional**
4. **Balance polarity in all outputs** (PHI threshold)
5. **Update AGENT_CONTEXT_STATE.md before ending**

---

## SERVER COMMANDS

```bash
# Start server
KMP_DUPLICATE_LIB_OK=TRUE ./venv/bin/python scripts/interface/visual_browser.py

# Check server
curl -s http://localhost:5001/

# Run search
KMP_DUPLICATE_LIB_OK=TRUE python scripts/search/semantic_search.py "query"
```

---

## WHATSAPP QUEUE

Check `dataland_proposal/WHATSAPP_LOG.md` for entries tagged #TODO or #RESEARCH

"""

    # Check if WhatsApp log exists and has content
    whatsapp = read_file_content("dataland_proposal/WHATSAPP_LOG.md")
    if whatsapp:
        # Extract recent entries
        lines = whatsapp.split('\n')
        recent = []
        for line in lines[-50:]:  # Last 50 lines
            if '#TODO' in line or '#RESEARCH' in line:
                recent.append(line.strip())

        if recent:
            briefing += "### Recent WhatsApp Items\n"
            for item in recent[-5:]:
                briefing += f"- {item}\n"
            briefing += "\n"

    briefing += """---

## SESSION END PROTOCOL

Before ending this session, you MUST:

1. **Update AGENT_CONTEXT_STATE.md** with:
   - Last action completed
   - Files modified
   - Next steps identified

2. **Create backup** if significant work was done:
   ```bash
   mkdir -p backups/session_$(date +%Y-%m-%d)_description/
   git add -A && git commit -m "Session: [description]"
   ```

3. **Do NOT leave work in incomplete state** without documenting

---

*This briefing was auto-generated. For full context, read the source files.*
*Required: AGENT_CONTEXT_STATE.md, docs/AGENT_ONBOARDING.md, docs/FOUNDER_QUOTES.md*
"""

    return briefing

def validate_required_files():
    """Check if all required files exist"""
    missing = []
    for filepath, description in REQUIRED_FILES:
        if not (PROJECT_ROOT / filepath).exists():
            missing.append((filepath, description))
    return missing

def main():
    print("=" * 60)
    print("AGENT INITIALIZATION")
    print("=" * 60)
    print()

    # Check required files
    missing = validate_required_files()
    if missing:
        print("WARNING: Missing required files:")
        for filepath, description in missing:
            print(f"  - {filepath}: {description}")
        print()

    # Generate briefing
    briefing = generate_briefing()

    # Write briefing file
    briefing_path = PROJECT_ROOT / "AGENT_BRIEFING.md"
    briefing_path.write_text(briefing, encoding='utf-8')

    print(f"Generated: AGENT_BRIEFING.md")
    print()
    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print()
    print("1. READ AGENT_BRIEFING.md completely")
    print("2. Verify you understand the current state")
    print("3. Check TODO queue for pending tasks")
    print("4. Ask user for clarification if needed")
    print()

    # Show quick summary
    context = read_file_content("AGENT_CONTEXT_STATE.md")
    if context:
        todos = get_todo_queue(context)
        print(f"TODO Items: {len(todos)}")
        if todos:
            print("Top 3 TODOs:")
            for todo in todos[:3]:
                print(f"  {todo}")

    print()
    print("=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
