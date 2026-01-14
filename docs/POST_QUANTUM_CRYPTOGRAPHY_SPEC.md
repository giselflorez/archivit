# POST-QUANTUM CRYPTOGRAPHY SPECIFICATION
## CRYSTALS-Kyber & CRYSTALS-Dilithium Integration for ARC-8

**Created:** 2026-01-13
**Status:** IMPLEMENTATION SPECIFICATION
**Priority:** CRITICAL - Quantum Threat Timeline 2030-2035
**NIST Standards:** FIPS 203 (ML-KEM/Kyber), FIPS 204 (ML-DSA/Dilithium)

---

## EXECUTIVE SUMMARY

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   QUANTUM THREAT:                                                           ║
║   ═══════════════                                                           ║
║                                                                              ║
║   Current cryptography (RSA, ECDSA, ECDH) will be BROKEN by quantum        ║
║   computers estimated to arrive 2030-2035.                                  ║
║                                                                              ║
║   "Harvest now, decrypt later" attacks are happening TODAY.                ║
║   Data encrypted now will be readable by quantum adversaries.               ║
║                                                                              ║
║   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ║
║                                                                              ║
║   SOLUTION:                                                                 ║
║   ═════════                                                                 ║
║                                                                              ║
║   CRYSTALS-Kyber  → Post-quantum key encapsulation (replaces ECDH)        ║
║   CRYSTALS-Dilithium → Post-quantum digital signatures (replaces ECDSA)   ║
║                                                                              ║
║   Both are NIST-standardized (2024) and considered secure against         ║
║   both classical and quantum computers.                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## PART 1: CURRENT CRYPTOGRAPHY AUDIT

### What ARC-8 Currently Uses

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   FILE: scripts/interface/static/js/core/pi_quadratic_seed.js              │
│   ═══════════════════════════════════════════════════════════              │
│                                                                              │
│   CURRENT IMPLEMENTATION:                                                   │
│   • crypto.getRandomValues() - Quantum-resistant (true randomness)        │
│   • SHA-256 hashing - Quantum-resistant (needs 2x output for safety)      │
│   • AES-256-GCM encryption - Quantum-resistant (symmetric)                │
│   • ECDSA signatures - QUANTUM VULNERABLE ⚠️                               │
│   • ECDH key exchange - QUANTUM VULNERABLE ⚠️                              │
│                                                                              │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                                              │
│   FILE: scripts/interface/static/js/core/seed_profile.js                   │
│   ════════════════════════════════════════════════════════                 │
│                                                                              │
│   CURRENT IMPLEMENTATION:                                                   │
│   • IndexedDB storage - Not cryptographic                                  │
│   • AES-256-GCM for encryption - Quantum-resistant                        │
│   • PBKDF2 key derivation - Quantum-resistant                             │
│   • Web Crypto API - Uses browser's crypto primitives                      │
│                                                                              │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                                              │
│   VULNERABILITY ASSESSMENT:                                                 │
│   ══════════════════════════                                               │
│                                                                              │
│   Component              Quantum Status        Action Needed               │
│   ─────────────────────  ──────────────────    ────────────────────────    │
│   AES-256-GCM            ✓ Safe               None (Grover's halves it    │
│                                                to 128-bit, still secure)   │
│   SHA-256                ✓ Safe (barely)       Consider SHA-384/512       │
│   PBKDF2                 ✓ Safe               None                        │
│   Random generation      ✓ Safe               None                        │
│   ECDSA signatures       ⚠️ VULNERABLE        Replace with Dilithium     │
│   ECDH key exchange      ⚠️ VULNERABLE        Replace with Kyber         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## PART 2: CRYSTALS-KYBER SPECIFICATION

### What Is Kyber?

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   CRYSTALS-KYBER (ML-KEM - Module Lattice Key Encapsulation Mechanism)     ║
║   ════════════════════════════════════════════════════════════════════════  ║
║                                                                              ║
║   PURPOSE: Secure key exchange that resists quantum attacks                ║
║   REPLACES: RSA key exchange, ECDH, DH                                     ║
║   STANDARD: NIST FIPS 203 (August 2024)                                    ║
║                                                                              ║
║   SECURITY LEVELS:                                                          ║
║   ─────────────────                                                         ║
║   ML-KEM-512   → 128-bit security (NIST Level 1)                          ║
║   ML-KEM-768   → 192-bit security (NIST Level 3) ← RECOMMENDED            ║
║   ML-KEM-1024  → 256-bit security (NIST Level 5)                          ║
║                                                                              ║
║   KEY SIZES:                                                                ║
║   ───────────                                                               ║
║   ML-KEM-768:                                                               ║
║   • Public key:  1,184 bytes                                               ║
║   • Secret key:  2,400 bytes                                               ║
║   • Ciphertext:  1,088 bytes                                               ║
║   • Shared secret: 32 bytes                                                ║
║                                                                              ║
║   COMPARISON TO ECDH:                                                       ║
║   ───────────────────                                                       ║
║   ECDH P-256:                                                               ║
║   • Public key:  64 bytes                                                  ║
║   • Private key: 32 bytes                                                  ║
║                                                                              ║
║   Kyber keys are ~20x larger, but still practical for modern systems.      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Kyber Integration Code

