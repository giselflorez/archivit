"""
Network Authenticity Analyzer
=============================
Deep forensic analysis of collector networks to detect:
- Wash trading
- Sybil attacks
- Circular trading rings
- Dead-end wallets
- Burst-and-silence patterns

This measures the AUTHENTICITY of activity, not the volume.
"""

import sqlite3
from datetime import datetime, timedelta, timezone

def _now_utc():
    """Return timezone-aware UTC now"""
    return datetime.now(timezone.utc)

def _make_aware(dt):
    """Ensure datetime is timezone-aware (assume UTC if naive)"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            # Parse ISO format strings
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def _days_since(dt):
    """Calculate days since a datetime, handling timezone issues"""
    if dt is None:
        return 9999  # Very old
    dt = _make_aware(dt)
    if dt is None:
        return 9999
    return (_now_utc() - dt).days
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib
import json


class SuspicionLevel(Enum):
    """How suspicious is this pattern?"""
    CLEAN = "clean"              # No red flags
    MINOR = "minor"              # Small concerns, could be innocent
    MODERATE = "moderate"        # Warrants investigation
    HIGH = "high"                # Strong indicators of manipulation
    SEVERE = "severe"            # Almost certainly fraudulent


@dataclass
class WalletProfile:
    """Deep profile of a wallet's behavior"""
    address: str

    # Age and activity
    first_seen: Optional[datetime] = None
    last_active: Optional[datetime] = None
    total_transactions: int = 0

    # Diversity metrics
    unique_artists_collected: int = 0
    unique_platforms_used: int = 0
    defi_activity: bool = False
    nft_activity_outside_artist: bool = False

    # Identity signals
    has_ens: bool = False
    has_twitter_link: bool = False
    has_other_social: bool = False

    # Funding analysis
    primary_funding_source: Optional[str] = None
    funding_chain_depth: int = 0  # How many hops from major exchange/known source

    # Holdings
    total_nfts_held: int = 0
    single_artist_ratio: float = 0.0  # What % of holdings are this one artist

    # Behavior patterns
    avg_hold_time_days: float = 0.0
    immediate_flip_count: int = 0  # Sold within 24 hours

    # Suspicion flags
    suspicion_flags: List[str] = field(default_factory=list)
    vitality_score: float = 0.0  # 0-100


@dataclass
class NetworkAnalysis:
    """Complete network analysis results"""
    artist_address: str
    analyzed_at: datetime

    # Collector metrics
    total_collectors: int = 0
    verified_real_collectors: int = 0
    suspicious_collectors: int = 0
    dead_end_wallets: int = 0
    sybil_cluster_count: int = 0

    # Network metrics
    circular_trading_detected: bool = False
    circular_ring_size: int = 0
    shared_funding_clusters: int = 0
    ecosystem_connectivity: float = 0.0  # How connected to broader NFT ecosystem

    # Transaction metrics
    wash_trade_indicators: int = 0
    self_dealing_volume_eth: float = 0.0
    legitimate_volume_eth: float = 0.0

    # Timeline metrics
    activity_pattern: str = "unknown"  # "organic", "burst_silence", "artificial"
    growth_consistency: float = 0.0

    # Final scores (0-100)
    collector_vitality_score: float = 0.0
    network_authenticity_score: float = 0.0
    transaction_legitimacy_score: float = 0.0
    timeline_health_score: float = 0.0

    # Overall
    overall_authenticity_score: float = 0.0
    suspicion_level: SuspicionLevel = SuspicionLevel.CLEAN

    # Detailed findings
    findings: List[Dict] = field(default_factory=list)


