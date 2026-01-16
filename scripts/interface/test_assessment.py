"""
Test Assessment Generator
=========================
Creates mock assessment data for testing the assessment report UI.
Also provides the route handler for the assessment report view.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List


def generate_test_assessment(twitter_handle: str = "@founder.art",
                              wallet: str = "0x7B...") -> Dict:
    """
    Generate a test assessment for UI development.

    In production, this would come from:
    1. Twitter OAuth scan
    2. Blockchain cross-reference
    3. Network authenticity analysis
    """

    # Test with ESTABLISHED badge for realistic scenario
    # (not too perfect, not suspicious)

    # Component scores
    scores = {
        'vitality': 72.5,       # Good - most collectors are real
        'network': 68.3,        # Good - connected to ecosystem
        'transaction': 81.2,    # Very good - organic sales
        'timeline': 65.0        # Decent - some gaps but natural
    }

    # Calculate weighted score
    weighted = (
        scores['vitality'] * 0.35 +
        scores['network'] * 0.30 +
        scores['transaction'] * 0.20 +
        scores['timeline'] * 0.15
    )

    # Determine badge state
    if weighted >= 75:
        badge_state = 'VERIFIED'
        fill_percent = 85
    elif weighted >= 55:
        badge_state = 'ESTABLISHED'
        fill_percent = 65
    elif weighted >= 35:
        badge_state = 'EMERGING'
        fill_percent = 40
    else:
        badge_state = 'UNCERTAIN'
        fill_percent = 15

    # Generate reasoning based on scores
    reasoning = generate_reasoning(scores, badge_state)

    # Generate findings
    positive_signals = [
        {
            'title': '23 verified real collectors',
            'description': 'These wallets show diverse activity across multiple artists and platforms'
        },
        {
            'title': '18 collectors active in broader ecosystem',
            'description': 'Your collectors also support 47 other artists on average'
        },
        {
            'title': 'No wash trading detected',
            'description': 'All transactions appear organic with reasonable hold times'
        }
    ]

    red_flags = [
        {
            'type': 'dead_end_wallets',
            'severity': 'warning',
            'title': '3 dead-end wallets detected',
            'description': 'These wallets received NFTs but show no other activity. Could be cold storage or requires investigation.'
        },
        {
            'type': 'timeline_gap',
            'severity': 'info',
            'title': '4-month activity gap (Mar-Jul 2024)',
            'description': 'Extended period of no minting activity. Natural if on hiatus, flag if unexplained.'
        }
    ]

    # Generate mock imported data
    imported_data = generate_mock_imported_data()

    return {
        'twitter_handle': twitter_handle,
        'wallet_address': wallet,
        'badge_state': badge_state,
        'fill_percent': fill_percent,
        'percentile': 68.5,
        'weighted_score': round(weighted, 2),
        'scores': scores,
        'reasoning': reasoning,
        'positive_signals': positive_signals,
        'red_flags': red_flags,
        'total_items': len(imported_data),
        'collectors_analyzed': 26,
        'transfers_scanned': 142,
        'nft_count': 47,
        'collectors_count': 26,
        'volume_eth': 12.85,
        'imported_data': imported_data
    }


def generate_reasoning(scores: Dict, badge_state: str) -> List[Dict]:
    """Generate human-readable reasoning for the score"""
    reasoning = []

    # Vitality reasoning
    if scores['vitality'] >= 70:
        reasoning.append({
            'bullet': '+',
            'text': '<strong>High collector vitality</strong> - 88% of your collectors are active wallets with diverse holdings'
        })
    elif scores['vitality'] >= 50:
        reasoning.append({
            'bullet': '~',
            'text': '<strong>Moderate collector vitality</strong> - Some collectors show limited activity outside your work'
        })
    else:
        reasoning.append({
            'bullet': '-',
            'text': '<strong>Low collector vitality</strong> - Many wallets appear dormant or single-artist focused'
        })

    # Network reasoning
    if scores['network'] >= 70:
        reasoning.append({
            'bullet': '+',
            'text': '<strong>Strong ecosystem connections</strong> - Your collectors are well-connected to the broader NFT community'
        })
    elif scores['network'] >= 50:
        reasoning.append({
            'bullet': '~',
            'text': '<strong>Moderate network connectivity</strong> - Some isolation detected but no circular patterns'
        })
    else:
        reasoning.append({
            'bullet': '-',
            'text': '<strong>Isolated network</strong> - Limited connections to the broader ecosystem'
        })

    # Transaction reasoning
    if scores['transaction'] >= 70:
        reasoning.append({
            'bullet': '+',
            'text': '<strong>Organic transaction patterns</strong> - No indicators of wash trading or self-dealing'
        })
    else:
        reasoning.append({
            'bullet': '~',
            'text': '<strong>Some transaction anomalies</strong> - A few quick flips detected but within normal range'
        })

    # Timeline reasoning
    if scores['timeline'] >= 70:
        reasoning.append({
            'bullet': '+',
            'text': '<strong>Natural growth pattern</strong> - Steady activity over time without artificial bursts'
        })
    elif scores['timeline'] >= 50:
        reasoning.append({
            'bullet': '~',
            'text': '<strong>Some timeline irregularities</strong> - Activity gaps detected but consistent overall'
        })
    else:
        reasoning.append({
            'bullet': '-',
            'text': '<strong>Concerning timeline pattern</strong> - Burst-and-silence or artificial growth detected'
        })

    # Overall conclusion
    if badge_state == 'VERIFIED':
        reasoning.append({
            'bullet': '=',
            'text': '<strong>Result:</strong> Your archive demonstrates high authenticity with minimal red flags'
        })
    elif badge_state == 'ESTABLISHED':
        reasoning.append({
            'bullet': '=',
            'text': '<strong>Result:</strong> Your archive shows good signals with room for continued growth'
        })
    elif badge_state == 'EMERGING':
        reasoning.append({
            'bullet': '=',
            'text': '<strong>Result:</strong> Building presence - more data needed for confident assessment'
        })
    else:
        reasoning.append({
            'bullet': '=',
            'text': '<strong>Result:</strong> Red flags detected - manual review recommended'
        })

    return reasoning


def generate_mock_imported_data() -> List[Dict]:
    """Generate realistic mock imported data"""

    data = []
    now = datetime.now()

    # Sample NFT mints from Twitter
    nft_titles = [
        "Ethereal Dreams #1",
        "Digital Fragments",
        "Convergence",
        "Neon Whispers",
        "Abstract Meditation",
        "Chromatic Flow",
        "Silent Echo",
        "Temporal Shift",
        "Parallel Lines",
        "Quantum Garden"
    ]

    platforms = ['SuperRare', 'Foundation', 'OpenSea', 'Manifold']
    sources = ['twitter_scan', 'blockchain', 'platform_api']

    for i, title in enumerate(nft_titles):
        days_ago = random.randint(30, 365)
        platform = random.choice(platforms)
        source = random.choice(sources)

        data.append({
            'title': title,
            'type': 'mint',
            'source': source,
            'platform': platform,
            'date': (now - timedelta(days=days_ago)).isoformat(),
            'image_url': f'/static/placeholder_{i % 5}.jpg' if random.random() > 0.3 else None,
            'contract': f'0x{random.randint(0, 2**64):016x}',
            'token_id': str(random.randint(1, 10000)),
            'chain': 'ethereum',
            'price_eth': round(random.uniform(0.1, 5.0), 3) if random.random() > 0.5 else None,
            'tags': random.sample(['digital', 'abstract', 'generative', 'animation', '1/1', 'edition'], k=random.randint(2, 4)),
            'description': f'A unique digital artwork exploring themes of {random.choice(["identity", "technology", "nature", "consciousness"])}.',
            'engagement': random.randint(50, 500) if source == 'twitter_scan' else None,
            'tweet_url': f'https://twitter.com/founder/status/{random.randint(10**18, 10**19)}' if source == 'twitter_scan' else None
        })

    # Add some sales
    for i in range(5):
        days_ago = random.randint(10, 200)
        data.append({
            'title': random.choice(nft_titles),
            'type': 'sale',
            'source': 'blockchain',
            'platform': random.choice(platforms),
            'date': (now - timedelta(days=days_ago)).isoformat(),
            'price_eth': round(random.uniform(0.5, 8.0), 3),
            'from_address': f'0x{random.randint(0, 2**64):016x}',
            'to_address': f'0x{random.randint(0, 2**64):016x}',
            'contract': f'0x{random.randint(0, 2**64):016x}',
            'token_id': str(random.randint(1, 10000)),
            'chain': 'ethereum',
            'tags': ['sale', 'secondary']
        })

    # Add some collection mentions from Twitter
    for i in range(3):
        days_ago = random.randint(5, 100)
        data.append({
            'title': f'Collection mention by @collector_{random.randint(100, 999)}',
            'type': 'mention',
            'source': 'twitter_scan',
            'date': (now - timedelta(days=days_ago)).isoformat(),
            'engagement': random.randint(20, 200),
            'tweet_url': f'https://twitter.com/collector_{random.randint(100, 999)}/status/{random.randint(10**18, 10**19)}',
            'description': 'Collector sharing their acquisition',
            'tags': ['collector', 'mention', 'social_proof']
        })

    # Sort by date (most recent first)
    data.sort(key=lambda x: x.get('date', ''), reverse=True)

    return data


def get_assessment_template_data(twitter_handle: str = "@founder.art") -> Dict:
    """
    Get all data needed to render the assessment report template.

    This function is called by the route handler.
    """
    assessment = generate_test_assessment(twitter_handle)
    return assessment


# For testing directly
if __name__ == '__main__':
    import json
    data = generate_test_assessment()
    print(json.dumps(data, indent=2, default=str))