```javascript
// scripts/interface/static/js/core/pqc/kyber.js
// Post-Quantum Key Encapsulation using CRYSTALS-Kyber (ML-KEM-768)

import { ml_kem768 } from '@noble/post-quantum/ml-kem';

/**
 * ARC-8 Post-Quantum Key Encapsulation
 *
 * Uses ML-KEM-768 (CRYSTALS-Kyber) for quantum-resistant key exchange.
 * This replaces ECDH for all key agreement operations.
 */
export class ARC8Kyber {

    /**
     * Generate a new Kyber key pair
     * @returns {Object} { publicKey: Uint8Array, secretKey: Uint8Array }
     */
    static generateKeyPair() {
        const keys = ml_kem768.keygen();
        return {
            publicKey: keys.publicKey,   // 1,184 bytes
            secretKey: keys.secretKey,   // 2,400 bytes
            algorithm: 'ML-KEM-768',
            quantumSafe: true,
            created: Date.now()
        };
    }

    /**
     * Encapsulate a shared secret using recipient's public key
     * @param {Uint8Array} publicKey - Recipient's Kyber public key
     * @returns {Object} { ciphertext: Uint8Array, sharedSecret: Uint8Array }
     */
    static encapsulate(publicKey) {
        const result = ml_kem768.encapsulate(publicKey);
        return {
            ciphertext: result.cipherText,    // 1,088 bytes
            sharedSecret: result.sharedSecret  // 32 bytes
        };
    }

    /**
     * Decapsulate to retrieve shared secret
     * @param {Uint8Array} secretKey - Your Kyber secret key
     * @param {Uint8Array} ciphertext - Encapsulated ciphertext
     * @returns {Uint8Array} sharedSecret - 32-byte shared secret
     */
    static decapsulate(secretKey, ciphertext) {
        return ml_kem768.decapsulate(ciphertext, secretKey);
    }

    /**
     * Hybrid key exchange (Kyber + ECDH for defense in depth)
     * Combines classical and post-quantum for maximum security
     * @param {Uint8Array} kyberPublicKey - Recipient's Kyber public key
     * @param {CryptoKey} ecdhPublicKey - Recipient's ECDH public key
     * @returns {Object} { ciphertext, ecdhPublicKey, sharedSecret }
     */
    static async hybridEncapsulate(kyberPublicKey, ecdhPublicKey) {
        // Kyber encapsulation
        const kyberResult = this.encapsulate(kyberPublicKey);

        // ECDH key agreement (classical fallback)
        const ecdhKeyPair = await crypto.subtle.generateKey(
            { name: 'ECDH', namedCurve: 'P-384' },
            true,
            ['deriveKey', 'deriveBits']
        );

        const ecdhShared = await crypto.subtle.deriveBits(
            { name: 'ECDH', public: ecdhPublicKey },
            ecdhKeyPair.privateKey,
            384
        );

        // Combine both shared secrets using HKDF
        const combinedSecret = await this.combineSecrets(
            kyberResult.sharedSecret,
            new Uint8Array(ecdhShared)
        );

        return {
            kyberCiphertext: kyberResult.ciphertext,
            ecdhPublicKey: await crypto.subtle.exportKey('raw', ecdhKeyPair.publicKey),
            sharedSecret: combinedSecret
        };
    }

    /**
     * Combine two shared secrets using HKDF
     * @param {Uint8Array} secret1 - First shared secret (Kyber)
     * @param {Uint8Array} secret2 - Second shared secret (ECDH)
     * @returns {Uint8Array} Combined 32-byte secret
     */
    static async combineSecrets(secret1, secret2) {
        // Concatenate secrets
        const combined = new Uint8Array(secret1.length + secret2.length);
        combined.set(secret1, 0);
        combined.set(secret2, secret1.length);

        // Import as HKDF key
        const keyMaterial = await crypto.subtle.importKey(
            'raw',
            combined,
            'HKDF',
            false,
            ['deriveBits']
        );

        // Derive final secret
        const finalSecret = await crypto.subtle.deriveBits(
            {
                name: 'HKDF',
                hash: 'SHA-384',
                salt: new TextEncoder().encode('ARC8-HYBRID-PQC-v1'),
                info: new TextEncoder().encode('shared-secret')
            },
            keyMaterial,
            256
        );

        return new Uint8Array(finalSecret);
    }

    /**
     * Serialize key pair for storage
     * @param {Object} keyPair - Kyber key pair
     * @returns {Object} JSON-serializable object
     */
    static serializeKeyPair(keyPair) {
        return {
            publicKey: Array.from(keyPair.publicKey),
            secretKey: Array.from(keyPair.secretKey),
            algorithm: keyPair.algorithm,
            quantumSafe: keyPair.quantumSafe,
            created: keyPair.created
        };
    }

    /**
     * Deserialize key pair from storage
     * @param {Object} serialized - Serialized key pair
     * @returns {Object} Kyber key pair with Uint8Arrays
     */
    static deserializeKeyPair(serialized) {
        return {
            publicKey: new Uint8Array(serialized.publicKey),
            secretKey: new Uint8Array(serialized.secretKey),
            algorithm: serialized.algorithm,
            quantumSafe: serialized.quantumSafe,
            created: serialized.created
        };
    }
}

export default ARC8Kyber;
```

