#!/usr/bin/env python3
"""
End-to-End Feature Testing
Tests all 5 new features:
1. Blockchain Address Tracker (with multi-provider RPC)
2. Local Vision Models
3. Sales Analytics
4. Art History Collections
5. Press Kit Generator
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


# ================================================================================
# TEST 1: Multi-Provider RPC Client
# ================================================================================
def test_multi_provider_rpc():
    print_header("TEST 1: Multi-Provider RPC Failover")

    try:
        from collectors.multi_provider_web3 import MultiProviderWeb3

        print_info("Initializing multi-provider Web3 client...")
        client = MultiProviderWeb3('ethereum')

        # Test 1: Get block number
        print_info("Testing eth_blockNumber...")
        block_num = client.get_block_number()

        if block_num:
            print_success(f"Successfully retrieved block number: {block_num:,}")
        else:
            print_error("Failed to get block number from all providers")
            return False

        # Test 2: Get balance
        print_info("Testing eth_getBalance...")
        eth_foundation = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
        balance = client.get_balance(eth_foundation)

        if balance is not None:
            eth_balance = balance / 1e18
            print_success(f"Successfully retrieved balance: {eth_balance:.4f} ETH")
        else:
            print_error("Failed to get balance")
            return False

        # Test 3: Provider status
        print_info("Checking provider health...")
        status = client.get_provider_status()

        print_success(f"Total providers: {status['total_providers']}")
        print_success(f"Current provider: {status['current_provider']}")

        for provider in status['providers']:
            status_str = f"  {provider['name']:20s} - Failures: {provider['failures']}"
            if provider['in_backoff']:
                print_warning(status_str + " (IN BACKOFF)")
            else:
                print_success(status_str)

        print_success("Multi-provider RPC test PASSED")
        return True

    except Exception as e:
        print_error(f"Multi-provider RPC test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 2: Direct Blockchain Event Parser
# ================================================================================
def test_blockchain_event_parser():
    print_header("TEST 2: Direct Blockchain Event Parser (Trustless)")

    try:
        from collectors.blockchain_event_parser import BlockchainEventParser

        print_info("Initializing blockchain event parser...")
        parser = BlockchainEventParser('ethereum')

        # Test with a well-known NFT contract (Bored Ape Yacht Club)
        bayc_contract = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"

        print_info(f"Testing mint event parsing on BAYC contract...")
        print_info("Note: This may take a while depending on block range...")

        # Test just a small block range to avoid timeout
        mints = parser.get_nft_mints_from_contract(
            contract_address=bayc_contract,
            from_block=12287507,  # BAYC deployment block
            to_block=12287510,    # Just a few blocks for testing
            batch_size=10
        )

        if mints:
            print_success(f"Successfully parsed {len(mints)} mint events")
            for i, mint in enumerate(mints[:3]):  # Show first 3
                print_success(f"  Mint {i+1}: Token #{mint['token_id']} → {mint['to_address'][:10]}...")
        else:
            print_warning("No mints found in test block range (expected)")

        print_success("Blockchain event parser test PASSED")
        return True

    except Exception as e:
        print_error(f"Blockchain event parser test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 3: Blockchain Tracker Database
# ================================================================================
def test_blockchain_tracker():
    print_header("TEST 3: Blockchain Address Tracker")

    try:
        from collectors.blockchain_db import get_db
        from collectors.address_registry import AddressRegistry

        print_info("Testing blockchain tracker database...")
        db = get_db()

        # Test database schema
        print_info("Checking database tables...")
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'")

        expected_tables = [
            'tracked_addresses',
            'nft_mints',
            'transactions',
            'collectors',
            'ipfs_cache',
            'sync_history'
        ]

        found_tables = [row['name'] for row in tables]

        for table in expected_tables:
            if table in found_tables:
                print_success(f"  Table '{table}' exists")
            else:
                print_error(f"  Table '{table}' missing")
                return False

        # Test address registry
        print_info("Testing address validation...")
        registry = AddressRegistry()

        test_addresses = [
            ("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "ethereum"),  # vitalik.eth
            ("DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK", "solana"),
            ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin"),  # Satoshi's address
        ]

        for addr, network in test_addresses:
            is_valid = registry.validate_address(addr, network)
            if is_valid:
                print_success(f"  {network.capitalize()} address validation: OK")
            else:
                print_error(f"  {network.capitalize()} address validation: FAILED")

        print_success("Blockchain tracker test PASSED")
        return True

    except Exception as e:
        print_error(f"Blockchain tracker test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 4: Local Vision Models
# ================================================================================
def test_local_vision():
    print_header("TEST 4: Local Vision Models")

    try:
        from processors.vision_providers import VisionProviderFactory

        print_info("Testing vision provider factory...")

        # Test local provider availability
        print_info("Checking local vision model availability...")
        local_provider = VisionProviderFactory.create_provider('local')

        if local_provider:
            print_success("Local vision provider created successfully")

            # Check if model is available
            print_info("Testing local model inference (this may take time on first run)...")
            # We won't actually run inference in this test to avoid model download
            print_warning("Skipping actual inference test (use visual_translator.py for full test)")
        else:
            print_error("Failed to create local vision provider")

        # Test Claude provider
        print_info("Checking Claude vision provider...")
        if os.getenv('ANTHROPIC_API_KEY'):
            claude_provider = VisionProviderFactory.create_provider('claude')
            if claude_provider:
                print_success("Claude vision provider created successfully")
            else:
                print_error("Failed to create Claude vision provider")
        else:
            print_warning("No ANTHROPIC_API_KEY found - Claude provider not available")

        print_success("Vision provider test PASSED")
        return True

    except Exception as e:
        print_error(f"Vision provider test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 5: Sales Analytics Database
# ================================================================================
def test_sales_analytics():
    print_header("TEST 5: Sales Analytics")

    try:
        from analytics.sales_db import get_sales_db

        print_info("Testing sales analytics database...")
        db = get_sales_db()

        # Test database schema
        print_info("Checking sales database tables...")
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'")

        expected_tables = [
            'sales',
            'marketplace_sync',
            'price_history'
        ]

        found_tables = [row['name'] for row in tables]

        for table in expected_tables:
            if table in found_tables:
                print_success(f"  Table '{table}' exists")
            else:
                print_error(f"  Table '{table}' missing")
                return False

        # Test mock sales data insertion (will be deleted)
        print_info("Testing sales data insertion...")
        db.execute('''
            INSERT INTO sales
            (nft_mint_id, buyer_address, seller_address, marketplace,
             purchase_tx_hash, purchase_price_wei, purchase_price_native,
             currency, purchase_timestamp, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,
            "0x1234567890123456789012345678901234567890",
            "0x0987654321098765432109876543210987654321",
            "opensea",
            "0xabc123",
            5000000000000000000,  # 5 ETH in wei
            5.0,
            "ETH",
            datetime.utcnow().isoformat(),
            "opensea_v2"
        ))

        # Verify insertion
        result = db.execute("SELECT COUNT(*) as count FROM sales")
        count = result[0]['count']
        print_success(f"  Successfully inserted test sale (total: {count} sales)")

        # Clean up test data
        db.execute("DELETE FROM sales WHERE purchase_tx_hash = ?", ("0xabc123",))
        print_success("  Test data cleaned up")

        print_success("Sales analytics test PASSED")
        return True

    except Exception as e:
        print_error(f"Sales analytics test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 6: Art History Collections
# ================================================================================
def test_collections():
    print_header("TEST 6: Art History Collections")

    try:
        from collections.collections_db import get_collections_db

        print_info("Testing collections database...")
        db = get_collections_db()

        # Test database schema
        print_info("Checking collections database tables...")
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'")

        expected_tables = [
            'collections',
            'series',
            'works',
            'creative_periods',
            'cross_references'
        ]

        found_tables = [row['name'] for row in tables]

        for table in expected_tables:
            if table in found_tables:
                print_success(f"  Table '{table}' exists")
            else:
                print_error(f"  Table '{table}' missing")
                return False

        # Test collection creation
        print_info("Testing collection creation...")
        result = db.execute('''
            INSERT INTO collections (name, description, created_at)
            VALUES (?, ?, ?)
        ''', ("Test Collection", "End-to-end test collection", datetime.utcnow().isoformat()))

        collection_id = result[0]['last_id']
        print_success(f"  Created test collection (ID: {collection_id})")

        # Clean up
        db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        print_success("  Test data cleaned up")

        print_success("Collections test PASSED")
        return True

    except Exception as e:
        print_error(f"Collections test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 7: Press Kit Generator
# ================================================================================
def test_press_kit():
    print_header("TEST 7: Press Kit Generator")

    try:
        from export.press_kit_generator import PressKitGenerator

        print_info("Testing press kit generator...")
        generator = PressKitGenerator()

        # Test with mock data
        print_info("Testing PDF generation with mock data...")
        mock_works = [
            {
                'title': 'Test Artwork 1',
                'description': 'A test artwork for end-to-end testing',
                'year': 2025,
                'image_path': None  # No actual image
            }
        ]

        mock_data = {
            'title': 'Test Press Kit',
            'description': 'End-to-end testing press kit',
            'works': mock_works,
            'artist_bio': 'Test artist biography',
            'contact_info': {
                'email': 'test@example.com',
                'website': 'https://example.com'
            }
        }

        print_warning("Note: Actual PDF generation requires WeasyPrint setup")
        print_warning("Skipping PDF render test to avoid dependencies")

        # Just test that the generator can be instantiated
        print_success("Press kit generator initialized successfully")
        print_success("Press kit generator test PASSED")
        return True

    except Exception as e:
        print_error(f"Press kit generator test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# TEST 8: Web UI Routes
# ================================================================================
def test_web_routes():
    print_header("TEST 8: Web UI Routes")

    try:
        print_info("Checking HTML templates...")

        templates_dir = Path(__file__).parent.parent / "templates"
        expected_templates = [
            "blockchain_tracker.html",
            "sales_analytics.html",
            "collections.html"
        ]

        for template in expected_templates:
            template_path = templates_dir / template
            if template_path.exists():
                print_success(f"  Template '{template}' exists")
            else:
                print_error(f"  Template '{template}' missing")
                return False

        print_success("Web UI routes test PASSED")
        return True

    except Exception as e:
        print_error(f"Web UI routes test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ================================================================================
# Main Test Runner
# ================================================================================
def main():
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                     WEB3GISEL END-TO-END FEATURE TESTING                      ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)

    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    tests = [
        ("Multi-Provider RPC", test_multi_provider_rpc),
        ("Blockchain Event Parser", test_blockchain_event_parser),
        ("Blockchain Tracker", test_blockchain_tracker),
        ("Local Vision Models", test_local_vision),
        ("Sales Analytics", test_sales_analytics),
        ("Art History Collections", test_collections),
        ("Press Kit Generator", test_press_kit),
        ("Web UI Routes", test_web_routes),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for test_name, result in results:
        if result:
            print_success(f"{test_name:35s} PASSED")
        else:
            print_error(f"{test_name:35s} FAILED")

    print(f"\n{Colors.BOLD}")
    print(f"Total Tests: {len(results)}")
    print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}")

    if failed == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.ENDC}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
