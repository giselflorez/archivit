/**
 * PQS-QUANTUM BRIDGE
 * ==================
 * Post-Quantum Cryptographic Extension for the Unified Seed Engine
 *
 * Extends the existing PQS (Pi-Quadratic Seed) system with quantum-resistant
 * cryptographic capabilities derived from the user's genesis entropy.
 *
 * ARCHITECTURE:
 * ┌─────────────────────────────────────────────────────────────────────────┐
 * │                         UNIFIED SEED ENGINE                             │
 * │                                │                                        │
 * │                    ┌───────────┴───────────┐                            │
 * │                    │                       │                            │
 * │           ┌────────▼────────┐    ┌────────▼────────┐                    │
 * │           │   PQS ENGINE    │    │   PQC ENGINE    │                    │
 * │           │  (Behavioral)   │    │   (Quantum)     │                    │
 * │           │                 │    │                 │                    │
 * │           │ π-Quadratic     │    │ ML-KEM-768      │                    │
 * │           │ Transform       │    │ ML-DSA-65       │                    │
 * │           └────────┬────────┘    └────────┬────────┘                    │
 * │                    │                       │                            │
 * │                    └───────────┬───────────┘                            │
 * │                                │                                        │
 * │                    ┌───────────▼───────────┐                            │
 * │                    │   GENESIS ENTROPY     │                            │
 * │                    │   (Root of Trust)     │                            │
 * │                    └───────────────────────┘                            │
 * └─────────────────────────────────────────────────────────────────────────┘
 *
 * NIST Standards: FIPS 203 (ML-KEM), FIPS 204 (ML-DSA)
 *
 * @module pqs_quantum
 * @version 1.0.0
 */

import { ARC8PQC, ARC8Kyber, ARC8Dilithium } from './pqc/index.js';
import { UnifiedSeedEngine } from './seed_pqs_integration.js';
import { PHI, GOLDEN_ANGLE } from './pi_quadratic_seed.js';
import { nistBeacon } from './nist_beacon.js';

/**
 * Quantum-Enhanced Unified Seed Engine
 * Extends UnifiedSeedEngine with post-quantum cryptographic capabilities
 */
class QuantumSeedEngine extends UnifiedSeedEngine {