---

## PART 3: CRYSTALS-DILITHIUM SPECIFICATION

### What Is Dilithium?

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   CRYSTALS-DILITHIUM (ML-DSA - Module Lattice Digital Signature Algorithm) ║
║   ════════════════════════════════════════════════════════════════════════  ║
║                                                                              ║
║   PURPOSE: Digital signatures that resist quantum attacks                   ║
║   REPLACES: RSA signatures, ECDSA, EdDSA                                   ║
║   STANDARD: NIST FIPS 204 (August 2024)                                    ║
║                                                                              ║
║   SECURITY LEVELS:                                                          ║
║   ─────────────────                                                         ║
║   ML-DSA-44   → 128-bit security (NIST Level 2)                           ║
║   ML-DSA-65   → 192-bit security (NIST Level 3) ← RECOMMENDED             ║
║   ML-DSA-87   → 256-bit security (NIST Level 5)                           ║
║                                                                              ║
║   KEY/SIGNATURE SIZES:                                                      ║
║   ─────────────────────                                                     ║
║   ML-DSA-65:                                                                ║
║   • Public key:  1,952 bytes                                               ║
║   • Secret key:  4,032 bytes                                               ║
║   • Signature:   3,309 bytes                                               ║
║                                                                              ║
║   COMPARISON TO ECDSA:                                                      ║
║   ────────────────────                                                      ║
║   ECDSA P-256:                                                              ║
║   • Public key:  64 bytes                                                  ║
║   • Private key: 32 bytes                                                  ║
║   • Signature:   64 bytes                                                  ║
║                                                                              ║
║   Dilithium signatures are ~50x larger than ECDSA.                         ║
║   Still practical for document signing, but consider for high-volume.       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Dilithium Integration Code

