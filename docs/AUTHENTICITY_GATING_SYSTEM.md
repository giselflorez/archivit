# AUTHENTICITY GATING SYSTEM

## Technical Specification

**Created:** 2026-01-16
**Status:** SPECIFICATION

---

## PURPOSE

Restrict access to features based on verified on-chain activity. Users who cannot prove authenticity via blockchain data cannot:
- View the map
- Use tools
- Mint provenance records

---

## AUTHENTICITY SCORE (0.0 - 1.0)

### Calculation

```
AUTHENTICITY = (0.40 × on_chain_verification) +
               (0.25 × behavioral_score) +
               (0.20 × temporal_trust) +
               (0.15 × network_attestation)
```

### Components

| Component | Weight | Source |
|-----------|--------|--------|
| On-chain verification | 40% | Blockchain transactions matching claims |
| Behavioral score | 25% | Quantum Containment ACU |
| Temporal trust | 20% | Wallet age (logarithmic) |
| Network attestation | 15% | Vouches from verified users |

### On-Chain Verification Formula

```
on_chain_verification = verified_claims / total_claims
```

Claims verified by:
- Mint transactions from user wallet
- Contract deployment by user wallet
- Primary sale transactions

### Temporal Trust Formula

```
temporal_trust = min(1.0, log10(wallet_age_days + 1) / log10(1100))
```

| Wallet Age | Trust Score |
|------------|-------------|
| 0 days | 0.00 |
| 30 days | 0.48 |
| 90 days | 0.64 |
| 365 days | 0.82 |
| 1000 days | 0.99 |

---

## ACCESS TIERS

| Tier | Score Range | Map Access | Mint | Vouch |
|------|-------------|------------|------|-------|
| BLOCKED | < 0.236 | None | No | No |
| OBSERVER | 0.236 - 0.382 | 2D only | No | No |
| PARTICIPANT | 0.382 - 0.618 | 3D view | No | No |
| CREATOR | 0.618 - 0.786 | Full | Yes | Yes |
| SOVEREIGN | ≥ 0.786 | Full + analytics | Yes | Yes |

---

## COOLDOWN SYSTEM

### Triggers

| Violation | Severity |
|-----------|----------|
| Fake mint claim | SEVERE |
| Wallet spoofing | SEVERE |
| Harassment | SEVERE |
| 3+ unverifiable claims in 24h | MODERATE |
| Spam behavior | MODERATE |

### Exponential Cooldown (Fibonacci)

| Violation # | Cooldown |
|-------------|----------|
| 1 | 24 hours |
| 2 | 24 hours |
| 3 | 48 hours (2 days) |
| 4 | 72 hours (3 days) |
| 5 | 120 hours (5 days) |
| 6 | 192 hours (8 days) |
| 7 | 312 hours (13 days) |
| 8 | 504 hours (21 days) |
| 9 | 816 hours (34 days) |
| 10 | 1320 hours (55 days) |
| 11 | 2136 hours (89 days) |
| 12+ | 3456 hours (144 days) |

### Formula

```javascript
cooldown_hours = 24 * fibonacci(violation_count)
```

### During Cooldown

- Access = BLOCKED
- Cannot view map
- Cannot use any features
- Shows countdown timer only

### Reset

- Violation counter resets after 90 days with no violations
- 12+ violations = permanent ban (appealable after 1 year)

---

## SYBIL RESISTANCE

### Problem

Users create new accounts to bypass cooldown.

### Solution

New accounts start at 0.0 authenticity.

To reach CREATOR tier (0.618), new account needs:
- Wallet with ≥30 days on-chain history
- ≥5 meaningful transactions
- ≥21 behavioral actions (Fibonacci minimum)
- OR vouches from existing SOVEREIGN users

### Time to CREATOR (New Account)

| Starting Point | Minimum Time |
|----------------|--------------|
| No wallet history | Impossible |
| Fresh wallet (0 days) | 30+ days |
| Active wallet (30+ days) | 7-14 days |
| Vouched by Sovereign | 3-5 days |

---

## VOUCH SYSTEM

### Rules

- Only SOVEREIGN users can vouch
- 3 vouches per quarter per Sovereign
- Vouch gives +0.10 to network_attestation
- If vouchee violates, voucher loses 1 future vouch slot
- Vouches expire after 1 year

---

## BLOCKCHAIN DATA POINTS

### Verified On-Chain Actions

| Action | Authenticity Weight |
|--------|---------------------|
| Deployed smart contract | 1.0 |
| Minted NFT (creator) | 1.0 |
| Primary sale (seller) | 0.9 |
| Secondary sale (seller) | 0.7 |
| Purchase (collector) | 0.5 |
| Transfer received | 0.3 |

### Supported Chains

| Chain | Status |
|-------|--------|
| Ethereum | Full support |
| Tezos | Full support |
| Polygon | Full support |
| Base | Partial |
| Solana | Planned |

---

## MAP ACCESS BY TIER

| Tier | View | Features |
|------|------|----------|
| BLOCKED | None | Login prompt |
| OBSERVER | 2D flat | Points only, no interaction |
| PARTICIPANT | 3D | Points + lines, interactive |
| CREATOR | 3D full | All features + minting |
| SOVEREIGN | 3D + analytics | All + network stats |

---

## IMPLEMENTATION

### Required Functions

```javascript
calculateAuthenticityScore(user)
getAccessTier(score)
checkCooldownStatus(user)
calculateCooldownDuration(violationCount)
verifyClaimOnChain(claim, wallets)
getWalletAge(address)
processVouch(fromUser, toUser)
```

### Database Schema

```sql
users:
  - wallet_address (primary)
  - authenticity_score
  - access_tier
  - violation_count
  - cooldown_until
  - last_violation_date

claims:
  - user_wallet
  - claim_type
  - claim_data
  - verified (boolean)
  - verification_tx_hash

vouches:
  - from_wallet
  - to_wallet
  - created_at
  - expires_at
  - active (boolean)
```

---

## SUMMARY

| Concept | Implementation |
|---------|----------------|
| Authenticity | Weighted score from on-chain + behavior + time + network |
| Access | 5 tiers with increasing privileges |
| Punishment | Fibonacci exponential cooldown |
| Sybil resistance | New accounts start at zero, need time + evidence |
| Map gating | Tier determines what you see |

---

*End of specification.*
