#!/usr/bin/env python3
"""
Multi-Provider Web3 Client
Provides resilient RPC access with automatic failover across multiple providers
Eliminates single point of failure from Alchemy-only approach
"""

import os
import logging
import requests
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiProviderWeb3:
    """
    Resilient Web3 RPC client with automatic failover

    Tries providers in priority order:
    1. Alchemy (fastest, best features)
    2. Infura (reliable fallback)
    3. Public RPC nodes (free, no auth)
    4. Ankr (backup)
    """

    def __init__(self, network: str = 'ethereum'):
        """
        Initialize multi-provider client

        Args:
            network: 'ethereum', 'polygon', 'arbitrum', etc.
        """
        self.network = network
        self.current_provider_index = 0
        self.failure_counts = {}
        self.last_failure_time = {}

        # Initialize providers
        self.providers = self._get_providers_for_network(network)

        if not self.providers:
            logger.warning(f"No RPC providers configured for {network}")

        logger.info(f"MultiProviderWeb3 initialized with {len(self.providers)} providers for {network}")

    def _get_providers_for_network(self, network: str) -> List[Tuple[str, str]]:
        """
        Get RPC provider list for specific network

        Returns:
            List of (name, url) tuples
        """
        if network == 'ethereum':
            providers = []

            # Alchemy (primary - fast and feature-rich)
            alchemy_key = os.getenv('ALCHEMY_API_KEY')
            if alchemy_key:
                providers.append(('alchemy', f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"))

            # Infura (reliable fallback)
            infura_key = os.getenv('INFURA_API_KEY')
            if infura_key:
                providers.append(('infura', f"https://mainnet.infura.io/v3/{infura_key}"))

            # Public RPC nodes (free, no auth required)
            providers.extend([
                ('cloudflare', "https://cloudflare-eth.com"),
                ('public-node', "https://eth.public-rpc.com"),
                ('ankr', "https://rpc.ankr.com/eth"),
                ('llamanodes', "https://eth.llamarpc.com"),
            ])

            return providers

        elif network == 'polygon':
            providers = []

            alchemy_key = os.getenv('ALCHEMY_API_KEY')
            if alchemy_key:
                providers.append(('alchemy-polygon', f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}"))

            infura_key = os.getenv('INFURA_API_KEY')
            if infura_key:
                providers.append(('infura-polygon', f"https://polygon-mainnet.infura.io/v3/{infura_key}"))

            providers.extend([
                ('polygon-rpc', "https://polygon-rpc.com"),
                ('ankr-polygon', "https://rpc.ankr.com/polygon"),
            ])

            return providers

        else:
            return []

    def _should_skip_provider(self, provider_name: str, max_failures: int = 3, backoff_seconds: int = 60) -> bool:
        """
        Check if provider should be temporarily skipped due to repeated failures

        Args:
            provider_name: Provider name
            max_failures: Max failures before backoff
            backoff_seconds: Seconds to wait after max failures

        Returns:
            True if provider should be skipped
        """
        failures = self.failure_counts.get(provider_name, 0)

        if failures >= max_failures:
            last_failure = self.last_failure_time.get(provider_name, 0)
            time_since_failure = time.time() - last_failure

            if time_since_failure < backoff_seconds:
                return True
            else:
                # Reset after backoff period
                self.failure_counts[provider_name] = 0
                return False

        return False

    def _record_failure(self, provider_name: str):
        """Record provider failure"""
        self.failure_counts[provider_name] = self.failure_counts.get(provider_name, 0) + 1
        self.last_failure_time[provider_name] = time.time()

    def _record_success(self, provider_name: str):
        """Record provider success (reset failure count)"""
        self.failure_counts[provider_name] = 0

    def rpc_call(self, method: str, params: List, timeout: int = 30) -> Optional[Dict]:
        """
        Make RPC call with automatic failover

        Args:
            method: JSON-RPC method (e.g., 'eth_blockNumber')
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            RPC result or None if all providers fail
        """
        if not self.providers:
            logger.error(f"No RPC providers configured for {self.network}")
            return None

        # Try each provider
        for attempt in range(len(self.providers)):
            provider_name, url = self.providers[self.current_provider_index]

            # Skip if provider is in backoff
            if self._should_skip_provider(provider_name):
                logger.debug(f"Skipping {provider_name} (in backoff)")
                self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
                continue

            try:
                logger.debug(f"Trying {provider_name} for {method}")

                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1
                }

                response = requests.post(url, json=payload, timeout=timeout)

                if response.status_code == 200:
                    result = response.json()

                    if 'result' in result:
                        self._record_success(provider_name)
                        logger.debug(f"✓ {provider_name} succeeded for {method}")
                        return result['result']

                    elif 'error' in result:
                        error_msg = result['error'].get('message', 'Unknown error')
                        logger.warning(f"{provider_name} returned error: {error_msg}")
                        self._record_failure(provider_name)

                else:
                    logger.warning(f"{provider_name} returned HTTP {response.status_code}")
                    self._record_failure(provider_name)

            except requests.Timeout:
                logger.warning(f"{provider_name} timeout for {method}")
                self._record_failure(provider_name)

            except requests.RequestException as e:
                logger.warning(f"{provider_name} request failed: {e}")
                self._record_failure(provider_name)

            except Exception as e:
                logger.error(f"{provider_name} unexpected error: {e}")
                self._record_failure(provider_name)

            # Move to next provider
            self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)

        # All providers failed
        logger.error(f"All RPC providers failed for {method}")
        return None

    def get_block_number(self) -> Optional[int]:
        """Get current block number"""
        result = self.rpc_call('eth_blockNumber', [])

        if result:
            return int(result, 16)
        return None

    def get_balance(self, address: str) -> Optional[int]:
        """Get balance for address in wei"""
        result = self.rpc_call('eth_getBalance', [address, 'latest'])

        if result:
            return int(result, 16)
        return None

    def call_contract(self, to: str, data: str) -> Optional[str]:
        """Make contract call"""
        result = self.rpc_call('eth_call', [
            {'to': to, 'data': data},
            'latest'
        ])

        return result

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction receipt"""
        return self.rpc_call('eth_getTransactionReceipt', [tx_hash])

    def get_block(self, block_number: int, full_transactions: bool = False) -> Optional[Dict]:
        """Get block data"""
        block_hex = hex(block_number)
        return self.rpc_call('eth_getBlockByNumber', [block_hex, full_transactions])

    def get_logs(self, from_block: int, to_block: int, address: str = None, topics: List[str] = None) -> Optional[List[Dict]]:
        """
        Get event logs

        Args:
            from_block: Starting block number
            to_block: Ending block number (or 'latest')
            address: Contract address filter
            topics: Event topic filters

        Returns:
            List of log entries
        """
        filter_params = {
            'fromBlock': hex(from_block),
            'toBlock': hex(to_block) if isinstance(to_block, int) else to_block
        }

        if address:
            filter_params['address'] = address

        if topics:
            filter_params['topics'] = topics

        return self.rpc_call('eth_getLogs', [filter_params])

    def get_provider_status(self) -> Dict:
        """
        Get status of all providers

        Returns:
            Dict with provider health info
        """
        status = {
            'total_providers': len(self.providers),
            'current_provider': self.providers[self.current_provider_index][0] if self.providers else None,
            'providers': []
        }

        for name, url in self.providers:
            provider_info = {
                'name': name,
                'url': url.split('/')[2],  # Just domain
                'failures': self.failure_counts.get(name, 0),
                'in_backoff': self._should_skip_provider(name)
            }
            status['providers'].append(provider_info)

        return status


# Test and CLI interface
if __name__ == '__main__':
    import sys

    client = MultiProviderWeb3('ethereum')

    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        # Show provider status
        status = client.get_provider_status()
        print("\n" + "="*60)
        print("Multi-Provider RPC Status")
        print("="*60)
        print(f"\nTotal Providers: {status['total_providers']}")
        print(f"Current Provider: {status['current_provider']}")
        print("\nProvider Health:")

        for p in status['providers']:
            backoff_str = " (IN BACKOFF)" if p['in_backoff'] else ""
            print(f"  {p['name']:20s} - Failures: {p['failures']}{backoff_str}")

        print()

    else:
        # Test RPC calls
        print("\nTesting Multi-Provider RPC Client...")
        print("="*60)

        # Test 1: Get block number
        print("\n1. Getting current block number...")
        block_num = client.get_block_number()
        print(f"   Current block: {block_num:,}")

        # Test 2: Get Ethereum Foundation balance
        print("\n2. Getting Ethereum Foundation balance...")
        eth_foundation = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
        balance = client.get_balance(eth_foundation)
        if balance:
            eth_balance = balance / 1e18
            print(f"   Balance: {eth_balance:,.4f} ETH")

        # Test 3: Provider status
        print("\n3. Provider Status:")
        status = client.get_provider_status()
        for p in status['providers']:
            print(f"   {p['name']:20s} - Failures: {p['failures']}")

        print("\n" + "="*60)
        print("✓ Multi-provider RPC client working!")
        print("="*60 + "\n")
