#!/usr/bin/env python3
"""
NFT-8 Batch Wallet Scanner

Scan UNLIMITED wallets at once to find all NFT mints across multiple chains.
Designed for artists who have minted from multiple addresses over time.

Features:
- Parallel scanning of multiple wallets
- Cross-chain support (ETH, Polygon, Tezos, Solana, Bitcoin Ordinals)
- Aggregated results with deduplication
- Export to JSON/CSV
- Progress tracking for large scans
"""

import os
import sys
import json
import logging
import time
import hashlib
from typing import List, Dict, Optional, Set
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.wallet_scanner import WalletScanner
from collectors.blockchain_db import get_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class NFTMint:
    """Represents a single NFT mint"""
    contract_address: str
    token_id: str
    name: Optional[str]
    description: Optional[str]
    image: Optional[str]
    platform: str
    network: str
    minter_address: str
    tx_hash: Optional[str]
    block_number: Optional[int]
    token_uri: Optional[str]
    attributes: List[Dict]

    def __hash__(self):
        # Unique by contract + token_id + network
        return hash(f"{self.network}:{self.contract_address}:{self.token_id}")

    def __eq__(self, other):
        if not isinstance(other, NFTMint):
            return False
        return (self.network == other.network and
                self.contract_address == other.contract_address and
                self.token_id == other.token_id)


@dataclass
class ScanResult:
    """Result from scanning a single wallet"""
    address: str
    network: str
    mints: List[NFTMint]
    collectors: List[Dict]
    owned: List[Dict]
    scan_time: float
    error: Optional[str] = None


