#!/usr/bin/env python3
"""
NFT-8 SUPER SCAN - Collector Network Mapper

ULTRATHINK: Deep recursive scanning of collector networks.

This tool:
1. Scans artist's wallets to find all their mints
2. Identifies all collectors who own the artist's work
3. Scans THOSE collector wallets to find what OTHER artists they collect
4. Maps the entire collector ecosystem
5. Identifies "taste clusters" - collectors with similar preferences
6. Finds potential audience based on collector overlap
7. Generates network visualizations

Use cases:
- "Who are my collectors and what else do they collect?"
- "Which artists share my collector base?"
- "What's my potential audience based on similar artists?"
- "Map the social graph of my collectors"
"""

import os
import sys
import json
import time
import math
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.wallet_scanner import WalletScanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PHI = 1.618033988749895
GOLDEN_ANGLE = 137.5077640500378


@dataclass
class ArtistNode:
    """Represents an artist in the network"""
    address: str
    network: str
    name: Optional[str] = None
    platform: Optional[str] = None
    total_mints: int = 0
    collectors_count: int = 0
    contracts: List[str] = field(default_factory=list)


@dataclass
class CollectorNode:
    """Represents a collector in the network"""
    address: str
    network: str

    # What they collected from the main artist
    pieces_from_artist: int = 0
    tokens_from_artist: List[Dict] = field(default_factory=list)

    # What else they own (other artists)
    total_nfts_owned: int = 0
    other_artists: List[str] = field(default_factory=list)
    other_contracts: List[str] = field(default_factory=list)

    # Calculated metrics
    taste_score: float = 0.0  # How similar to other collectors
    influence_score: float = 0.0  # Based on collection size and diversity


@dataclass
class ArtistConnection:
    """Connection between two artists via shared collectors"""
    artist1: str
    artist2: str
    shared_collectors: int = 0
    collector_addresses: List[str] = field(default_factory=list)
    strength: float = 0.0  # Normalized connection strength


@dataclass
class TasteCluster:
    """Group of collectors with similar taste"""
    cluster_id: str
    collectors: List[str] = field(default_factory=list)
    common_artists: List[str] = field(default_factory=list)
    defining_traits: List[str] = field(default_factory=list)
    size: int = 0


@dataclass
class SuperScanResult:
    """Complete result of a SUPER SCAN"""
    # Metadata
    scan_id: str
    artist_name: str
    artist_wallets: List[str]
    scan_date: str
    scan_duration_seconds: float
    scan_depth: int

    # Artist's own data
    total_mints: int = 0
    mints_by_platform: Dict[str, int] = field(default_factory=dict)
    mints_by_network: Dict[str, int] = field(default_factory=dict)

    # Collector network
    total_collectors: int = 0
    collectors: List[CollectorNode] = field(default_factory=list)
    super_collectors: List[CollectorNode] = field(default_factory=list)  # 3+ pieces

    # Related artists (via collector overlap)
    related_artists: List[ArtistNode] = field(default_factory=list)
    artist_connections: List[ArtistConnection] = field(default_factory=list)

    # Taste analysis
    taste_clusters: List[TasteCluster] = field(default_factory=list)

    # Network metrics
    network_density: float = 0.0
    avg_collector_diversity: float = 0.0
    top_shared_artists: List[Dict] = field(default_factory=list)

    # Potential audience
    potential_audience: List[str] = field(default_factory=list)
    audience_size: int = 0


