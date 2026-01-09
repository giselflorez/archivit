#!/usr/bin/env python3
"""
Living Works Temporal Framework
Tracks NFTs as temporal entities with past iterations, future events, and live reactivity

This module treats NFTs not as static snapshots but as living entities that:
- Have PAST: Previous states, reveals, evolutions
- Have PRESENT: Current live state, real-time reactivity
- Have FUTURE: Scheduled reveals, phase changes, decay

Classes:
    HistoricalStateTracker: Extract and archive historical states of NFTs
    FutureEventDetector: Detect scheduled events in contracts and metadata
    LiveWorkTracker: Track and archive states of reactive/living NFTs
"""

import os
import json
import requests
import logging
import time
import hashlib
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.multi_provider_web3 import MultiProviderWeb3
from collectors.blockchain_db import get_db
from collectors.raw_nft_parser import RawNFTParser, IPFS_GATEWAYS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event signatures for detecting metadata updates
METADATA_UPDATE_TOPICS = [
    # Standard ERC-1155 URI event
    "0x6bb7ff708619ba0610cba295a58592e0451dee2622938c8755667688daf3529b",  # URI(string,uint256)
    # Common custom events
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",  # MetadataUpdate(uint256)
]

# Common reveal-related function signatures
REVEAL_FUNCTION_SIGS = {
    '0x9a8a0592': 'reveal()',
    '0xa475b5dd': 'reveal()',
    '0x5b7633d0': 'revealAll()',
    '0x40c10f19': 'mint(address,uint256)',  # Sometimes triggers reveal
}

# Common time-related storage variable patterns
TIME_VAR_PATTERNS = [
    'revealTime', 'revealDate', 'revealTimestamp',
    'startTime', 'endTime', 'closeTime',
    'phaseEnd', 'phaseStart', 'phase1End', 'phase2Start',
    'unlockTime', 'lockEnd',
    'expirationTime', 'expiry', 'expires',
    'decayStart', 'decayRate',
    'auctionEnd', 'auctionStart',
    'mintStart', 'mintEnd', 'publicMintStart',
]