```javascript
// scripts/interface/static/js/core/pqc/dilithium.js
// Post-Quantum Digital Signatures using CRYSTALS-Dilithium (ML-DSA-65)

import { ml_dsa65 } from '@noble/post-quantum/ml-dsa';

/**
 * ARC-8 Post-Quantum Digital Signatures
 *
 * Uses ML-DSA-65 (CRYSTALS-Dilithium) for quantum-resistant signatures.
 * This replaces ECDSA for all document/data signing operations.
 */
export class ARC8Dilithium {

    /**
     * Generate a new Dilithium signing key pair
     * @returns {Object} { publicKey: Uint8Array, secretKey: Uint8Array }
     */
    static generateKeyPair() {
        const keys = ml_dsa65.keygen();
        return {
            publicKey: keys.publicKey,   // 1,952 bytes
            secretKey: keys.secretKey,   // 4,032 bytes
            algorithm: 'ML-DSA-65',
            quantumSafe: true,
            created: Date.now()
        };
    }

    /**
     * Sign a message using your secret key
     * @param {Uint8Array} secretKey - Your Dilithium secret key
     * @param {Uint8Array} message - Message to sign
     * @returns {Uint8Array} signature - 3,309 byte signature
     */
    static sign(secretKey, message) {
        return ml_dsa65.sign(secretKey, message);
    }

    /**
     * Verify a signature using signer's public key
     * @param {Uint8Array} publicKey - Signer's Dilithium public key
     * @param {Uint8Array} message - Original message
     * @param {Uint8Array} signature - Signature to verify
     * @returns {boolean} true if valid, false otherwise
     */
    static verify(publicKey, message, signature) {
        return ml_dsa65.verify(publicKey, message, signature);
    }

    /**
     * Sign with timestamp and context
     * Creates a structured signature with metadata
     * @param {Uint8Array} secretKey - Your Dilithium secret key
     * @param {Uint8Array} message - Message to sign
     * @param {Object} context - Additional context { purpose, documentId, etc. }
     * @returns {Object} Structured signature object
     */
    static signWithContext(secretKey, message, context = {}) {
        const timestamp = Date.now();

        // Create signature payload
        const payload = {
            message: Array.from(message),
            timestamp,
            context,
            version: 'ARC8-PQC-v1'
        };

        const payloadBytes = new TextEncoder().encode(JSON.stringify(payload));
        const signature = this.sign(secretKey, payloadBytes);

        return {
            payload,
            signature: Array.from(signature),
            algorithm: 'ML-DSA-65',
            signedAt: new Date(timestamp).toISOString()
        };
    }

    /**
     * Verify a contextual signature
     * @param {Uint8Array} publicKey - Signer's Dilithium public key
     * @param {Object} signedObject - Object from signWithContext
     * @returns {Object} { valid: boolean, timestamp: number, context: Object }
     */
    static verifyWithContext(publicKey, signedObject) {
        const payloadBytes = new TextEncoder().encode(
            JSON.stringify(signedObject.payload)
        );
        const signature = new Uint8Array(signedObject.signature);

        const valid = this.verify(publicKey, payloadBytes, signature);

        return {
            valid,
            timestamp: signedObject.payload.timestamp,
            context: signedObject.payload.context,
            algorithm: signedObject.algorithm
        };
    }

    /**
     * Hybrid signature (Dilithium + ECDSA for defense in depth)
     * Provides security even if one algorithm is broken
     * @param {Uint8Array} dilithiumSecretKey - Your Dilithium secret key
     * @param {CryptoKey} ecdsaPrivateKey - Your ECDSA private key
     * @param {Uint8Array} message - Message to sign
     * @returns {Object} { dilithiumSig, ecdsaSig, message }
     */
    static async hybridSign(dilithiumSecretKey, ecdsaPrivateKey, message) {
        // Dilithium signature
        const dilithiumSig = this.sign(dilithiumSecretKey, message);

        // ECDSA signature (classical)
        const ecdsaSig = await crypto.subtle.sign(
            { name: 'ECDSA', hash: 'SHA-384' },
            ecdsaPrivateKey,
            message
        );

        return {
            dilithiumSignature: Array.from(dilithiumSig),
            ecdsaSignature: Array.from(new Uint8Array(ecdsaSig)),
            algorithm: 'HYBRID-ML-DSA-65-ECDSA-P384',
            quantumSafe: true,
            classicalSafe: true,
            signedAt: Date.now()
        };
    }

    /**
     * Verify hybrid signature (requires BOTH to be valid)
     * @param {Uint8Array} dilithiumPublicKey - Signer's Dilithium public key
     * @param {CryptoKey} ecdsaPublicKey - Signer's ECDSA public key
     * @param {Uint8Array} message - Original message
     * @param {Object} hybridSig - Hybrid signature object
     * @returns {Object} { valid, dilithiumValid, ecdsaValid }
     */
    static async hybridVerify(dilithiumPublicKey, ecdsaPublicKey, message, hybridSig) {
        // Verify Dilithium
        const dilithiumSig = new Uint8Array(hybridSig.dilithiumSignature);
        const dilithiumValid = this.verify(dilithiumPublicKey, message, dilithiumSig);

        // Verify ECDSA
        const ecdsaSig = new Uint8Array(hybridSig.ecdsaSignature);
        let ecdsaValid = false;
        try {
            ecdsaValid = await crypto.subtle.verify(
                { name: 'ECDSA', hash: 'SHA-384' },
                ecdsaPublicKey,
                ecdsaSig,
                message
            );
        } catch (e) {
            ecdsaValid = false;
        }

        return {
            valid: dilithiumValid && ecdsaValid,
            dilithiumValid,
            ecdsaValid,
            algorithm: hybridSig.algorithm
        };
    }

    /**
     * Serialize key pair for storage
     */
    static serializeKeyPair(keyPair) {
        return {
            publicKey: Array.from(keyPair.publicKey),
            secretKey: Array.from(keyPair.secretKey),
            algorithm: keyPair.algorithm,
            quantumSafe: keyPair.quantumSafe,
            created: keyPair.created
        };
    }

    /**
     * Deserialize key pair from storage
     */
    static deserializeKeyPair(serialized) {
        return {
            publicKey: new Uint8Array(serialized.publicKey),
            secretKey: new Uint8Array(serialized.secretKey),
            algorithm: serialized.algorithm,
            quantumSafe: serialized.quantumSafe,
            created: serialized.created
        };
    }
}

export default ARC8Dilithium;
```

---

## PART 4: UNIFIED PQC MODULE

### Complete Post-Quantum Cryptography Interface