class NFTSuperScanner:
    """
    ULTRATHINK: Deep recursive collector network scanner

    Scans artist → collectors → collector holdings → related artists
    to build a complete network map of the collector ecosystem.
    """

    def __init__(self, max_workers: int = 3, scan_depth: int = 2):
        """
        Initialize SUPER SCAN

        Args:
            max_workers: Parallel scan workers
            scan_depth: How deep to recurse (1=collectors only, 2=collector holdings, 3+=related artist collectors)
        """
        self.scanner = WalletScanner()
        self.max_workers = max_workers
        self.scan_depth = scan_depth

        # Caches
        self.scanned_addresses: Set[str] = set()
        self.artist_mints: Dict[str, List[Dict]] = {}
        self.collector_holdings: Dict[str, List[Dict]] = {}
        self.contract_to_artist: Dict[str, str] = {}

        logger.info(f"NFT SUPER SCAN initialized (depth={scan_depth}, workers={max_workers})")

    def super_scan(
        self,
        artist_wallets: List[str],
        artist_name: str = "Artist",
        max_collectors: int = 100,
        scan_collector_holdings: bool = True
    ) -> SuperScanResult:
        """
        Execute SUPER SCAN on artist's wallets

        ULTRATHINK FLOW:
        1. Scan all artist wallets for mints
        2. Find all collectors of those mints
        3. Scan collector wallets for their full holdings
        4. Identify other artists they collect
        5. Calculate artist connections via shared collectors
        6. Identify taste clusters
        7. Calculate potential audience

        Args:
            artist_wallets: List of artist's wallet addresses
            artist_name: Artist display name
            max_collectors: Max collectors to deep scan
            scan_collector_holdings: Whether to scan what collectors own

        Returns:
            SuperScanResult with complete network analysis
        """
        start_time = time.time()
        scan_id = f"superscan_{int(start_time)}"

        logger.info(f"\n{'='*70}")
        logger.info(f"NFT SUPER SCAN: {artist_name}")
        logger.info(f"{'='*70}")
        logger.info(f"Wallets: {len(artist_wallets)}")
        logger.info(f"Scan depth: {self.scan_depth}")
        logger.info(f"Max collectors to deep scan: {max_collectors}")
        logger.info(f"{'='*70}\n")

        result = SuperScanResult(
            scan_id=scan_id,
            artist_name=artist_name,
            artist_wallets=artist_wallets,
            scan_date=datetime.utcnow().isoformat(),
            scan_duration_seconds=0,
            scan_depth=self.scan_depth
        )

        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: Scan artist's mints
        # ═══════════════════════════════════════════════════════════════
        logger.info("PHASE 1: Scanning artist's mints...")

        all_mints = []
        all_collectors_raw = []

        for wallet in artist_wallets:
            logger.info(f"  Scanning wallet: {wallet[:16]}...")

            networks = self.scanner.detect_all_networks(wallet)

            for network in networks:
                try:
                    if network == 'ethereum':
                        scan_result = self.scanner.scan_ethereum_wallet(wallet)
                    elif network == 'tezos':
                        scan_result = self.scanner.scan_tezos_wallet(wallet)
                    elif network == 'polygon':
                        scan_result = self.scanner.scan_polygon_wallet(wallet)
                    else:
                        continue

                    mints = scan_result.get('minted_nfts', [])
                    collectors = scan_result.get('collectors', [])

                    # Tag mints with artist info
                    for mint in mints:
                        mint['artist_wallet'] = wallet
                        mint['network'] = network

                        # Map contract to artist
                        contract = mint.get('contract_address', '')
                        if contract:
                            self.contract_to_artist[contract.lower()] = wallet

                    all_mints.extend(mints)
                    all_collectors_raw.extend(collectors)

                    logger.info(f"    {network}: {len(mints)} mints, {len(collectors)} collectors")

                except Exception as e:
                    logger.warning(f"    Error scanning {network}: {e}")

        # Aggregate mint stats
        result.total_mints = len(all_mints)

        for mint in all_mints:
            platform = mint.get('platform', 'Unknown')
            network = mint.get('network', 'unknown')

            result.mints_by_platform[platform] = result.mints_by_platform.get(platform, 0) + 1
            result.mints_by_network[network] = result.mints_by_network.get(network, 0) + 1

        self.artist_mints[artist_name] = all_mints

        logger.info(f"\n  Total mints found: {result.total_mints}")
        logger.info(f"  Platforms: {result.mints_by_platform}")
        logger.info(f"  Networks: {result.mints_by_network}")

        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: Process collectors
        # ═══════════════════════════════════════════════════════════════
        logger.info("\nPHASE 2: Processing collectors...")

        # Deduplicate collectors
        collector_map: Dict[str, CollectorNode] = {}

        for raw_collector in all_collectors_raw:
            addr = raw_collector.get('address', '')
            if not addr:
                continue

            addr_lower = addr.lower()

            if addr_lower not in collector_map:
                # Detect network
                network, _ = self.scanner.detect_blockchain(addr)

                collector_map[addr_lower] = CollectorNode(
                    address=addr,
                    network=network,
                    pieces_from_artist=0,
                    tokens_from_artist=[]
                )

            # Add pieces
            collector_map[addr_lower].pieces_from_artist += raw_collector.get('total_pieces', 1)
            collector_map[addr_lower].tokens_from_artist.extend(
                raw_collector.get('nfts_acquired', [])
            )

        # Sort by pieces owned
        collectors_sorted = sorted(
            collector_map.values(),
            key=lambda x: x.pieces_from_artist,
            reverse=True
        )

        result.total_collectors = len(collectors_sorted)
        result.collectors = collectors_sorted

        # Identify super collectors (3+ pieces)
        result.super_collectors = [c for c in collectors_sorted if c.pieces_from_artist >= 3]

        logger.info(f"  Total unique collectors: {result.total_collectors}")
        logger.info(f"  Super collectors (3+): {len(result.super_collectors)}")

        # ═══════════════════════════════════════════════════════════════
        # PHASE 3: Deep scan collector holdings
        # ═══════════════════════════════════════════════════════════════
        if scan_collector_holdings and self.scan_depth >= 2:
            logger.info("\nPHASE 3: Deep scanning collector holdings...")

            # Scan top collectors
            collectors_to_scan = collectors_sorted[:max_collectors]

            other_artists_count: Dict[str, int] = defaultdict(int)
            other_contracts_count: Dict[str, int] = defaultdict(int)

            scanned = 0

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_collector = {
                    executor.submit(self._scan_collector_holdings, c.address): c
                    for c in collectors_to_scan
                    if c.address.lower() not in self.scanned_addresses
                }

                for future in as_completed(future_to_collector):
                    collector = future_to_collector[future]

                    try:
                        holdings = future.result()

                        if holdings:
                            collector.total_nfts_owned = len(holdings)

                            # Find other artists/contracts
                            for nft in holdings:
                                contract = nft.get('contract_address', '').lower()

                                if contract and contract not in [c.lower() for m in all_mints for c in [m.get('contract_address', '')]]:
                                    collector.other_contracts.append(contract)
                                    other_contracts_count[contract] += 1

                                    # Try to identify artist
                                    if contract in self.contract_to_artist:
                                        artist = self.contract_to_artist[contract]
                                        collector.other_artists.append(artist)
                                        other_artists_count[artist] += 1

                            self.collector_holdings[collector.address] = holdings

                        scanned += 1
                        if scanned % 10 == 0:
                            logger.info(f"    Scanned {scanned}/{len(collectors_to_scan)} collectors")

                    except Exception as e:
                        logger.warning(f"    Error scanning {collector.address[:16]}: {e}")

            logger.info(f"  Scanned {scanned} collector holdings")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 4: Identify related artists
            # ═══════════════════════════════════════════════════════════════
            logger.info("\nPHASE 4: Identifying related artists...")

            # Find most common other contracts (potential related artists)
            top_contracts = sorted(
                other_contracts_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:50]

            result.top_shared_artists = [
                {'contract': c, 'shared_collectors': count}
                for c, count in top_contracts
            ]

            logger.info(f"  Found {len(top_contracts)} related contracts")

            # Build artist connections
            for contract, shared_count in top_contracts[:20]:
                if shared_count >= 2:  # At least 2 shared collectors
                    # Find which collectors share this
                    shared_collectors = [
                        c.address for c in collectors_sorted
                        if contract in [cc.lower() for cc in c.other_contracts]
                    ]

                    connection = ArtistConnection(
                        artist1=artist_name,
                        artist2=contract[:20] + '...',
                        shared_collectors=shared_count,
                        collector_addresses=shared_collectors[:10],
                        strength=shared_count / result.total_collectors if result.total_collectors > 0 else 0
                    )
                    result.artist_connections.append(connection)

            logger.info(f"  Built {len(result.artist_connections)} artist connections")

        # ═══════════════════════════════════════════════════════════════
        # PHASE 5: Taste cluster analysis
        # ═══════════════════════════════════════════════════════════════
        logger.info("\nPHASE 5: Analyzing taste clusters...")

        result.taste_clusters = self._identify_taste_clusters(collectors_sorted[:max_collectors])

        logger.info(f"  Identified {len(result.taste_clusters)} taste clusters")

        # ═══════════════════════════════════════════════════════════════
        # PHASE 6: Calculate potential audience
        # ═══════════════════════════════════════════════════════════════
        logger.info("\nPHASE 6: Calculating potential audience...")

        # Potential audience = collectors of related artists who don't yet collect this artist
        existing_collectors = set(c.address.lower() for c in collectors_sorted)

        potential = set()
        for connection in result.artist_connections:
            for addr in connection.collector_addresses:
                if addr.lower() not in existing_collectors:
                    potential.add(addr)

        result.potential_audience = list(potential)[:100]
        result.audience_size = len(potential)

        logger.info(f"  Potential audience size: {result.audience_size}")

        # ═══════════════════════════════════════════════════════════════
        # PHASE 7: Calculate network metrics
        # ═══════════════════════════════════════════════════════════════
        logger.info("\nPHASE 7: Calculating network metrics...")

        # Network density (connections / possible connections)
        n = result.total_collectors
        if n > 1:
            max_connections = n * (n - 1) / 2
            actual_connections = sum(len(c.other_artists) for c in collectors_sorted[:max_collectors])
            result.network_density = actual_connections / max_connections if max_connections > 0 else 0

        # Average collector diversity
        diversities = [
            len(set(c.other_contracts))
            for c in collectors_sorted[:max_collectors]
            if c.other_contracts
        ]
        result.avg_collector_diversity = sum(diversities) / len(diversities) if diversities else 0

        # ═══════════════════════════════════════════════════════════════
        # COMPLETE
        # ═══════════════════════════════════════════════════════════════
        result.scan_duration_seconds = time.time() - start_time

        logger.info(f"\n{'='*70}")
        logger.info(f"SUPER SCAN COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Duration: {result.scan_duration_seconds:.1f}s")
        logger.info(f"Total mints: {result.total_mints}")
        logger.info(f"Total collectors: {result.total_collectors}")
        logger.info(f"Super collectors: {len(result.super_collectors)}")
        logger.info(f"Related artists: {len(result.artist_connections)}")
        logger.info(f"Taste clusters: {len(result.taste_clusters)}")
        logger.info(f"Potential audience: {result.audience_size}")
        logger.info(f"{'='*70}\n")

        return result

    def _scan_collector_holdings(self, address: str) -> List[Dict]:
        """Scan what a collector owns"""
        self.scanned_addresses.add(address.lower())

        try:
            networks = self.scanner.detect_all_networks(address)
            all_owned = []

            for network in networks:
                try:
                    if network == 'ethereum':
                        # For owned NFTs, we'd need a different approach
                        # This is simplified - in production use an indexer
                        pass
                    elif network == 'tezos':
                        result = self.scanner.scan_tezos_wallet(address, scan_collectors=False)
                        all_owned.extend(result.get('owned_nfts', []))
                except:
                    continue

            return all_owned

        except Exception as e:
            logger.debug(f"Error scanning collector {address[:16]}: {e}")
            return []

    def _identify_taste_clusters(self, collectors: List[CollectorNode]) -> List[TasteCluster]:
        """
        Identify groups of collectors with similar taste

        Uses simple overlap-based clustering
        """
        clusters = []

        # Group collectors by what they own
        contract_to_collectors: Dict[str, Set[str]] = defaultdict(set)

        for collector in collectors:
            for contract in collector.other_contracts:
                contract_to_collectors[contract].add(collector.address)

        # Find clusters where multiple collectors share same contracts
        processed = set()
        cluster_id = 0

        for contract, coll_set in contract_to_collectors.items():
            if len(coll_set) >= 3:  # At least 3 collectors
                # Check if this forms a new cluster
                key = frozenset(coll_set)
                if key not in processed:
                    processed.add(key)

                    # Find common contracts for this group
                    common_contracts = []
                    for c, collectors_in_c in contract_to_collectors.items():
                        if coll_set.issubset(collectors_in_c) or len(coll_set & collectors_in_c) >= len(coll_set) * 0.5:
                            common_contracts.append(c)

                    cluster = TasteCluster(
                        cluster_id=f"cluster_{cluster_id}",
                        collectors=list(coll_set),
                        common_artists=common_contracts[:10],
                        size=len(coll_set)
                    )
                    clusters.append(cluster)
                    cluster_id += 1

        # Sort by size
        clusters.sort(key=lambda x: x.size, reverse=True)

        return clusters[:10]  # Top 10 clusters

    def export_results(self, result: SuperScanResult, output_dir: Path) -> Dict[str, Path]:
        """Export SUPER SCAN results"""
        output_dir.mkdir(parents=True, exist_ok=True)
        files = {}

        # JSON export
        json_path = output_dir / f"{result.scan_id}.json"
        with open(json_path, 'w') as f:
            # Convert to serializable format
            data = asdict(result)
            json.dump(data, f, indent=2, default=str)
        files['json'] = json_path

        # Summary markdown
        md_path = output_dir / f"{result.scan_id}_summary.md"
        with open(md_path, 'w') as f:
            f.write(f"# NFT SUPER SCAN: {result.artist_name}\n\n")
            f.write(f"**Scan Date:** {result.scan_date}\n")
            f.write(f"**Duration:** {result.scan_duration_seconds:.1f}s\n")
            f.write(f"**Scan Depth:** {result.scan_depth}\n\n")

            f.write("## Artist Stats\n\n")
            f.write(f"- **Total Mints:** {result.total_mints}\n")
            f.write(f"- **Total Collectors:** {result.total_collectors}\n")
            f.write(f"- **Super Collectors (3+):** {len(result.super_collectors)}\n\n")

            f.write("### Mints by Platform\n\n")
            for platform, count in result.mints_by_platform.items():
                f.write(f"- {platform}: {count}\n")

            f.write("\n### Mints by Network\n\n")
            for network, count in result.mints_by_network.items():
                f.write(f"- {network}: {count}\n")

            f.write("\n## Super Collectors\n\n")
            for i, collector in enumerate(result.super_collectors[:10], 1):
                f.write(f"{i}. `{collector.address[:16]}...` - {collector.pieces_from_artist} pieces\n")

            if result.artist_connections:
                f.write("\n## Related Artists (by collector overlap)\n\n")
                for conn in result.artist_connections[:10]:
                    f.write(f"- **{conn.artist2}** - {conn.shared_collectors} shared collectors ({conn.strength:.1%} overlap)\n")

            if result.taste_clusters:
                f.write("\n## Taste Clusters\n\n")
                for cluster in result.taste_clusters[:5]:
                    f.write(f"### {cluster.cluster_id} ({cluster.size} collectors)\n")
                    f.write(f"Common interests: {len(cluster.common_artists)} contracts\n\n")

            f.write(f"\n## Potential Audience\n\n")
            f.write(f"**Size:** {result.audience_size} addresses\n\n")
            f.write("These are collectors of related artists who don't yet collect your work.\n")

        files['markdown'] = md_path

        logger.info(f"Exported results to {output_dir}")
        return files

    def generate_network_visualization(self, result: SuperScanResult, output_path: Path) -> str:
        """Generate 4D network visualization HTML"""

        # Build visualization data
        nodes = []
        edges = []

        # Artist node (center)
        nodes.append({
            'id': 'artist',
            'type': 'artist',
            'label': result.artist_name,
            'color': '#d4a574',
            'size': 3,
            'x': 0, 'y': 0, 'z': 0
        })

        # Collector nodes (inner ring)
        for i, collector in enumerate(result.collectors[:100]):
            angle = i * GOLDEN_ANGLE * math.pi / 180
            radius = 5 + math.sqrt(collector.pieces_from_artist) * 2

            nodes.append({
                'id': f'collector_{i}',
                'type': 'collector',
                'label': collector.address[:8] + '...',
                'address': collector.address,
                'pieces': collector.pieces_from_artist,
                'color': '#54a876' if collector.pieces_from_artist >= 3 else '#7865ba',
                'size': 0.5 + math.log(collector.pieces_from_artist + 1) * 0.5,
                'x': math.cos(angle) * radius,
                'y': (collector.pieces_from_artist - 2) * 0.5,
                'z': math.sin(angle) * radius
            })

            # Edge to artist
            edges.append({
                'source': 'artist',
                'target': f'collector_{i}',
                'type': 'collected',
                'weight': collector.pieces_from_artist
            })

        # Related artist nodes (outer ring)
        for i, conn in enumerate(result.artist_connections[:30]):
            angle = i * GOLDEN_ANGLE * 1.5 * math.pi / 180
            radius = 15 + i * 0.5

            nodes.append({
                'id': f'related_{i}',
                'type': 'related_artist',
                'label': conn.artist2[:12],
                'shared': conn.shared_collectors,
                'color': '#ba6587',
                'size': 1 + math.log(conn.shared_collectors + 1) * 0.3,
                'x': math.cos(angle) * radius,
                'y': 0,
                'z': math.sin(angle) * radius
            })

            # Edge to artist
            edges.append({
                'source': 'artist',
                'target': f'related_{i}',
                'type': 'related',
                'weight': conn.shared_collectors
            })

            # Edges to shared collectors
            for coll_addr in conn.collector_addresses[:5]:
                # Find collector node
                for j, coll in enumerate(result.collectors[:100]):
                    if coll.address.lower() == coll_addr.lower():
                        edges.append({
                            'source': f'collector_{j}',
                            'target': f'related_{i}',
                            'type': 'also_collects'
                        })
                        break

        # Generate HTML (using template from nft_connections_visualizer)
        html = self._generate_visualization_html(
            nodes, edges, result.artist_name, result
        )

        with open(output_path, 'w') as f:
            f.write(html)

        return str(output_path)

    def _generate_visualization_html(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        title: str,
        result: SuperScanResult
    ) -> str:
        """Generate the visualization HTML"""

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - NFT SUPER SCAN Network</title>
    <style>
        :root {{
            --void: #030308;
            --cosmic: #0a0a12;
            --panel: #0e0e18;
            --border: rgba(255,255,255,0.06);
            --gold: #d4a574;
            --emerald: #54a876;
            --rose: #ba6587;
            --violet: #7865ba;
            --text: #f0ece7;
            --text-dim: #9a9690;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: var(--void);
            color: var(--text);
            font-family: 'Inter', -apple-system, sans-serif;
            overflow: hidden;
        }}
        #container {{ width: 100vw; height: 100vh; }}

        .panel {{
            position: fixed;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            z-index: 100;
        }}

        .info-panel {{
            top: 20px;
            left: 20px;
            max-width: 320px;
        }}

        .stats-panel {{
            top: 20px;
            right: 20px;
            max-width: 280px;
        }}

        h1 {{
            font-size: 1.1rem;
            font-weight: 300;
            letter-spacing: 0.15em;
            margin-bottom: 5px;
            background: linear-gradient(90deg, #d4a574, #ba6587);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            font-size: 0.6rem;
            color: var(--text-dim);
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 15px;
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }}

        .stat {{
            text-align: center;
            padding: 10px;
            background: var(--cosmic);
            border-radius: 8px;
        }}

        .stat-value {{
            font-size: 1.4rem;
            font-weight: 200;
            color: var(--gold);
        }}

        .stat-label {{
            font-size: 0.55rem;
            color: var(--text-dim);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-top: 2px;
        }}

        .legend {{
            margin-top: 15px;
            padding-top: 12px;
            border-top: 1px solid var(--border);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 6px 0;
            font-size: 0.65rem;
            color: var(--text-dim);
        }}

        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}

        .tooltip {{
            position: fixed;
            background: var(--panel);
            border: 1px solid var(--gold);
            border-radius: 8px;
            padding: 12px 16px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s;
            z-index: 200;
            max-width: 260px;
        }}

        .tooltip.visible {{ opacity: 1; }}

        .tooltip h3 {{
            font-size: 0.75rem;
            font-weight: 400;
            color: var(--gold);
            margin-bottom: 6px;
        }}

        .tooltip p {{
            font-size: 0.6rem;
            color: var(--text-dim);
            margin: 2px 0;
        }}

        .controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 8px;
        }}

        .controls button {{
            background: var(--panel);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 0.6rem;
            letter-spacing: 0.1em;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .controls button:hover {{
            border-color: var(--gold);
        }}

        .controls button.active {{
            border-color: var(--gold);
            color: var(--gold);
        }}
    </style>
</head>
<body>
    <div id="container">
        <canvas id="canvas"></canvas>
    </div>

    <div class="panel info-panel">
        <h1>NFT SUPER SCAN</h1>
        <p class="subtitle">{title} Collector Network</p>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-dot" style="background: var(--gold);"></div>
                <span>Artist (center)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: var(--emerald);"></div>
                <span>Super Collectors (3+ pieces)</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: var(--violet);"></div>
                <span>Regular Collectors</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background: var(--rose);"></div>
                <span>Related Artists</span>
            </div>
        </div>
    </div>

    <div class="panel stats-panel">
        <div class="stat-grid">
            <div class="stat">
                <div class="stat-value">{result.total_mints}</div>
                <div class="stat-label">Total Mints</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.total_collectors}</div>
                <div class="stat-label">Collectors</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(result.super_collectors)}</div>
                <div class="stat-label">Super Collectors</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(result.artist_connections)}</div>
                <div class="stat-label">Related Artists</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(result.taste_clusters)}</div>
                <div class="stat-label">Taste Clusters</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.audience_size}</div>
                <div class="stat-label">Potential Audience</div>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip">
        <h3 id="tooltip-title">Node</h3>
        <p id="tooltip-info"></p>
    </div>

    <div class="controls">
        <button onclick="toggleRotation()" id="rotateBtn" class="active">AUTO-ROTATE</button>
        <button onclick="resetView()">RESET</button>
        <button onclick="toggleEdges()" id="edgesBtn" class="active">CONNECTIONS</button>
        <button onclick="focusCollectors()">COLLECTORS</button>
        <button onclick="focusRelated()">RELATED</button>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        const nodesData = {json.dumps(nodes)};
        const edgesData = {json.dumps(edges)};

        // Three.js setup
        const canvas = document.getElementById('canvas');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x030308);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(25, 18, 25);

        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const controls = new THREE.OrbitControls(camera, canvas);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.3;

        // Lights
        scene.add(new THREE.AmbientLight(0x404040, 0.4));

        const light1 = new THREE.PointLight(0xd4a574, 1, 100);
        light1.position.set(20, 20, 20);
        scene.add(light1);

        const light2 = new THREE.PointLight(0x54a876, 0.6, 100);
        light2.position.set(-20, -10, -20);
        scene.add(light2);

        // Create nodes
        const nodeObjects = [];
        const nodeMeshMap = {{}};

        nodesData.forEach(node => {{
            let geometry;
            const size = node.size || 1;

            if (node.type === 'artist') {{
                geometry = new THREE.OctahedronGeometry(size * 1.5);
            }} else if (node.type === 'related_artist') {{
                geometry = new THREE.IcosahedronGeometry(size);
            }} else {{
                geometry = new THREE.SphereGeometry(size * 0.6, 16, 16);
            }}

            const material = new THREE.MeshPhongMaterial({{
                color: new THREE.Color(node.color),
                emissive: new THREE.Color(node.color),
                emissiveIntensity: node.type === 'artist' ? 0.5 : 0.25,
                transparent: true,
                opacity: 0.9
            }});

            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(node.x, node.y, node.z);
            mesh.userData = node;

            scene.add(mesh);
            nodeObjects.push(mesh);
            nodeMeshMap[node.id] = mesh;
        }});

        // Create edges
        const edgeLines = [];

        edgesData.forEach(edge => {{
            const source = nodeMeshMap[edge.source];
            const target = nodeMeshMap[edge.target];

            if (source && target) {{
                const geometry = new THREE.BufferGeometry().setFromPoints([
                    source.position.clone(),
                    target.position.clone()
                ]);

                let color = 0x444444;
                if (edge.type === 'collected') color = 0x54a876;
                else if (edge.type === 'related') color = 0xba6587;
                else if (edge.type === 'also_collects') color = 0x7865ba;

                const material = new THREE.LineBasicMaterial({{
                    color,
                    transparent: true,
                    opacity: 0.15
                }});

                const line = new THREE.Line(geometry, material);
                scene.add(line);
                edgeLines.push(line);
            }}
        }});

        // Interaction
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        const tooltip = document.getElementById('tooltip');

        function onMouseMove(e) {{
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(nodeObjects);

            if (intersects.length > 0) {{
                const node = intersects[0].object.userData;

                document.getElementById('tooltip-title').textContent = node.label;

                let info = '';
                if (node.type === 'artist') {{
                    info = 'Center of the network';
                }} else if (node.type === 'collector') {{
                    info = `Pieces owned: ${{node.pieces}}<br>Address: ${{node.address}}`;
                }} else if (node.type === 'related_artist') {{
                    info = `Shared collectors: ${{node.shared}}`;
                }}

                document.getElementById('tooltip-info').innerHTML = info;
                tooltip.classList.add('visible');
                tooltip.style.left = e.clientX + 15 + 'px';
                tooltip.style.top = e.clientY + 15 + 'px';

                intersects[0].object.material.emissiveIntensity = 0.8;
            }} else {{
                tooltip.classList.remove('visible');
                nodeObjects.forEach(obj => {{
                    obj.material.emissiveIntensity = obj.userData.type === 'artist' ? 0.5 : 0.25;
                }});
            }}
        }}

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        // Controls
        function toggleRotation() {{
            controls.autoRotate = !controls.autoRotate;
            document.getElementById('rotateBtn').classList.toggle('active');
        }}

        function resetView() {{
            camera.position.set(25, 18, 25);
            controls.target.set(0, 0, 0);
        }}

        function toggleEdges() {{
            edgeLines.forEach(l => l.visible = !l.visible);
            document.getElementById('edgesBtn').classList.toggle('active');
        }}

        function focusCollectors() {{
            camera.position.set(10, 8, 10);
            controls.target.set(0, 0, 0);
        }}

        function focusRelated() {{
            camera.position.set(0, 5, 25);
            controls.target.set(0, 0, 0);
        }}

        // Animation
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        animate();
    </script>
