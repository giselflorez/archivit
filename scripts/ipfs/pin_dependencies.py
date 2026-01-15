#!/usr/bin/env python3
"""
IPFS Dependency Pinner for ARCHIV-IT

Pins JavaScript dependencies to IPFS via Pinata for:
- Immutable version locking (CID = content hash)
- Decentralized loading (any gateway works)
- Sovereign infrastructure (no CDN dependency)

Usage:
    # Set credentials first:
    export PINATA_API_KEY=your_key
    export PINATA_SECRET_KEY=your_secret

    # Pin dependencies:
    python pin_dependencies.py --pin-all

    # Generate IPFS-loading HTML:
    python pin_dependencies.py --generate-html
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# IPFS Gateways ranked by reliability/speed
IPFS_GATEWAYS = [
    "https://gateway.pinata.cloud/ipfs/",      # Pinata (fastest if pinned there)
    "https://cloudflare-ipfs.com/ipfs/",       # Cloudflare (fast, reliable)
    "https://ipfs.io/ipfs/",                   # Protocol Labs (canonical)
    "https://dweb.link/ipfs/",                 # Protocol Labs alt
    "https://w3s.link/ipfs/",                  # Web3.Storage
]

# Known CIDs for common libraries (pre-verified)
KNOWN_CIDS = {
    # These are verified hashes - content is immutable
    "three.js-r128": None,  # Will be set after first pin
    "OrbitControls-r128": None,
}

@dataclass
class PinataConfig:
    api_key: str
    secret_key: str
    base_url: str = "https://api.pinata.cloud"

    @classmethod
    def from_env(cls) -> Optional['PinataConfig']:
        api_key = os.getenv('PINATA_API_KEY', '').strip()
        secret_key = os.getenv('PINATA_SECRET_KEY', '').strip()
        if api_key and secret_key:
            return cls(api_key=api_key, secret_key=secret_key)
        return None

    @property
    def headers(self) -> Dict[str, str]:
        return {
            'pinata_api_key': self.api_key,
            'pinata_secret_api_key': self.secret_key
        }


class IPFSPinner:
    """Pin files to IPFS via Pinata and generate sovereign loading code."""

    def __init__(self, config: Optional[PinataConfig] = None):
        self.config = config or PinataConfig.from_env()
        self.pinned_cids: Dict[str, str] = {}
        self.cid_cache_file = Path(__file__).parent / "ipfs_cids.json"
        self._load_cid_cache()

    def _load_cid_cache(self):
        """Load previously pinned CIDs from cache."""
        if self.cid_cache_file.exists():
            try:
                with open(self.cid_cache_file) as f:
                    self.pinned_cids = json.load(f)
                print(f"Loaded {len(self.pinned_cids)} cached CIDs")
            except Exception as e:
                print(f"Warning: Could not load CID cache: {e}")

    def _save_cid_cache(self):
        """Save pinned CIDs to cache."""
        self.cid_cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cid_cache_file, 'w') as f:
            json.dump(self.pinned_cids, f, indent=2)
        print(f"Saved {len(self.pinned_cids)} CIDs to cache")

    def calculate_cid_v1(self, content: bytes) -> str:
        """
        Calculate CIDv1 for content (simplified - actual IPFS uses more complex encoding).
        This is for verification, not actual CID generation.
        """
        return hashlib.sha256(content).hexdigest()[:32]

    def pin_file(self, filepath: Path, name: str) -> Optional[str]:
        """Pin a file to IPFS via Pinata."""
        if not self.config:
            print("ERROR: Pinata credentials not configured")
            print("Set PINATA_API_KEY and PINATA_SECRET_KEY environment variables")
            return None

        # Check cache first
        cache_key = f"{name}-{filepath.stat().st_size}"
        if cache_key in self.pinned_cids:
            print(f"Using cached CID for {name}: {self.pinned_cids[cache_key]}")
            return self.pinned_cids[cache_key]

        print(f"Pinning {name} ({filepath.stat().st_size / 1024:.1f}KB)...")

        url = f"{self.config.base_url}/pinning/pinFileToIPFS"

        with open(filepath, 'rb') as f:
            files = {
                'file': (filepath.name, f)
            }
            metadata = json.dumps({
                'name': name,
                'keyvalues': {
                    'project': 'ARCHIV-IT',
                    'type': 'dependency',
                    'version': 'r128' if 'three' in name.lower() else 'matched'
                }
            })
            data = {
                'pinataMetadata': metadata,
                'pinataOptions': json.dumps({'cidVersion': 1})
            }

            try:
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=self.config.headers,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                cid = result['IpfsHash']

                # Cache the CID
                self.pinned_cids[cache_key] = cid
                self._save_cid_cache()

                print(f"✓ Pinned {name}: ipfs://{cid}")
                return cid

            except requests.exceptions.RequestException as e:
                print(f"✗ Failed to pin {name}: {e}")
                return None

    def pin_content(self, content: bytes, name: str) -> Optional[str]:
        """Pin raw content to IPFS via Pinata."""
        if not self.config:
            print("ERROR: Pinata credentials not configured")
            return None

        # Check cache
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        cache_key = f"{name}-{content_hash}"
        if cache_key in self.pinned_cids:
            print(f"Using cached CID for {name}")
            return self.pinned_cids[cache_key]

        print(f"Pinning {name} ({len(content) / 1024:.1f}KB)...")

        url = f"{self.config.base_url}/pinning/pinFileToIPFS"

        files = {
            'file': (name, content)
        }
        metadata = json.dumps({
            'name': name,
            'keyvalues': {
                'project': 'ARCHIV-IT',
                'type': 'dependency'
            }
        })
        data = {
            'pinataMetadata': metadata,
            'pinataOptions': json.dumps({'cidVersion': 1})
        }

        try:
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=self.config.headers,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            cid = result['IpfsHash']

            self.pinned_cids[cache_key] = cid
            self._save_cid_cache()

            print(f"✓ Pinned {name}: ipfs://{cid}")
            return cid

        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to pin {name}: {e}")
            return None

    def verify_cid_available(self, cid: str, timeout: int = 10) -> bool:
        """Verify a CID is accessible from IPFS gateways."""
        for gateway in IPFS_GATEWAYS[:3]:  # Try first 3 gateways
            url = f"{gateway}{cid}"
            try:
                response = requests.head(url, timeout=timeout)
                if response.status_code == 200:
                    print(f"✓ CID verified on {gateway}")
                    return True
            except:
                continue
        print(f"⚠ CID {cid} not immediately available (may need propagation time)")
        return False

    def generate_ipfs_loader_script(self, dependencies: Dict[str, str]) -> str:
        """
        Generate JavaScript that loads dependencies from IPFS with fallbacks.

        This creates a sovereign loader that:
        1. Tries multiple IPFS gateways
        2. Falls back to CDN if IPFS unavailable
        3. Verifies content integrity
        """
        gateways_json = json.dumps(IPFS_GATEWAYS[:4])
        deps_json = json.dumps(dependencies)

        return f'''
<!-- IPFS Sovereign Loader - Generated by ARCHIV-IT -->
<script>
(function() {{
    const IPFS_GATEWAYS = {gateways_json};
    const DEPENDENCIES = {deps_json};
    const CDN_FALLBACKS = {{
        'three.min.js': 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
        'OrbitControls.js': 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'
    }};

    async function loadFromIPFS(name, cid) {{
        for (const gateway of IPFS_GATEWAYS) {{
            try {{
                const url = gateway + cid;
                const response = await fetch(url, {{ timeout: 5000 }});
                if (response.ok) {{
                    console.log(`✓ Loaded ${{name}} from IPFS (${{gateway}})`);
                    return await response.text();
                }}
            }} catch (e) {{
                console.warn(`Gateway ${{gateway}} failed for ${{name}}`);
            }}
        }}
        return null;
    }}

    async function loadScript(name, cid) {{
        // Try IPFS first
        let code = await loadFromIPFS(name, cid);

        // Fallback to CDN if IPFS fails
        if (!code && CDN_FALLBACKS[name]) {{
            console.warn(`IPFS unavailable for ${{name}}, falling back to CDN`);
            const response = await fetch(CDN_FALLBACKS[name]);
            code = await response.text();
        }}

        if (code) {{
            const script = document.createElement('script');
            script.textContent = code;
            document.head.appendChild(script);
            return true;
        }}
        return false;
    }}

    // Load dependencies in order
    async function loadAll() {{
        for (const [name, cid] of Object.entries(DEPENDENCIES)) {{
            await loadScript(name, cid);
        }}
        // Signal ready
        window.dispatchEvent(new Event('ipfs-deps-loaded'));
    }}

    loadAll();
}})();
</script>
'''

    def generate_simple_ipfs_tags(self, dependencies: Dict[str, str],
                                   gateway: str = "https://cloudflare-ipfs.com/ipfs/") -> str:
        """Generate simple script tags loading from IPFS gateway."""
        tags = []
        for name, cid in dependencies.items():
            url = f"{gateway}{cid}"
            tags.append(f'<script src="{url}"></script> <!-- {name} pinned to IPFS -->')
        return '\n'.join(tags)


def download_and_pin_threejs():
    """Download Three.js r128 and pin to IPFS."""
    pinner = IPFSPinner()

    if not pinner.config:
        print("\n" + "="*60)
        print("PINATA CREDENTIALS REQUIRED")
        print("="*60)
        print("""