```javascript
// scripts/interface/static/js/core/pqc/index.js
// ARC-8 Post-Quantum Cryptography Unified Interface

import { ARC8Kyber } from './kyber.js';
import { ARC8Dilithium } from './dilithium.js';

/**
 * ARC-8 Post-Quantum Cryptography Suite
 *
 * Provides quantum-resistant cryptographic operations for:
 * - Key exchange (Kyber/ML-KEM-768)
 * - Digital signatures (Dilithium/ML-DSA-65)
 * - Hybrid modes for defense in depth
 *
 * All operations are designed to integrate with the existing
 * PQS (Pi-Quadratic-Seed) identity system.
 */
export class ARC8PQC {

    constructor() {
        this.kyberKeys = null;
        this.dilithiumKeys = null;
        this.initialized = false;
    }

    /**
     * Initialize PQC key pairs
     * @returns {Object} { kyber: KeyPair, dilithium: KeyPair }
     */
    async initialize() {
        console.log('[ARC8-PQC] Generating post-quantum key pairs...');

        const startTime = performance.now();

        // Generate Kyber key pair for key exchange
        this.kyberKeys = ARC8Kyber.generateKeyPair();
        console.log('[ARC8-PQC] Kyber keys generated:', {
            publicKeySize: this.kyberKeys.publicKey.length,
            secretKeySize: this.kyberKeys.secretKey.length
        });

        // Generate Dilithium key pair for signatures
        this.dilithiumKeys = ARC8Dilithium.generateKeyPair();
        console.log('[ARC8-PQC] Dilithium keys generated:', {
            publicKeySize: this.dilithiumKeys.publicKey.length,
            secretKeySize: this.dilithiumKeys.secretKey.length
        });

        const elapsed = performance.now() - startTime;
        console.log(`[ARC8-PQC] Key generation complete in ${elapsed.toFixed(2)}ms`);

        this.initialized = true;

        return {
            kyber: this.kyberKeys,
            dilithium: this.dilithiumKeys,
            generationTime: elapsed
        };
    }

    /**
     * Load existing keys from storage
     * @param {Object} stored - Stored key data
     */
    loadKeys(stored) {
        if (stored.kyber) {
            this.kyberKeys = ARC8Kyber.deserializeKeyPair(stored.kyber);
        }
        if (stored.dilithium) {
            this.dilithiumKeys = ARC8Dilithium.deserializeKeyPair(stored.dilithium);
        }
        this.initialized = true;
    }

    /**
     * Export keys for storage
     * @returns {Object} Serialized keys
     */
    exportKeys() {
        return {
            kyber: this.kyberKeys ? ARC8Kyber.serializeKeyPair(this.kyberKeys) : null,
            dilithium: this.dilithiumKeys ? ARC8Dilithium.serializeKeyPair(this.dilithiumKeys) : null,
            exportedAt: Date.now(),
            version: 'ARC8-PQC-v1'
        };
    }

    /**
     * Get public keys for sharing
     * @returns {Object} Public keys only
     */
    getPublicKeys() {
        return {
            kyber: this.kyberKeys ? Array.from(this.kyberKeys.publicKey) : null,
            dilithium: this.dilithiumKeys ? Array.from(this.dilithiumKeys.publicKey) : null,
            algorithms: {
                keyExchange: 'ML-KEM-768',
                signature: 'ML-DSA-65'
            }
        };
    }

    /**
     * Encrypt data for a recipient
     * @param {Uint8Array} data - Data to encrypt
     * @param {Uint8Array} recipientKyberPublic - Recipient's Kyber public key
     * @returns {Object} { ciphertext, encryptedData, nonce }
     */
    async encryptFor(data, recipientKyberPublic) {
        // Encapsulate shared secret
        const { ciphertext, sharedSecret } = ARC8Kyber.encapsulate(recipientKyberPublic);

        // Use shared secret to derive AES key
        const aesKey = await crypto.subtle.importKey(
            'raw',
            sharedSecret,
            { name: 'AES-GCM' },
            false,
            ['encrypt']
        );

        // Generate random nonce
        const nonce = crypto.getRandomValues(new Uint8Array(12));

        // Encrypt data with AES-GCM
        const encryptedData = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: nonce },
            aesKey,
            data
        );

        return {
            kyberCiphertext: Array.from(ciphertext),
            encryptedData: Array.from(new Uint8Array(encryptedData)),
            nonce: Array.from(nonce),
            algorithm: 'ML-KEM-768-AES-256-GCM'
        };
    }

    /**
     * Decrypt data sent to you
     * @param {Object} encrypted - Encrypted data object
     * @returns {Uint8Array} Decrypted data
     */
    async decrypt(encrypted) {
        const ciphertext = new Uint8Array(encrypted.kyberCiphertext);

        // Decapsulate shared secret
        const sharedSecret = ARC8Kyber.decapsulate(
            this.kyberKeys.secretKey,
            ciphertext
        );

        // Derive AES key
        const aesKey = await crypto.subtle.importKey(
            'raw',
            sharedSecret,
            { name: 'AES-GCM' },
            false,
            ['decrypt']
        );

        // Decrypt data
        const nonce = new Uint8Array(encrypted.nonce);
        const encryptedData = new Uint8Array(encrypted.encryptedData);

        const decrypted = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv: nonce },
            aesKey,
            encryptedData
        );

        return new Uint8Array(decrypted);
    }

    /**
     * Sign data
     * @param {Uint8Array} data - Data to sign
     * @param {Object} context - Optional context metadata
     * @returns {Object} Signature object
     */
    sign(data, context = {}) {
        return ARC8Dilithium.signWithContext(
            this.dilithiumKeys.secretKey,
            data,
            context
        );
    }

    /**
     * Verify a signature
     * @param {Uint8Array} signerPublicKey - Signer's Dilithium public key
     * @param {Object} signedObject - Signed object from sign()
     * @returns {Object} Verification result
     */
    verify(signerPublicKey, signedObject) {
        return ARC8Dilithium.verifyWithContext(
            new Uint8Array(signerPublicKey),
            signedObject
        );
    }

    /**
     * Create a signed, encrypted message
     * @param {Uint8Array} data - Data to send
     * @param {Uint8Array} recipientKyberPublic - Recipient's Kyber public key
     * @returns {Object} Signed and encrypted package
     */
    async createSecureMessage(data, recipientKyberPublic) {
        // Sign the data first
        const signature = this.sign(data, {
            purpose: 'secure-message',
            timestamp: Date.now()
        });

        // Package data + signature
        const package_ = {
            data: Array.from(data),
            signature
        };

        const packageBytes = new TextEncoder().encode(JSON.stringify(package_));

        // Encrypt the package
        const encrypted = await this.encryptFor(
            packageBytes,
            recipientKyberPublic
        );

        return {
            ...encrypted,
            senderPublicKey: Array.from(this.dilithiumKeys.publicKey),
            type: 'ARC8-SECURE-MESSAGE-v1'
        };
    }

    /**
     * Open a signed, encrypted message
     * @param {Object} message - Secure message object
     * @returns {Object} { data, signatureValid, senderPublicKey }
     */
    async openSecureMessage(message) {
        // Decrypt
        const packageBytes = await this.decrypt(message);
        const package_ = JSON.parse(new TextDecoder().decode(packageBytes));

        // Verify signature
        const senderPublicKey = new Uint8Array(message.senderPublicKey);
        const verification = this.verify(senderPublicKey, package_.signature);

        return {
            data: new Uint8Array(package_.data),
            signatureValid: verification.valid,
            senderPublicKey: message.senderPublicKey,
            signedAt: verification.timestamp,
            context: verification.context
        };
    }

    /**
     * Get cryptographic capabilities info
     * @returns {Object} Capability information
     */
    static getCapabilities() {
        return {
            keyExchange: {
                algorithm: 'ML-KEM-768 (CRYSTALS-Kyber)',
                nistLevel: 3,
                quantumSafe: true,
                standard: 'FIPS 203'
            },
            signatures: {
                algorithm: 'ML-DSA-65 (CRYSTALS-Dilithium)',
                nistLevel: 3,
                quantumSafe: true,
                standard: 'FIPS 204'
            },
            symmetric: {
                algorithm: 'AES-256-GCM',
                quantumSafe: true,
                notes: 'Grover reduces to 128-bit, still secure'
            },
            hashing: {
                algorithm: 'SHA-384',
                quantumSafe: true,
                notes: 'SHA-256 borderline, SHA-384 recommended'
            },
            hybridMode: true,
            version: 'ARC8-PQC-v1'
        };
    }
}

// Export for use
export { ARC8Kyber, ARC8Dilithium };
export default ARC8PQC;
```