</body>
</html>'''


# CLI Interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""
NFT-8 SUPER SCAN - Collector Network Mapper

ULTRATHINK deep scanning of collector networks.

Usage:
  python nft_super_scan.py <wallet1> [wallet2] ... [--name "Artist Name"] [--output ./results/]
  python nft_super_scan.py --file wallets.txt [--name "Artist Name"] [--output ./results/]

Options:
  --name <name>       Artist display name
  --output <dir>      Export directory for results
  --depth <n>         Scan depth (1=collectors, 2=holdings, default: 2)
  --max-collectors <n> Max collectors to deep scan (default: 50)
  --visualize         Generate 4D network visualization

Examples:
  # Scan single wallet
  python nft_super_scan.py 0x1234... --name "My Artist" --output ./scans/

  # Scan multiple wallets with visualization
  python nft_super_scan.py 0x123... tz1abc... --name "Artist" --output ./scans/ --visualize
        """)
        sys.exit(0)

    # Parse arguments
    wallets = []
    artist_name = "Artist"
    output_dir = None
    scan_depth = 2
    max_collectors = 50
    visualize = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--name':
            artist_name = sys.argv[i + 1]
            i += 2
        elif arg == '--output':
            output_dir = Path(sys.argv[i + 1])
            i += 2
        elif arg == '--depth':
            scan_depth = int(sys.argv[i + 1])
            i += 2
        elif arg == '--max-collectors':
            max_collectors = int(sys.argv[i + 1])
            i += 2
        elif arg == '--visualize':
            visualize = True
            i += 1
        elif arg == '--file':
            file_path = Path(sys.argv[i + 1])
            if file_path.exists():
                with open(file_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            wallets.append(line)
            i += 2
        elif not arg.startswith('--'):
            wallets.append(arg)
            i += 1
        else:
            i += 1

    if not wallets:
        print("No wallets provided.")
        sys.exit(1)

    # Run SUPER SCAN
    scanner = NFTSuperScanner(max_workers=3, scan_depth=scan_depth)

    result = scanner.super_scan(
        artist_wallets=wallets,
        artist_name=artist_name,
        max_collectors=max_collectors
    )

    # Export
    if output_dir:
        files = scanner.export_results(result, output_dir)
        print(f"\nExported to: {output_dir}")

        if visualize:
            viz_path = output_dir / f"{result.scan_id}_network.html"
            scanner.generate_network_visualization(result, viz_path)
            print(f"Visualization: {viz_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUPER SCAN SUMMARY: {artist_name}")
    print(f"{'='*60}")
    print(f"Total Mints: {result.total_mints}")
    print(f"Total Collectors: {result.total_collectors}")
    print(f"Super Collectors (3+): {len(result.super_collectors)}")
    print(f"Related Artists: {len(result.artist_connections)}")
    print(f"Taste Clusters: {len(result.taste_clusters)}")
    print(f"Potential Audience: {result.audience_size}")
    print(f"Scan Duration: {result.scan_duration_seconds:.1f}s")
    print()
