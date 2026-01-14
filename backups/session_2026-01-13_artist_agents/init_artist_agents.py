#!/usr/bin/env python3
"""
Artist Agent Initialization & Recovery Script
==============================================

CRASH-PROOF RECOVERY SYSTEM

This script ensures artist agents can be rebuilt from scratch even if:
- Claude resets completely
- The system crashes
- Context is lost
- Session ends unexpectedly

IMPORTANT: Always read ARTIST_RIGHTS_NOTICE.md before using any artist data.
Artists' actual works are NEVER to be reproduced - only their techniques taught.

Usage:
    ./venv/bin/python scripts/agents/init_artist_agents.py
    ./venv/bin/python scripts/agents/init_artist_agents.py --verify
    ./venv/bin/python scripts/agents/init_artist_agents.py --list
    ./venv/bin/python scripts/agents/init_artist_agents.py --agent hildegard
    ./venv/bin/python scripts/agents/init_artist_agents.py --research tesla
    ./venv/bin/python scripts/agents/init_artist_agents.py --add-artist

Output:
    ARTIST_AGENT_BRIEFING.md - Contains all artist context for the session
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
os.chdir(PROJECT_ROOT)

# Critical files
ARTIST_AGENTS_FILE = PROJECT_ROOT / "scripts/agents/ARTIST_AGENTS.json"
RIGHTS_NOTICE_FILE = PROJECT_ROOT / "scripts/agents/ARTIST_RIGHTS_NOTICE.md"
OUTPUT_BRIEFING = PROJECT_ROOT / "ARTIST_AGENT_BRIEFING.md"


def load_artist_agents() -> Dict:
    """Load the artist agents registry"""
    if not ARTIST_AGENTS_FILE.exists():
        print(f"ERROR: {ARTIST_AGENTS_FILE} not found!")
        print("This file is critical for artist agent recovery.")
        sys.exit(1)

    with open(ARTIST_AGENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_rights_notice() -> bool:
    """Verify the rights notice exists and is readable"""
    if not RIGHTS_NOTICE_FILE.exists():
        print(f"WARNING: {RIGHTS_NOTICE_FILE} not found!")
        print("Artist rights protections may not be enforced.")
        return False

    content = RIGHTS_NOTICE_FILE.read_text(encoding='utf-8')
    required_sections = [
        "SACRED COVENANT",
        "WHAT IS PROTECTED",
        "WHAT IS SHARED",
        "OPT-IN EXCEPTION",
        "ENFORCEMENT PROTOCOL"
    ]

    missing = [s for s in required_sections if s not in content]
    if missing:
        print(f"WARNING: Rights notice missing sections: {missing}")
        return False

    return True


def get_all_artists(data: Dict) -> List[Dict]:
    """Get all artist profiles from both feminine and masculine categories"""
    artists = []
    if "agents" in data:
        artists.extend(data["agents"].get("feminine", []))
        artists.extend(data["agents"].get("masculine", []))
    return artists


def get_artist_by_id(data: Dict, artist_id: str) -> Optional[Dict]:
    """Find a specific artist by their ID"""
    for artist in get_all_artists(data):
        if artist.get("id") == artist_id.lower():
            return artist
    return None


def list_all_artists(data: Dict):
    """List all registered artists"""
    print("\n" + "=" * 60)
    print("REGISTERED ARTIST AGENTS")
    print("=" * 60)

    feminine = data.get("agents", {}).get("feminine", [])
    masculine = data.get("agents", {}).get("masculine", [])

    print(f"\nFeminine Energy ({len(feminine)} artists):")
    print("-" * 40)
    for artist in feminine:
        print(f"  /artist-{artist['id']:12} - {artist['name']} ({artist['era']})")
        print(f"                   Domain: {artist['domain']}")

    print(f"\nMasculine Energy ({len(masculine)} artists):")
    print("-" * 40)
    for artist in masculine:
        print(f"  /artist-{artist['id']:12} - {artist['name']} ({artist['era']})")
        print(f"                   Domain: {artist['domain']}")

    print(f"\nTotal: {len(feminine) + len(masculine)} artist agents")
    print("=" * 60)


def show_artist_profile(artist: Dict):
    """Display a full artist profile"""
    print("\n" + "=" * 60)
    print(f"ARTIST AGENT: {artist['name']}")
    print("=" * 60)

    print(f"\nSkill Command: {artist['skill_command']}")
    print(f"Polarity: {artist['polarity'].upper()}")
    print(f"Era: {artist['era']}")
    print(f"Domain: {artist['domain']}")
    print(f"Opt-in Status: {artist['opt_in_status']}")

    print("\n--- TECHNIQUES (Teachable) ---")
    for i, tech in enumerate(artist.get('techniques', []), 1):
        print(f"  {i}. {tech}")

    print("\n--- PHILOSOPHIES ---")
    for i, phil in enumerate(artist.get('philosophies', []), 1):
        print(f"  {i}. {phil}")

    print("\n--- VERIFIED QUOTES ---")
    for quote_data in artist.get('verified_quotes', []):
        print(f'  "{quote_data["quote"]}"')
        print(f"    - {quote_data['source']} ({quote_data['year']})")

    print("\n--- TEACHING POINTS ---")
    for i, point in enumerate(artist.get('teaching_points', []), 1):
        print(f"  {i}. {point}")

    print("\n--- CROSS-REFERENCES ---")
    refs = artist.get('cross_references', [])
    print(f"  Related masters: {', '.join(refs) if refs else 'None'}")

    print("\n--- RESEARCH URLS ---")
    for url in artist.get('research_urls', []):
        print(f"  - {url}")

    print("\n" + "=" * 60)


def generate_research_report(artist: Dict):
    """Generate a research update report for an artist"""
    print("\n" + "=" * 60)
    print(f"RESEARCH UPDATE: {artist['name']}")
    print("=" * 60)

    print(f"\nTo maintain relevance for this artist agent, research these URLs:")
    for url in artist.get('research_urls', []):
        print(f"  - {url}")

    print("\nResearch focus areas:")
    print("  1. New verified quotes or interviews")
    print("  2. Updated techniques or methodologies")
    print("  3. Recent publications or releases")
    print("  4. Cross-references with other masters")
    print("  5. Community discussions of their work")

    print("\nREMINDER: Only extract techniques and philosophies.")
    print("          NEVER reproduce their actual artwork.")

    print("\n" + "=" * 60)


def add_artist_wizard():
    """Interactive wizard for adding a new artist"""
    print("\n" + "=" * 60)
    print("ADD NEW ARTIST AGENT")
    print("=" * 60)
    print("\nBefore proceeding, ensure you have read:")
    print("  - scripts/agents/ARTIST_RIGHTS_NOTICE.md")
    print("\nNew artist checklist:")
    print("  [ ] All quotes verified from primary sources")
    print("  [ ] Techniques extracted WITHOUT reproducing art")
    print("  [ ] Added to honor roll in ARTIST_RIGHTS_NOTICE.md")
    print("  [ ] Cross-references documented")
    print()

    template = {
        "id": "lowercase_identifier",
        "name": "Full Display Name",
        "polarity": "feminine | masculine",
        "era": "birth-death | Contemporary",
        "domain": "Primary expertise area",
        "techniques": [
            "Technique 1 - description",
            "Technique 2 - description",
            "Technique 3 - description",
            "Technique 4 - description",
            "Technique 5 - description"
        ],
        "philosophies": [
            "Philosophy 1",
            "Philosophy 2",
            "Philosophy 3",
            "Philosophy 4",
            "Philosophy 5"
        ],
        "verified_quotes": [
            {"quote": "Exact quote text", "source": "Source name", "year": "YYYY"}
        ],
        "teaching_points": [
            "What users can learn 1",
            "What users can learn 2",
            "What users can learn 3",
            "What users can learn 4"
        ],
        "research_urls": [
            "https://official-website.com",
            "https://reference-site.com"
        ],
        "cross_references": ["related_master_1", "related_master_2"],
        "skill_command": "/artist-{id}",
        "opt_in_status": "none"
    }

    print("JSON template for new artist:")
    print("-" * 40)
    print(json.dumps(template, indent=2))
    print("-" * 40)
    print("\nAdd this to scripts/agents/ARTIST_AGENTS.json")
    print("under agents.feminine or agents.masculine")
    print("\n" + "=" * 60)


def generate_briefing(data: Dict) -> str:
    """Generate a complete artist agent briefing"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    artists = get_all_artists(data)

    briefing = f"""# ARTIST AGENT BRIEFING
> **Generated**: {timestamp}
> **Total Artists**: {len(artists)}
> **Schema Version**: {data.get('metadata', {}).get('schema_version', 'unknown')}

---

## CRITICAL NOTICE

**READ FIRST**: scripts/agents/ARTIST_RIGHTS_NOTICE.md

These agents teach artist TECHNIQUES and PHILOSOPHIES.
They do NOT and MUST NOT reproduce artist ARTWORK.

---

## RECOVERY PROTOCOL

If Claude has reset, follow these steps:

1. Read this file completely
2. Read scripts/agents/ARTIST_RIGHTS_NOTICE.md
3. Artist agents can be rebuilt from scripts/agents/ARTIST_AGENTS.json
4. Honor all artist protections
5. Teach techniques, never reproduce art

---

## AVAILABLE ARTIST AGENTS

"""

    # Feminine artists
    feminine = data.get("agents", {}).get("feminine", [])
    briefing += f"### Feminine Energy ({len(feminine)} agents)\n\n"
    for artist in feminine:
        briefing += f"**{artist['skill_command']}** - {artist['name']}\n"
        briefing += f"- Domain: {artist['domain']}\n"
        briefing += f"- Era: {artist['era']}\n"
        briefing += f"- Key technique: {artist['techniques'][0] if artist['techniques'] else 'N/A'}\n\n"

    # Masculine artists
    masculine = data.get("agents", {}).get("masculine", [])
    briefing += f"### Masculine Energy ({len(masculine)} agents)\n\n"
    for artist in masculine:
        briefing += f"**{artist['skill_command']}** - {artist['name']}\n"
        briefing += f"- Domain: {artist['domain']}\n"
        briefing += f"- Era: {artist['era']}\n"
        briefing += f"- Key technique: {artist['techniques'][0] if artist['techniques'] else 'N/A'}\n\n"

    # Quick reference
    briefing += """---

## QUICK REFERENCE

### To invoke an artist agent:
```
/artist-{name}
```

### To get full profile:
```bash
./venv/bin/python scripts/agents/init_artist_agents.py --agent {name}
```

### To research updates:
```bash
./venv/bin/python scripts/agents/init_artist_agents.py --research {name}
```

### To add new artist:
```bash
./venv/bin/python scripts/agents/init_artist_agents.py --add-artist
```

---

## ENFORCEMENT REMINDER

Before generating any content inspired by an artist:
1. Ask: "Am I teaching their technique, or reproducing their art?"
2. If reproducing: **STOP. DO NOT PROCEED.**
3. If teaching: Proceed with proper attribution

---

*This briefing was auto-generated from scripts/agents/ARTIST_AGENTS.json*
*For complete profiles, run with --agent {name}*
"""

    return briefing


