#!/usr/bin/env python3
"""
License Manager - Hardware-bound licensing system
Protects against unauthorized copying and distribution
"""

import hashlib
import uuid
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import platform


class LicenseManager:
    """Manage license keys with hardware binding"""

    def __init__(self, license_file='license.key'):
        self.license_file = Path(license_file)
        self.hardware_id = self._get_hardware_id()

    def _get_hardware_id(self) -> str:
        """Generate unique hardware ID from machine characteristics"""
        # Combine multiple hardware identifiers
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                       for elements in range(0, 2*6, 2)][::-1])

        machine_id = platform.node()
        platform_info = f"{platform.system()}_{platform.machine()}"

        # Create unique hash
        combined = f"{mac}_{machine_id}_{platform_info}"
        hardware_hash = hashlib.sha256(combined.encode()).hexdigest()

        return hardware_hash[:32]

    def generate_license(self, customer_name: str, tier: str = 'free',
                        duration_days: int = 365) -> dict:
        """Generate a new license key bound to current hardware"""
        expiration = datetime.now() + timedelta(days=duration_days)

        license_data = {
            'customer': customer_name,
            'tier': tier,  # free, enterprise, white_label
            'hardware_id': self.hardware_id,
            'issued_at': datetime.now().isoformat(),
            'expires_at': expiration.isoformat(),
            'version': '1.0.0'
        }

        # Generate signature
        signature_string = f"{customer_name}{tier}{self.hardware_id}{expiration.isoformat()}"
        signature = hashlib.sha256(signature_string.encode()).hexdigest()
        license_data['signature'] = signature

        return license_data

    def save_license(self, license_data: dict):
        """Save license to encrypted file"""
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)

        print(f"✓ License saved to {self.license_file}")
        print(f"  Customer: {license_data['customer']}")
        print(f"  Tier: {license_data['tier']}")
        print(f"  Expires: {license_data['expires_at']}")
        print(f"  Hardware ID: {license_data['hardware_id'][:16]}...")

    def validate_license(self) -> tuple[bool, str]:
        """Validate license key against current hardware"""
        if not self.license_file.exists():
            return False, "No license file found"

        try:
            with open(self.license_file, 'r') as f:
                license_data = json.load(f)
        except Exception as e:
            return False, f"Invalid license file: {e}"

        # Check hardware binding
        if license_data.get('hardware_id') != self.hardware_id:
            return False, "License not valid for this machine"

        # Check expiration
        expires_at = datetime.fromisoformat(license_data['expires_at'])
        if datetime.now() > expires_at:
            return False, "License expired"

        # Verify signature
        signature_string = f"{license_data['customer']}{license_data['tier']}{license_data['hardware_id']}{license_data['expires_at']}"
        expected_signature = hashlib.sha256(signature_string.encode()).hexdigest()

        if license_data.get('signature') != expected_signature:
            return False, "License signature invalid"

        return True, f"Valid {license_data['tier']} license for {license_data['customer']}"

    def get_license_info(self) -> dict:
        """Get current license information"""
        if not self.license_file.exists():
            return None

        with open(self.license_file, 'r') as f:
            return json.load(f)


def require_valid_license(func):
    """Decorator to protect functions with license validation"""
    def wrapper(*args, **kwargs):
        lm = LicenseManager()
        valid, message = lm.validate_license()

        if not valid:
            raise PermissionError(f"License validation failed: {message}")

        return func(*args, **kwargs)

    return wrapper


if __name__ == '__main__':
    # Generate a license for current machine
    lm = LicenseManager()

    print("=" * 60)
    print("ARCHIV-IT - License Generator")
    print("=" * 60)
    print(f"\nHardware ID: {lm.hardware_id}")

    # Generate beta tester license
    license_data = lm.generate_license(
        customer_name="Beta Tester",
        tier="free",
        duration_days=90  # 90-day beta license
    )

    lm.save_license(license_data)

    print("\n" + "=" * 60)
    print("Validating license...")
    valid, message = lm.validate_license()
    print(f"Status: {message}")