    constructor() {
        super();

        // Post-quantum cryptography engine
        this.pqc = new ARC8PQC();
        this.isPQCInitialized = false;

        // Quantum state
        this.quantumState = {
            keyGenerationTime: null,
            lastKeyRotation: null,
            signatureCount: 0,
            encryptionCount: 0
        };

        // Configuration
        this.quantumConfig = {
            autoGenerateKeys: true,           // Generate keys on initialization
            rotationThreshold: 10000,         // Rotate keys after N signatures
            hybridMode: true,                 // Use hybrid (PQC + classical)
            persistKeys: true                 // Store keys in seed
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Initialize with quantum capabilities
     * @returns {Promise<Object>}
     */
    async initialize() {
        // Initialize base engine first
        await super.initialize();

        // Check quantum availability
        const pqcAvailable = await this.pqc.checkAvailability();

        if (!pqcAvailable) {
            console.warn('[PQS-Quantum] Post-quantum crypto not available');
            this._emit('quantum_unavailable', {
                reason: 'Library not loaded',
                fallback: 'classical'
            });
            return this;
        }

        // Initialize quantum keys
        if (this.quantumConfig.autoGenerateKeys) {
            await this._initializeQuantumKeys();
        }

        console.log('[PQS-Quantum] Quantum-enhanced engine initialized');

        return this;
    }

    /**
     * Initialize quantum keys from genesis entropy
     * @private
     */
    async _initializeQuantumKeys() {
        // Check if keys exist in seed
        if (this.seedEngine.seed?.meta?.quantum_keys) {
            console.log('[PQS-Quantum] Restoring existing quantum keys');
            this.pqc.loadKeys(this.seedEngine.seed.meta.quantum_keys);
            this.isPQCInitialized = true;

            this._emit('quantum_restored', {
                hasKyber: !!this.pqc.kyberKeys,
                hasDilithium: !!this.pqc.dilithiumKeys
            });

            return;
        }

        // Generate new keys
        console.log('[PQS-Quantum] Generating quantum key pairs...');

        const result = await this.pqc.initialize();

        if (!result.available) {
            console.warn('[PQS-Quantum] Key generation failed');
            return;
        }

        this.quantumState.keyGenerationTime = result.generationTime;
        this.quantumState.lastKeyRotation = Date.now();
        this.isPQCInitialized = true;

        // Persist keys to seed
        if (this.quantumConfig.persistKeys) {
            await this._persistQuantumKeys();
        }

        this._emit('quantum_initialized', {
            kyberPublicKeySize: result.kyber.publicKey.length,
            dilithiumPublicKeySize: result.dilithium.publicKey.length,
            generationTime: result.generationTime
        });
    }

    /**
     * Persist quantum keys to seed storage
     * @private
     */
    async _persistQuantumKeys() {
        if (!this.seedEngine.seed) return;

        // Store serialized keys in meta
        this.seedEngine.seed.meta.quantum_keys = this.pqc.exportKeys();

        // Also store quantum state
        this.seedEngine.seed.meta.quantum_state = {
            ...this.quantumState,
            lastUpdated: Date.now()
        };

        await this.seedEngine._saveToStorage();

        console.log('[PQS-Quantum] Quantum keys persisted to seed');
    }

    // ═══════════════════════════════════════════════════════════════════════
    // KEY MANAGEMENT
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get public keys for sharing
     * @returns {Object|null}
     */
    getPublicKeys() {
        if (!this.isPQCInitialized) {
            return null;
        }

        return {
            ...this.pqc.getPublicKeys(),
            seedFingerprint: this.seedEngine.seed?.genesis?.root_signature,
            pqsVertex: this.pqs?.vertex,
            generatedAt: this.quantumState.keyGenerationTime
        };
    }

    /**
     * Rotate quantum keys (after threshold or on demand)
     * @param {boolean} force - Force rotation even if threshold not met
     * @returns {Promise<Object>}
     */
    async rotateKeys(force = false) {
        if (!this.isPQCInitialized && !force) {
            throw new Error('Quantum not initialized');
        }

        const shouldRotate = force ||
            this.quantumState.signatureCount >= this.quantumConfig.rotationThreshold;

        if (!shouldRotate) {
            return {
                rotated: false,
                reason: 'Threshold not met',
                currentCount: this.quantumState.signatureCount,
                threshold: this.quantumConfig.rotationThreshold
            };
        }

        console.log('[PQS-Quantum] Rotating quantum keys...');

        // Archive old public keys (for verification of old signatures)
        const oldPublicKeys = this.getPublicKeys();

        // Generate new keys
        await this.pqc.initialize();

        // Reset counters
        this.quantumState.signatureCount = 0;
        this.quantumState.lastKeyRotation = Date.now();

        // Persist new keys
        await this._persistQuantumKeys();

        this._emit('keys_rotated', {
            oldKeyFingerprint: this._fingerprintKey(oldPublicKeys?.dilithium),
            newKeyFingerprint: this._fingerprintKey(this.pqc.dilithiumKeys?.publicKey),
            rotatedAt: Date.now()
        });

        return {
            rotated: true,
            newPublicKeys: this.getPublicKeys()
        };
    }

    /**
     * Generate fingerprint for a public key
     * @private
     */
    _fingerprintKey(publicKey) {
        if (!publicKey) return null;

        const bytes = publicKey instanceof Uint8Array
            ? publicKey
            : new Uint8Array(publicKey);

        // Simple fingerprint: first 8 bytes as hex
        return Array.from(bytes.slice(0, 8))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    // ═══════════════════════════════════════════════════════════════════════
    // QUANTUM SIGNATURES
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Sign data with quantum-safe signature
     * @param {Uint8Array|string} data - Data to sign
     * @param {Object} context - Optional context
     * @returns {Object} Signature object
     */
    quantumSign(data, context = {}) {
        this._checkQuantumInitialized();

        // Convert string to Uint8Array if needed
        const dataBytes = typeof data === 'string'
            ? new TextEncoder().encode(data)
            : data;

        // Add seed context
        const enrichedContext = {
            ...context,
            seedFingerprint: this.seedEngine.seed?.genesis?.root_signature,
            pqsVertex: this.pqs?.vertex,
            signatureIndex: this.quantumState.signatureCount
        };

        const signature = this.pqc.sign(dataBytes, enrichedContext);

        // Update state
        this.quantumState.signatureCount++;

        // Check if rotation needed
        if (this.quantumState.signatureCount >= this.quantumConfig.rotationThreshold) {
            this._emit('rotation_recommended', {
                signatureCount: this.quantumState.signatureCount,
                threshold: this.quantumConfig.rotationThreshold
            });
        }

        return {
            ...signature,
            quantumSafe: true,
            algorithm: 'ML-DSA-65',
            signerPublicKey: Array.from(this.pqc.dilithiumKeys.publicKey)
        };
    }

    /**
     * Verify a quantum signature
     * @param {Object} signedObject - Signature object
     * @param {Uint8Array|Array} publicKey - Optional specific public key
     * @returns {Object} Verification result
     */
    quantumVerify(signedObject, publicKey = null) {
        const signerKey = publicKey || signedObject.signerPublicKey;

        if (!signerKey) {
            return {
                valid: false,
                error: 'No public key provided'
            };
        }

        return this.pqc.verify(signerKey, signedObject);
    }

    /**
     * Sign a seed export for authenticity verification
     * @returns {Object}
     */
    signSeedExport() {
        this._checkQuantumInitialized();

        const exportData = this.exportPlaintext();
        const exportBytes = new TextEncoder().encode(JSON.stringify(exportData));

        const signature = this.quantumSign(exportBytes, {
            purpose: 'seed-export',
            exportedAt: Date.now()
        });

        return {
            export: exportData,
            signature,
            quantumSafe: true,
            verificationKey: Array.from(this.pqc.dilithiumKeys.publicKey)
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // QUANTUM ENCRYPTION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Encrypt data for a recipient using quantum-safe encryption
     * @param {Uint8Array|string} data - Data to encrypt
     * @param {Uint8Array|Array} recipientKyberPublic - Recipient's Kyber public key
     * @returns {Promise<Object>}
     */
    async quantumEncrypt(data, recipientKyberPublic) {
        this._checkQuantumInitialized();

        const dataBytes = typeof data === 'string'
            ? new TextEncoder().encode(data)
            : data;

        const recipientKey = recipientKyberPublic instanceof Uint8Array
            ? recipientKyberPublic
            : new Uint8Array(recipientKyberPublic);

        const encrypted = await this.pqc.encryptFor(dataBytes, recipientKey);

        this.quantumState.encryptionCount++;

        return {
            ...encrypted,
            senderPublicKey: this.getPublicKeys()
        };
    }

    /**
     * Decrypt data sent to you
     * @param {Object} encrypted - Encrypted data object
     * @returns {Promise<Uint8Array>}
     */
    async quantumDecrypt(encrypted) {
        this._checkQuantumInitialized();
        return await this.pqc.decrypt(encrypted);
    }

    /**
     * Create a secure, signed and encrypted message
     * @param {Uint8Array|string} data
     * @param {Uint8Array|Array} recipientKyberPublic
     * @returns {Promise<Object>}
     */
    async createSecureMessage(data, recipientKyberPublic) {
        this._checkQuantumInitialized();

        const dataBytes = typeof data === 'string'
            ? new TextEncoder().encode(data)
            : data;

        const recipientKey = recipientKyberPublic instanceof Uint8Array
            ? recipientKyberPublic
            : new Uint8Array(recipientKyberPublic);

        const message = await this.pqc.createSecureMessage(dataBytes, recipientKey);

        // Add seed provenance
        return {
            ...message,
            senderSeedFingerprint: this.seedEngine.seed?.genesis?.root_signature,
            senderPQSVertex: this.pqs?.vertex
        };
    }

    /**
     * Open a secure message and verify signature
     * @param {Object} message
     * @returns {Promise<Object>}
     */
    async openSecureMessage(message) {
        this._checkQuantumInitialized();
        return await this.pqc.openSecureMessage(message);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // OWNERSHIP & PROVENANCE
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Generate quantum-enhanced ownership proof
     * Combines PQS behavioral proof with quantum signature
     * @returns {Object}
     */
    generateQuantumOwnershipProof() {
        this._checkQuantumInitialized();

        // Get base ownership proof
        const baseProof = this.generateOwnershipProof();

        // Sign the proof with quantum signature
        const proofBytes = new TextEncoder().encode(JSON.stringify(baseProof));
        const quantumSignature = this.quantumSign(proofBytes, {
            purpose: 'ownership-proof',
            timestamp: Date.now()
        });

        return {
            ...baseProof,
            quantum: {
                signature: quantumSignature,
                publicKey: Array.from(this.pqc.dilithiumKeys.publicKey),
                algorithm: 'ML-DSA-65',
                quantumSafe: true
            },
            proofVersion: 'ARC8-QUANTUM-v1'
        };
    }

    /**
     * Verify a quantum ownership proof
     * @param {Object} proof
     * @returns {Object}
     */
    verifyQuantumOwnershipProof(proof) {
        // Verify base PQS proof
        const pqsValid = this.verifyOwnershipProof(proof);

        // Verify quantum signature
        let quantumValid = false;
        if (proof.quantum?.signature && proof.quantum?.publicKey) {
            const baseProofData = { ...proof };
            delete baseProofData.quantum;

            const proofBytes = new TextEncoder().encode(JSON.stringify(baseProofData));
            const verification = this.quantumVerify(
                proof.quantum.signature,
                proof.quantum.publicKey
            );
            quantumValid = verification.valid;
        }

        return {
            valid: pqsValid && quantumValid,
            pqsValid,
            quantumValid,
            proofVersion: proof.proofVersion,
            verifiedAt: Date.now()
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // CONTENT PROVENANCE
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Create provenance record for content
     * @param {Object} content - Content metadata
     * @param {Uint8Array} contentHash - Hash of actual content
     * @returns {Promise<Object>}
     */
    async createProvenanceRecord(content, contentHash) {
        this._checkQuantumInitialized();

        // Get NIST beacon anchor for institutional-grade timestamp
        const beaconAnchor = await nistBeacon.createTimestampAnchor(contentHash);

        const record = {
            contentHash: Array.from(contentHash),
            metadata: content,
            creator: {
                seedFingerprint: this.seedEngine.seed?.genesis?.root_signature,
                pqsVertex: this.pqs?.vertex,
                dilithiumPublicKey: Array.from(this.pqc.dilithiumKeys.publicKey)
            },
            timestamp: Date.now(),
            // NIST Quantum Random Beacon anchor for unforgeable timestamps
            nistBeacon: beaconAnchor.anchored ? {
                pulseIndex: beaconAnchor.anchor.beaconPulse.pulseIndex,
                outputValue: beaconAnchor.anchor.beaconPulse.outputValue,
                beaconTimestamp: beaconAnchor.anchor.beaconPulse.timeStamp,
                anchorHash: beaconAnchor.anchor.anchorHash,
                verificationUrl: beaconAnchor.verificationUrl
            } : null,
            beaconAnchored: beaconAnchor.anchored,
            version: 'ARC8-PROVENANCE-v2'
        };

        // Sign the record
        const recordBytes = new TextEncoder().encode(JSON.stringify(record));
        const signature = this.quantumSign(recordBytes, {
            purpose: 'content-provenance',
            contentType: content.type,
            beaconAnchored: beaconAnchor.anchored
        });

        return {
            record,
            signature,
            quantumSafe: true,
            beaconAnchored: beaconAnchor.anchored,
            institutionallyVerifiable: beaconAnchor.anchored
        };
    }

    /**
     * Verify content provenance record
     * @param {Object} provenance
     * @param {boolean} verifyBeacon - Also verify NIST beacon (requires network)
     * @returns {Promise<Object>}
     */
    async verifyProvenanceRecord(provenance, verifyBeacon = false) {
        const record = provenance.record;
        const signature = provenance.signature;

        // Reconstruct and verify signature
        const recordBytes = new TextEncoder().encode(JSON.stringify(record));

        const verification = this.quantumVerify(
            signature,
            record.creator.dilithiumPublicKey
        );

        // Verify NIST beacon if requested and available
        let beaconVerification = null;
        if (verifyBeacon && record.nistBeacon) {
            beaconVerification = await nistBeacon.verifyPulse({
                pulseIndex: record.nistBeacon.pulseIndex,
                outputValue: record.nistBeacon.outputValue,
                timeStamp: record.nistBeacon.beaconTimestamp
            });
        }

        return {
            valid: verification.valid,
            creator: record.creator.seedFingerprint,
            createdAt: record.timestamp,
            quantumSafe: provenance.quantumSafe,
            algorithm: signature.algorithm,
            // NIST beacon verification
            beaconAnchored: record.beaconAnchored || false,
            beaconVerified: beaconVerification?.valid || null,
            beaconTimestamp: record.nistBeacon?.beaconTimestamp || null,
            institutionallyVerifiable: record.beaconAnchored,
            verificationUrl: record.nistBeacon?.verificationUrl || null
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UTILITIES
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Check if quantum is initialized
     * @private
     */
    _checkQuantumInitialized() {
        if (!this.isPQCInitialized) {
            throw new Error('Quantum not initialized. Call initialize() first.');
        }
    }

    /**
     * Get quantum capabilities and status
     * @returns {Object}
     */
    getQuantumStatus() {
        return {
            available: this.pqc.available,
            initialized: this.isPQCInitialized,
            state: { ...this.quantumState },
            config: { ...this.quantumConfig },
            capabilities: ARC8PQC.getCapabilities(),
            publicKeyFingerprints: {
                kyber: this._fingerprintKey(this.pqc.kyberKeys?.publicKey),
                dilithium: this._fingerprintKey(this.pqc.dilithiumKeys?.publicKey)
            }
        };
    }

    /**
     * Get full mathematical state including quantum
     * @returns {Object}
     */
    getMathematicalState() {
        const baseState = super.getMathematicalState();

        return {
            ...baseState,
            quantum: {
                initialized: this.isPQCInitialized,
                algorithms: {
                    keyExchange: 'ML-KEM-768',
                    signature: 'ML-DSA-65'
                },
                keyFingerprints: {
                    kyber: this._fingerprintKey(this.pqc.kyberKeys?.publicKey),
                    dilithium: this._fingerprintKey(this.pqc.dilithiumKeys?.publicKey)
                },
                signatureCount: this.quantumState.signatureCount,
                encryptionCount: this.quantumState.encryptionCount
            }
        };
    }

    /**
     * Export complete state including quantum keys
     * @returns {Promise<Object>}
     */
    async export() {
        const baseExport = await super.export();

        return {
            ...baseExport,
            quantum: {
                keys: this.pqc.exportKeys(),
                state: this.quantumState,
                config: this.quantumConfig
            },
            quantumSafe: true,
            version: 'ARC8-QUANTUM-SEED-v1'
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const quantumSeed = new QuantumSeedEngine();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export { QuantumSeedEngine, quantumSeed };
export default quantumSeed;
