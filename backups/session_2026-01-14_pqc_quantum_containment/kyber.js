/**
 * ARC-8 Post-Quantum Key Encapsulation
 *
 * Uses ML-KEM-768 (CRYSTALS-Kyber) for quantum-resistant key exchange.
 * NIST FIPS 203 compliant.
 *
 * @module pqc/kyber
 * @version 1.0.0
 */

// Note: Requires @noble/post-quantum package
// npm install @noble/post-quantum

let ml_kem768 = null;

/**
 * Initialize the Kyber module
 * Lazy loads the @noble/post-quantum library
 */
async function initKyber() {
    if (!ml_kem768) {
        try {
            const module = await import('@noble/post-quantum/ml-kem');
            ml_kem768 = module.ml_kem768;
            console.log('[ARC8-Kyber] ML-KEM-768 initialized');
        } catch (e) {
            console.warn('[ARC8-Kyber] @noble/post-quantum not available, using fallback');
            // Fallback: use classical ECDH only
            ml_kem768 = null;
        }
    }
    return ml_kem768 !== null;
}

/**
 * ARC-8 Kyber Key Encapsulation
 */
export class ARC8Kyber {

    /**
     * Check if Kyber is available
     * @returns {Promise<boolean>}
     */
    static async isAvailable() {
        return await initKyber();
    }

    /**
     * Generate a new Kyber key pair
     * @returns {Promise<Object>} { publicKey, secretKey, algorithm, quantumSafe, created }
     */
    static async generateKeyPair() {
        await initKyber();

        if (!ml_kem768) {
            throw new Error('Post-quantum crypto not available');
        }

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
     * @returns {Object} { ciphertext, sharedSecret }
     */
    static encapsulate(publicKey) {
        if (!ml_kem768) {
            throw new Error('Post-quantum crypto not available');
        }

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
     * @returns {Uint8Array} 32-byte shared secret
     */
    static decapsulate(secretKey, ciphertext) {
        if (!ml_kem768) {
            throw new Error('Post-quantum crypto not available');
        }

        return ml_kem768.decapsulate(ciphertext, secretKey);
    }

    /**
     * Hybrid key exchange (Kyber + ECDH for defense in depth)
     * @param {Uint8Array} kyberPublicKey - Recipient's Kyber public key
     * @param {CryptoKey} ecdhPublicKey - Recipient's ECDH public key
     * @returns {Promise<Object>} { kyberCiphertext, ecdhPublicKey, sharedSecret }
     */
    static async hybridEncapsulate(kyberPublicKey, ecdhPublicKey) {
        // Kyber encapsulation
        const kyberResult = this.encapsulate(kyberPublicKey);

        // ECDH key agreement
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

        // Combine secrets using HKDF
        const combinedSecret = await this.combineSecrets(
            kyberResult.sharedSecret,
            new Uint8Array(ecdhShared)
        );

        return {
            kyberCiphertext: kyberResult.ciphertext,
            ecdhPublicKey: await crypto.subtle.exportKey('raw', ecdhKeyPair.publicKey),
            sharedSecret: combinedSecret,
            algorithm: 'HYBRID-ML-KEM-768-ECDH-P384'
        };
    }

    /**
     * Combine two shared secrets using HKDF
     * @param {Uint8Array} secret1 - Kyber shared secret
     * @param {Uint8Array} secret2 - ECDH shared secret
     * @returns {Promise<Uint8Array>} Combined 32-byte secret
     */
    static async combineSecrets(secret1, secret2) {
        const combined = new Uint8Array(secret1.length + secret2.length);
        combined.set(secret1, 0);
        combined.set(secret2, secret1.length);

        const keyMaterial = await crypto.subtle.importKey(
            'raw',
            combined,
            'HKDF',
            false,
            ['deriveBits']
        );

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
     * @param {Object} keyPair
     * @returns {Object} JSON-serializable
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
     * @param {Object} serialized
     * @returns {Object} Key pair with Uint8Arrays
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
     * @returns {Object}
     */
    static getInfo() {
        return {
            name: 'ML-KEM-768',
            alias: 'CRYSTALS-Kyber',
            standard: 'NIST FIPS 203',
            securityLevel: 3,
            publicKeySize: 1184,
            secretKeySize: 2400,
            ciphertextSize: 1088,
            sharedSecretSize: 32,
            quantumSafe: true
        };
    }
}

export default ARC8Kyber;
