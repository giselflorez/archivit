#!/usr/bin/env python3
"""
Historical Purchase Analyzer
Scrapes and analyzes all historical NFT purchases from blockchain data
Identifies collectors, price trends, holding patterns, and collector profiles
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.blockchain_event_parser import BlockchainEventParser
from collectors.multi_provider_web3 import MultiProviderWeb3
from analytics.sales_db import get_sales_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalPurchaseAnalyzer:
    """
    Analyze historical NFT purchases and collector behavior

    Features:
    - Scrape all Transfer events from blockchain
    - Track purchase prices (from transaction value)
    - Identify collectors and their behavior patterns
    - Analyze holding periods
    - Detect flippers vs. long-term holders
    - Calculate price appreciation
    """

    def __init__(self, network: str = 'ethereum'):
        self.network = network
        self.parser = BlockchainEventParser(network)
        self.web3 = MultiProviderWeb3(network)
        self.sales_db = get_sales_db()

    def analyze_nft_full_history(
        self,
        contract_address: str,
        token_id: int,
        from_block: int = 0
    ) -> Dict:
        """
        Analyze complete purchase history for a specific NFT

        Returns:
        - All transfers (mint, sales, transfers)
        - Price paid at each sale
        - Holding periods for each owner
        - Current owner
        - Total appreciation
        """
        logger.info(f"Analyzing history for {contract_address} #{token_id}")

        # Get all transfers for this token
        transfers = self.parser.get_nft_transfers_for_token(
            contract_address,
            token_id,
            from_block
        )

        if not transfers:
            logger.warning(f"No transfer history found")
            return {
                'success': False,
                'error': 'No transfer history found'
            }

        # Enrich each transfer with price data
        enriched_transfers = []

        for transfer in transfers:
            enriched = transfer.copy()

            # Get transaction details for price
            tx_receipt = self.web3.get_transaction_receipt(transfer['tx_hash'])

            if tx_receipt:
                # Get full transaction data
                tx_data = self._get_transaction_data(transfer['tx_hash'])

                if tx_data:
                    enriched['value_wei'] = tx_data.get('value', 0)
                    enriched['value_eth'] = int(tx_data.get('value', 0)) / 1e18 if tx_data.get('value') else 0
                    enriched['gas_price'] = tx_data.get('gasPrice', 0)
                    enriched['gas_used'] = tx_receipt.get('gasUsed', 0)

                # Get block timestamp
                block = self.web3.get_block(transfer['block_number'])
                if block:
                    enriched['timestamp'] = block.get('timestamp')
                    enriched['date'] = datetime.fromtimestamp(block['timestamp']).isoformat()

            # Classify transfer type
            if transfer['from_address'] == '0x0000000000000000000000000000000000000000':
                enriched['transfer_type'] = 'mint'
            elif enriched.get('value_eth', 0) > 0:
                enriched['transfer_type'] = 'sale'
            else:
                enriched['transfer_type'] = 'transfer'

            enriched_transfers.append(enriched)

        # Calculate ownership periods
        ownership_periods = self._calculate_ownership_periods(enriched_transfers)

        # Identify current owner
        current_owner = enriched_transfers[-1]['to_address'] if enriched_transfers else None

        # Calculate price appreciation
        mint_price = 0
        latest_sale_price = 0

        for transfer in enriched_transfers:
            if transfer['transfer_type'] == 'mint':
                mint_price = transfer.get('value_eth', 0)
            if transfer['transfer_type'] == 'sale':
                latest_sale_price = transfer.get('value_eth', 0)

        appreciation = ((latest_sale_price - mint_price) / mint_price * 100) if mint_price > 0 else 0

        # Detect sales from marketplace patterns
        sales = self.parser.detect_sales_from_transfers(enriched_transfers)

        return {
            'success': True,
            'contract_address': contract_address,
            'token_id': token_id,
            'total_transfers': len(enriched_transfers),
            'total_sales': len(sales),
            'current_owner': current_owner,
            'mint_price_eth': mint_price,
            'latest_sale_price_eth': latest_sale_price,
            'appreciation_percent': round(appreciation, 2),
            'transfers': enriched_transfers,
            'sales': sales,
            'ownership_periods': ownership_periods
        }

    def analyze_collection_buyers(
        self,
        contract_address: str,
        from_block: int = 0,
        max_tokens: int = 100
    ) -> Dict:
        """
        Analyze all buyers/collectors for an entire collection

        Identifies:
        - Early supporters (minted or bought early)
        - Top collectors (bought multiple pieces)
        - Flippers (bought and resold quickly)
        - Diamond hands (still holding)
        - Price trends over time
        """
        logger.info(f"Analyzing collection buyers for {contract_address}")

        # Get all mints first
        mints = self.parser.get_nft_mints_from_contract(
            contract_address,
            from_block=from_block,
            batch_size=10000
        )

        if not mints:
            return {
                'success': False,
                'error': 'No mints found'
            }

        logger.info(f"Found {len(mints)} mints")

        # Limit to max_tokens for analysis
        tokens_to_analyze = mints[:max_tokens]

        # Track collectors
        collectors_data = defaultdict(lambda: {
            'tokens_owned': [],
            'tokens_sold': [],
            'total_spent_eth': 0,
            'total_earned_eth': 0,
            'first_purchase_date': None,
            'last_activity_date': None,
            'is_holder': False,
            'avg_holding_period_days': 0
        })

        # Analyze each token
        for i, mint in enumerate(tokens_to_analyze):
            if i % 10 == 0:
                logger.info(f"Analyzing token {i+1}/{len(tokens_to_analyze)}")

            token_id = int(mint['token_id'])

            # Get transfer history
            transfers = self.parser.get_nft_transfers_for_token(
                contract_address,
                token_id
            )

            # Track each owner
            for transfer in transfers:
                to_addr = transfer['to_address']
                from_addr = transfer['from_address']

                # Get transaction value (price paid)
                value_eth = transfer.get('value_eth', 0)

                # Update buyer data
                if to_addr and to_addr != '0x0000000000000000000000000000000000000000':
                    collectors_data[to_addr]['total_spent_eth'] += value_eth

                    # Track purchase date
                    if not collectors_data[to_addr]['first_purchase_date']:
                        collectors_data[to_addr]['first_purchase_date'] = transfer.get('date')

                    collectors_data[to_addr]['last_activity_date'] = transfer.get('date')

                # Update seller data
                if from_addr and from_addr != '0x0000000000000000000000000000000000000000':
                    collectors_data[from_addr]['total_earned_eth'] += value_eth
                    collectors_data[from_addr]['tokens_sold'].append(token_id)

            # Current owner
            if transfers:
                current_owner = transfers[-1]['to_address']
                collectors_data[current_owner]['tokens_owned'].append(token_id)
                collectors_data[current_owner]['is_holder'] = True

        # Convert to list and sort
        collectors_list = []

        for address, data in collectors_data.items():
            collector = {
                'address': address,
                'tokens_currently_owned': len(data['tokens_owned']),
                'tokens_sold': len(data['tokens_sold']),
                'total_spent_eth': round(data['total_spent_eth'], 4),
                'total_earned_eth': round(data['total_earned_eth'], 4),
                'net_profit_eth': round(data['total_earned_eth'] - data['total_spent_eth'], 4),
                'first_purchase_date': data['first_purchase_date'],
                'last_activity_date': data['last_activity_date'],
                'is_current_holder': data['is_holder'],
                'collector_type': self._classify_collector(data)
            }
            collectors_list.append(collector)

        # Sort by tokens owned
        collectors_list.sort(key=lambda x: x['tokens_currently_owned'], reverse=True)

        # Identify top collectors
        top_collectors = collectors_list[:20]

        # Identify flippers (sold > owned)
        flippers = [c for c in collectors_list if c['tokens_sold'] > c['tokens_currently_owned']]
        flippers.sort(key=lambda x: x['net_profit_eth'], reverse=True)

        # Identify diamond hands (bought early, still holding)
        diamond_hands = [c for c in collectors_list if c['is_current_holder'] and c['tokens_currently_owned'] > 1]
        diamond_hands.sort(key=lambda x: x['tokens_currently_owned'], reverse=True)

        return {
            'success': True,
            'contract_address': contract_address,
            'total_unique_collectors': len(collectors_list),
            'total_current_holders': len([c for c in collectors_list if c['is_current_holder']]),
            'top_collectors': top_collectors,
            'flippers': flippers[:10],
            'diamond_hands': diamond_hands[:10],
            'all_collectors': collectors_list
        }

    def generate_collector_report(
        self,
        collector_address: str,
        contract_address: str = None
    ) -> Dict:
        """
        Generate detailed report for a specific collector

        Shows:
        - All NFTs owned
        - Purchase history
        - Total spent
        - Average holding period
        - Collector behavior classification
        """
        logger.info(f"Generating collector report for {collector_address}")

        # TODO: Implement collector-specific analysis
        # This would query the database for all NFTs owned by this address
        # across all tracked collections

        return {
            'collector_address': collector_address,
            'total_nfts_owned': 0,
            'total_spent_eth': 0,
            'collections': [],
            'behavior_classification': 'unknown'
        }

    def _get_transaction_data(self, tx_hash: str) -> Optional[Dict]:
        """Get full transaction data including value"""
        try:
            result = self.web3.rpc_call('eth_getTransactionByHash', [tx_hash])
            return result
        except Exception as e:
            logger.error(f"Error getting transaction data: {e}")
            return None

    def _calculate_ownership_periods(self, transfers: List[Dict]) -> List[Dict]:
        """Calculate how long each owner held the NFT"""
        periods = []

        for i in range(len(transfers) - 1):
            current_transfer = transfers[i]
            next_transfer = transfers[i + 1]

            owner = current_transfer['to_address']
            start_timestamp = current_transfer.get('timestamp')
            end_timestamp = next_transfer.get('timestamp')

            if start_timestamp and end_timestamp:
                holding_period_seconds = end_timestamp - start_timestamp
                holding_period_days = holding_period_seconds / 86400

                periods.append({
                    'owner': owner,
                    'start_date': datetime.fromtimestamp(start_timestamp).isoformat(),
                    'end_date': datetime.fromtimestamp(end_timestamp).isoformat(),
                    'holding_period_days': round(holding_period_days, 1),
                    'sold_for_eth': next_transfer.get('value_eth', 0)
                })

        # Current owner (still holding)
        if transfers:
            last_transfer = transfers[-1]
            if last_transfer.get('timestamp'):
                current_holding_days = (datetime.now().timestamp() - last_transfer['timestamp']) / 86400

                periods.append({
                    'owner': last_transfer['to_address'],
                    'start_date': datetime.fromtimestamp(last_transfer['timestamp']).isoformat(),
                    'end_date': None,
                    'holding_period_days': round(current_holding_days, 1),
                    'sold_for_eth': None,
                    'is_current_owner': True
                })

        return periods

    def _classify_collector(self, collector_data: Dict) -> str:
        """
        Classify collector type based on behavior

        Types:
        - Early Supporter: Bought during mint period
        - Collector: Owns multiple pieces, didn't sell
        - Flipper: Sold more than owns
        - Diamond Hands: Early buyer still holding
        - Whale: Owns many pieces
        """
        tokens_owned = len(collector_data['tokens_owned'])
        tokens_sold = len(collector_data['tokens_sold'])

        if tokens_owned >= 5:
            return 'whale'
        elif tokens_owned > tokens_sold and tokens_owned > 1:
            return 'collector'
        elif tokens_sold > tokens_owned:
            return 'flipper'
        elif collector_data['is_holder']:
            return 'holder'
        else:
            return 'casual_buyer'


# CLI interface
if __name__ == '__main__':
    import json

    analyzer = HistoricalPurchaseAnalyzer('ethereum')

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python historical_purchase_analyzer.py nft <contract> <token_id> [from_block]")
        print("  python historical_purchase_analyzer.py collection <contract> [from_block] [max_tokens]")
        print("\nExamples:")
        print("  # Analyze single NFT history")
        print("  python scripts/analytics/historical_purchase_analyzer.py nft 0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D 1234")
        print("\n  # Analyze collection buyers")
        print("  python scripts/analytics/historical_purchase_analyzer.py collection 0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D 0 50")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'nft':
        contract = sys.argv[2]
        token_id = int(sys.argv[3])
        from_block = int(sys.argv[4]) if len(sys.argv) > 4 else 0

        print(f"\n{'='*80}")
        print(f"NFT Purchase History Analysis")
        print(f"{'='*80}\n")

        result = analyzer.analyze_nft_full_history(contract, token_id, from_block)

        if result['success']:
            print(f"Contract: {result['contract_address']}")
            print(f"Token ID: {result['token_id']}")
            print(f"Total Transfers: {result['total_transfers']}")
            print(f"Total Sales: {result['total_sales']}")
            print(f"Current Owner: {result['current_owner']}")
            print(f"Mint Price: {result['mint_price_eth']} ETH")
            print(f"Latest Sale: {result['latest_sale_price_eth']} ETH")
            print(f"Appreciation: {result['appreciation_percent']}%")

            print(f"\n{'='*80}")
            print(f"Transfer History:")
            print(f"{'='*80}\n")

            for i, transfer in enumerate(result['transfers'], 1):
                print(f"{i}. {transfer['transfer_type'].upper()}")
                print(f"   Block: {transfer['block_number']}")
                print(f"   From: {transfer['from_address']}")
                print(f"   To: {transfer['to_address']}")
                print(f"   Price: {transfer.get('value_eth', 0)} ETH")
                print(f"   Date: {transfer.get('date', 'Unknown')}")
                print()

            print(f"\n{'='*80}")
            print(f"Ownership Periods:")
            print(f"{'='*80}\n")

            for period in result['ownership_periods']:
                print(f"Owner: {period['owner']}")
                print(f"  Held for: {period['holding_period_days']} days")
                print(f"  From: {period['start_date']}")
                print(f"  To: {period.get('end_date', 'Present (still holding)')}")
                if period.get('sold_for_eth'):
                    print(f"  Sold for: {period['sold_for_eth']} ETH")
                print()
        else:
            print(f"Error: {result.get('error')}")

    elif command == 'collection':
        contract = sys.argv[2]
        from_block = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        max_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 50

        print(f"\n{'='*80}")
        print(f"Collection Buyer Analysis")
        print(f"{'='*80}\n")

        result = analyzer.analyze_collection_buyers(contract, from_block, max_tokens)

        if result['success']:
            print(f"Contract: {result['contract_address']}")
            print(f"Total Unique Collectors: {result['total_unique_collectors']}")
            print(f"Current Holders: {result['total_current_holders']}")

            print(f"\n{'='*80}")
            print(f"Top Collectors (by tokens owned):")
            print(f"{'='*80}\n")

            for i, collector in enumerate(result['top_collectors'], 1):
                print(f"{i}. {collector['address']}")
                print(f"   Owns: {collector['tokens_currently_owned']} tokens")
                print(f"   Sold: {collector['tokens_sold']} tokens")
                print(f"   Spent: {collector['total_spent_eth']} ETH")
                print(f"   Earned: {collector['total_earned_eth']} ETH")
                print(f"   Net: {collector['net_profit_eth']} ETH")
                print(f"   Type: {collector['collector_type']}")
                print()

            print(f"\n{'='*80}")
            print(f"Top Flippers (sold > owned):")
            print(f"{'='*80}\n")

            for i, flipper in enumerate(result['flippers'], 1):
                print(f"{i}. {flipper['address']}")
                print(f"   Sold: {flipper['tokens_sold']} tokens")
                print(f"   Still owns: {flipper['tokens_currently_owned']} tokens")
                print(f"   Net Profit: {flipper['net_profit_eth']} ETH")
                print()

            print(f"\n{'='*80}")
            print(f"Diamond Hands (early buyers still holding multiple):")
            print(f"{'='*80}\n")

            for i, holder in enumerate(result['diamond_hands'], 1):
                print(f"{i}. {holder['address']}")
                print(f"   Owns: {holder['tokens_currently_owned']} tokens")
                print(f"   First purchase: {holder['first_purchase_date']}")
                print(f"   Total spent: {holder['total_spent_eth']} ETH")
                print()

            # Save full report to JSON
            output_file = f"collector_analysis_{contract[:8]}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\n✓ Full report saved to: {output_file}")
        else:
            print(f"Error: {result.get('error')}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
