#!/usr/bin/env python3
"""
Generate Beta Tester License
Creates hardware-bound license keys for testers
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.protection.license_manager import LicenseManager


def generate_tester_license(tester_name: str, duration_days: int = 90):
    """Generate a beta tester license"""
    lm = LicenseManager()

    print("=" * 70)
    print("ARCHIV-IT - Beta Tester License Generator")
    print("=" * 70)
    print(f"\nTester Name: {tester_name}")
    print(f"Duration: {duration_days} days")
    print(f"Hardware ID: {lm.hardware_id}")
    print("\n" + "-" * 70)

    # Generate license
    license_data = lm.generate_license(
        customer_name=tester_name,
        tier="beta",
        duration_days=duration_days
    )

    # Save to current directory
    lm.save_license(license_data)

    print("\n" + "=" * 70)
    print("IMPORTANT INSTRUCTIONS FOR TESTER")
    print("=" * 70)
    print("\n1. Copy 'license.key' to the root of the ARCHIV-IT folder")
    print("2. Run the application using: python start_protected.py")
    print("3. DO NOT share your license key - it's hardware-bound")
    print("4. DO NOT share the source code or redistribute the software")
    print("\nThis license is valid ONLY on this specific machine.")
    print(f"Hardware ID: {lm.hardware_id[:16]}...")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_tester_license.py <tester_name> [duration_days]")
        print("\nExample:")
        print("  python generate_tester_license.py 'John Doe' 90")
        sys.exit(1)

    tester_name = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    generate_tester_license(tester_name, duration)