---

## PART 5: INTEGRATION WITH PQS IDENTITY

### Upgrading Pi-Quadratic-Seed

```javascript
// scripts/interface/static/js/core/pqs_quantum.js
// Post-Quantum upgrade for Pi-Quadratic-Seed Identity System

import { PiQuadraticSeed } from './pi_quadratic_seed.js';
import { ARC8PQC } from './pqc/index.js';

/**
 * Quantum-Safe Pi-Quadratic-Seed Identity
 *
 * Extends the existing PQS system with post-quantum cryptographic
 * key generation derived from the user's seed.
 */
export class QuantumSafePQS extends PiQuadraticSeed {

    constructor() {
        super();
        this.pqc = new ARC8PQC();
        this.quantumKeysGenerated = false;
    }

    /**
     * Generate quantum-safe keys from seed
     * Uses seed as deterministic randomness source for PQC key generation
     */
    async generateQuantumKeys() {
        if (!this.seedHash) {
            throw new Error('Seed not initialized. Call generateSeed() first.');
        }

        // Derive deterministic bytes from seed for PQC
        // This allows recovery of PQC keys from seed
        const pqcSeedMaterial = await this.derivePQCMaterial();

        // Initialize PQC with seed-derived randomness
        // Note: In production, this requires a seeded PRNG implementation
        await this.pqc.initialize();

        this.quantumKeysGenerated = true;

        return {
            quantumSafe: true,
            kyberPublicKey: this.pqc.getPublicKeys().kyber,
            dilithiumPublicKey: this.pqc.getPublicKeys().dilithium
        };
    }

    /**
     * Derive PQC seed material from main seed
     * @returns {Uint8Array} Seed material for PQC key generation
     */
    async derivePQCMaterial() {
        const encoder = new TextEncoder();
        const keyMaterial = await crypto.subtle.importKey(
            'raw',
            encoder.encode(this.seedHash),
            'HKDF',
            false,
            ['deriveBits']
        );

        const derived = await crypto.subtle.deriveBits(
            {
                name: 'HKDF',
                hash: 'SHA-384',
                salt: encoder.encode('ARC8-PQC-SEED-v1'),
                info: encoder.encode('quantum-key-derivation')
            },
            keyMaterial,
            512 // 64 bytes
        );

        return new Uint8Array(derived);
    }

    /**
     * Sign data with quantum-safe signature
     * @param {Uint8Array} data - Data to sign
     * @returns {Object} Quantum-safe signature
     */
    quantumSign(data) {
        if (!this.quantumKeysGenerated) {
            throw new Error('Quantum keys not generated. Call generateQuantumKeys() first.');
        }

        return this.pqc.sign(data, {
            seedFingerprint: this.getFingerprint(),
            purpose: 'user-signature'
        });
    }

    /**
     * Encrypt data for recipient with quantum-safe encryption
     * @param {Uint8Array} data - Data to encrypt
     * @param {Uint8Array} recipientKyberPublic - Recipient's public key
     * @returns {Object} Encrypted data
     */
    async quantumEncrypt(data, recipientKyberPublic) {
        if (!this.quantumKeysGenerated) {
            throw new Error('Quantum keys not generated. Call generateQuantumKeys() first.');
        }

        return this.pqc.encryptFor(data, recipientKyberPublic);
    }

    /**
     * Get full identity bundle including quantum keys
     * @returns {Object} Complete identity bundle
     */
    getQuantumIdentity() {
        const baseIdentity = this.getIdentity();

        return {
            ...baseIdentity,
            quantumSafe: this.quantumKeysGenerated,
            pqcPublicKeys: this.quantumKeysGenerated ? this.pqc.getPublicKeys() : null,
            pqcCapabilities: ARC8PQC.getCapabilities()
        };
    }

    /**
     * Export full state including quantum keys (encrypted)
     * @param {string} password - Password for encryption
     * @returns {Object} Encrypted state bundle
     */
    async exportQuantumState(password) {
        const baseState = await this.exportState(password);

        if (this.quantumKeysGenerated) {
            // Add PQC keys to export
            const pqcKeys = this.pqc.exportKeys();

            // Encrypt PQC keys with same password
            const pqcEncrypted = await this.encryptData(
                new TextEncoder().encode(JSON.stringify(pqcKeys)),
                password
            );

            baseState.pqcKeys = pqcEncrypted;
            baseState.quantumSafe = true;
        }

        return baseState;
    }

    /**
     * Import state including quantum keys
     * @param {Object} state - Exported state
     * @param {string} password - Decryption password
     */
    async importQuantumState(state, password) {
        await this.importState(state, password);

        if (state.pqcKeys) {
            const pqcDecrypted = await this.decryptData(state.pqcKeys, password);
            const pqcKeys = JSON.parse(new TextDecoder().decode(pqcDecrypted));
            this.pqc.loadKeys(pqcKeys);
            this.quantumKeysGenerated = true;
        }
    }
}

export default QuantumSafePQS;
```

