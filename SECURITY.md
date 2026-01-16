# Security Policy

## Overview

ARCHIV-IT (ARC-8) is an open-source local-first archive platform licensed under AGPL-3.0.

## Supported Versions

| Version | Supported |
|---------|-----------|
| main branch | Yes |
| Tagged releases | Yes |

## Cryptography

| Component | Algorithm | Standard |
|-----------|-----------|----------|
| Key encapsulation | ML-KEM-768 (Kyber) | NIST FIPS 203 |
| Digital signatures | ML-DSA-65 (Dilithium) | NIST FIPS 204 |
| Hashing | SHA-384 | NIST approved |
| Symmetric encryption | AES-256-GCM | NIST approved |

## Access Control

- Quantum Equilibrium V2: Gaming-resistant scoring
- Minimum 21 actions before tier calculation
- Fibonacci-weighted behavioral analysis
- Variance detection for oscillation attacks

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

**Contact:** security@archivit.io

**Please DO NOT:**
- Open public issues for security vulnerabilities
- Exploit vulnerabilities beyond proof-of-concept
- Share vulnerability details publicly before resolution

**We commit to:**
- Acknowledge receipt within 48 hours
- Provide status updates every 7 days
- Credit researchers who report responsibly (if desired)

## Security Measures

1. **Post-Quantum Cryptography**
   - NIST-standardized algorithms (FIPS 203, 204)
   - Quantum-resistant key exchange and signatures

2. **Access Control**
   - Blockchain-verified authenticity scoring
   - Gaming-resistant tier system
   - Exponential cooldown for violations

3. **Data Protection**
   - Local-first storage (user device)
   - No server-side user data
   - User controls deletion

4. **Input Validation**
   - Content Security Policy headers
   - Input sanitization
   - DOM-safe rendering

## Known Limitations

1. Browser crypto relies on Web Crypto API
2. PQC uses @noble/post-quantum (audited, newer library)
3. Local storage subject to browser limits

## License

AGPL-3.0 - See [LICENSE](LICENSE)

## Version

Security Policy Version: 2.0
Last Updated: 2026-01-16
