/**
 * ARC-8 Post-Quantum Digital Signatures
 *
 * Uses ML-DSA-65 (CRYSTALS-Dilithium) for quantum-resistant signatures.
 * NIST FIPS 204 compliant.
 *
 * @module pqc/dilithium
 * @version 1.0.0
 */

let ml_dsa65 = null;

/**
 * Initialize the Dilithium module
 */
async function initDilithium() {
    if (!ml_dsa65) {
        try {
            const module = await import('@noble/post-quantum/ml-dsa');
            ml_dsa65 = module.ml_dsa65;
            console.log('[ARC8-Dilithium] ML-DSA-65 initialized');
        } catch (e) {
            console.warn('[ARC8-Dilithium] @noble/post-quantum not available');
            ml_dsa65 = null;
        }
    }
    return ml_dsa65 !== null;
}

/**
 * ARC-8 Dilithium Digital Signatures
 */
export class ARC8Dilithium {

    /**
     * Check if Dilithium is available
     * @returns {Promise<boolean>}
     */
    static async isAvailable() {
        return await initDilithium();
    }

    /**
     * Generate a new Dilithium signing key pair
     * @returns {Promise<Object>} { publicKey, secretKey, algorithm, quantumSafe, created }
     */
    static async generateKeyPair() {
        await initDilithium();

        if (!ml_dsa65) {
            throw new Error('Post-quantum crypto not available');
        }

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
     * Sign a message
     * @param {Uint8Array} secretKey - Dilithium secret key
     * @param {Uint8Array} message - Message to sign
     * @returns {Uint8Array} Signature (3,309 bytes)
     */
    static sign(secretKey, message) {
        if (!ml_dsa65) {
            throw new Error('Post-quantum crypto not available');
        }

        return ml_dsa65.sign(secretKey, message);
    }

    /**
     * Verify a signature
     * @param {Uint8Array} publicKey - Signer's public key
     * @param {Uint8Array} message - Original message
     * @param {Uint8Array} signature - Signature to verify
     * @returns {boolean} True if valid
     */
    static verify(publicKey, message, signature) {
        if (!ml_dsa65) {
            throw new Error('Post-quantum crypto not available');
        }

        return ml_dsa65.verify(publicKey, message, signature);
    }

    /**
     * Sign with context and timestamp
     * @param {Uint8Array} secretKey - Dilithium secret key
     * @param {Uint8Array} message - Message to sign
     * @param {Object} context - Additional context
     * @returns {Object} Structured signature
     */
    static signWithContext(secretKey, message, context = {}) {
        const timestamp = Date.now();

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
     * @param {Uint8Array} publicKey - Signer's public key
     * @param {Object} signedObject - Object from signWithContext
     * @returns {Object} { valid, timestamp, context }
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
     * Hybrid signature (Dilithium + ECDSA)
     * @param {Uint8Array} dilithiumSecretKey
     * @param {CryptoKey} ecdsaPrivateKey
     * @param {Uint8Array} message
     * @returns {Promise<Object>}
     */
    static async hybridSign(dilithiumSecretKey, ecdsaPrivateKey, message) {
        // Dilithium signature
        const dilithiumSig = this.sign(dilithiumSecretKey, message);

        // ECDSA signature
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
     * Verify hybrid signature (both must be valid)
     * @param {Uint8Array} dilithiumPublicKey
     * @param {CryptoKey} ecdsaPublicKey
     * @param {Uint8Array} message
     * @param {Object} hybridSig
     * @returns {Promise<Object>}
     */
    static async hybridVerify(dilithiumPublicKey, ecdsaPublicKey, message, hybridSig) {
        const dilithiumSig = new Uint8Array(hybridSig.dilithiumSignature);
        const dilithiumValid = this.verify(dilithiumPublicKey, message, dilithiumSig);

        let ecdsaValid = false;
        try {
            const ecdsaSig = new Uint8Array(hybridSig.ecdsaSignature);
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
     * Serialize key pair
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
     * Deserialize key pair
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

    /**
     * Get algorithm information
     */
    static getInfo() {
        return {
            name: 'ML-DSA-65',
            alias: 'CRYSTALS-Dilithium',
            standard: 'NIST FIPS 204',
            securityLevel: 3,
            publicKeySize: 1952,
            secretKeySize: 4032,
            signatureSize: 3309,
            quantumSafe: true
        };
    }
}

export default ARC8Dilithium;