class NetworkAuthenticityAnalyzer:
    """
    Analyzes the authenticity of an artist's collector network.

    This is NOT about volume - it's about detecting manipulation:
    - Are collectors real people or sybil wallets?
    - Is trading organic or circular/wash trading?
    - Do wallets show signs of life or are they dead ends?
    """

    # Known exchange/bridge addresses (funding sources that are legitimate)
    KNOWN_LEGITIMATE_SOURCES = {
        '0x28c6c06298d514db089934071355e5743bf21d60': 'Binance Hot Wallet',
        '0x21a31ee1afc51d94c2efccaa2092ad1028285549': 'Binance Hot Wallet 2',
        '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': 'Binance Hot Wallet 3',
        '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': 'Coinbase Prime',
        '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43': 'Coinbase Commerce',
        '0x71660c4005ba85c37ccec55d0c4493e66fe775d3': 'Coinbase Hot Wallet',
        '0x503828976d22510aad0201ac7ec88293211d23da': 'Coinbase Cold Wallet',
        '0x0d0707963952f2fba59dd06f2b425ace40b492fe': 'Gate.io',
        '0xd24400ae8bfebb18ca49be86258a3c749cf46853': 'Gemini',
        '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0': 'Kraken',
    }

    # Suspicious patterns
    DEAD_WALLET_INACTIVITY_DAYS = 180  # No activity in 6 months
    SYBIL_CREATION_WINDOW_DAYS = 7     # Wallets created within 7 days of each other
    WASH_TRADE_TIME_THRESHOLD_HOURS = 24
    MIN_HOLD_TIME_DAYS = 1             # Less than this is suspicious

    def __init__(self, db_path: str = "db/blockchain_tracking.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize analysis tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.executescript("""
            -- Wallet profiles cache
            CREATE TABLE IF NOT EXISTS wallet_profiles (
                address TEXT PRIMARY KEY,
                profile_json TEXT,
                analyzed_at TIMESTAMP,
                vitality_score REAL
            );

            -- Network analysis results
            CREATE TABLE IF NOT EXISTS network_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_address TEXT,
                analysis_json TEXT,
                analyzed_at TIMESTAMP,
                overall_score REAL,
                suspicion_level TEXT
            );

            -- Funding source graph
            CREATE TABLE IF NOT EXISTS funding_graph (
                from_address TEXT,
                to_address TEXT,
                total_eth REAL,
                first_transfer TIMESTAMP,
                last_transfer TIMESTAMP,
                transfer_count INTEGER,
                PRIMARY KEY (from_address, to_address)
            );

            -- Sybil clusters
            CREATE TABLE IF NOT EXISTS sybil_clusters (
                cluster_id INTEGER,
                wallet_address TEXT,
                confidence REAL,
                detected_at TIMESTAMP,
                PRIMARY KEY (cluster_id, wallet_address)
            );

            -- Circular trading rings
            CREATE TABLE IF NOT EXISTS circular_rings (
                ring_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ring_members TEXT,  -- JSON array of addresses
                ring_size INTEGER,
                total_volume_eth REAL,
                detected_at TIMESTAMP
            );
        """)

        conn.commit()
        conn.close()

    def analyze_artist_network(self, artist_address: str,
                                collector_addresses: List[str],
                                transfers: List[Dict]) -> NetworkAnalysis:
        """
        Perform complete network authenticity analysis.

        Args:
            artist_address: The artist's wallet
            collector_addresses: All wallets that have collected from this artist
            transfers: All transfer records involving the artist's works

        Returns:
            NetworkAnalysis with scores and findings
        """
        analysis = NetworkAnalysis(
            artist_address=artist_address,
            analyzed_at=_now_utc(),
            total_collectors=len(collector_addresses)
        )

        # Step 1: Profile each collector wallet
        wallet_profiles = self._profile_all_wallets(collector_addresses, artist_address)

        # Step 2: Analyze funding sources for sybil detection
        sybil_clusters = self._detect_sybil_clusters(wallet_profiles)
        analysis.sybil_cluster_count = len(sybil_clusters)

        # Step 3: Detect circular trading
        circular_rings = self._detect_circular_trading(transfers)
        analysis.circular_trading_detected = len(circular_rings) > 0
        analysis.circular_ring_size = max([len(r) for r in circular_rings], default=0)

        # Step 4: Identify dead-end wallets
        dead_ends = self._identify_dead_end_wallets(wallet_profiles)
        analysis.dead_end_wallets = len(dead_ends)

        # Step 5: Analyze transaction legitimacy
        wash_analysis = self._analyze_wash_trading(transfers, wallet_profiles)
        analysis.wash_trade_indicators = wash_analysis['indicators']
        analysis.self_dealing_volume_eth = wash_analysis['suspicious_volume']
        analysis.legitimate_volume_eth = wash_analysis['legitimate_volume']

        # Step 6: Analyze timeline patterns
        timeline_analysis = self._analyze_timeline_patterns(transfers)
        analysis.activity_pattern = timeline_analysis['pattern']
        analysis.growth_consistency = timeline_analysis['consistency']

        # Step 7: Calculate component scores
        analysis.collector_vitality_score = self._calculate_vitality_score(wallet_profiles)
        analysis.network_authenticity_score = self._calculate_network_score(
            sybil_clusters, circular_rings, wallet_profiles
        )
        analysis.transaction_legitimacy_score = self._calculate_transaction_score(wash_analysis)
        analysis.timeline_health_score = timeline_analysis['score']

        # Step 8: Calculate overall score with weights
        analysis.overall_authenticity_score = (
            analysis.collector_vitality_score * 0.35 +
            analysis.network_authenticity_score * 0.30 +
            analysis.transaction_legitimacy_score * 0.20 +
            analysis.timeline_health_score * 0.15
        )

        # Step 9: Determine suspicion level
        analysis.suspicion_level = self._determine_suspicion_level(analysis)

        # Step 10: Compile findings
        analysis.findings = self._compile_findings(
            analysis, wallet_profiles, sybil_clusters, circular_rings, dead_ends
        )

        # Store results
        self._store_analysis(analysis)

        return analysis

    def _profile_all_wallets(self, addresses: List[str],
                             artist_address: str) -> Dict[str, WalletProfile]:
        """Create detailed profiles for all collector wallets"""
        profiles = {}

        for address in addresses:
            profile = self._profile_wallet(address, artist_address)
            profiles[address] = profile

        return profiles

    def _profile_wallet(self, address: str, artist_address: str) -> WalletProfile:
        """
        Deep profile of a single wallet's behavior.

        We're looking for signs of REAL activity vs fake/sybil.
        """
        profile = WalletProfile(address=address)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get wallet's first and last activity
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
            FROM nft_transfers
            WHERE from_address = ? OR to_address = ?
        """, (address, address))

        row = cursor.fetchone()
        if row and row[0]:
            profile.first_seen = datetime.fromisoformat(row[0]) if isinstance(row[0], str) else row[0]
            profile.last_active = datetime.fromisoformat(row[1]) if isinstance(row[1], str) else row[1]
            profile.total_transactions = row[2]

        # Count unique artists this wallet has collected
        cursor.execute("""
            SELECT COUNT(DISTINCT creator_address)
            FROM nft_transfers t
            JOIN tracked_nfts n ON t.contract_address = n.contract_address
                AND t.token_id = n.token_id
            WHERE t.to_address = ?
        """, (address,))

        row = cursor.fetchone()
        profile.unique_artists_collected = row[0] if row else 0

        # Check if wallet has activity outside this artist
        cursor.execute("""
            SELECT COUNT(*)
            FROM nft_transfers t
            JOIN tracked_nfts n ON t.contract_address = n.contract_address
                AND t.token_id = n.token_id
            WHERE (t.to_address = ? OR t.from_address = ?)
            AND n.creator_address != ?
        """, (address, address, artist_address))

        row = cursor.fetchone()
        profile.nft_activity_outside_artist = (row[0] if row else 0) > 0

        # Calculate single-artist ratio
        cursor.execute("""
            SELECT
                SUM(CASE WHEN n.creator_address = ? THEN 1 ELSE 0 END) as artist_count,
                COUNT(*) as total_count
            FROM nft_transfers t
            JOIN tracked_nfts n ON t.contract_address = n.contract_address
                AND t.token_id = n.token_id
            WHERE t.to_address = ?
        """, (artist_address, address))

        row = cursor.fetchone()
        if row and row[1] > 0:
            profile.single_artist_ratio = row[0] / row[1]

        # Calculate average hold time
        cursor.execute("""
            SELECT AVG(
                JULIANDAY(sell_time) - JULIANDAY(buy_time)
            ) as avg_hold_days
            FROM (
                SELECT
                    t1.timestamp as buy_time,
                    t2.timestamp as sell_time
                FROM nft_transfers t1
                JOIN nft_transfers t2
                    ON t1.contract_address = t2.contract_address
                    AND t1.token_id = t2.token_id
                    AND t1.to_address = ?
                    AND t2.from_address = ?
                    AND t2.timestamp > t1.timestamp
            )
        """, (address, address))

        row = cursor.fetchone()
        profile.avg_hold_time_days = row[0] if row and row[0] else 0

        # Count immediate flips (sold within 24 hours)
        cursor.execute("""
            SELECT COUNT(*)
            FROM nft_transfers t1
            JOIN nft_transfers t2
                ON t1.contract_address = t2.contract_address
                AND t1.token_id = t2.token_id
                AND t1.to_address = ?
                AND t2.from_address = ?
                AND JULIANDAY(t2.timestamp) - JULIANDAY(t1.timestamp) < 1
        """, (address, address))

        row = cursor.fetchone()
        profile.immediate_flip_count = row[0] if row else 0

        conn.close()

        # Calculate vitality score
        profile.vitality_score = self._calculate_wallet_vitality(profile)

        # Add suspicion flags
        profile.suspicion_flags = self._get_wallet_suspicion_flags(profile)

        return profile

    def _calculate_wallet_vitality(self, profile: WalletProfile) -> float:
        """
        Calculate how "alive" and "real" this wallet appears.

        High vitality = real, active collector
        Low vitality = potential sybil/dead-end
        """
        score = 50.0  # Start at neutral

        # Positive signals
        if profile.unique_artists_collected > 5:
            score += 15
        elif profile.unique_artists_collected > 1:
            score += 10

        if profile.nft_activity_outside_artist:
            score += 10

        if profile.has_ens:
            score += 10

        if profile.has_twitter_link:
            score += 10

        if profile.defi_activity:
            score += 5

        # Check for recent activity
        if profile.last_active:
            days_inactive = _days_since(profile.last_active)
            if days_inactive < 30:
                score += 10
            elif days_inactive < 90:
                score += 5
            elif days_inactive > self.DEAD_WALLET_INACTIVITY_DAYS:
                score -= 20

        # Negative signals
        if profile.single_artist_ratio > 0.9:
            score -= 15  # Only collects this one artist

        if profile.immediate_flip_count > 2:
            score -= 10  # Multiple quick flips

        if profile.avg_hold_time_days < self.MIN_HOLD_TIME_DAYS and profile.avg_hold_time_days > 0:
            score -= 15  # Holds for less than a day on average

        if profile.total_transactions < 3:
            score -= 10  # Very limited activity

        return max(0, min(100, score))

    def _get_wallet_suspicion_flags(self, profile: WalletProfile) -> List[str]:
        """Identify specific red flags for a wallet"""
        flags = []

        if profile.single_artist_ratio > 0.95:
            flags.append("single_artist_collector")

        if profile.avg_hold_time_days < 1 and profile.avg_hold_time_days > 0:
            flags.append("very_short_hold_times")

        if profile.immediate_flip_count > 3:
            flags.append("frequent_immediate_flips")

        if profile.last_active:
            days_inactive = _days_since(profile.last_active)
            if days_inactive > self.DEAD_WALLET_INACTIVITY_DAYS:
                flags.append("dormant_wallet")

        if profile.total_transactions < 3:
            flags.append("minimal_activity")

        if not profile.nft_activity_outside_artist:
            flags.append("no_external_nft_activity")

        return flags

    def _detect_sybil_clusters(self, profiles: Dict[str, WalletProfile]) -> List[Set[str]]:
        """
        Detect clusters of wallets that appear to be controlled by the same entity.

        Sybil indicators:
        - Funded from same source
        - Created around same time
        - Similar behavior patterns
        - Only interact with each other and the artist
        """
        clusters = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Group wallets by funding source
        funding_groups = defaultdict(set)

        for address in list(profiles.keys()):
            # Get primary funding source (simplified - would need full chain trace)
            cursor.execute("""
                SELECT from_address, SUM(value_eth) as total
                FROM eth_transfers
                WHERE to_address = ?
                GROUP BY from_address
                ORDER BY total DESC
                LIMIT 1
            """, (address,))

            row = cursor.fetchone()
            if row:
                # Check if funding source is a known exchange (legitimate)
                if row[0] not in self.KNOWN_LEGITIMATE_SOURCES:
                    funding_groups[row[0]].add(address)

        # Any funding group with 3+ wallets is suspicious
        for source, wallets in list(funding_groups.items()):
            if len(wallets) >= 3:
                clusters.append(wallets)

        # Also check for wallets created at similar times with similar patterns
        addresses = list(profiles.keys())
        for i, addr1 in enumerate(addresses):
            for addr2 in addresses[i+1:]:
                p1, p2 = profiles[addr1], profiles[addr2]

                # Check if created around same time
                if p1.first_seen and p2.first_seen:
                    dt1 = _make_aware(p1.first_seen)
                    dt2 = _make_aware(p2.first_seen)
                    if dt1 and dt2:
                        days_apart = abs((dt1 - dt2).days)
                    else:
                        days_apart = 9999

                    if days_apart < self.SYBIL_CREATION_WINDOW_DAYS:
                        # Check for behavioral similarity
                        similarity_score = self._calculate_behavior_similarity(p1, p2)

                        if similarity_score > 0.8:
                            # Find or create cluster
                            found_cluster = False
                            for cluster in clusters:
                                if addr1 in cluster or addr2 in cluster:
                                    cluster.add(addr1)
                                    cluster.add(addr2)
                                    found_cluster = True
                                    break

                            if not found_cluster:
                                clusters.append({addr1, addr2})

        conn.close()

        return clusters

    def _calculate_behavior_similarity(self, p1: WalletProfile, p2: WalletProfile) -> float:
        """Calculate how similar two wallet's behaviors are (0-1)"""
        similarity = 0.0
        checks = 0

        # Similar hold times
        if p1.avg_hold_time_days > 0 and p2.avg_hold_time_days > 0:
            time_diff = abs(p1.avg_hold_time_days - p2.avg_hold_time_days)
            if time_diff < 2:  # Within 2 days
                similarity += 1
            checks += 1

        # Similar activity levels
        if p1.total_transactions > 0 and p2.total_transactions > 0:
            ratio = min(p1.total_transactions, p2.total_transactions) / max(p1.total_transactions, p2.total_transactions)
            if ratio > 0.7:
                similarity += 1
            checks += 1

        # Both single-artist collectors
        if p1.single_artist_ratio > 0.9 and p2.single_artist_ratio > 0.9:
            similarity += 1
        checks += 1

        # Both no external activity
        if not p1.nft_activity_outside_artist and not p2.nft_activity_outside_artist:
            similarity += 1
        checks += 1

        # Similar flip patterns
        if abs(p1.immediate_flip_count - p2.immediate_flip_count) <= 1:
            similarity += 1
        checks += 1

        return similarity / checks if checks > 0 else 0

    def _detect_circular_trading(self, transfers: List[Dict]) -> List[List[str]]:
        """
        Detect circular trading patterns where NFTs pass through a ring
        of wallets and return near the origin.

        A -> B -> C -> A (or close to A)
        """
        rings = []

        # Build transfer graph
        graph = defaultdict(lambda: defaultdict(int))
        for t in transfers:
            from_addr = t.get('from_address', '').lower()
            to_addr = t.get('to_address', '').lower()
            if from_addr and to_addr:
                graph[from_addr][to_addr] += 1

        # Find cycles using DFS
        visited_global = set()

        def find_cycles(start: str, current: str, path: List[str], visited: Set[str]) -> List[List[str]]:
            cycles = []

            for next_addr in graph[current]:
                if next_addr == start and len(path) >= 3:
                    # Found a cycle back to start
                    cycles.append(path + [next_addr])
                elif next_addr not in visited and len(path) < 10:  # Limit depth
                    cycles.extend(find_cycles(
                        start, next_addr, path + [next_addr], visited | {next_addr}
                    ))

            return cycles

        for start_addr in list(graph.keys()):
            if start_addr not in visited_global:
                cycles = find_cycles(start_addr, start_addr, [start_addr], {start_addr})
                for cycle in cycles:
                    if len(cycle) >= 3 and cycle not in rings:
                        rings.append(cycle)
                        visited_global.update(cycle)

        return rings

    def _identify_dead_end_wallets(self, profiles: Dict[str, WalletProfile]) -> List[str]:
        """
        Find wallets that receive NFTs but show no subsequent activity.
        These could be storage wallets used to fake collector count.
        """
        dead_ends = []

        for address, profile in list(profiles.items()):
            is_dead_end = True

            # Check for recent activity
            if profile.last_active:
                days_inactive = _days_since(profile.last_active)
                if days_inactive < self.DEAD_WALLET_INACTIVITY_DAYS:
                    is_dead_end = False

            # Check for any outgoing transfers
            if profile.total_transactions > 1:  # More than just receiving
                is_dead_end = False

            # Check for other activity
            if profile.nft_activity_outside_artist or profile.defi_activity:
                is_dead_end = False

            if is_dead_end:
                dead_ends.append(address)

        return dead_ends

    def _analyze_wash_trading(self, transfers: List[Dict],
                              profiles: Dict[str, WalletProfile]) -> Dict:
        """
        Analyze transfers for wash trading indicators.

        Wash trading: selling to yourself (directly or through intermediaries)
        to create fake volume/price history.
        """
        result = {
            'indicators': 0,
            'suspicious_volume': 0.0,
            'legitimate_volume': 0.0,
            'suspicious_transfers': []
        }

        for transfer in transfers:
            suspicious = False
            reasons = []

            from_addr = transfer.get('from_address', '').lower()
            to_addr = transfer.get('to_address', '').lower()
            value_eth = transfer.get('value_eth', 0)

            if not from_addr or not to_addr:
                continue

            # Get profiles
            from_profile = profiles.get(from_addr)
            to_profile = profiles.get(to_addr)

            # Check 1: Buyer has low vitality
            if to_profile and to_profile.vitality_score < 30:
                suspicious = True
                reasons.append("buyer_low_vitality")

            # Check 2: Buyer only collects this artist
            if to_profile and to_profile.single_artist_ratio > 0.95:
                suspicious = True
                reasons.append("buyer_single_artist")

            # Check 3: Very quick flip (if we can detect)
            if to_profile and to_profile.avg_hold_time_days < 1:
                suspicious = True
                reasons.append("likely_quick_flip")

            # Check 4: Suspicion flags on buyer
            if to_profile and len(to_profile.suspicion_flags) >= 3:
                suspicious = True
                reasons.append("buyer_multiple_red_flags")

            if suspicious:
                result['indicators'] += 1
                result['suspicious_volume'] += value_eth
                result['suspicious_transfers'].append({
                    'from': from_addr,
                    'to': to_addr,
                    'value_eth': value_eth,
                    'reasons': reasons
                })
            else:
                result['legitimate_volume'] += value_eth

        return result

    def _analyze_timeline_patterns(self, transfers: List[Dict]) -> Dict:
        """
        Analyze the timeline of activity for organic vs artificial patterns.

        Organic: Gradual growth, sustained activity
        Artificial: Burst of activity, then silence
        """
        if not transfers:
            return {
                'pattern': 'no_data',
                'consistency': 0,
                'score': 50
            }

        # Group transfers by month
        monthly_counts = defaultdict(int)
        for t in transfers:
            timestamp = t.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp)
                else:
                    dt = timestamp
                month_key = f"{dt.year}-{dt.month:02d}"
                monthly_counts[month_key] += 1

        if not monthly_counts:
            return {
                'pattern': 'no_data',
                'consistency': 0,
                'score': 50
            }

        # Sort by month
        sorted_months = sorted(monthly_counts.items())
        counts = [c for _, c in sorted_months]

        # Analyze pattern
        if len(counts) < 3:
            return {
                'pattern': 'limited_data',
                'consistency': 50,
                'score': 50
            }

        # Calculate metrics
        max_count = max(counts)
        avg_count = sum(counts) / len(counts)

        # Check for burst-and-silence
        # If first few months are way higher than later months
        first_quarter = counts[:len(counts)//4] if len(counts) >= 4 else counts[:1]
        last_quarter = counts[-(len(counts)//4):] if len(counts) >= 4 else counts[-1:]

        first_avg = sum(first_quarter) / len(first_quarter) if first_quarter else 0
        last_avg = sum(last_quarter) / len(last_quarter) if last_quarter else 0

        # Pattern detection
        pattern = 'organic'
        consistency = 0
        score = 70

        if first_avg > 0 and last_avg == 0:
            pattern = 'burst_silence'
            consistency = 20
            score = 25
        elif first_avg > 0 and first_avg > last_avg * 5:
            pattern = 'declining'
            consistency = 40
            score = 45
        elif last_avg > first_avg:
            pattern = 'growing'
            consistency = 80
            score = 85
        else:
            # Calculate coefficient of variation for consistency
            if avg_count > 0:
                variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
                std_dev = variance ** 0.5
                cv = std_dev / avg_count

                consistency = max(0, 100 - (cv * 50))
                score = 50 + (consistency / 2)

        return {
            'pattern': pattern,
            'consistency': consistency,
            'score': score,
            'monthly_data': dict(sorted_months)
        }

    def _calculate_vitality_score(self, profiles: Dict[str, WalletProfile]) -> float:
        """Calculate overall collector vitality score"""
        if not profiles:
            return 50.0

        # Average vitality across all collectors
        total_vitality = sum(p.vitality_score for p in profiles.values())
        avg_vitality = total_vitality / len(profiles)

        # Bonus for having diverse collectors
        high_vitality_count = sum(1 for p in profiles.values() if p.vitality_score > 70)
        diversity_bonus = min(20, (high_vitality_count / len(profiles)) * 30)

        return min(100, avg_vitality + diversity_bonus)

    def _calculate_network_score(self, sybil_clusters: List[Set[str]],
                                  circular_rings: List[List[str]],
                                  profiles: Dict[str, WalletProfile]) -> float:
        """Calculate network authenticity score"""
        score = 100.0

        total_collectors = len(profiles)
        if total_collectors == 0:
            return 50.0

        # Penalty for sybil clusters
        sybil_count = sum(len(c) for c in sybil_clusters)
        sybil_ratio = sybil_count / total_collectors
        score -= sybil_ratio * 40  # Up to 40 point penalty

        # Penalty for circular trading
        if circular_rings:
            ring_size = max(len(r) for r in circular_rings)
            score -= min(30, ring_size * 5)  # Up to 30 point penalty

        # Bonus for ecosystem connectivity
        connected_collectors = sum(
            1 for p in profiles.values()
            if p.unique_artists_collected > 3
        )
        connectivity_ratio = connected_collectors / total_collectors
        score += connectivity_ratio * 20  # Up to 20 point bonus

        return max(0, min(100, score))

    def _calculate_transaction_score(self, wash_analysis: Dict) -> float:
        """Calculate transaction legitimacy score"""
        total_volume = wash_analysis['suspicious_volume'] + wash_analysis['legitimate_volume']

        if total_volume == 0:
            return 50.0

        legitimate_ratio = wash_analysis['legitimate_volume'] / total_volume

        # Base score from legitimate ratio
        score = legitimate_ratio * 80

        # Penalty for high number of indicators
        indicator_penalty = min(30, wash_analysis['indicators'] * 3)
        score -= indicator_penalty

        # Bonus if no suspicious activity
        if wash_analysis['indicators'] == 0:
            score += 20

        return max(0, min(100, score))

    def _determine_suspicion_level(self, analysis: NetworkAnalysis) -> SuspicionLevel:
        """Determine overall suspicion level from analysis"""
        score = analysis.overall_authenticity_score

        # Also consider specific red flags
        severe_flags = 0

        if analysis.circular_trading_detected and analysis.circular_ring_size >= 4:
            severe_flags += 1

        if analysis.sybil_cluster_count >= 3:
            severe_flags += 1

        if analysis.dead_end_wallets > analysis.total_collectors * 0.5:
            severe_flags += 1

        if analysis.activity_pattern == 'burst_silence':
            severe_flags += 1

        # Determine level
        if severe_flags >= 3 or score < 20:
            return SuspicionLevel.SEVERE
        elif severe_flags >= 2 or score < 35:
            return SuspicionLevel.HIGH
        elif severe_flags >= 1 or score < 50:
            return SuspicionLevel.MODERATE
        elif score < 70:
            return SuspicionLevel.MINOR
        else:
            return SuspicionLevel.CLEAN

    def _compile_findings(self, analysis: NetworkAnalysis,
                          profiles: Dict[str, WalletProfile],
                          sybil_clusters: List[Set[str]],
                          circular_rings: List[List[str]],
                          dead_ends: List[str]) -> List[Dict]:
        """Compile human-readable findings"""
        findings = []

        # Sybil findings
        if sybil_clusters:
            findings.append({
                'type': 'sybil_clusters',
                'severity': 'high' if len(sybil_clusters) > 2 else 'moderate',
                'title': f'Detected {len(sybil_clusters)} potential sybil cluster(s)',
                'description': f'{sum(len(c) for c in sybil_clusters)} wallets appear to be controlled by fewer unique entities',
                'details': [list(c) for c in sybil_clusters]
            })

        # Circular trading findings
        if circular_rings:
            findings.append({
                'type': 'circular_trading',
                'severity': 'high',
                'title': f'Circular trading detected',
                'description': f'Found {len(circular_rings)} trading ring(s) where NFTs cycle through the same wallets',
                'details': circular_rings
            })

        # Dead-end wallet findings
        if dead_ends:
            ratio = len(dead_ends) / len(profiles) if profiles else 0
            severity = 'high' if ratio > 0.4 else 'moderate' if ratio > 0.2 else 'minor'
            findings.append({
                'type': 'dead_end_wallets',
                'severity': severity,
                'title': f'{len(dead_ends)} dead-end wallet(s) detected',
                'description': f'{ratio*100:.1f}% of collectors show no activity after receiving NFTs',
                'details': dead_ends[:10]  # First 10
            })

        # Timeline pattern findings
        if analysis.activity_pattern == 'burst_silence':
            findings.append({
                'type': 'timeline_anomaly',
                'severity': 'high',
                'title': 'Burst-and-silence activity pattern',
                'description': 'Activity spiked then dropped to near zero, suggesting artificial inflation',
                'details': None
            })

        # Positive findings
        verified_real = sum(1 for p in profiles.values() if p.vitality_score > 70)
        if verified_real > 0:
            findings.append({
                'type': 'positive',
                'severity': 'good',
                'title': f'{verified_real} verified real collector(s)',
                'description': f'These collectors show diverse activity and authentic engagement',
                'details': [addr for addr, p in profiles.items() if p.vitality_score > 70][:10]
            })

        return findings

    def _store_analysis(self, analysis: NetworkAnalysis):
        """Store analysis results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO network_analyses
            (artist_address, analysis_json, analyzed_at, overall_score, suspicion_level)
            VALUES (?, ?, ?, ?, ?)
        """, (
            analysis.artist_address,
            json.dumps({
                'total_collectors': analysis.total_collectors,
                'sybil_clusters': analysis.sybil_cluster_count,
                'circular_trading': analysis.circular_trading_detected,
                'dead_end_wallets': analysis.dead_end_wallets,
                'activity_pattern': analysis.activity_pattern,
                'scores': {
                    'collector_vitality': analysis.collector_vitality_score,
                    'network_authenticity': analysis.network_authenticity_score,
                    'transaction_legitimacy': analysis.transaction_legitimacy_score,
                    'timeline_health': analysis.timeline_health_score
                },
                'findings': analysis.findings
            }),
            analysis.analyzed_at.isoformat(),
            analysis.overall_authenticity_score,
            analysis.suspicion_level.value
        ))

        conn.commit()
        conn.close()


# Convenience function
def analyze_artist_network(artist_address: str,
                           collector_addresses: List[str],
                           transfers: List[Dict]) -> NetworkAnalysis:
    """Analyze an artist's collector network for authenticity"""
    analyzer = NetworkAuthenticityAnalyzer()
    return analyzer.analyze_artist_network(artist_address, collector_addresses, transfers)
