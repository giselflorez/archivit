/**
 * ARC-8 PQC Integration Tests
 *
 * Tests for the unified post-quantum cryptography suite
 * ML-KEM-768 + ML-DSA-65 integration
 */

import ARC8PQC, { ARC8Kyber, ARC8Dilithium } from '../index.js';

describe('ARC8PQC', () => {

    describe('initialization', () => {
        test('should create instance', () => {
            const pqc = new ARC8PQC();

            expect(pqc).toBeInstanceOf(ARC8PQC);
            expect(pqc.initialized).toBe(false);
            expect(pqc.available).toBe(false);
            expect(pqc.kyberKeys).toBeNull();
            expect(pqc.dilithiumKeys).toBeNull();
        });

        test('should check availability', async () => {
            const pqc = new ARC8PQC();
            const available = await pqc.checkAvailability();

            expect(typeof available).toBe('boolean');
            expect(pqc.available).toBe(available);
        });

        test('should initialize with key pairs', async () => {
            const pqc = new ARC8PQC();
            const result = await pqc.initialize();

            expect(result.available).toBe(true);
            expect(pqc.initialized).toBe(true);
            expect(pqc.kyberKeys).toBeDefined();
            expect(pqc.dilithiumKeys).toBeDefined();
            expect(result.generationTime).toBeGreaterThan(0);
        });

        test('should report key generation timing', async () => {
            const pqc = new ARC8PQC();
            const result = await pqc.initialize();

            expect(result.generationTime).toBeDefined();
            expect(typeof result.generationTime).toBe('number');
        });
    });

    describe('key management', () => {
        let pqc;

        beforeAll(async () => {
            pqc = new ARC8PQC();
            await pqc.initialize();
        });

        test('should export keys', () => {
            const exported = pqc.exportKeys();

            expect(exported.kyber).toBeDefined();
            expect(exported.dilithium).toBeDefined();
            expect(exported.version).toBe('ARC8-PQC-v1');
            expect(exported.exportedAt).toBeDefined();

            // Keys should be arrays (JSON-safe)
            expect(Array.isArray(exported.kyber.publicKey)).toBe(true);
            expect(Array.isArray(exported.kyber.secretKey)).toBe(true);
        });

        test('should get public keys only', () => {
            const publicKeys = pqc.getPublicKeys();

            expect(publicKeys.kyber).toBeDefined();
            expect(publicKeys.dilithium).toBeDefined();
            expect(publicKeys.algorithms.keyExchange).toBe('ML-KEM-768');
            expect(publicKeys.algorithms.signature).toBe('ML-DSA-65');

            // Should be arrays
            expect(Array.isArray(publicKeys.kyber)).toBe(true);
            expect(Array.isArray(publicKeys.dilithium)).toBe(true);
        });

        test('should load keys from storage', async () => {
            const pqc1 = new ARC8PQC();
            await pqc1.initialize();
            const exported = pqc1.exportKeys();

            // Simulate storage roundtrip
            const json = JSON.stringify(exported);
            const stored = JSON.parse(json);

            // Load into new instance
            const pqc2 = new ARC8PQC();
            pqc2.loadKeys(stored);

            expect(pqc2.initialized).toBe(true);
            expect(pqc2.available).toBe(true);
            expect(pqc2.kyberKeys.publicKey.length).toBe(1184);
            expect(pqc2.dilithiumKeys.publicKey.length).toBe(1952);
        });
    });

    describe('encryption/decryption', () => {
        let sender;
        let recipient;
        const testData = new TextEncoder().encode('Secret quantum message');

        beforeAll(async () => {
            sender = new ARC8PQC();
            recipient = new ARC8PQC();
            await sender.initialize();
            await recipient.initialize();
        });

        test('should encrypt data for recipient', async () => {
            const encrypted = await sender.encryptFor(
                testData,
                recipient.kyberKeys.publicKey
            );

            expect(encrypted).toBeDefined();
            expect(encrypted.kyberCiphertext).toBeDefined();
            expect(encrypted.encryptedData).toBeDefined();
            expect(encrypted.nonce).toBeDefined();
            expect(encrypted.algorithm).toBe('ML-KEM-768-AES-256-GCM');
            expect(encrypted.quantumSafe).toBe(true);
        });

        test('should decrypt data as recipient', async () => {
            const encrypted = await sender.encryptFor(
                testData,
                recipient.kyberKeys.publicKey
            );

            const decrypted = await recipient.decrypt(encrypted);

            expect(decrypted).toBeInstanceOf(Uint8Array);
            expect(new TextDecoder().decode(decrypted)).toBe('Secret quantum message');
        });

        test('should fail decryption with wrong key', async () => {
            const encrypted = await sender.encryptFor(
                testData,
                recipient.kyberKeys.publicKey
            );

            // Try to decrypt with sender's keys (wrong)
            await expect(sender.decrypt(encrypted)).rejects.toThrow();
        });

        test('should encrypt/decrypt large data', async () => {
            const largeData = new Uint8Array(100000);
            // Fill in chunks of 65536 bytes (Node crypto.getRandomValues limit)
            for (let i = 0; i < largeData.length; i += 65536) {
                const chunk = Math.min(65536, largeData.length - i);
                crypto.getRandomValues(largeData.subarray(i, i + chunk));
            }

            const encrypted = await sender.encryptFor(
                largeData,
                recipient.kyberKeys.publicKey
            );

            const decrypted = await recipient.decrypt(encrypted);

            expect(decrypted.length).toBe(largeData.length);
            expect(Array.from(decrypted.slice(0, 100)).join(','))
                .toBe(Array.from(largeData.slice(0, 100)).join(','));
        });

        test('should produce different ciphertext each time', async () => {
            const enc1 = await sender.encryptFor(
                testData,
                recipient.kyberKeys.publicKey
            );
            const enc2 = await sender.encryptFor(
                testData,
                recipient.kyberKeys.publicKey
            );

            // Nonces should be different
            expect(enc1.nonce.join(',')).not.toBe(enc2.nonce.join(','));
        });
    });

    describe('signing/verification', () => {
        let pqc;
        const testData = new TextEncoder().encode('Data to sign');

        beforeAll(async () => {
            pqc = new ARC8PQC();
            await pqc.initialize();
        });

        test('should sign data with context', () => {
            const signed = pqc.sign(testData, { purpose: 'test' });

            expect(signed).toBeDefined();
            expect(signed.payload).toBeDefined();
            expect(signed.signature).toBeDefined();
            expect(signed.algorithm).toBe('ML-DSA-65');
        });

        test('should verify valid signature', () => {
            const signed = pqc.sign(testData, { purpose: 'test' });
            const result = pqc.verify(pqc.dilithiumKeys.publicKey, signed);

            expect(result.valid).toBe(true);
            expect(result.context.purpose).toBe('test');
        });

        test('should reject tampered data', () => {
            const signed = pqc.sign(testData, { purpose: 'test' });
            signed.payload.message[0] = 0xFF;

            const result = pqc.verify(pqc.dilithiumKeys.publicKey, signed);

            expect(result.valid).toBe(false);
        });

        test('should verify signature from another instance', async () => {
            const signer = new ARC8PQC();
            await signer.initialize();

            const signed = signer.sign(testData, { signer: 'external' });

            // Verify with verifier instance
            const result = pqc.verify(signer.dilithiumKeys.publicKey, signed);

            expect(result.valid).toBe(true);
            expect(result.context.signer).toBe('external');
        });
    });

    describe('secure messages', () => {
        let alice;
        let bob;
        const secretMessage = new TextEncoder().encode('Eyes only: quantum secured');

        beforeAll(async () => {
            alice = new ARC8PQC();
            bob = new ARC8PQC();
            await alice.initialize();
            await bob.initialize();
        });

        test('should create secure message', async () => {
            const message = await alice.createSecureMessage(
                secretMessage,
                bob.kyberKeys.publicKey
            );

            expect(message).toBeDefined();
            expect(message.type).toBe('ARC8-SECURE-MESSAGE-v1');
            expect(message.senderPublicKey).toBeDefined();
            expect(message.kyberCiphertext).toBeDefined();
            expect(message.encryptedData).toBeDefined();
        });

        test('should open secure message', async () => {
            const message = await alice.createSecureMessage(
                secretMessage,
                bob.kyberKeys.publicKey
            );

            const opened = await bob.openSecureMessage(message);

            expect(opened.data).toBeInstanceOf(Uint8Array);
            expect(new TextDecoder().decode(opened.data)).toBe('Eyes only: quantum secured');
            expect(opened.signatureValid).toBe(true);
            expect(opened.senderPublicKey).toBeDefined();
        });

        test('should detect tampered secure message', async () => {
            const message = await alice.createSecureMessage(
                secretMessage,
                bob.kyberKeys.publicKey
            );

            // Tamper with encrypted data
            message.encryptedData[0] ^= 0xFF;

            // Should fail to decrypt (AES-GCM authentication)
            await expect(bob.openSecureMessage(message)).rejects.toThrow();
        });

        test('should verify sender identity', async () => {
            const message = await alice.createSecureMessage(
                secretMessage,
                bob.kyberKeys.publicKey
            );

            const opened = await bob.openSecureMessage(message);

            // Sender public key should match Alice's
            const alicePubKey = Array.from(alice.dilithiumKeys.publicKey).join(',');
            const senderPubKey = opened.senderPublicKey.join(',');
            expect(senderPubKey).toBe(alicePubKey);
        });

        test('should handle bidirectional secure messaging', async () => {
            // Alice sends to Bob
            const messageAtoB = await alice.createSecureMessage(
                new TextEncoder().encode('Hello Bob'),
                bob.kyberKeys.publicKey
            );

            // Bob opens Alice's message
            const fromAlice = await bob.openSecureMessage(messageAtoB);
            expect(new TextDecoder().decode(fromAlice.data)).toBe('Hello Bob');

            // Bob replies to Alice
            const messageBtoA = await bob.createSecureMessage(
                new TextEncoder().encode('Hello Alice'),
                alice.kyberKeys.publicKey
            );

            // Alice opens Bob's reply
            const fromBob = await alice.openSecureMessage(messageBtoA);
            expect(new TextDecoder().decode(fromBob.data)).toBe('Hello Alice');
        });
    });

    describe('static methods', () => {
        test('should return capabilities', () => {
            const caps = ARC8PQC.getCapabilities();

            expect(caps.keyExchange.algorithm).toContain('ML-KEM-768');
            expect(caps.signatures.algorithm).toContain('ML-DSA-65');
            expect(caps.symmetric.algorithm).toBe('AES-256-GCM');
            expect(caps.hashing.algorithm).toBe('SHA-384');
            expect(caps.hybridMode).toBe(true);
            expect(caps.version).toBe('ARC8-PQC-v1');
        });

        test('should expose Kyber and Dilithium modules', () => {
            expect(ARC8Kyber).toBeDefined();
            expect(ARC8Dilithium).toBeDefined();
        });
    });

    describe('error handling', () => {
        test('should throw when not initialized', () => {
            const pqc = new ARC8PQC();
            const testData = new TextEncoder().encode('test');

            expect(() => pqc.sign(testData)).toThrow('PQC not initialized');
        });

        test('should throw when encrypting without init', async () => {
            const pqc = new ARC8PQC();
            const recipient = new ARC8PQC();
            await recipient.initialize();

            await expect(
                pqc.encryptFor(new Uint8Array(10), recipient.kyberKeys.publicKey)
            ).rejects.toThrow('PQC not initialized');
        });

        test('should throw when decrypting without init', async () => {
            const sender = new ARC8PQC();
            const recipient = new ARC8PQC();
            await sender.initialize();
            await recipient.initialize();

            const encrypted = await sender.encryptFor(
                new TextEncoder().encode('test'),
                recipient.kyberKeys.publicKey
            );

            // Create uninitialized instance
            const uninit = new ARC8PQC();
            await expect(uninit.decrypt(encrypted)).rejects.toThrow('PQC not initialized');
        });
    });

    describe('performance', () => {
        test('key generation should complete in reasonable time', async () => {
            const pqc = new ARC8PQC();
            const start = performance.now();
            await pqc.initialize();
            const elapsed = performance.now() - start;

            // Should complete within 5 seconds (generous for CI)
            expect(elapsed).toBeLessThan(5000);
            console.log(`Key generation time: ${elapsed.toFixed(2)}ms`);
        });

        test('encryption should complete in reasonable time', async () => {
            const sender = new ARC8PQC();
            const recipient = new ARC8PQC();
            await sender.initialize();
            await recipient.initialize();

            const data = new Uint8Array(10000);
            crypto.getRandomValues(data);

            const start = performance.now();
            await sender.encryptFor(data, recipient.kyberKeys.publicKey);
            const elapsed = performance.now() - start;

            // Should complete within 500ms
            expect(elapsed).toBeLessThan(500);
            console.log(`Encryption time (10KB): ${elapsed.toFixed(2)}ms`);
        });

        test('signing should complete in reasonable time', async () => {
            const pqc = new ARC8PQC();
            await pqc.initialize();

            const data = new Uint8Array(10000);
            crypto.getRandomValues(data);

            const start = performance.now();
            pqc.sign(data, {});
            const elapsed = performance.now() - start;

            // Should complete within 500ms
            expect(elapsed).toBeLessThan(500);
            console.log(`Signing time (10KB): ${elapsed.toFixed(2)}ms`);
        });
    });
});