def verify_all_artists(data: Dict) -> bool:
    """Verify all artist profiles are complete"""
    print("\n" + "=" * 60)
    print("ARTIST AGENT VERIFICATION")
    print("=" * 60)

    required_fields = [
        'id', 'name', 'polarity', 'era', 'domain',
        'techniques', 'philosophies', 'verified_quotes',
        'teaching_points', 'research_urls', 'skill_command'
    ]

    all_valid = True
    artists = get_all_artists(data)

    for artist in artists:
        missing = [f for f in required_fields if f not in artist or not artist[f]]
        if missing:
            print(f"\n  WARNING: {artist.get('name', 'Unknown')} missing: {missing}")
            all_valid = False
        else:
            print(f"  ✓ {artist['name']} - Complete")

    # Verify rights notice
    print("\n--- Rights Notice ---")
    if verify_rights_notice():
        print("  ✓ ARTIST_RIGHTS_NOTICE.md - Valid")
    else:
        print("  ✗ ARTIST_RIGHTS_NOTICE.md - Issues detected")
        all_valid = False

    print("\n" + "-" * 40)
    if all_valid:
        print("All artist agents verified successfully!")
    else:
        print("Some issues detected - please review above.")
    print("=" * 60)

    return all_valid


def main():
    parser = argparse.ArgumentParser(
        description="Artist Agent Initialization & Recovery Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python init_artist_agents.py            # Generate briefing
  python init_artist_agents.py --list     # List all artists
  python init_artist_agents.py --verify   # Verify all profiles
  python init_artist_agents.py --agent tesla  # Show Tesla's profile
  python init_artist_agents.py --research bjork  # Research updates for Bjork
  python init_artist_agents.py --add-artist  # Add new artist wizard
        """
    )

    parser.add_argument('--list', action='store_true', help='List all registered artists')
    parser.add_argument('--verify', action='store_true', help='Verify all artist profiles')
    parser.add_argument('--agent', type=str, help='Show specific artist profile')
    parser.add_argument('--research', type=str, help='Generate research report for artist')
    parser.add_argument('--add-artist', action='store_true', help='Show template for adding new artist')

    args = parser.parse_args()

    # Load data
    data = load_artist_agents()

    # Handle specific commands
    if args.list:
        list_all_artists(data)
        return 0

    if args.verify:
        success = verify_all_artists(data)
        return 0 if success else 1

    if args.agent:
        artist = get_artist_by_id(data, args.agent)
        if artist:
            show_artist_profile(artist)
        else:
            print(f"Artist '{args.agent}' not found. Use --list to see all artists.")
            return 1
        return 0

    if args.research:
        artist = get_artist_by_id(data, args.research)
        if artist:
            generate_research_report(artist)
        else:
            print(f"Artist '{args.research}' not found. Use --list to see all artists.")
            return 1
        return 0

    if args.add_artist:
        add_artist_wizard()
        return 0

    # Default: generate briefing
    print("=" * 60)
    print("ARTIST AGENT INITIALIZATION")
    print("=" * 60)
    print()

    # Verify rights notice first
    if not verify_rights_notice():
        print("\nWARNING: Rights notice has issues. Please review.")

    # Generate briefing
    briefing = generate_briefing(data)
    OUTPUT_BRIEFING.write_text(briefing, encoding='utf-8')

    print(f"Generated: {OUTPUT_BRIEFING}")
    print()

    # Summary
    artists = get_all_artists(data)
    feminine = data.get("agents", {}).get("feminine", [])
    masculine = data.get("agents", {}).get("masculine", [])

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total Artists: {len(artists)}")
    print(f"  Feminine: {len(feminine)}")
    print(f"  Masculine: {len(masculine)}")
    print()
    print("Commands:")
    print(f"  --list        List all artists")
    print(f"  --verify      Verify all profiles")
    print(f"  --agent NAME  Show specific profile")
    print(f"  --research NAME  Research update report")
    print(f"  --add-artist  Template for new artist")
    print()
    print("=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