class HistoricalStateTracker:
    """
    Extract and archive historical states of NFTs

    Tracks:
    - Reveal mechanisms (placeholder -> revealed artwork)
    - Dynamic metadata updates
    - On-chain attribute evolution
    - Generative variations over time
    """

    def __init__(self, network: str = 'ethereum'):
        """Initialize with blockchain connection"""
        self.web3 = MultiProviderWeb3(network)
        self.network = network
        self.parser = RawNFTParser(network)
        self.db = get_db()

    def get_token_uri_at_block(
        self,
        contract: str,
        token_id: int,
        block_number: int
    ) -> Optional[str]:
        """
        Query tokenURI at a specific historical block

        This allows us to see what the metadata was at different points in time.
        """
        # Encode call data: tokenURI(uint256)
        call_data = "0xc87b56dd" + hex(token_id)[2:].zfill(64)

        result = self.web3.rpc_call('eth_call', [
            {'to': contract, 'data': call_data},
            hex(block_number)
        ])

        if result and result != '0x':
            try:
                hex_data = result[2:]
                if len(hex_data) >= 128:
                    length = int(hex_data[64:128], 16)
                    string_hex = hex_data[128:128 + length * 2]
                    return bytes.fromhex(string_hex).decode('utf-8').strip('\x00')
            except Exception as e:
                logger.debug(f"Failed to decode tokenURI at block {block_number}: {e}")

        return None

    def get_metadata_update_events(
        self,
        contract: str,
        token_id: int = None,
        from_block: int = 0
    ) -> List[Dict]:
        """
        Find all metadata update events for a contract/token

        Searches for:
        - Standard URI events (ERC-1155)
        - Custom MetadataUpdate events
        - Reveal transactions
        """
        events = []
        to_block = self.web3.get_block_number() or from_block + 10000

        # Search for each metadata update topic
        for topic in METADATA_UPDATE_TOPICS:
            logs = self._get_logs_chunked(
                contract=contract,
                topics=[topic],
                from_block=from_block,
                to_block=to_block
            )

            for log in logs:
                event = self._parse_metadata_event(log)
                if event:
                    if token_id is None or event.get('token_id') == token_id:
                        events.append(event)

        # Also search for reveal() transactions
        reveal_events = self._find_reveal_transactions(contract, from_block, to_block)
        events.extend(reveal_events)

        # Sort by block number
        events.sort(key=lambda x: x.get('block_number', 0))

        return events

    def _get_logs_chunked(
        self,
        contract: str,
        topics: List[str],
        from_block: int,
        to_block: int,
        chunk_size: int = 500
    ) -> List[Dict]:
        """Get logs in chunks to avoid timeout"""
        all_logs = []
        current = from_block

        while current < to_block:
            end = min(current + chunk_size, to_block)

            logs = self.web3.get_logs(
                from_block=current,
                to_block=end,
                address=contract,
                topics=topics
            )

            if logs:
                all_logs.extend(logs)

            current = end + 1
            time.sleep(0.05)  # Rate limiting

        return all_logs

    def _parse_metadata_event(self, log: Dict) -> Optional[Dict]:
        """Parse a metadata update event log"""
        try:
            block_num = log.get('blockNumber')
            if isinstance(block_num, str):
                block_num = int(block_num, 16)

            return {
                'type': 'metadata_update',
                'block_number': block_num,
                'tx_hash': log.get('transactionHash'),
                'contract': log.get('address'),
                'log_index': log.get('logIndex'),
            }
        except Exception as e:
            logger.debug(f"Failed to parse metadata event: {e}")
            return None

    def _find_reveal_transactions(
        self,
        contract: str,
        from_block: int,
        to_block: int
    ) -> List[Dict]:
        """Find reveal() function calls to the contract"""
        events = []

        # This requires iterating through transactions, which is expensive
        # For now, we'll rely on event-based detection
        # In production, you'd use a transaction indexer or The Graph

        return events

    def get_token_uri_history(
        self,
        contract: str,
        token_id: int,
        from_block: int = 0
    ) -> List[Dict]:
        """
        Get all tokenURI values this NFT has had over time

        Returns list of states with:
        - block number
        - timestamp
        - token_uri
        - metadata (fetched from IPFS)
        - state_type (initial, reveal, update)
        """
        history = []

        # Find metadata update events
        events = self.get_metadata_update_events(contract, token_id, from_block)

        # Get mint block (first Transfer from 0x0)
        transfers = self.parser.get_nft_transfers(
            contract,
            from_block=from_block,
            token_id=token_id
        )
        mint = next((t for t in transfers if t.get('is_mint')), None)
        mint_block = mint['block_number'] if mint else from_block

        # Sample blocks to check: mint, events, and current
        blocks_to_check = [mint_block]
        for event in events:
            blocks_to_check.append(event['block_number'])
        blocks_to_check.append(self.web3.get_block_number())

        # Deduplicate and sort
        blocks_to_check = sorted(set(blocks_to_check))

        # Query tokenURI at each block
        prev_uri = None
        state_number = 0

        for block in blocks_to_check:
            uri = self.get_token_uri_at_block(contract, token_id, block)

            if uri and uri != prev_uri:
                # State changed - record it
                timestamp = self.parser.get_block_timestamp(block)
                metadata = self.parser.fetch_ipfs_metadata(uri) if uri else None

                # Determine state type
                if state_number == 0:
                    state_type = 'initial'
                elif self._is_placeholder(prev_uri, uri):
                    state_type = 'reveal'
                else:
                    state_type = 'update'

                state = {
                    'state_number': state_number,
                    'block_number': block,
                    'timestamp': timestamp,
                    'token_uri': uri,
                    'metadata': metadata,
                    'image': metadata.get('image') if metadata else None,
                    'state_type': state_type,
                    'trigger': 'mint' if state_number == 0 else 'transaction',
                }

                history.append(state)
                prev_uri = uri
                state_number += 1

        return history

    def _is_placeholder(self, old_uri: str, new_uri: str) -> bool:
        """Detect if transition is from placeholder to revealed"""
        if not old_uri:
            return False

        # Common placeholder patterns
        placeholder_patterns = [
            'hidden', 'unrevealed', 'placeholder', 'mystery',
            'prereveal', 'pre-reveal', 'coming-soon'
        ]

        old_lower = old_uri.lower()
        for pattern in placeholder_patterns:
            if pattern in old_lower:
                return True

        return False

    def detect_reveal_pattern(self, contract: str) -> Dict:
        """
        Detect if contract uses reveal mechanism

        Analyzes:
        - Contract ABI for reveal functions
        - Storage for revealed boolean
        - Storage for revealTime timestamp
        """
        patterns = {
            'has_reveal_function': False,
            'has_revealed_state': False,
            'has_reveal_time': False,
            'reveal_time_value': None,
            'is_revealed': None,
        }

        # Check for reveal function by attempting to get its signature from bytecode
        bytecode = self.web3.rpc_call('eth_getCode', [contract, 'latest'])

        if bytecode:
            for sig, name in REVEAL_FUNCTION_SIGS.items():
                if sig[2:] in bytecode.lower():
                    patterns['has_reveal_function'] = True
                    patterns['reveal_function'] = name
                    break

        # Try to read common storage slots for reveal state
        # This is heuristic - actual slot depends on contract layout
        try:
            # Try reading 'revealed' at common slots
            for slot in range(10):
                storage = self.web3.rpc_call('eth_getStorageAt', [
                    contract,
                    hex(slot),
                    'latest'
                ])
                if storage and storage not in ['0x0', '0x']:
                    val = int(storage, 16)
                    if val == 1:  # Boolean true
                        patterns['has_revealed_state'] = True
                        patterns['is_revealed'] = True
                    elif val > 1000000000:  # Likely a timestamp
                        patterns['has_reveal_time'] = True
                        patterns['reveal_time_value'] = datetime.fromtimestamp(val).isoformat()
        except Exception as e:
            logger.debug(f"Error checking reveal pattern: {e}")

        return patterns

    def save_state_to_db(self, nft_id: int, state: Dict) -> int:
        """Save a historical state to the database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO nft_states (
                nft_id, state_number, block_number, timestamp, state_type,
                token_uri, metadata_json, trigger_type, trigger_tx_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nft_id,
            state.get('state_number', 0),
            state.get('block_number'),
            state.get('timestamp'),
            state.get('state_type', 'unknown'),
            state.get('token_uri'),
            json.dumps(state.get('metadata')) if state.get('metadata') else None,
            state.get('trigger', 'unknown'),
            state.get('tx_hash'),
        ))

        conn.commit()
        state_id = cursor.lastrowid
        conn.close()

        return state_id

    def get_full_history(self, contract: str, token_id: int) -> Dict:
        """
        Get complete historical record for an NFT

        Returns comprehensive state history with all metadata changes.
        """
        history = self.get_token_uri_history(contract, token_id)
        reveal_pattern = self.detect_reveal_pattern(contract)

        return {
            'contract': contract,
            'token_id': token_id,
            'network': self.network,
            'states': history,
            'current_state': len(history) - 1 if history else 0,
            'total_transitions': len(history) - 1 if history else 0,
            'is_mutable': len(history) > 1,
            'reveal_pattern': reveal_pattern,
            'mutability_type': self._classify_mutability(history),
        }

    def _classify_mutability(self, history: List[Dict]) -> List[str]:
        """Classify what types of mutations have occurred"""
        types = set()

        for state in history:
            state_type = state.get('state_type', '')
            if state_type == 'reveal':
                types.add('reveal')
            elif state_type == 'update':
                types.add('metadata_update')

        return list(types)


class FutureEventDetector:
    """
    Detect scheduled events encoded in contracts and metadata

    Finds:
    - Timed reveals (revealTime timestamp in contract)
    - Phased releases (phaseEndTimes array)
    - Decay/expiration mechanics
    - Seasonal/cyclical changes
    - Events from metadata fields
    """

    def __init__(self, network: str = 'ethereum'):
        """Initialize detector"""
        self.web3 = MultiProviderWeb3(network)
        self.network = network
        self.parser = RawNFTParser(network)
        self.db = get_db()

    def analyze_contract_for_time_logic(self, contract: str) -> Dict:
        """
        Parse contract for time-dependent logic

        Looks for:
        - Timestamp comparisons (block.timestamp < X)
        - Time storage variables (revealTime, endTime, etc.)
        - Phase/stage logic
        """
        result = {
            'has_time_logic': False,
            'time_variables': [],
            'future_events': [],
            'time_functions': [],
        }

        # Get contract bytecode
        bytecode = self.web3.rpc_call('eth_getCode', [contract, 'latest'])

        if not bytecode or bytecode == '0x':
            return result

        # Look for timestamp opcodes in bytecode (0x42 = TIMESTAMP)
        if '42' in bytecode.lower():
            result['has_time_logic'] = True

        # Try to read storage slots that might contain timestamps
        now = int(time.time())

        for slot in range(20):  # Check first 20 slots
            try:
                storage = self.web3.rpc_call('eth_getStorageAt', [
                    contract,
                    hex(slot),
                    'latest'
                ])

                if storage and storage not in ['0x0', '0x', '0x0000000000000000000000000000000000000000000000000000000000000000']:
                    value = int(storage, 16)

                    # Check if value looks like a Unix timestamp
                    # Timestamps are typically between year 2000 and 2100
                    min_ts = 946684800   # 2000-01-01
                    max_ts = 4102444800  # 2100-01-01

                    if min_ts < value < max_ts:
                        ts_date = datetime.fromtimestamp(value)
                        is_future = value > now

                        var_info = {
                            'slot': slot,
                            'value': value,
                            'timestamp': value,
                            'date': ts_date.isoformat(),
                            'is_future': is_future,
                            'name': f'time_slot_{slot}',  # Unknown actual name
                        }

                        result['time_variables'].append(var_info)
                        result['has_time_logic'] = True

                        if is_future:
                            result['future_events'].append({
                                'event_type': 'scheduled_time',
                                'scheduled_time': ts_date.isoformat(),
                                'timestamp': value,
                                'source': 'contract_storage',
                                'slot': slot,
                                'countdown_seconds': value - now,
                            })

            except Exception as e:
                logger.debug(f"Error reading slot {slot}: {e}")

        return result

    def extract_metadata_time_events(self, metadata: Dict) -> List[Dict]:
        """
        Extract time-based events from NFT metadata

        Common patterns:
        - reveal_date / reveal_time
        - unlock_date / unlock_time
        - phase_end / edition_close
        - expiration / decay_start
        """
        events = []

        if not metadata:
            return events

        # Time-related field names to check
        time_fields = [
            'reveal_date', 'reveal_time', 'revealDate', 'revealTime',
            'unlock_date', 'unlock_time', 'unlockDate', 'unlockTime',
            'phase_end', 'phaseEnd', 'phase_2_start',
            'edition_close', 'editionClose', 'edition_end',
            'auction_end', 'auctionEnd', 'auction_start',
            'expiration', 'expires', 'expiry',
            'decay_start', 'decayStart',
            'next_phase', 'nextPhase',
            'scheduled_update', 'scheduledUpdate',
            'start_date', 'startDate', 'end_date', 'endDate',
        ]

        now = time.time()

        # Check top-level fields
        for field in time_fields:
            if field in metadata:
                value = metadata[field]
                parsed = self._parse_time_value(value)

                if parsed:
                    events.append({
                        'event_type': self._classify_time_field(field),
                        'field': field,
                        'raw_value': value,
                        'timestamp': parsed['timestamp'],
                        'date': parsed['date'],
                        'is_future': parsed['timestamp'] > now if parsed['timestamp'] else False,
                        'source': 'metadata',
                    })

        # Check attributes for time data
        for attr in metadata.get('attributes', []):
            trait_type = attr.get('trait_type', '').lower()

            if any(t in trait_type for t in ['time', 'date', 'expires', 'unlock', 'reveal', 'phase']):
                value = attr.get('value')
                parsed = self._parse_time_value(value)

                if parsed:
                    events.append({
                        'event_type': trait_type.replace(' ', '_'),
                        'field': f"attribute:{attr.get('trait_type')}",
                        'raw_value': value,
                        'timestamp': parsed['timestamp'],
                        'date': parsed['date'],
                        'is_future': parsed['timestamp'] > now if parsed['timestamp'] else False,
                        'source': 'metadata_attribute',
                    })

        return events

    def _parse_time_value(self, value: Any) -> Optional[Dict]:
        """Parse a time value from various formats"""
        if value is None:
            return None

        timestamp = None

        # If it's already a number (Unix timestamp)
        if isinstance(value, (int, float)):
            if 946684800 < value < 4102444800:  # Valid timestamp range
                timestamp = int(value)

        # If it's a string
        elif isinstance(value, str):
            # Try ISO format
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                timestamp = int(dt.timestamp())
            except:
                pass

            # Try Unix timestamp as string
            if not timestamp:
                try:
                    val = int(value)
                    if 946684800 < val < 4102444800:
                        timestamp = val
                except:
                    pass

        if timestamp:
            return {
                'timestamp': timestamp,
                'date': datetime.fromtimestamp(timestamp).isoformat(),
            }

        return None

    def _classify_time_field(self, field: str) -> str:
        """Classify what type of event a time field represents"""
        field_lower = field.lower()

        if 'reveal' in field_lower:
            return 'reveal'
        elif 'unlock' in field_lower:
            return 'unlock'
        elif 'phase' in field_lower:
            return 'phase_change'
        elif 'auction' in field_lower:
            return 'auction_event'
        elif 'expire' in field_lower or 'expir' in field_lower:
            return 'expiration'
        elif 'decay' in field_lower:
            return 'decay'
        elif 'edition' in field_lower:
            return 'edition_close'
        else:
            return 'scheduled_event'

    def build_event_calendar(
        self,
        contracts: List[str] = None,
        include_past: bool = False
    ) -> Dict[str, List[Dict]]:
        """
        Build calendar of events across all tracked NFTs

        Returns events grouped by date.
        """
        calendar = defaultdict(list)
        now = time.time()

        # Get all NFTs from database
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if contracts:
            placeholders = ','.join(['?' for _ in contracts])
            cursor.execute(f'''
                SELECT * FROM nft_mints WHERE contract_address IN ({placeholders})
            ''', contracts)
        else:
            cursor.execute('SELECT * FROM nft_mints')

        nfts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for nft in nfts:
            # Analyze contract
            contract_events = self.analyze_contract_for_time_logic(nft['contract_address'])

            # Analyze metadata
            metadata = json.loads(nft.get('metadata_json', '{}') or '{}')
            metadata_events = self.extract_metadata_time_events(metadata)

            all_events = contract_events.get('future_events', []) + metadata_events

            for event in all_events:
                if event.get('is_future') or include_past:
                    timestamp = event.get('timestamp')
                    if timestamp:
                        date_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                        calendar[date_key].append({
                            'nft': {
                                'contract': nft['contract_address'],
                                'token_id': nft.get('token_id'),
                                'name': nft.get('name'),
                            },
                            'event': event,
                        })

        return dict(calendar)

    def save_event_to_db(self, nft_id: int, event: Dict) -> int:
        """Save a scheduled event to the database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO nft_scheduled_events (
                nft_id, event_type, scheduled_time, source,
                source_variable, description, is_recurring, recurrence_pattern
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nft_id,
            event.get('event_type', 'unknown'),
            event.get('date'),
            event.get('source', 'unknown'),
            event.get('field') or event.get('slot'),
            event.get('description', f"Scheduled {event.get('event_type', 'event')}"),
            event.get('is_recurring', False),
            event.get('recurrence_pattern'),
        ))

        conn.commit()
        event_id = cursor.lastrowid
        conn.close()

        return event_id

    def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """Get all events scheduled within the next N days"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        future_date = (datetime.now() + timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT e.*, m.contract_address, m.token_id, m.name
            FROM nft_scheduled_events e
            JOIN nft_mints m ON e.nft_id = m.id
            WHERE e.completed = FALSE
            AND e.scheduled_time <= ?
            ORDER BY e.scheduled_time
        ''', (future_date,))

        events = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return events


class LiveWorkTracker:
    """
    Track and archive states of reactive/living NFTs

    Handles:
    - Oracle-fed data (price feeds, weather, etc.)
    - Time-responsive works (day/night, seasons)
    - Chain-state responsive (block number, gas price)
    - Interaction-responsive (view count, votes)
    """

    # Known oracle addresses (Chainlink mainnet)
    KNOWN_ORACLES = {
        '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419': {'name': 'ETH/USD', 'type': 'price'},
        '0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c': {'name': 'BTC/USD', 'type': 'price'},
        '0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c': {'name': 'LINK/USD', 'type': 'price'},
        '0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6': {'name': 'USDC/USD', 'type': 'price'},
    }

    # Reactivity type definitions
    REACTIVITY_TYPES = {
        'oracle_fed': 'Work displays or responds to external data feeds',
        'time_responsive': 'Work changes based on time (day/night, seasons)',
        'chain_state': 'Work reflects blockchain state (block, gas)',
        'interactive': 'Work responds to viewer/owner interactions',
        'owner_responsive': 'Work changes based on current holder',
        'generative_live': 'Generative work that produces new outputs',
    }

    def __init__(self, network: str = 'ethereum'):
        """Initialize tracker"""
        self.web3 = MultiProviderWeb3(network)
        self.network = network
        self.parser = RawNFTParser(network)
        self.db = get_db()

    def identify_reactivity_type(
        self,
        contract: str,
        metadata: Dict = None
    ) -> Dict:
        """
        Determine what type of reactivity this work has

        Analyzes contract and metadata to identify:
        - Data sources it uses
        - How often it updates
        - Whether it's deterministic
        """
        reactivity = {
            'is_reactive': False,
            'types': [],
            'data_sources': [],
            'update_frequency': None,
            'is_deterministic': True,
        }

        # Check for oracle usage in contract
        bytecode = self.web3.rpc_call('eth_getCode', [contract, 'latest'])

        if bytecode:
            bytecode_lower = bytecode.lower()

            # Check for known oracle addresses in bytecode
            for oracle_addr, oracle_info in self.KNOWN_ORACLES.items():
                if oracle_addr[2:].lower() in bytecode_lower:
                    reactivity['is_reactive'] = True
                    reactivity['types'].append('oracle_fed')
                    reactivity['data_sources'].append({
                        'type': 'chainlink_oracle',
                        'feed': oracle_info['name'],
                        'address': oracle_addr,
                    })

            # Check for timestamp usage (time-responsive)
            if '42' in bytecode_lower:  # TIMESTAMP opcode
                reactivity['is_reactive'] = True
                if 'time_responsive' not in reactivity['types']:
                    reactivity['types'].append('time_responsive')

            # Check for block-related opcodes
            if '43' in bytecode_lower or '44' in bytecode_lower:  # NUMBER, DIFFICULTY
                reactivity['is_reactive'] = True
                if 'chain_state' not in reactivity['types']:
                    reactivity['types'].append('chain_state')

        # Check metadata for reactivity hints
        if metadata:
            # Animation URL usually means interactive/animated
            if metadata.get('animation_url'):
                reactivity['is_reactive'] = True
                if 'interactive' not in reactivity['types']:
                    reactivity['types'].append('interactive')

            # Check for reactivity-related attributes
            for attr in metadata.get('attributes', []):
                trait = attr.get('trait_type', '').lower()
                if any(t in trait for t in ['dynamic', 'reactive', 'live', 'generative']):
                    reactivity['is_reactive'] = True
                    reactivity['types'].append('generative_live')

        # Determine update frequency based on types
        reactivity['update_frequency'] = self._estimate_update_frequency(reactivity['types'])

        # Determine if deterministic
        if any(t in reactivity['types'] for t in ['oracle_fed', 'chain_state']):
            reactivity['is_deterministic'] = False

        return reactivity

    def _estimate_update_frequency(self, types: List[str]) -> str:
        """Estimate how often a reactive work updates"""
        if 'chain_state' in types:
            return 'real_time'  # Every block
        elif 'oracle_fed' in types:
            return 'hourly'  # Oracles update periodically
        elif 'time_responsive' in types:
            return 'daily'  # Day/night, etc.
        elif 'interactive' in types:
            return 'on_trigger'  # User interaction
        else:
            return 'unknown'

    def capture_live_state(
        self,
        contract: str,
        token_id: int,
        trigger: str = 'manual'
    ) -> Dict:
        """
        Capture current state of a reactive work

        Snapshots:
        - Current visual output
        - Current data values (oracles, chain state)
        - Timestamp and block
        """
        capture_id = f"state_{int(time.time())}_{token_id}"

        state = {
            'capture_id': capture_id,
            'captured_at': datetime.utcnow().isoformat(),
            'block_height': self.web3.get_block_number(),
            'trigger': trigger,
            'chain_state': {},
            'oracle_values': {},
        }

        # Get chain state
        try:
            state['chain_state'] = {
                'block_number': state['block_height'],
                'timestamp': int(time.time()),
            }

            # Try to get gas price
            gas_price = self.web3.rpc_call('eth_gasPrice', [])
            if gas_price:
                state['chain_state']['gas_price_gwei'] = int(gas_price, 16) / 1e9
        except Exception as e:
            logger.debug(f"Error getting chain state: {e}")

        # Get oracle values if contract uses them
        reactivity = self.identify_reactivity_type(contract)

        for source in reactivity.get('data_sources', []):
            if source.get('type') == 'chainlink_oracle':
                value = self._get_oracle_value(source['address'])
                if value:
                    state['oracle_values'][source['feed']] = value

        # Get current metadata
        token_uri = self.parser.get_token_uri(contract, token_id)
        if token_uri:
            metadata = self.parser.fetch_ipfs_metadata(token_uri)
            state['metadata_snapshot'] = metadata
            state['token_uri'] = token_uri

        return state

    def _get_oracle_value(self, oracle_address: str) -> Optional[Dict]:
        """Get current value from a Chainlink oracle"""
        try:
            # Chainlink latestRoundData() call
            call_data = "0xfeaf968c"  # latestRoundData()

            result = self.web3.rpc_call('eth_call', [
                {'to': oracle_address, 'data': call_data},
                'latest'
            ])

            if result and result != '0x':
                # Parse response: roundId, answer, startedAt, updatedAt, answeredInRound
                hex_data = result[2:]

                if len(hex_data) >= 320:  # 5 * 64 chars
                    answer = int(hex_data[64:128], 16)
                    updated_at = int(hex_data[192:256], 16)

                    return {
                        'value': answer / 1e8,  # Chainlink uses 8 decimals
                        'updated_at': datetime.fromtimestamp(updated_at).isoformat(),
                    }
        except Exception as e:
            logger.debug(f"Error getting oracle value: {e}")

        return None

    def setup_monitoring(
        self,
        contract: str,
        token_id: int
    ) -> Dict:
        """
        Configure ongoing monitoring for a reactive work

        Returns monitoring configuration to track state changes.
        """
        reactivity = self.identify_reactivity_type(contract)

        monitoring = {
            'contract': contract,
            'token_id': token_id,
            'is_active': reactivity['is_reactive'],
            'capture_schedule': [],
        }

        if 'time_responsive' in reactivity['types']:
            # Capture at different times of day
            monitoring['capture_schedule'].append({
                'type': 'time_of_day',
                'times': ['00:00', '06:00', '12:00', '18:00'],
                'timezone': 'UTC',
            })

        if 'oracle_fed' in reactivity['types']:
            # Capture when oracle values change significantly
            monitoring['capture_schedule'].append({
                'type': 'oracle_change',
                'threshold_percent': 5.0,  # 5% change triggers capture
                'data_sources': reactivity['data_sources'],
            })

        if 'chain_state' in reactivity['types']:
            # Capture periodically
            monitoring['capture_schedule'].append({
                'type': 'periodic',
                'interval_hours': 4,
            })

        if 'interactive' in reactivity['types']:
            # Capture on interactions (transfer events)
            monitoring['capture_schedule'].append({
                'type': 'on_event',
                'events': ['transfer'],
            })

        return monitoring

    def save_reactivity_profile(self, nft_id: int, reactivity: Dict) -> int:
        """Save reactivity profile to database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO nft_reactivity (
                nft_id, is_reactive, reactivity_types, data_sources,
                update_frequency, is_deterministic, monitoring_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            nft_id,
            reactivity.get('is_reactive', False),
            json.dumps(reactivity.get('types', [])),
            json.dumps(reactivity.get('data_sources', [])),
            reactivity.get('update_frequency'),
            reactivity.get('is_deterministic', True),
            False,  # Not active by default
        ))

        conn.commit()
        profile_id = cursor.lastrowid
        conn.close()

        return profile_id

    def save_live_capture(self, nft_id: int, capture: Dict) -> int:
        """Save a live state capture to database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO nft_live_captures (
                nft_id, capture_id, capture_timestamp, block_height,
                input_state, metadata_snapshot, capture_trigger
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            nft_id,
            capture.get('capture_id'),
            capture.get('captured_at'),
            capture.get('block_height'),
            json.dumps({
                'chain_state': capture.get('chain_state', {}),
                'oracle_values': capture.get('oracle_values', {}),
            }),
            json.dumps(capture.get('metadata_snapshot')),
            capture.get('trigger', 'manual'),
        ))

        conn.commit()
        capture_id = cursor.lastrowid
        conn.close()

        return capture_id

    def get_capture_history(self, nft_id: int, limit: int = 100) -> List[Dict]:
        """Get capture history for an NFT"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM nft_live_captures
            WHERE nft_id = ?
            ORDER BY capture_timestamp DESC
            LIMIT ?
        ''', (nft_id, limit))

        captures = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Parse JSON fields
        for capture in captures:
            if capture.get('input_state'):
                capture['input_state'] = json.loads(capture['input_state'])
            if capture.get('metadata_snapshot'):
                capture['metadata_snapshot'] = json.loads(capture['metadata_snapshot'])

        return captures


# Combined analyzer for convenience
class LivingWorksAnalyzer:
    """
    Combined analyzer that uses all three trackers

    Provides unified interface for analyzing NFTs as living entities.
    """

    def __init__(self, network: str = 'ethereum'):
        """Initialize all trackers"""
        self.network = network
        self.history_tracker = HistoricalStateTracker(network)
        self.event_detector = FutureEventDetector(network)
        self.live_tracker = LiveWorkTracker(network)
        self.db = get_db()

    def analyze_nft(self, contract: str, token_id: int) -> Dict:
        """
        Complete temporal analysis of an NFT

        Returns comprehensive data about past, present, and future.
        """
        logger.info(f"Analyzing {contract} #{token_id} as living entity...")

        # Get basic data
        parser = RawNFTParser(self.network)
        basic_data = parser.get_full_nft_data(contract, token_id)

        # Get historical states (PAST)
        history = self.history_tracker.get_full_history(contract, token_id)

        # Get scheduled events (FUTURE)
        metadata = basic_data.get('metadata_raw', {})
        contract_time_logic = self.event_detector.analyze_contract_for_time_logic(contract)
        metadata_events = self.event_detector.extract_metadata_time_events(metadata)

        # Get reactivity profile (PRESENT - live state)
        reactivity = self.live_tracker.identify_reactivity_type(contract, metadata)
        current_capture = None
        if reactivity['is_reactive']:
            current_capture = self.live_tracker.capture_live_state(contract, token_id)

        return {
            'basic': {
                'contract': contract,
                'token_id': token_id,
                'network': self.network,
                'name': basic_data.get('name'),
                'current_owner': basic_data.get('current_owner'),
            },

            'past': {
                'states': history.get('states', []),
                'total_transitions': history.get('total_transitions', 0),
                'is_mutable': history.get('is_mutable', False),
                'mutability_types': history.get('mutability_type', []),
                'reveal_pattern': history.get('reveal_pattern', {}),
            },

            'present': {
                'reactivity': reactivity,
                'current_capture': current_capture,
                'is_living': reactivity['is_reactive'],
            },

            'future': {
                'has_time_logic': contract_time_logic.get('has_time_logic', False),
                'contract_events': contract_time_logic.get('future_events', []),
                'metadata_events': [e for e in metadata_events if e.get('is_future')],
                'time_variables': contract_time_logic.get('time_variables', []),
            },

            'visualization': self._build_visualization_data(
                history, contract_time_logic, reactivity
            ),
        }

    def _build_visualization_data(
        self,
        history: Dict,
        future_events: Dict,
        reactivity: Dict
    ) -> Dict:
        """Build data structure for point cloud visualization"""

        timeline = []

        # Add past states to timeline
        for state in history.get('states', []):
            timeline.append({
                'time_offset_days': self._calculate_offset(state.get('timestamp')),
                'type': 'past_state',
                'label': state.get('state_type', 'state'),
                'data': state,
            })

        # Add current state
        timeline.append({
            'time_offset_days': 0,
            'type': 'current',
            'label': 'Now',
            'data': {},
        })

        # Add future events
        for event in future_events.get('future_events', []):
            offset = (event.get('timestamp', 0) - time.time()) / 86400  # Days from now
            if offset > 0:
                timeline.append({
                    'time_offset_days': offset,
                    'type': 'future_event',
                    'label': event.get('event_type', 'event'),
                    'data': event,
                })

        return {
            'is_living': reactivity.get('is_reactive', False),
            'pulse_rate': 0.5 if reactivity.get('is_reactive') else 0,
            'has_history': len(history.get('states', [])) > 1,
            'history_depth': len(history.get('states', [])),
            'has_future_events': len(future_events.get('future_events', [])) > 0,
            'next_event_days': self._get_next_event_days(future_events),
            'timeline': sorted(timeline, key=lambda x: x['time_offset_days']),
            'reactivity_types': reactivity.get('types', []),
        }

    def _calculate_offset(self, timestamp_str: str) -> float:
        """Calculate days offset from now"""
        if not timestamp_str:
            return -9999

        try:
            if isinstance(timestamp_str, str):
                ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                ts = timestamp_str

            delta = ts - datetime.now(ts.tzinfo)
            return delta.total_seconds() / 86400
        except:
            return -9999

    def _get_next_event_days(self, future_events: Dict) -> Optional[float]:
        """Get days until next event"""
        events = future_events.get('future_events', [])
        if not events:
            return None

        now = time.time()
        future = [e for e in events if e.get('timestamp', 0) > now]

        if not future:
            return None

        next_event = min(future, key=lambda x: x.get('timestamp', float('inf')))
        return (next_event['timestamp'] - now) / 86400


# CLI Interface
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("""
Living Works Temporal Framework
Track NFTs as living entities with past, present, and future

Usage:
  python living_works_tracker.py analyze <contract> <token_id>   Full temporal analysis
  python living_works_tracker.py history <contract> <token_id>   Get state history
  python living_works_tracker.py events <contract>               Detect scheduled events
  python living_works_tracker.py reactive <contract> <token_id>  Check if reactive
  python living_works_tracker.py capture <contract> <token_id>   Capture live state
  python living_works_tracker.py calendar                        Show event calendar

Examples:
  python living_works_tracker.py analyze 0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d 1
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'analyze':
        if len(sys.argv) < 4:
            print("Usage: python living_works_tracker.py analyze <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        analyzer = LivingWorksAnalyzer()

        print(f"\n{'='*60}")
        print(f"TEMPORAL ANALYSIS: {contract[:20]}... #{token_id}")
        print(f"{'='*60}")

        result = analyzer.analyze_nft(contract, token_id)

        print(f"\n--- BASIC INFO ---")
        basic = result['basic']
        print(f"Name: {basic.get('name', 'Unknown')}")
        print(f"Owner: {basic.get('current_owner', 'Unknown')[:20]}...")

        print(f"\n--- PAST (Historical States) ---")
        past = result['past']
        print(f"Total State Transitions: {past['total_transitions']}")
        print(f"Is Mutable: {past['is_mutable']}")
        print(f"Mutability Types: {past['mutability_types']}")
        if past.get('reveal_pattern', {}).get('has_reveal_function'):
            print(f"Has Reveal Mechanism: Yes")

        print(f"\n--- PRESENT (Live State) ---")
        present = result['present']
        print(f"Is Living/Reactive: {present['is_living']}")
        if present['is_living']:
            print(f"Reactivity Types: {present['reactivity']['types']}")
            print(f"Update Frequency: {present['reactivity']['update_frequency']}")
            print(f"Data Sources: {len(present['reactivity']['data_sources'])}")

        print(f"\n--- FUTURE (Scheduled Events) ---")
        future = result['future']
        print(f"Has Time Logic: {future['has_time_logic']}")
        print(f"Contract Events: {len(future['contract_events'])}")
        print(f"Metadata Events: {len(future['metadata_events'])}")

        if future['contract_events']:
            print("\nUpcoming Contract Events:")
            for event in future['contract_events']:
                print(f"  - {event.get('event_type', 'event')}: {event.get('date', 'unknown')}")

        print(f"\n--- VISUALIZATION DATA ---")
        viz = result['visualization']
        print(f"Is Living (pulse): {viz['is_living']}")
        print(f"History Depth: {viz['history_depth']} states")
        print(f"Has Future Events: {viz['has_future_events']}")
        if viz['next_event_days']:
            print(f"Next Event In: {viz['next_event_days']:.1f} days")

    elif command == 'history':
        if len(sys.argv) < 4:
            print("Usage: python living_works_tracker.py history <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        tracker = HistoricalStateTracker()
        history = tracker.get_full_history(contract, token_id)

        print(f"\n--- State History for {contract[:20]}... #{token_id} ---")
        print(f"Total Transitions: {history['total_transitions']}")

        for state in history['states']:
            print(f"\n  State #{state['state_number']}: {state['state_type']}")
            print(f"    Block: {state.get('block_number')}")
            print(f"    Time: {state.get('timestamp')}")
            print(f"    URI: {state.get('token_uri', 'N/A')[:50]}...")

    elif command == 'events':
        if len(sys.argv) < 3:
            print("Usage: python living_works_tracker.py events <contract>")
            sys.exit(1)

        contract = sys.argv[2]

        detector = FutureEventDetector()
        result = detector.analyze_contract_for_time_logic(contract)

        print(f"\n--- Time Logic Analysis for {contract[:20]}... ---")
        print(f"Has Time Logic: {result['has_time_logic']}")
        print(f"Time Variables Found: {len(result['time_variables'])}")

        if result['time_variables']:
            print("\nDetected Time Variables:")
            for var in result['time_variables']:
                future_marker = " [FUTURE]" if var['is_future'] else " [PAST]"
                print(f"  Slot {var['slot']}: {var['date']}{future_marker}")

        if result['future_events']:
            print("\nFuture Events:")
            for event in result['future_events']:
                days = event.get('countdown_seconds', 0) / 86400
                print(f"  - {event.get('scheduled_time')}: {event.get('event_type')} (in {days:.1f} days)")

    elif command == 'reactive':
        if len(sys.argv) < 4:
            print("Usage: python living_works_tracker.py reactive <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        tracker = LiveWorkTracker()

        # Get metadata for analysis
        parser = RawNFTParser()
        uri = parser.get_token_uri(contract, token_id)
        metadata = parser.fetch_ipfs_metadata(uri) if uri else {}

        reactivity = tracker.identify_reactivity_type(contract, metadata)

        print(f"\n--- Reactivity Analysis for {contract[:20]}... #{token_id} ---")
        print(f"Is Reactive: {reactivity['is_reactive']}")
        print(f"Types: {reactivity['types']}")
        print(f"Update Frequency: {reactivity['update_frequency']}")
        print(f"Is Deterministic: {reactivity['is_deterministic']}")

        if reactivity['data_sources']:
            print("\nData Sources:")
            for source in reactivity['data_sources']:
                print(f"  - {source.get('type')}: {source.get('feed')}")

    elif command == 'capture':
        if len(sys.argv) < 4:
            print("Usage: python living_works_tracker.py capture <contract> <token_id>")
            sys.exit(1)

        contract = sys.argv[2]
        token_id = int(sys.argv[3])

        tracker = LiveWorkTracker()
        capture = tracker.capture_live_state(contract, token_id, trigger='cli')

        print(f"\n--- Live State Capture ---")
        print(f"Capture ID: {capture['capture_id']}")
        print(f"Timestamp: {capture['captured_at']}")
        print(f"Block: {capture['block_height']}")

        if capture.get('chain_state'):
            print(f"\nChain State:")
            for k, v in capture['chain_state'].items():
                print(f"  {k}: {v}")

        if capture.get('oracle_values'):
            print(f"\nOracle Values:")
            for feed, data in capture['oracle_values'].items():
                print(f"  {feed}: ${data.get('value', 'N/A'):.2f}")

    elif command == 'calendar':
        detector = FutureEventDetector()
        calendar = detector.build_event_calendar()

        print(f"\n--- Event Calendar ---")

        if not calendar:
            print("No upcoming events found.")
        else:
            for date, events in sorted(calendar.items()):
                print(f"\n{date}:")
                for item in events:
                    nft = item['nft']
                    event = item['event']
                    print(f"  - {nft.get('name', 'NFT')}: {event.get('event_type')}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