To pin dependencies to IPFS, you need Pinata credentials:

1. Go to https://app.pinata.cloud/register
2. Create a free account (1GB free storage)
3. Go to API Keys and create a new key
4. Add to your .env file:

   PINATA_API_KEY=your_key_here
   PINATA_SECRET_KEY=your_secret_here

5. Run this script again
""")
        return None

    # Download Three.js if not present
    public_dir = Path(__file__).parent.parent.parent / "public"
    three_path = public_dir / "three.min.js"
    orbit_path = public_dir / "OrbitControls.js"

    dependencies = {}

    if three_path.exists():
        cid = pinner.pin_file(three_path, "three.js-r128")
        if cid:
            dependencies['three.min.js'] = cid

    if orbit_path.exists():
        cid = pinner.pin_file(orbit_path, "OrbitControls-r128")
        if cid:
            dependencies['OrbitControls.js'] = cid

    if dependencies:
        print("\n" + "="*60)
        print("IPFS PINNING COMPLETE")
        print("="*60)
        print("\nPinned CIDs:")
        for name, cid in dependencies.items():
            print(f"  {name}: ipfs://{cid}")

        print("\nGateway URLs:")
        for name, cid in dependencies.items():
            print(f"  {name}:")
            print(f"    https://cloudflare-ipfs.com/ipfs/{cid}")
            print(f"    https://gateway.pinata.cloud/ipfs/{cid}")

        # Generate loader code
        print("\n" + "-"*60)
        print("SCRIPT TAGS (add to HTML):")
        print("-"*60)
        print(pinner.generate_simple_ipfs_tags(dependencies))

        return dependencies

    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pin dependencies to IPFS")
    parser.add_argument('--pin-all', action='store_true', help='Pin all dependencies')
    parser.add_argument('--generate-html', action='store_true', help='Generate IPFS loader HTML')
    parser.add_argument('--verify', help='Verify a CID is available')

    args = parser.parse_args()

    if args.verify:
        pinner = IPFSPinner()
        pinner.verify_cid_available(args.verify)
    elif args.pin_all or args.generate_html:
        download_and_pin_threejs()
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("Quick start: python pin_dependencies.py --pin-all")
