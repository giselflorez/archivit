/**
 * ARC-8 Post-Quantum Cryptography Suite
 *
 * Unified interface for quantum-resistant cryptographic operations:
 * - Key exchange: ML-KEM-768 (CRYSTALS-Kyber)
 * - Digital signatures: ML-DSA-65 (CRYSTALS-Dilithium)
 *
 * NIST Standards: FIPS 203, FIPS 204 (August 2024)
 *
 * @module pqc
 * @version 1.0.0
 */

import { ARC8Kyber } from './kyber.js';
import { ARC8Dilithium } from './dilithium.js';

/**
 * ARC-8 Post-Quantum Cryptography Suite
 */
export class ARC8PQC {

    constructor() {
        this.kyberKeys = null;
        this.dilithiumKeys = null;
        this.initialized = false;
        this.available = false;
    }

    /**
     * Check if PQC is available in this environment
     * @returns {Promise<boolean>}
     */
    async checkAvailability() {
        const kyberAvailable = await ARC8Kyber.isAvailable();
        const dilithiumAvailable = await ARC8Dilithium.isAvailable();
        this.available = kyberAvailable && dilithiumAvailable;
        return this.available;
    }

    /**
     * Initialize PQC key pairs
     * @returns {Promise<Object>} { kyber, dilithium, generationTime }
     */
    async initialize() {
        console.log('[ARC8-PQC] Initializing post-quantum cryptography...');

        const startTime = performance.now();

        // Check availability
        if (!await this.checkAvailability()) {
            console.warn('[ARC8-PQC] Post-quantum crypto not available');
            return { available: false };
        }

        // Generate Kyber keys
        this.kyberKeys = await ARC8Kyber.generateKeyPair();
        console.log('[ARC8-PQC] Kyber keys generated:', {
            publicKeySize: this.kyberKeys.publicKey.length,
            secretKeySize: this.kyberKeys.secretKey.length
        });

        // Generate Dilithium keys
        this.dilithiumKeys = await ARC8Dilithium.generateKeyPair();
        console.log('[ARC8-PQC] Dilithium keys generated:', {
            publicKeySize: this.dilithiumKeys.publicKey.length,
            secretKeySize: this.dilithiumKeys.secretKey.length
        });

        const elapsed = performance.now() - startTime;
        console.log(`[ARC8-PQC] Initialization complete in ${elapsed.toFixed(2)}ms`);

        this.initialized = true;

        return {
            available: true,
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
        this.available = true;
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
     * @returns {Promise<Object>}
     */
    async encryptFor(data, recipientKyberPublic) {
        this._checkInitialized();

        const { ciphertext, sharedSecret } = ARC8Kyber.encapsulate(recipientKyberPublic);

        const aesKey = await crypto.subtle.importKey(
            'raw',
            sharedSecret,
            { name: 'AES-GCM' },
            false,
            ['encrypt']
        );

        const nonce = crypto.getRandomValues(new Uint8Array(12));

        const encryptedData = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: nonce },
            aesKey,
            data
        );

        return {
            kyberCiphertext: Array.from(ciphertext),
            encryptedData: Array.from(new Uint8Array(encryptedData)),
            nonce: Array.from(nonce),
            algorithm: 'ML-KEM-768-AES-256-GCM',
            quantumSafe: true
        };
    }

    /**
     * Decrypt data sent to you
     * @param {Object} encrypted - Encrypted data object
     * @returns {Promise<Uint8Array>}
     */
    async decrypt(encrypted) {
        this._checkInitialized();

        const ciphertext = new Uint8Array(encrypted.kyberCiphertext);
        const sharedSecret = ARC8Kyber.decapsulate(this.kyberKeys.secretKey, ciphertext);

        const aesKey = await crypto.subtle.importKey(
            'raw',
            sharedSecret,
            { name: 'AES-GCM' },
            false,
            ['decrypt']
        );

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
     * @param {Object} context - Optional context
     * @returns {Object} Signature
     */
    sign(data, context = {}) {
        this._checkInitialized();

        return ARC8Dilithium.signWithContext(
            this.dilithiumKeys.secretKey,
            data,
            context
        );
    }

    /**
     * Verify a signature
     * @param {Uint8Array|Array} signerPublicKey - Signer's Dilithium public key
     * @param {Object} signedObject - Signed object
     * @returns {Object} Verification result
     */
    verify(signerPublicKey, signedObject) {
        const pubKey = signerPublicKey instanceof Uint8Array
            ? signerPublicKey
            : new Uint8Array(signerPublicKey);

        return ARC8Dilithium.verifyWithContext(pubKey, signedObject);
    }

    /**
     * Create signed + encrypted message
     * @param {Uint8Array} data
     * @param {Uint8Array} recipientKyberPublic
     * @returns {Promise<Object>}
     */
    async createSecureMessage(data, recipientKyberPublic) {
        this._checkInitialized();

        const signature = this.sign(data, {
            purpose: 'secure-message',
            timestamp: Date.now()
        });

        const package_ = {
            data: Array.from(data),
            signature
        };

        const packageBytes = new TextEncoder().encode(JSON.stringify(package_));
        const encrypted = await this.encryptFor(packageBytes, recipientKyberPublic);

        return {
            ...encrypted,
            senderPublicKey: Array.from(this.dilithiumKeys.publicKey),
            type: 'ARC8-SECURE-MESSAGE-v1'
        };
    }

    /**
     * Open signed + encrypted message
     * @param {Object} message
     * @returns {Promise<Object>}
     */
    async openSecureMessage(message) {
        this._checkInitialized();

        const packageBytes = await this.decrypt(message);
        const package_ = JSON.parse(new TextDecoder().decode(packageBytes));

        const verification = this.verify(message.senderPublicKey, package_.signature);

        return {
            data: new Uint8Array(package_.data),
            signatureValid: verification.valid,
            senderPublicKey: message.senderPublicKey,
            signedAt: verification.timestamp,
            context: verification.context
        };
    }

    /**
     * Check if initialized
     * @private
     */
    _checkInitialized() {
        if (!this.initialized) {
            throw new Error('PQC not initialized. Call initialize() first.');
        }
    }

    /**
     * Get cryptographic capabilities
     * @returns {Object}
     */
    static getCapabilities() {
        return {
            keyExchange: {
                algorithm: 'ML-KEM-768 (CRYSTALS-Kyber)',
                nistLevel: 3,
                quantumSafe: true,
                standard: 'FIPS 203',
                ...ARC8Kyber.getInfo()
            },
            signatures: {
                algorithm: 'ML-DSA-65 (CRYSTALS-Dilithium)',
                nistLevel: 3,
                quantumSafe: true,
                standard: 'FIPS 204',
                ...ARC8Dilithium.getInfo()
            },
            symmetric: {
                algorithm: 'AES-256-GCM',
                quantumSafe: true,
                notes: 'Grover reduces to 128-bit, still secure'
            },
            hashing: {
                algorithm: 'SHA-384',
                quantumSafe: true
            },
            hybridMode: true,
            version: 'ARC8-PQC-v1'
        };
    }
}

// Export individual modules
export { ARC8Kyber, ARC8Dilithium };

// Default export
export default ARC8PQC;