class BatchWalletScanner:
    """
    Scan unlimited wallets to find all NFT mints

    Usage:
        scanner = BatchWalletScanner()
        results = scanner.scan_wallets([
            "0x123...",
            "0x456...",
            "tz1abc...",
        ])
    """

    def __init__(self, max_workers: int = 5):
        """
        Initialize batch scanner

        Args:
            max_workers: Max parallel scans (be careful with rate limits)
        """
        self.scanner = WalletScanner()
        self.max_workers = max_workers
        self.db = get_db()

        # Track all unique mints
        self.all_mints: Set[NFTMint] = set()
        self.all_collectors: Dict[str, Dict] = {}

        logger.info(f"BatchWalletScanner initialized with {max_workers} workers")

    def detect_networks(self, address: str) -> List[str]:
        """Detect which networks to scan for an address"""
        return self.scanner.detect_all_networks(address)

    def scan_single_wallet(self, address: str) -> ScanResult:
        """
        Scan a single wallet across all compatible networks

        Args:
            address: Wallet address

        Returns:
            ScanResult with mints, collectors, etc.
        """
        start_time = time.time()
        mints = []
        collectors = []
        owned = []
        error = None

        try:
            # Detect networks for this address
            networks = self.detect_networks(address)

            if not networks:
                return ScanResult(
                    address=address,
                    network='unknown',
                    mints=[],
                    collectors=[],
                    owned=[],
                    scan_time=0,
                    error=f"Could not detect network for address: {address}"
                )

            logger.info(f"Scanning {address[:16]}... on {', '.join(networks)}")

            # Scan each network
            for network in networks:
                try:
                    if network == 'ethereum':
                        result = self.scanner.scan_ethereum_wallet(address)
                    elif network == 'polygon':
                        result = self.scanner.scan_polygon_wallet(address)
                    elif network == 'tezos':
                        result = self.scanner.scan_tezos_wallet(address)
                    elif network == 'solana':
                        result = self.scanner.scan_solana_wallet(address)
                    elif network == 'bitcoin':
                        result = self.scanner.scan_bitcoin_ordinals(address)
                    else:
                        continue

                    # Process mints
                    for mint_data in result.get('minted_nfts', []):
                        mint = NFTMint(
                            contract_address=mint_data.get('contract_address', ''),
                            token_id=str(mint_data.get('token_id', '')),
                            name=mint_data.get('name'),
                            description=mint_data.get('description'),
                            image=mint_data.get('image'),
                            platform=mint_data.get('platform', network),
                            network=network,
                            minter_address=address,
                            tx_hash=mint_data.get('tx_hash'),
                            block_number=mint_data.get('block_number'),
                            token_uri=mint_data.get('token_uri'),
                            attributes=mint_data.get('attributes', [])
                        )
                        mints.append(mint)

                    # Process collectors
                    collectors.extend(result.get('collectors', []))

                    # Process owned NFTs
                    owned.extend(result.get('owned_nfts', []))

                except Exception as e:
                    logger.warning(f"Error scanning {network} for {address[:16]}: {e}")

            scan_time = time.time() - start_time

            return ScanResult(
                address=address,
                network=networks[0] if networks else 'unknown',
                mints=mints,
                collectors=collectors,
                owned=owned,
                scan_time=scan_time
            )

        except Exception as e:
            logger.error(f"Failed to scan {address}: {e}")
            return ScanResult(
                address=address,
                network='unknown',
                mints=[],
                collectors=[],
                owned=[],
                scan_time=time.time() - start_time,
                error=str(e)
            )

    def scan_wallets(
        self,
        addresses: List[str],
        parallel: bool = True,
        progress_callback=None
    ) -> Dict:
        """
        Scan multiple wallets and aggregate results

        Args:
            addresses: List of wallet addresses (any chain)
            parallel: Use parallel scanning (faster but watch rate limits)
            progress_callback: Optional callback(completed, total, address)

        Returns:
            Aggregated results with all mints, collectors, stats
        """
        logger.info(f"Starting batch scan of {len(addresses)} wallets")
        start_time = time.time()

        results = []
        completed = 0

        if parallel and len(addresses) > 1:
            # Parallel scanning
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_addr = {
                    executor.submit(self.scan_single_wallet, addr): addr
                    for addr in addresses
                }

                for future in as_completed(future_to_addr):
                    addr = future_to_addr[future]
                    try:
                        result = future.result()
                        results.append(result)

                        # Add mints to global set
                        for mint in result.mints:
                            self.all_mints.add(mint)

                        # Track collectors
                        for collector in result.collectors:
                            coll_addr = collector.get('address', '')
                            if coll_addr not in self.all_collectors:
                                self.all_collectors[coll_addr] = collector
                            else:
                                # Merge collector data
                                existing = self.all_collectors[coll_addr]
                                existing['total_pieces'] = existing.get('total_pieces', 0) + collector.get('total_pieces', 0)

                        completed += 1
                        if progress_callback:
                            progress_callback(completed, len(addresses), addr)

                        logger.info(f"[{completed}/{len(addresses)}] Scanned {addr[:16]}... - Found {len(result.mints)} mints")

                    except Exception as e:
                        logger.error(f"Failed to get result for {addr}: {e}")
                        completed += 1
        else:
            # Sequential scanning
            for addr in addresses:
                result = self.scan_single_wallet(addr)
                results.append(result)

                for mint in result.mints:
                    self.all_mints.add(mint)

                for collector in result.collectors:
                    coll_addr = collector.get('address', '')
                    if coll_addr not in self.all_collectors:
                        self.all_collectors[coll_addr] = collector

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(addresses), addr)

                logger.info(f"[{completed}/{len(addresses)}] Scanned {addr[:16]}... - Found {len(result.mints)} mints")

        total_time = time.time() - start_time

        # Aggregate results
        aggregated = self._aggregate_results(results, total_time)

        logger.info(f"\nBatch scan complete:")
        logger.info(f"  Wallets scanned: {len(addresses)}")
        logger.info(f"  Total mints found: {len(self.all_mints)}")
        logger.info(f"  Unique collectors: {len(self.all_collectors)}")
        logger.info(f"  Total time: {total_time:.1f}s")

        return aggregated

    def _aggregate_results(self, results: List[ScanResult], total_time: float) -> Dict:
        """Aggregate all scan results into final output"""
        # Group mints by network
        mints_by_network = {}
        for mint in self.all_mints:
            network = mint.network
            if network not in mints_by_network:
                mints_by_network[network] = []
            mints_by_network[network].append(asdict(mint))

        # Group mints by platform
        mints_by_platform = {}
        for mint in self.all_mints:
            platform = mint.platform
            if platform not in mints_by_platform:
                mints_by_platform[platform] = []
            mints_by_platform[platform].append(asdict(mint))

        # Top collectors
        top_collectors = sorted(
            self.all_collectors.values(),
            key=lambda x: x.get('total_pieces', 0),
            reverse=True
        )[:50]

        # Errors
        errors = [
            {'address': r.address, 'error': r.error}
            for r in results if r.error
        ]

        return {
            'scan_date': datetime.utcnow().isoformat(),
            'total_time_seconds': total_time,
            'wallets_scanned': len(results),
            'wallets_with_errors': len(errors),

            'stats': {
                'total_mints': len(self.all_mints),
                'unique_collectors': len(self.all_collectors),
                'networks': list(mints_by_network.keys()),
                'platforms': list(mints_by_platform.keys()),
                'mints_per_network': {k: len(v) for k, v in mints_by_network.items()},
                'mints_per_platform': {k: len(v) for k, v in mints_by_platform.items()},
            },

            'all_mints': [asdict(m) for m in self.all_mints],
            'mints_by_network': mints_by_network,
            'mints_by_platform': mints_by_platform,

            'top_collectors': top_collectors,
            'all_collectors': list(self.all_collectors.values()),

            'errors': errors,

            'wallet_summaries': [
                {
                    'address': r.address,
                    'network': r.network,
                    'mints_found': len(r.mints),
                    'collectors': len(r.collectors),
                    'owned': len(r.owned),
                    'scan_time': r.scan_time,
                    'error': r.error
                }
                for r in results
            ]
        }

    def export_to_json(self, results: Dict, output_path: Path) -> bool:
        """Export results to JSON file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Exported results to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False

    def export_to_csv(self, results: Dict, output_path: Path) -> bool:
        """Export mints to CSV file"""
        try:
            import csv

            mints = results.get('all_mints', [])

            with open(output_path, 'w', newline='') as f:
                if not mints:
                    f.write("No mints found\n")
                    return True

                # Get all fields
                fieldnames = list(mints[0].keys())

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for mint in mints:
                    # Convert lists/dicts to strings for CSV
                    row = {}
                    for k, v in mint.items():
                        if isinstance(v, (list, dict)):
                            row[k] = json.dumps(v)
                        else:
                            row[k] = v
                    writer.writerow(row)

            logger.info(f"Exported {len(mints)} mints to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False

    def save_to_db(self, results: Dict) -> bool:
        """Save scan results to database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Save each mint
            for mint in results.get('all_mints', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO nft_mints
                    (address_id, token_id, contract_address, mint_tx_hash,
                     mint_block_number, token_uri, name, description, platform)
                    VALUES (
                        (SELECT id FROM tracked_addresses WHERE LOWER(address) = LOWER(?)),
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''', (
                    mint['minter_address'],
                    mint['token_id'],
                    mint['contract_address'],
                    mint['tx_hash'],
                    mint['block_number'],
                    mint['token_uri'],
                    mint['name'],
                    mint['description'],
                    mint['platform']
                ))

            conn.commit()
            conn.close()

            logger.info(f"Saved {len(results.get('all_mints', []))} mints to database")
            return True

        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            return False


def scan_artist_wallets(addresses: List[str], output_dir: Path = None) -> Dict:
    """
    Convenience function to scan an artist's wallets

    Args:
        addresses: List of artist's wallet addresses
        output_dir: Optional output directory for results

    Returns:
        Scan results
    """
    scanner = BatchWalletScanner(max_workers=3)

    def progress(completed, total, addr):
        pct = (completed / total) * 100
        print(f"Progress: {pct:.0f}% ({completed}/{total})")

    results = scanner.scan_wallets(addresses, parallel=True, progress_callback=progress)

    # Export if output dir specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"scan_results_{timestamp}.json"
        csv_path = output_dir / f"mints_{timestamp}.csv"

        scanner.export_to_json(results, json_path)
        scanner.export_to_csv(results, csv_path)

    return results


# CLI Interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""
NFT-8 Batch Wallet Scanner

Scan UNLIMITED wallets to find all your NFT mints.

Usage:
  python batch_wallet_scanner.py <address1> [address2] [address3] ...
  python batch_wallet_scanner.py --file <addresses.txt>
  python batch_wallet_scanner.py --file <addresses.txt> --output ./results/

Options:
  --file <path>     Read addresses from file (one per line)
  --output <dir>    Export results to directory (JSON + CSV)
  --parallel        Use parallel scanning (default)
  --sequential      Use sequential scanning (slower but safer)
  --workers <n>     Number of parallel workers (default: 3)

Examples:
  # Scan a single wallet
  python batch_wallet_scanner.py 0x1234567890abcdef...

  # Scan multiple wallets
  python batch_wallet_scanner.py 0x123... 0x456... tz1abc...

  # Scan from file
  python batch_wallet_scanner.py --file my_wallets.txt --output ./scan_results/

Supported Networks:
  - Ethereum (0x...)
  - Polygon (0x...)
  - Tezos (tz1.../KT1...)
  - Solana (base58)
  - Bitcoin Ordinals (1.../3.../bc1...)
        """)
        sys.exit(0)

    # Parse arguments
    addresses = []
    output_dir = None
    parallel = True
    workers = 3

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--file':
            # Read addresses from file
            file_path = Path(sys.argv[i + 1])
            if file_path.exists():
                with open(file_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            addresses.append(line)
            else:
                print(f"File not found: {file_path}")
                sys.exit(1)
            i += 2

        elif arg == '--output':
            output_dir = Path(sys.argv[i + 1])
            i += 2

        elif arg == '--sequential':
            parallel = False
            i += 1

        elif arg == '--parallel':
            parallel = True
            i += 1

        elif arg == '--workers':
            workers = int(sys.argv[i + 1])
            i += 2

        elif arg.startswith('0x') or arg.startswith('tz') or arg.startswith('bc1') or arg.startswith('1') or arg.startswith('3'):
            # Looks like an address
            addresses.append(arg)
            i += 1

        else:
            # Assume it's an address
            addresses.append(arg)
            i += 1

    if not addresses:
        print("No addresses provided. Use --file or pass addresses as arguments.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"NFT-8 Batch Wallet Scanner")
    print(f"{'='*60}")
    print(f"\nScanning {len(addresses)} wallet(s)...")
    print(f"Mode: {'Parallel' if parallel else 'Sequential'}")
    if parallel:
        print(f"Workers: {workers}")
    print()

    # Initialize scanner
    scanner = BatchWalletScanner(max_workers=workers)

    def progress(completed, total, addr):
        pct = (completed / total) * 100
        bar_len = 30
        filled = int(bar_len * completed / total)
        bar = '=' * filled + '-' * (bar_len - filled)
        print(f"\r[{bar}] {pct:.0f}% ({completed}/{total})", end='', flush=True)

    # Scan
    results = scanner.scan_wallets(addresses, parallel=parallel, progress_callback=progress)
    print()  # Newline after progress bar

    # Export if requested
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"scan_results_{timestamp}.json"
        csv_path = output_dir / f"mints_{timestamp}.csv"

        scanner.export_to_json(results, json_path)
        scanner.export_to_csv(results, csv_path)

        print(f"\nResults exported to:")
        print(f"  JSON: {json_path}")
        print(f"  CSV:  {csv_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"\nTotal mints found: {results['stats']['total_mints']}")
    print(f"Unique collectors: {results['stats']['unique_collectors']}")
    print(f"Networks: {', '.join(results['stats']['networks'])}")
    print(f"Platforms: {', '.join(results['stats']['platforms'])}")
    print(f"\nMints by network:")
    for network, count in results['stats']['mints_per_network'].items():
        print(f"  {network}: {count}")
    print(f"\nMints by platform:")
    for platform, count in results['stats']['mints_per_platform'].items():
        print(f"  {platform}: {count}")

    if results['top_collectors']:
        print(f"\nTop collectors:")
        for i, coll in enumerate(results['top_collectors'][:5], 1):
            addr = coll.get('address', 'Unknown')[:20]
            pieces = coll.get('total_pieces', 0)
            print(f"  {i}. {addr}... - {pieces} pieces")

    if results['errors']:
        print(f"\nErrors ({len(results['errors'])}):")
        for err in results['errors']:
            print(f"  {err['address'][:20]}...: {err['error']}")

    print(f"\nTotal scan time: {results['total_time_seconds']:.1f}s")
    print()