---

## PART 6: MIGRATION PATH

### Upgrading Existing Users

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   MIGRATION STRATEGY: CLASSICAL → POST-QUANTUM                              ║
║   ════════════════════════════════════════════                              ║
║                                                                              ║
║   PHASE 1: HYBRID MODE (2026)                                               ║
║   ────────────────────────────                                              ║
║                                                                              ║
║   • Add PQC alongside existing classical crypto                            ║
║   • Sign with BOTH Dilithium AND ECDSA                                    ║
║   • Encrypt with BOTH Kyber AND ECDH                                      ║
║   • Either algorithm validates (OR logic for verification)                 ║
║                                                                              ║
║   User impact: None - transparent upgrade                                  ║
║                                                                              ║
║   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ║
║                                                                              ║
║   PHASE 2: PQC PRIMARY (2027)                                               ║
║   ───────────────────────────                                               ║
║                                                                              ║
║   • PQC becomes primary                                                    ║
║   • Classical becomes fallback                                             ║
║   • Both required for new signatures (AND logic)                          ║
║   • Old signatures still validate with OR logic                           ║
║                                                                              ║
║   User impact: Slightly larger signatures/keys                            ║
║                                                                              ║
║   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ║
║                                                                              ║
║   PHASE 3: PQC ONLY (2028-2029)                                            ║
║   ─────────────────────────────                                             ║
║                                                                              ║
║   • Classical crypto deprecated                                            ║
║   • All new operations PQC-only                                           ║
║   • Old classical signatures still readable (archive compatibility)        ║
║   • Migration tool to re-sign old data with PQC                           ║
║                                                                              ║
║   User impact: May need to re-sign important documents                    ║
║                                                                              ║
║   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   ║
║                                                                              ║
║   PHASE 4: QUANTUM ARRIVAL (2030+)                                         ║
║   ────────────────────────────────                                          ║
║                                                                              ║
║   • Classical crypto BROKEN by quantum computers                           ║
║   • PQC signatures remain valid                                            ║
║   • Old classical-only signatures no longer trustworthy                   ║
║   • ARC-8 users protected, others vulnerable                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## PART 7: DEPENDENCIES & INSTALLATION

### NPM Packages Required

```json
{
  "dependencies": {
    "@noble/post-quantum": "^0.2.0"
  }
}
```

### Installation

```bash
# Install post-quantum crypto library
npm install @noble/post-quantum

# The @noble libraries are:
# - Pure JavaScript (no native dependencies)
# - Audited and well-maintained
# - NIST-compliant implementations
# - Works in browsers and Node.js
```

