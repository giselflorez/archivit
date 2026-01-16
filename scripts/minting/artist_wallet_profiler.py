#!/usr/bin/env python3
"""
NFT-8 Artist Wallet Profiler - ULTRATHINK Edition

Comprehensive artist profile builder that:
- Links multiple wallets to a single artist identity
- Resolves ENS/Tezos domains to wallets
- Discovers wallets from Twitter/social profiles
- Aggregates all NFT mints across chains
- Maps collector networks
- Generates detailed artist reports

ULTRATHINK: Deep comprehensive analysis of artist's blockchain presence.
"""

import os
import sys
import json
import re
import logging
import time
import requests
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.wallet_scanner import WalletScanner
from minting.batch_wallet_scanner import BatchWalletScanner, NFTMint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SocialProfile:
    """Social media profile data"""
    platform: str  # twitter, instagram, farcaster, lens
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers: Optional[int] = None
    verified: bool = False
    url: Optional[str] = None
    linked_wallets: List[str] = field(default_factory=list)


@dataclass
class DomainRecord:
    """Blockchain domain record"""
    domain: str  # vitalik.eth, founder.tez
    domain_type: str  # ens, tezos_domains
    resolved_address: str
    network: str
    expires: Optional[str] = None


@dataclass
class ArtistProfile:
    """Complete artist profile with all wallets and data"""
    artist_id: str  # Generated unique ID
    display_name: str
    primary_twitter: Optional[str] = None

    # Wallets
    wallets: List[Dict] = field(default_factory=list)
    domains: List[DomainRecord] = field(default_factory=list)

    # Social
    social_profiles: List[SocialProfile] = field(default_factory=list)

    # NFT Data
    total_mints: int = 0
    mints_by_network: Dict[str, int] = field(default_factory=dict)
    mints_by_platform: Dict[str, int] = field(default_factory=dict)
    all_mints: List[Dict] = field(default_factory=list)

    # Collectors
    unique_collectors: int = 0
    top_collectors: List[Dict] = field(default_factory=list)
    collector_overlap: Dict[str, int] = field(default_factory=dict)

    # Analytics
    first_mint_date: Optional[str] = None
    last_mint_date: Optional[str] = None
    most_active_year: Optional[int] = None
    primary_network: Optional[str] = None
    primary_platform: Optional[str] = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ENSResolver:
    """Resolve ENS domains to Ethereum addresses"""

    ENS_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"

    def __init__(self):
        self.cache = {}

    def resolve(self, domain: str) -> Optional[str]:
        """
        Resolve ENS domain to address

        Args:
            domain: ENS domain (e.g., vitalik.eth)

        Returns:
            Ethereum address or None
        """
        if domain in self.cache:
            return self.cache[domain]

        try:
            # Normalize domain
            domain = domain.lower().strip()
            if not domain.endswith('.eth'):
                domain += '.eth'

            # Try ENS public resolver via web3 RPC
            # Using eth_call to ENS registry
            from web3 import Web3

            # Use public RPC
            w3 = Web3(Web3.HTTPProvider('https://cloudflare-eth.com'))

            # namehash the domain
            def namehash(name):
                if name == '':
                    return b'\x00' * 32
                label, _, remainder = name.partition('.')
                return Web3.keccak(namehash(remainder) + Web3.keccak(text=label))

            node = namehash(domain)

            # ENS Registry address
            ENS_REGISTRY = '0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e'

            # Get resolver
            resolver_call = w3.eth.call({
                'to': ENS_REGISTRY,
                'data': '0x0178b8bf' + node.hex()  # resolver(bytes32)
            })

            resolver_addr = '0x' + resolver_call.hex()[-40:]

            if resolver_addr == '0x' + '0' * 40:
                return None

            # Get address from resolver
            addr_call = w3.eth.call({
                'to': Web3.to_checksum_address(resolver_addr),
                'data': '0x3b3b57de' + node.hex()  # addr(bytes32)
            })

            address = '0x' + addr_call.hex()[-40:]

            if address != '0x' + '0' * 40:
                self.cache[domain] = address
                logger.info(f"Resolved ENS {domain} -> {address}")
                return address

        except Exception as e:
            logger.debug(f"ENS resolution failed for {domain}: {e}")

        # Fallback: Try ENS API
        try:
            response = requests.get(
                f"https://api.ensideas.com/ens/resolve/{domain}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                address = data.get('address')
                if address:
                    self.cache[domain] = address
                    return address
        except:
            pass

        return None

    def reverse_resolve(self, address: str) -> Optional[str]:
        """Get ENS name for an address (reverse resolution)"""
        try:
            response = requests.get(
                f"https://api.ensideas.com/ens/resolve/{address}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('name')
        except:
            pass
        return None


class TezosDomainsResolver:
    """Resolve Tezos domains"""

    TZKT_API = "https://api.tzkt.io/v1"

    def __init__(self):
        self.cache = {}

    def resolve(self, domain: str) -> Optional[str]:
        """Resolve Tezos domain to address"""
        if domain in self.cache:
            return self.cache[domain]

        try:
            domain = domain.lower().strip()
            if not domain.endswith('.tez'):
                domain += '.tez'

            response = requests.get(
                f"{self.TZKT_API}/domains",
                params={'name': domain},
                timeout=15
            )

            if response.status_code == 200:
                domains = response.json()
                if domains and len(domains) > 0:
                    address = domains[0].get('owner', {}).get('address')
                    if address:
                        self.cache[domain] = address
                        logger.info(f"Resolved Tezos domain {domain} -> {address}")
                        return address

        except Exception as e:
            logger.debug(f"Tezos domain resolution failed: {e}")

        return None

    def get_domains_for_address(self, address: str) -> List[str]:
        """Get all Tezos domains owned by an address"""
        try:
            response = requests.get(
                f"{self.TZKT_API}/domains",
                params={'owner': address},
                timeout=15
            )

            if response.status_code == 200:
                domains = response.json()
                return [d.get('name') for d in domains if d.get('name')]

        except:
            pass

        return []


class TwitterWalletFinder:
    """Find wallet addresses linked to Twitter profiles"""

    def __init__(self):
        self.ens_resolver = ENSResolver()
        self.tezos_resolver = TezosDomainsResolver()

    def find_wallets_from_profile(self, username: str) -> Dict:
        """
        Find wallet addresses from Twitter profile

        Searches:
        - Twitter bio for wallet addresses
        - ENS names in bio/username
        - Tezos domains in bio
        - Linked websites

        Args:
            username: Twitter username (without @)

        Returns:
            Dict with found wallets and domains
        """
        result = {
            'username': username,
            'wallets': [],
            'domains': [],
            'profile_data': None,
            'sources': []
        }

        # Patterns to look for
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        ens_pattern = r'[\w-]+\.eth'
        tezos_pattern = r'tz[123][1-9A-HJ-NP-Za-km-z]{33}'
        tezos_domain_pattern = r'[\w-]+\.tez'
        solana_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'

        # Try to get profile data from various sources
        profile_text = ""

        # Method 1: Nitter (Twitter mirror)
        try:
            nitter_instances = [
                f"https://nitter.net/{username}",
                f"https://nitter.cz/{username}",
            ]

            for nitter_url in nitter_instances:
                try:
                    response = requests.get(nitter_url, timeout=10)
                    if response.status_code == 200:
                        profile_text = response.text

                        # Extract bio
                        bio_match = re.search(r'class="profile-bio"[^>]*>([^<]+)', profile_text)
                        if bio_match:
                            profile_text += " " + bio_match.group(1)

                        result['sources'].append('nitter')
                        break
                except:
                    continue
        except:
            pass

        # Method 2: Check well-known NFT platforms for linked Twitter
        try:
            # SuperRare API
            sr_response = requests.get(
                f"https://superrare.com/api/v2/user?username={username}",
                timeout=10
            )
            if sr_response.status_code == 200:
                data = sr_response.json()
                if data.get('ethAddress'):
                    result['wallets'].append({
                        'address': data['ethAddress'],
                        'network': 'ethereum',
                        'source': 'superrare'
                    })
                    result['sources'].append('superrare')
        except:
            pass

        # Method 3: Foundation
        try:
            fnd_response = requests.get(
                f"https://api.foundation.app/graphql",
                json={
                    "query": """
                        query GetUserByUsername($username: String!) {
                            user(username: $username) {
                                publicKey
                            }
                        }
                    """,
                    "variables": {"username": username}
                },
                timeout=10
            )
            if fnd_response.status_code == 200:
                data = fnd_response.json()
                pk = data.get('data', {}).get('user', {}).get('publicKey')
                if pk:
                    result['wallets'].append({
                        'address': pk,
                        'network': 'ethereum',
                        'source': 'foundation'
                    })
                    result['sources'].append('foundation')
        except:
            pass

        # Method 4: Objkt (Tezos)
        try:
            objkt_response = requests.get(
                f"https://api.objkt.com/v1/graphql",
                json={
                    "query": """
                        query GetHolder($twitter: String!) {
                            holder(where: {twitter: {_eq: $twitter}}) {
                                address
                            }
                        }
                    """,
                    "variables": {"twitter": username}
                },
                timeout=10
            )
            if objkt_response.status_code == 200:
                data = objkt_response.json()
                holders = data.get('data', {}).get('holder', [])
                for holder in holders:
                    if holder.get('address'):
                        result['wallets'].append({
                            'address': holder['address'],
                            'network': 'tezos',
                            'source': 'objkt'
                        })
                        result['sources'].append('objkt')
        except:
            pass

        # Extract addresses from profile text
        if profile_text:
            # ETH addresses
            eth_matches = re.findall(eth_pattern, profile_text)
            for addr in set(eth_matches):
                if not any(w['address'].lower() == addr.lower() for w in result['wallets']):
                    result['wallets'].append({
                        'address': addr,
                        'network': 'ethereum',
                        'source': 'bio'
                    })

            # ENS names
            ens_matches = re.findall(ens_pattern, profile_text.lower())
            for ens in set(ens_matches):
                resolved = self.ens_resolver.resolve(ens)
                if resolved:
                    result['domains'].append({
                        'domain': ens,
                        'type': 'ens',
                        'address': resolved
                    })
                    if not any(w['address'].lower() == resolved.lower() for w in result['wallets']):
                        result['wallets'].append({
                            'address': resolved,
                            'network': 'ethereum',
                            'source': f'ens:{ens}'
                        })

            # Tezos addresses
            tez_matches = re.findall(tezos_pattern, profile_text)
            for addr in set(tez_matches):
                if not any(w['address'] == addr for w in result['wallets']):
                    result['wallets'].append({
                        'address': addr,
                        'network': 'tezos',
                        'source': 'bio'
                    })

            # Tezos domains
            tez_domain_matches = re.findall(tezos_domain_pattern, profile_text.lower())
            for domain in set(tez_domain_matches):
                resolved = self.tezos_resolver.resolve(domain)
                if resolved:
                    result['domains'].append({
                        'domain': domain,
                        'type': 'tezos_domains',
                        'address': resolved
                    })
                    if not any(w['address'] == resolved for w in result['wallets']):
                        result['wallets'].append({
                            'address': resolved,
                            'network': 'tezos',
                            'source': f'tezos_domain:{domain}'
                        })

        # Try to resolve username as ENS
        ens_from_username = self.ens_resolver.resolve(f"{username}.eth")
        if ens_from_username:
            result['domains'].append({
                'domain': f"{username}.eth",
                'type': 'ens',
                'address': ens_from_username
            })
            if not any(w['address'].lower() == ens_from_username.lower() for w in result['wallets']):
                result['wallets'].append({
                    'address': ens_from_username,
                    'network': 'ethereum',
                    'source': f'ens:{username}.eth'
                })

        # Try as Tezos domain
        tez_from_username = self.tezos_resolver.resolve(f"{username}.tez")
        if tez_from_username:
            result['domains'].append({
                'domain': f"{username}.tez",
                'type': 'tezos_domains',
                'address': tez_from_username
            })
            if not any(w['address'] == tez_from_username for w in result['wallets']):
                result['wallets'].append({
                    'address': tez_from_username,
                    'network': 'tezos',
                    'source': f'tezos_domain:{username}.tez'
                })

        logger.info(f"Found {len(result['wallets'])} wallets for @{username}")
        return result


class ArtistWalletProfiler:
    """
    Build comprehensive artist profiles from wallets and social links

    ULTRATHINK: Deep analysis connecting social identity to blockchain presence.
    """

    def __init__(self, max_workers: int = 3):
        self.batch_scanner = BatchWalletScanner(max_workers=max_workers)
        self.twitter_finder = TwitterWalletFinder()
        self.ens_resolver = ENSResolver()
        self.tezos_resolver = TezosDomainsResolver()

    def build_profile_from_twitter(self, twitter_username: str) -> ArtistProfile:
        """
        Build complete artist profile starting from Twitter username

        ULTRATHINK FLOW:
        1. Find all wallets linked to Twitter
        2. Resolve any ENS/Tezos domains
        3. Scan all wallets for mints
        4. Aggregate and analyze data
        5. Build comprehensive profile

        Args:
            twitter_username: Twitter username (without @)

        Returns:
            Complete ArtistProfile
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"ULTRATHINK: Building profile for @{twitter_username}")
        logger.info(f"{'='*60}\n")

        # Generate artist ID
        artist_id = f"artist_{twitter_username.lower()}_{int(time.time())}"

        profile = ArtistProfile(
            artist_id=artist_id,
            display_name=twitter_username,
            primary_twitter=twitter_username
        )

        # Step 1: Find wallets from Twitter
        logger.info("Step 1: Discovering wallets from Twitter profile...")
        twitter_data = self.twitter_finder.find_wallets_from_profile(twitter_username)

        profile.social_profiles.append(SocialProfile(
            platform='twitter',
            username=twitter_username,
            url=f"https://twitter.com/{twitter_username}",
            linked_wallets=[w['address'] for w in twitter_data['wallets']]
        ))

        # Add domains
        for domain_data in twitter_data['domains']:
            profile.domains.append(DomainRecord(
                domain=domain_data['domain'],
                domain_type=domain_data['type'],
                resolved_address=domain_data['address'],
                network='ethereum' if domain_data['type'] == 'ens' else 'tezos'
            ))

        # Collect all wallets
        all_wallets = []
        for wallet in twitter_data['wallets']:
            all_wallets.append(wallet)
            profile.wallets.append(wallet)

        logger.info(f"Found {len(all_wallets)} wallets from Twitter discovery")

        if not all_wallets:
            logger.warning("No wallets found. Profile will be incomplete.")
            return profile

        # Step 2: Scan all wallets
        logger.info("\nStep 2: Scanning all wallets for NFT mints...")
        addresses = [w['address'] for w in all_wallets]

        scan_results = self.batch_scanner.scan_wallets(addresses, parallel=True)

        # Step 3: Aggregate mint data
        logger.info("\nStep 3: Aggregating mint data...")

        profile.total_mints = scan_results['stats']['total_mints']
        profile.mints_by_network = scan_results['stats']['mints_per_network']
        profile.mints_by_platform = scan_results['stats']['mints_per_platform']
        profile.all_mints = scan_results['all_mints']

        # Step 4: Collector analysis
        logger.info("\nStep 4: Analyzing collector network...")

        profile.unique_collectors = scan_results['stats']['unique_collectors']
        profile.top_collectors = scan_results['top_collectors'][:20]

        # Calculate collector overlap (collectors who own multiple pieces)
        collector_counts = defaultdict(int)
        for collector in scan_results.get('all_collectors', []):
            addr = collector.get('address', '')
            pieces = collector.get('total_pieces', 0)
            if pieces >= 2:
                collector_counts[addr] = pieces

        profile.collector_overlap = dict(sorted(
            collector_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20])

        # Step 5: Analytics
        logger.info("\nStep 5: Computing analytics...")

        if profile.all_mints:
            # Find date range
            blocks = [m.get('block_number') for m in profile.all_mints if m.get('block_number')]
            if blocks:
                profile.first_mint_date = f"block_{min(blocks)}"
                profile.last_mint_date = f"block_{max(blocks)}"

            # Primary network
            if profile.mints_by_network:
                profile.primary_network = max(profile.mints_by_network, key=profile.mints_by_network.get)

            # Primary platform
            if profile.mints_by_platform:
                profile.primary_platform = max(profile.mints_by_platform, key=profile.mints_by_platform.get)

        profile.last_updated = datetime.utcnow().isoformat()

        logger.info(f"\n{'='*60}")
        logger.info(f"ULTRATHINK PROFILE COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Artist: @{twitter_username}")
        logger.info(f"Wallets: {len(profile.wallets)}")
        logger.info(f"Domains: {len(profile.domains)}")
        logger.info(f"Total Mints: {profile.total_mints}")
        logger.info(f"Networks: {', '.join(profile.mints_by_network.keys())}")
        logger.info(f"Platforms: {', '.join(profile.mints_by_platform.keys())}")
        logger.info(f"Unique Collectors: {profile.unique_collectors}")
        logger.info(f"Primary Network: {profile.primary_network}")
        logger.info(f"Primary Platform: {profile.primary_platform}")

        return profile

    def build_profile_from_wallets(
        self,
        wallets: List[str],
        display_name: str = "Artist",
        twitter_username: str = None
    ) -> ArtistProfile:
        """
        Build profile from list of known wallet addresses

        Args:
            wallets: List of wallet addresses
            display_name: Artist display name
            twitter_username: Optional Twitter handle

        Returns:
            ArtistProfile
        """
        artist_id = f"artist_{display_name.lower().replace(' ', '_')}_{int(time.time())}"

        profile = ArtistProfile(
            artist_id=artist_id,
            display_name=display_name,
            primary_twitter=twitter_username
        )

        # Detect network for each wallet
        scanner = WalletScanner()
        for addr in wallets:
            network, confidence = scanner.detect_blockchain(addr)
            profile.wallets.append({
                'address': addr,
                'network': network,
                'source': 'manual'
            })

            # Try to find ENS/domains
            if network == 'ethereum':
                ens = self.ens_resolver.reverse_resolve(addr)
                if ens:
                    profile.domains.append(DomainRecord(
                        domain=ens,
                        domain_type='ens',
                        resolved_address=addr,
                        network='ethereum'
                    ))
            elif network == 'tezos':
                tez_domains = self.tezos_resolver.get_domains_for_address(addr)
                for domain in tez_domains:
                    profile.domains.append(DomainRecord(
                        domain=domain,
                        domain_type='tezos_domains',
                        resolved_address=addr,
                        network='tezos'
                    ))

        # Scan wallets
        scan_results = self.batch_scanner.scan_wallets(wallets, parallel=True)

        # Populate profile
        profile.total_mints = scan_results['stats']['total_mints']
        profile.mints_by_network = scan_results['stats']['mints_per_network']
        profile.mints_by_platform = scan_results['stats']['mints_per_platform']
        profile.all_mints = scan_results['all_mints']
        profile.unique_collectors = scan_results['stats']['unique_collectors']
        profile.top_collectors = scan_results['top_collectors'][:20]

        if profile.mints_by_network:
            profile.primary_network = max(profile.mints_by_network, key=profile.mints_by_network.get)

        if profile.mints_by_platform:
            profile.primary_platform = max(profile.mints_by_platform, key=profile.mints_by_platform.get)

        return profile

    def export_profile(self, profile: ArtistProfile, output_dir: Path) -> Dict[str, Path]:
        """
        Export profile to multiple formats

        Returns:
            Dict of format -> file path
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        # JSON export
        json_path = output_dir / f"{profile.artist_id}_profile.json"
        with open(json_path, 'w') as f:
            json.dump(asdict(profile), f, indent=2, default=str)
        files['json'] = json_path

        # Summary markdown
        md_path = output_dir / f"{profile.artist_id}_summary.md"
        with open(md_path, 'w') as f:
            f.write(f"# Artist Profile: {profile.display_name}\n\n")
            f.write(f"Generated: {profile.last_updated}\n\n")

            if profile.primary_twitter:
                f.write(f"**Twitter:** [@{profile.primary_twitter}](https://twitter.com/{profile.primary_twitter})\n\n")

            f.write("## Wallets\n\n")
            for wallet in profile.wallets:
                f.write(f"- `{wallet['address']}` ({wallet['network']}) - {wallet.get('source', 'unknown')}\n")

            if profile.domains:
                f.write("\n## Domains\n\n")
                for domain in profile.domains:
                    f.write(f"- **{domain.domain}** -> `{domain.resolved_address}`\n")

            f.write(f"\n## Statistics\n\n")
            f.write(f"- **Total Mints:** {profile.total_mints}\n")
            f.write(f"- **Unique Collectors:** {profile.unique_collectors}\n")
            f.write(f"- **Primary Network:** {profile.primary_network}\n")
            f.write(f"- **Primary Platform:** {profile.primary_platform}\n")

            f.write(f"\n### Mints by Network\n\n")
            for network, count in profile.mints_by_network.items():
                f.write(f"- {network}: {count}\n")

            f.write(f"\n### Mints by Platform\n\n")
            for platform, count in profile.mints_by_platform.items():
                f.write(f"- {platform}: {count}\n")

            if profile.top_collectors:
                f.write(f"\n## Top Collectors\n\n")
                for i, collector in enumerate(profile.top_collectors[:10], 1):
                    addr = collector.get('address', 'Unknown')[:20]
                    pieces = collector.get('total_pieces', 0)
                    f.write(f"{i}. `{addr}...` - {pieces} pieces\n")

        files['markdown'] = md_path

        # Mints CSV
        if profile.all_mints:
            import csv
            csv_path = output_dir / f"{profile.artist_id}_mints.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(profile.all_mints[0].keys()))
                writer.writeheader()
                for mint in profile.all_mints:
                    row = {k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in mint.items()}
                    writer.writerow(row)
            files['csv'] = csv_path

        logger.info(f"Exported profile to {output_dir}")
        return files


# CLI Interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""
NFT-8 Artist Wallet Profiler - ULTRATHINK Edition

Build comprehensive artist profiles from Twitter or wallet addresses.

Usage:
  python artist_wallet_profiler.py --twitter <username>
  python artist_wallet_profiler.py --wallets <addr1> <addr2> ...
  python artist_wallet_profiler.py --twitter <username> --output ./profiles/

Options:
  --twitter <user>    Build profile from Twitter username
  --wallets <addrs>   Build profile from wallet addresses
  --name <name>       Display name for wallet-based profiles
  --output <dir>      Export results to directory

Examples:
  # Build profile from Twitter
  python artist_wallet_profiler.py --twitter bardionson --output ./profiles/

  # Build profile from known wallets
  python artist_wallet_profiler.py --wallets 0x123... tz1abc... --name "My Artist" --output ./profiles/
        """)
        sys.exit(0)

    # Parse arguments
    twitter_username = None
    wallets = []
    output_dir = None
    display_name = "Artist"

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--twitter':
            twitter_username = sys.argv[i + 1].replace('@', '')
            i += 2

        elif arg == '--wallets':
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                wallets.append(sys.argv[i])
                i += 1

        elif arg == '--name':
            display_name = sys.argv[i + 1]
            i += 2

        elif arg == '--output':
            output_dir = Path(sys.argv[i + 1])
            i += 2

        else:
            i += 1

    profiler = ArtistWalletProfiler()

    if twitter_username:
        print(f"\nBuilding profile for @{twitter_username}...")
        profile = profiler.build_profile_from_twitter(twitter_username)

    elif wallets:
        print(f"\nBuilding profile from {len(wallets)} wallets...")
        profile = profiler.build_profile_from_wallets(wallets, display_name)

    else:
        print("Please provide --twitter or --wallets")
        sys.exit(1)

    # Export if output dir specified
    if output_dir:
        files = profiler.export_profile(profile, output_dir)
        print(f"\nExported to:")
        for fmt, path in files.items():
            print(f"  {fmt}: {path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"PROFILE SUMMARY")
    print(f"{'='*60}")
    print(f"Display Name: {profile.display_name}")
    print(f"Wallets: {len(profile.wallets)}")
    print(f"Domains: {len(profile.domains)}")
    print(f"Total Mints: {profile.total_mints}")
    print(f"Unique Collectors: {profile.unique_collectors}")
    print(f"Primary Network: {profile.primary_network}")
    print(f"Primary Platform: {profile.primary_platform}")

    if profile.mints_by_network:
        print(f"\nMints by Network:")
        for network, count in profile.mints_by_network.items():
            print(f"  {network}: {count}")

    if profile.mints_by_platform:
        print(f"\nMints by Platform:")
        for platform, count in profile.mints_by_platform.items():
            print(f"  {platform}: {count}")

    print()
