#!/usr/bin/env python3
"""
Network Data Builder for Point Cloud Visualization
Prepares blockchain data for 3D force-directed graph visualization

Builds nodes and edges from:
- NFT mints and metadata
- Collectors and ownership
- Transfers and sales
- Artist relationships
- Cross-chain connections

Output format compatible with Three.js force-directed graphs.
"""

import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from pathlib import Path
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.blockchain_db import get_db
from collectors.provenance_certifier import ProvenanceCertifier
from collectors.living_works_tracker import LivingWorksAnalyzer, LiveWorkTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkDataBuilder:
    """
    Build network graph data for point cloud visualization

    Creates:
    - Nodes: NFTs, Artists, Collectors, Contracts
    - Edges: created_by, owned_by, transferred, same_collection, etc.
    """

    # Node types and their visual properties
    NODE_TYPES = {
        'nft': {
            'base_size': 10,
            'color': '#4CAF50',  # Green
            'shape': 'sphere'
        },
        'artist': {
            'base_size': 20,
            'color': '#2196F3',  # Blue
            'shape': 'sphere'
        },
        'collector': {
            'base_size': 12,
            'color': '#FF9800',  # Orange
            'shape': 'sphere'
        },
        'contract': {
            'base_size': 15,
            'color': '#9C27B0',  # Purple
            'shape': 'cube'
        },
        'transaction': {
            'base_size': 5,
            'color': '#607D8B',  # Gray
            'shape': 'sphere'
        }
    }

    # Edge types and their visual properties
    EDGE_TYPES = {
        'created_by': {'weight': 1.0, 'color': '#2196F3'},
        'owned_by': {'weight': 1.0, 'color': '#FF9800'},
        'previously_owned': {'weight': 0.3, 'color': '#FFCC80'},
        'same_collection': {'weight': 0.5, 'color': '#9C27B0'},
        'same_artist': {'weight': 0.7, 'color': '#64B5F6'},
        'same_collector': {'weight': 0.4, 'color': '#FFB74D'},
        'transfer': {'weight': 0.8, 'color': '#4CAF50'},
        'sale': {'weight': 0.9, 'color': '#F44336'},
        'minted_on': {'weight': 0.6, 'color': '#9C27B0'},
    }

    # Blockchain colors for visual distinction
    BLOCKCHAIN_COLORS = {
        'ethereum': '#627EEA',
        'polygon': '#8247E5',
        'tezos': '#2C7DF7',
        'solana': '#00FFA3',
        'bitcoin': '#F7931A',
    }

    def __init__(self, include_temporal: bool = True):
        """Initialize builder with database access

        Args:
            include_temporal: Whether to include temporal/living works data (slower but richer)
        """
        self.db = get_db()
        self.certifier = ProvenanceCertifier()
        self.include_temporal = include_temporal

        # Initialize temporal analyzer if needed
        if include_temporal:
            try:
                self.live_tracker = LiveWorkTracker()
            except Exception as e:
                logger.warning(f"Could not initialize temporal tracker: {e}")
                self.live_tracker = None
        else:
            self.live_tracker = None

        # Node and edge caches
        self.nodes = {}
        self.edges = []
        self.node_id_map = {}

    def _generate_node_id(self, node_type: str, identifier: str) -> str:
        """Generate unique node ID"""
        raw = f"{node_type}:{identifier}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _get_or_create_node(
        self,
        node_type: str,
        identifier: str,
        data: Dict = None
    ) -> str:
        """Get existing node or create new one"""
        node_id = self._generate_node_id(node_type, identifier)

        if node_id not in self.nodes:
            type_config = self.NODE_TYPES.get(node_type, self.NODE_TYPES['nft'])

            self.nodes[node_id] = {
                'id': node_id,
                'type': node_type,
                'identifier': identifier,
                'size': type_config['base_size'],
                'color': type_config['color'],
                'shape': type_config['shape'],
                'connections': 0,
                'data': data or {}
            }

        return node_id

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        data: Dict = None
    ):
        """Add edge between two nodes"""
        edge_config = self.EDGE_TYPES.get(edge_type, {'weight': 0.5, 'color': '#999'})

        edge = {
            'source': source_id,
            'target': target_id,
            'type': edge_type,
            'weight': edge_config['weight'],
            'color': edge_config['color'],
            'data': data or {}
        }

        self.edges.append(edge)

        # Update connection counts
        if source_id in self.nodes:
            self.nodes[source_id]['connections'] += 1
        if target_id in self.nodes:
            self.nodes[target_id]['connections'] += 1

    def build_from_database(self) -> Dict:
        """
        Build complete network from database

        Returns:
            Network data with nodes and edges
        """
        logger.info("Building network from database...")

        # Clear existing data
        self.nodes = {}
        self.edges = []

        # Load data from database
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # 1. Add artist nodes (tracked addresses)
        cursor.execute('''
            SELECT * FROM tracked_addresses WHERE sync_enabled = TRUE
        ''')
        for row in cursor.fetchall():
            addr = dict(row)
            node_id = self._get_or_create_node(
                'artist',
                addr['address'],
                {
                    'label': addr.get('label', 'Unknown Artist'),
                    'network': addr.get('network'),
                    'address': addr['address'],
                    'blockchain_color': self.BLOCKCHAIN_COLORS.get(addr.get('network'), '#999')
                }
            )
            # Override color with blockchain color
            self.nodes[node_id]['color'] = self.BLOCKCHAIN_COLORS.get(addr.get('network'), '#2196F3')

        # 2. Add NFT nodes
        cursor.execute('''
            SELECT m.*, a.address as artist_address, a.network, a.label as artist_label
            FROM nft_mints m
            JOIN tracked_addresses a ON m.address_id = a.id
        ''')

        for row in cursor.fetchall():
            nft = dict(row)

            # Create NFT node
            nft_identifier = f"{nft.get('contract_address', '')}:{nft.get('token_id', '')}"
            nft_node_id = self._get_or_create_node(
                'nft',
                nft_identifier,
                {
                    'name': nft.get('name', f"Token #{nft.get('token_id')}"),
                    'description': nft.get('description'),
                    'contract': nft.get('contract_address'),
                    'token_id': nft.get('token_id'),
                    'platform': nft.get('platform'),
                    'network': nft.get('network'),
                    'token_uri': nft.get('token_uri'),
                    'image': nft.get('image_ipfs_hash'),
                    'blockchain_color': self.BLOCKCHAIN_COLORS.get(nft.get('network'), '#999')
                }
            )

            # Color by blockchain
            self.nodes[nft_node_id]['color'] = self.BLOCKCHAIN_COLORS.get(nft.get('network'), '#4CAF50')

            # Create artist node (if not exists)
            artist_node_id = self._get_or_create_node(
                'artist',
                nft['artist_address'],
                {
                    'label': nft.get('artist_label', 'Unknown'),
                    'address': nft['artist_address'],
                    'network': nft.get('network')
                }
            )

            # Edge: NFT -> created_by -> Artist
            self._add_edge(nft_node_id, artist_node_id, 'created_by')

            # Create contract node
            if nft.get('contract_address'):
                contract_node_id = self._get_or_create_node(
                    'contract',
                    nft['contract_address'],
                    {
                        'address': nft['contract_address'],
                        'platform': nft.get('platform'),
                        'network': nft.get('network')
                    }
                )

                # Edge: NFT -> minted_on -> Contract
                self._add_edge(nft_node_id, contract_node_id, 'minted_on')

        # 3. Add collector nodes and ownership edges
        cursor.execute('''
            SELECT c.*, m.contract_address, m.token_id, a.network
            FROM collectors c
            JOIN nft_mints m ON c.nft_mint_id = m.id
            JOIN tracked_addresses a ON m.address_id = a.id
        ''')

        for row in cursor.fetchall():
            collector = dict(row)

            # Create collector node
            collector_node_id = self._get_or_create_node(
                'collector',
                collector['collector_address'],
                {
                    'address': collector['collector_address'],
                    'network': collector.get('network'),
                    'blockchain_color': self.BLOCKCHAIN_COLORS.get(collector.get('network'), '#999')
                }
            )

            # Find NFT node
            nft_identifier = f"{collector.get('contract_address', '')}:{collector.get('token_id', '')}"
            nft_node_id = self._generate_node_id('nft', nft_identifier)

            if nft_node_id in self.nodes:
                # Edge: NFT -> owned_by -> Collector
                edge_data = {}
                if collector.get('purchase_price_native'):
                    edge_data['price'] = collector['purchase_price_native']
                    edge_data['currency'] = collector.get('currency', 'ETH')

                self._add_edge(nft_node_id, collector_node_id, 'owned_by', edge_data)

        # 4. Add same_collection edges
        self._add_collection_edges()

        # 5. Add same_collector edges
        self._add_collector_relationship_edges()

        conn.close()

        # 6. Adjust node sizes based on connections
        self._adjust_node_sizes()

        # 7. Add certification scores
        self._add_certification_data()

        # 8. Add temporal/living works data
        self._add_temporal_data()

        logger.info(f"Built network: {len(self.nodes)} nodes, {len(self.edges)} edges")

        return self.get_network_data()

    def _add_collection_edges(self):
        """Add edges between NFTs in same collection"""
        # Group NFTs by contract
        collections = {}
        for node_id, node in self.nodes.items():
            if node['type'] == 'nft':
                contract = node['data'].get('contract')
                if contract:
                    if contract not in collections:
                        collections[contract] = []
                    collections[contract].append(node_id)

        # Add edges within collections (limit to avoid too many edges)
        for contract, nft_ids in collections.items():
            if len(nft_ids) > 1 and len(nft_ids) <= 20:
                for i, nft1 in enumerate(nft_ids):
                    for nft2 in nft_ids[i+1:]:
                        self._add_edge(nft1, nft2, 'same_collection')

    def _add_collector_relationship_edges(self):
        """Add edges between collectors who own same artist's work"""
        # Group collectors by artist they collect from
        artist_collectors = {}

        for edge in self.edges:
            if edge['type'] == 'owned_by':
                nft_id = edge['source']
                collector_id = edge['target']

                # Find artist for this NFT
                for e in self.edges:
                    if e['type'] == 'created_by' and e['source'] == nft_id:
                        artist_id = e['target']
                        if artist_id not in artist_collectors:
                            artist_collectors[artist_id] = set()
                        artist_collectors[artist_id].add(collector_id)
                        break

        # Add same_collector edges
        for artist_id, collectors in artist_collectors.items():
            collectors_list = list(collectors)
            if len(collectors_list) > 1 and len(collectors_list) <= 10:
                for i, c1 in enumerate(collectors_list):
                    for c2 in collectors_list[i+1:]:
                        self._add_edge(c1, c2, 'same_collector', {'artist': artist_id})

    def _adjust_node_sizes(self):
        """Adjust node sizes based on number of connections"""
        max_connections = max(n['connections'] for n in self.nodes.values()) if self.nodes else 1

        for node in self.nodes.values():
            base_size = self.NODE_TYPES.get(node['type'], {}).get('base_size', 10)
            # Scale size by connections (1x to 3x)
            connection_factor = 1 + (2 * node['connections'] / max(max_connections, 1))
            node['size'] = base_size * connection_factor

    def _add_certification_data(self):
        """Add provenance certification scores to NFT nodes"""
        for node_id, node in self.nodes.items():
            if node['type'] == 'nft':
                # Add placeholder certification (actual would require network calls)
                node['data']['certification'] = {
                    'status': 'pending',
                    'score': None
                }

    def _add_temporal_data(self):
        """
        Add temporal/living works data to NFT nodes

        This enriches nodes with:
        - Historical state count (past iterations)
        - Scheduled future events
        - Reactivity profile (is it a living work?)
        - Animation/pulse rate for visualization
        """
        if not self.include_temporal or not self.live_tracker:
            return

        logger.info("Adding temporal data to NFT nodes...")

        for node_id, node in self.nodes.items():
            if node['type'] != 'nft':
                continue

            contract = node['data'].get('contract')
            token_id = node['data'].get('token_id')

            if not contract or token_id is None:
                continue

            # Initialize temporal data structure
            node['temporal'] = {
                'is_living': False,
                'pulse_rate': 0,
                'has_history': False,
                'history_depth': 0,
                'has_future_events': False,
                'next_event_days': None,
                'reactivity_types': [],
                'timeline': [],
            }

            try:
                # Get metadata for analysis
                metadata = node['data'].get('metadata_raw', {})

                # Check reactivity (this is fast - just bytecode analysis)
                reactivity = self.live_tracker.identify_reactivity_type(contract, metadata)

                if reactivity.get('is_reactive'):
                    node['temporal']['is_living'] = True
                    node['temporal']['reactivity_types'] = reactivity.get('types', [])

                    # Set pulse rate based on update frequency
                    freq = reactivity.get('update_frequency', 'unknown')
                    if freq == 'real_time':
                        node['temporal']['pulse_rate'] = 1.0
                    elif freq == 'hourly':
                        node['temporal']['pulse_rate'] = 0.7
                    elif freq == 'daily':
                        node['temporal']['pulse_rate'] = 0.4
                    else:
                        node['temporal']['pulse_rate'] = 0.2

                # Check for historical states in database
                conn = self.db.get_connection()
                cursor = conn.cursor()

                # Get state history count
                cursor.execute('''
                    SELECT COUNT(*) as count FROM nft_states
                    WHERE nft_id = (
                        SELECT id FROM nft_mints
                        WHERE contract_address = ? AND token_id = ?
                    )
                ''', (contract, str(token_id)))

                result = cursor.fetchone()
                if result and result['count'] > 0:
                    node['temporal']['has_history'] = True
                    node['temporal']['history_depth'] = result['count']

                # Check for scheduled events
                cursor.execute('''
                    SELECT * FROM nft_scheduled_events
                    WHERE nft_id = (
                        SELECT id FROM nft_mints
                        WHERE contract_address = ? AND token_id = ?
                    )
                    AND completed = FALSE
                    AND scheduled_time > datetime('now')
                    ORDER BY scheduled_time
                    LIMIT 5
                ''', (contract, str(token_id)))

                events = cursor.fetchall()
                if events:
                    node['temporal']['has_future_events'] = True

                    # Calculate days to next event
                    from datetime import datetime
                    next_event_time = events[0]['scheduled_time']
                    if next_event_time:
                        try:
                            event_dt = datetime.fromisoformat(next_event_time)
                            delta = event_dt - datetime.now()
                            node['temporal']['next_event_days'] = delta.total_seconds() / 86400
                        except:
                            pass

                    # Build timeline entries for future events
                    for event in events:
                        node['temporal']['timeline'].append({
                            'type': 'future_event',
                            'event_type': event['event_type'],
                            'date': event['scheduled_time'],
                            'label': event.get('description', event['event_type']),
                        })

                conn.close()

            except Exception as e:
                logger.debug(f"Error adding temporal data for {contract} #{token_id}: {e}")

        logger.info("Temporal data added to NFT nodes")

    def get_network_data(self) -> Dict:
        """
        Get network data in format for visualization

        Returns:
            Dict with nodes and edges arrays, including temporal data
        """
        # Count temporal stats
        living_count = sum(1 for n in self.nodes.values()
                         if n.get('temporal', {}).get('is_living', False))
        with_history = sum(1 for n in self.nodes.values()
                         if n.get('temporal', {}).get('has_history', False))
        with_events = sum(1 for n in self.nodes.values()
                        if n.get('temporal', {}).get('has_future_events', False))

        return {
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'node_count': len(self.nodes),
                'edge_count': len(self.edges),
                'node_types': list(set(n['type'] for n in self.nodes.values())),
                'edge_types': list(set(e['type'] for e in self.edges)),
                'temporal': {
                    'living_works_count': living_count,
                    'works_with_history': with_history,
                    'works_with_future_events': with_events,
                    'temporal_analysis_enabled': self.include_temporal,
                },
            },
            'nodes': list(self.nodes.values()),
            'edges': self.edges,
            'config': {
                'node_types': self.NODE_TYPES,
                'edge_types': self.EDGE_TYPES,
                'blockchain_colors': self.BLOCKCHAIN_COLORS,
                'temporal_visualization': {
                    'living_pulse_enabled': True,
                    'history_trail_enabled': True,
                    'future_event_indicators': True,
                    'pulse_rate_scale': [0, 0.2, 0.4, 0.7, 1.0],
                },
            }
        }

    def export_to_json(self, filepath: str):
        """Export network data to JSON file"""
        data = self.get_network_data()

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported network data to {filepath}")

    def get_subgraph(
        self,
        center_node_id: str,
        depth: int = 2,
        max_nodes: int = 100
    ) -> Dict:
        """
        Get subgraph centered on a specific node

        Args:
            center_node_id: ID of center node
            depth: How many hops from center to include
            max_nodes: Maximum nodes to include

        Returns:
            Subgraph data
        """
        if center_node_id not in self.nodes:
            return {'nodes': [], 'edges': [], 'error': 'Node not found'}

        included_nodes = {center_node_id}
        frontier = {center_node_id}

        for _ in range(depth):
            new_frontier = set()
            for node_id in frontier:
                # Find connected nodes
                for edge in self.edges:
                    if edge['source'] == node_id and edge['target'] not in included_nodes:
                        new_frontier.add(edge['target'])
                    elif edge['target'] == node_id and edge['source'] not in included_nodes:
                        new_frontier.add(edge['source'])

            included_nodes.update(new_frontier)
            frontier = new_frontier

            if len(included_nodes) >= max_nodes:
                break

        # Build subgraph
        subgraph_nodes = [self.nodes[nid] for nid in included_nodes if nid in self.nodes]
        subgraph_edges = [
            e for e in self.edges
            if e['source'] in included_nodes and e['target'] in included_nodes
        ]

        return {
            'center': center_node_id,
            'depth': depth,
            'nodes': subgraph_nodes,
            'edges': subgraph_edges
        }