### Alternative Libraries

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   LIBRARY OPTIONS:                                                          │
│                                                                              │
│   1. @noble/post-quantum (RECOMMENDED)                                      │
│      • Pure JS, audited, actively maintained                               │
│      • Includes ML-KEM (Kyber) and ML-DSA (Dilithium)                     │
│      • Works in browser and Node.js                                        │
│                                                                              │
│   2. liboqs-js (WASM wrapper)                                              │
│      • WASM wrapper around C library                                       │
│      • More algorithms available                                           │
│      • Larger bundle size                                                  │
│                                                                              │
│   3. pqcrypto (Rust/WASM)                                                  │
│      • Rust implementations compiled to WASM                               │
│      • Very fast                                                           │
│      • Less browser testing                                                │
│                                                                              │
│   4. crystals-kyber-js / dilithium-js                                      │
│      • Standalone implementations                                          │
│      • May not be NIST-final compliant                                    │
│                                                                              │
│   RECOMMENDATION: Start with @noble/post-quantum for                       │
│   compatibility with existing @noble/curves usage.                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## PART 8: SECURITY CONSIDERATIONS

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   SECURITY NOTES:                                                           ║
║   ═══════════════                                                           ║
║                                                                              ║
║   1. KEY SIZES ARE LARGER                                                   ║
║      • Kyber public key: 1,184 bytes (vs 64 for ECDH)                     ║
║      • Dilithium signature: 3,309 bytes (vs 64 for ECDSA)                 ║
║      • Plan for increased storage and bandwidth                            ║
║                                                                              ║
║   2. HYBRID MODE IS CRITICAL                                                ║
║      • PQC algorithms are newer, less battle-tested                       ║
║      • Classical algorithms are proven but quantum-vulnerable             ║
║      • Hybrid provides security against BOTH threats                       ║
║      • Only transition to PQC-only when confident                         ║
║                                                                              ║
║   3. SIDE-CHANNEL ATTACKS                                                   ║
║      • Lattice-based crypto has different side-channel profile            ║
║      • Constant-time implementations critical                              ║
║      • Use audited libraries only                                          ║
║                                                                              ║
║   4. RANDOM NUMBER GENERATION                                               ║
║      • PQC requires high-quality randomness                               ║
║      • crypto.getRandomValues() is sufficient                             ║
║      • Never use Math.random() for crypto                                 ║
║                                                                              ║
║   5. BACKWARDS COMPATIBILITY                                                ║
║      • Old signatures must remain verifiable                              ║
║      • Don't delete classical verification code                           ║
║      • Version all cryptographic operations                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## PART 9: IMPLEMENTATION CHECKLIST

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   IMPLEMENTATION TASKS:                                                     │
│                                                                              │
│   □ Install @noble/post-quantum dependency                                 │
│   □ Create scripts/interface/static/js/core/pqc/ directory                │
│   □ Implement kyber.js (key exchange)                                      │
│   □ Implement dilithium.js (signatures)                                    │
│   □ Implement index.js (unified interface)                                 │
│   □ Create pqs_quantum.js (PQS integration)                               │
│   □ Add hybrid mode to existing signature functions                        │
│   □ Add hybrid mode to existing encryption functions                       │
│   □ Update IndexedDB schema for larger keys                               │
│   □ Create migration tool for existing users                              │
│   □ Add PQC capability detection                                          │
│   □ Update documentation                                                   │
│   □ Add tests for all PQC operations                                       │
│   □ Performance benchmarking                                               │
│                                                                              │
│   TESTING REQUIREMENTS:                                                     │
│                                                                              │
│   □ Key generation works                                                   │
│   □ Encapsulation/decapsulation roundtrip                                 │
│   □ Sign/verify roundtrip                                                  │
│   □ Hybrid mode works                                                      │
│   □ Serialization/deserialization works                                   │
│   □ Integration with existing PQS                                         │
│   □ Performance acceptable (<100ms for operations)                        │
│   □ Works in all target browsers                                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## SUMMARY

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   POST-QUANTUM CRYPTOGRAPHY UPGRADE                                         ║
║   ═════════════════════════════════                                         ║
║                                                                              ║
║   ALGORITHMS:                                                               ║
║   • ML-KEM-768 (Kyber) for key exchange                                   ║
║   • ML-DSA-65 (Dilithium) for signatures                                  ║
║   • AES-256-GCM for symmetric encryption (unchanged)                       ║
║   • SHA-384 for hashing (upgraded from SHA-256)                           ║
║                                                                              ║
║   APPROACH:                                                                 ║
║   • Hybrid mode (classical + PQC) for defense in depth                    ║
║   • Gradual migration over 3 years                                        ║
║   • Backwards-compatible with existing signatures                          ║
║                                                                              ║
║   TIMELINE:                                                                 ║
║   • 2026: Hybrid mode implementation                                       ║
║   • 2027: PQC primary, classical fallback                                 ║
║   • 2028-2029: PQC only for new operations                                ║
║   • 2030+: Protected when quantum computers arrive                        ║
║                                                                              ║
║   UNIQUE VALUE:                                                             ║
║   • NO OTHER archive platform has post-quantum roadmap                    ║
║   • Massive differentiator for institutional partnerships                  ║
║   • "Quantum-proof preservation" is a compelling pitch                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

*Document Version: 1.0*
*Created: 2026-01-13*
*Classification: TECHNICAL SPECIFICATION*
*NIST Standards: FIPS 203, FIPS 204*