# CLI Interface
if __name__ == '__main__':
    import sys

    builder = NetworkDataBuilder()

    if len(sys.argv) < 2:
        print("""
Network Data Builder for Point Cloud

Usage:
  python network_data_builder.py build                    Build full network
  python network_data_builder.py export <filepath>        Export to JSON
  python network_data_builder.py subgraph <node_id>       Get subgraph around node
  python network_data_builder.py stats                    Show network statistics

Examples:
  python network_data_builder.py build
  python network_data_builder.py export network_data.json
        """)
        sys.exit(0)

    command = sys.argv[1]

    if command == 'build':
        print("Building network from database...")
        data = builder.build_from_database()

        print(f"\n--- Network Built ---")
        print(f"Nodes: {len(data['nodes'])}")
        print(f"Edges: {len(data['edges'])}")

        print(f"\nNode Types:")
        type_counts = {}
        for node in data['nodes']:
            t = node['type']
            type_counts[t] = type_counts.get(t, 0) + 1
        for t, c in type_counts.items():
            print(f"  {t}: {c}")

        print(f"\nEdge Types:")
        edge_counts = {}
        for edge in data['edges']:
            t = edge['type']
            edge_counts[t] = edge_counts.get(t, 0) + 1
        for t, c in edge_counts.items():
            print(f"  {t}: {c}")

    elif command == 'export':
        if len(sys.argv) < 3:
            print("Usage: python network_data_builder.py export <filepath>")
            sys.exit(1)

        filepath = sys.argv[2]

        print("Building network...")
        builder.build_from_database()

        print(f"Exporting to {filepath}...")
        builder.export_to_json(filepath)

        print(f"✅ Exported to {filepath}")

    elif command == 'subgraph':
        if len(sys.argv) < 3:
            print("Usage: python network_data_builder.py subgraph <node_id>")
            sys.exit(1)

        node_id = sys.argv[2]

        print("Building full network first...")
        builder.build_from_database()

        print(f"Extracting subgraph around {node_id}...")
        subgraph = builder.get_subgraph(node_id, depth=2)

        print(f"\n--- Subgraph ---")
        print(f"Center: {subgraph.get('center')}")
        print(f"Nodes: {len(subgraph['nodes'])}")
        print(f"Edges: {len(subgraph['edges'])}")

    elif command == 'stats':
        print("Building network...")
        data = builder.build_from_database()

        print(f"\n{'='*50}")
        print("NETWORK STATISTICS")
        print(f"{'='*50}")

        print(f"\nTotal Nodes: {len(data['nodes'])}")
        print(f"Total Edges: {len(data['edges'])}")

        # Most connected nodes
        sorted_nodes = sorted(data['nodes'], key=lambda x: x['connections'], reverse=True)
        print(f"\nMost Connected Nodes:")
        for node in sorted_nodes[:5]:
            label = node['data'].get('label') or node['data'].get('name') or node['identifier'][:20]
            print(f"  {node['type']}: {label} ({node['connections']} connections)")

        # Blockchain distribution
        blockchain_counts = {}
        for node in data['nodes']:
            bc = node['data'].get('network', 'unknown')
            blockchain_counts[bc] = blockchain_counts.get(bc, 0) + 1

        print(f"\nBlockchain Distribution:")
        for bc, count in sorted(blockchain_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {bc}: {count} nodes")

        # Temporal/Living Works Statistics
        temporal = data['metadata'].get('temporal', {})
        print(f"\n{'='*50}")
        print("TEMPORAL/LIVING WORKS STATISTICS")
        print(f"{'='*50}")
        print(f"\nLiving Works (Reactive): {temporal.get('living_works_count', 0)}")
        print(f"Works with History (Past States): {temporal.get('works_with_history', 0)}")
        print(f"Works with Future Events: {temporal.get('works_with_future_events', 0)}")

        # List living works
        living_nodes = [n for n in data['nodes'] if n.get('temporal', {}).get('is_living')]
        if living_nodes:
            print(f"\nLiving/Reactive Works:")
            for node in living_nodes[:10]:
                name = node['data'].get('name', 'Unknown')
                types = node['temporal'].get('reactivity_types', [])
                pulse = node['temporal'].get('pulse_rate', 0)
                print(f"  - {name}: {types} (pulse: {pulse})")

        # List works with upcoming events
        event_nodes = [n for n in data['nodes'] if n.get('temporal', {}).get('has_future_events')]
        if event_nodes:
            print(f"\nWorks with Upcoming Events:")
            for node in event_nodes[:10]:
                name = node['data'].get('name', 'Unknown')
                days = node['temporal'].get('next_event_days')
                if days:
                    print(f"  - {name}: next event in {days:.1f} days")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
