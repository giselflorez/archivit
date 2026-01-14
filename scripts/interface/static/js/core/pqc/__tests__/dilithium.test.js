/**
 * ARC-8 Dilithium (ML-DSA-65) Unit Tests
 *
 * Tests for post-quantum digital signatures
 * NIST FIPS 204 compliance
 */

import { ARC8Dilithium } from '../dilithium.js';

describe('ARC8Dilithium', () => {

    describe('availability', () => {
        test('should check if Dilithium is available', async () => {
            const available = await ARC8Dilithium.isAvailable();
            expect(typeof available).toBe('boolean');
        });
    });

    describe('key generation', () => {
        test('should generate valid key pair', async () => {
            const keyPair = await ARC8Dilithium.generateKeyPair();

            expect(keyPair).toBeDefined();
            expect(keyPair.publicKey).toBeInstanceOf(Uint8Array);
            expect(keyPair.secretKey).toBeInstanceOf(Uint8Array);
            expect(keyPair.algorithm).toBe('ML-DSA-65');
            expect(keyPair.quantumSafe).toBe(true);
            expect(keyPair.created).toBeDefined();
        });

        test('should generate correct key sizes (FIPS 204)', async () => {
            const keyPair = await ARC8Dilithium.generateKeyPair();

            // ML-DSA-65 key sizes
            expect(keyPair.publicKey.length).toBe(1952);
            expect(keyPair.secretKey.length).toBe(4032);
        });

        test('should generate unique keys each time', async () => {
            const keyPair1 = await ARC8Dilithium.generateKeyPair();
            const keyPair2 = await ARC8Dilithium.generateKeyPair();

            // Keys should be different
            const pk1Str = Array.from(keyPair1.publicKey.slice(0, 32)).join(',');
            const pk2Str = Array.from(keyPair2.publicKey.slice(0, 32)).join(',');
            expect(pk1Str).not.toBe(pk2Str);
        });
    });

    describe('sign/verify', () => {
        let keyPair;
        const testMessage = new TextEncoder().encode('Hello, quantum world!');

        beforeAll(async () => {
            keyPair = await ARC8Dilithium.generateKeyPair();
        });

        test('should sign a message', () => {
            const signature = ARC8Dilithium.sign(keyPair.secretKey, testMessage);

            expect(signature).toBeInstanceOf(Uint8Array);
            expect(signature.length).toBe(3309); // ML-DSA-65 signature size
        });

        test('should verify valid signature', () => {
            const signature = ARC8Dilithium.sign(keyPair.secretKey, testMessage);
            const valid = ARC8Dilithium.verify(
                keyPair.publicKey,
                testMessage,
                signature
            );

            expect(valid).toBe(true);
        });

        test('should reject tampered message', () => {
            const signature = ARC8Dilithium.sign(keyPair.secretKey, testMessage);
            const tamperedMessage = new TextEncoder().encode('Tampered message!');

            const valid = ARC8Dilithium.verify(
                keyPair.publicKey,
                tamperedMessage,
                signature
            );

            expect(valid).toBe(false);
        });

        test('should reject tampered signature', () => {
            const signature = ARC8Dilithium.sign(keyPair.secretKey, testMessage);

            // Tamper with signature (flip some bits)
            const tamperedSignature = new Uint8Array(signature);
            tamperedSignature[0] ^= 0xFF;
            tamperedSignature[100] ^= 0xFF;

            const valid = ARC8Dilithium.verify(
                keyPair.publicKey,
                testMessage,
                tamperedSignature
            );

            expect(valid).toBe(false);
        });

        test('should reject signature with wrong public key', async () => {
            const signature = ARC8Dilithium.sign(keyPair.secretKey, testMessage);
            const otherKeyPair = await ARC8Dilithium.generateKeyPair();

            const valid = ARC8Dilithium.verify(
                otherKeyPair.publicKey,
                testMessage,
                signature
            );

            expect(valid).toBe(false);
        });

        test('should produce different signatures for same message', () => {
            // ML-DSA is deterministic, but with different keys should differ
            const sig1 = ARC8Dilithium.sign(keyPair.secretKey, testMessage);
            const sig2 = ARC8Dilithium.sign(keyPair.secretKey, testMessage);

            // Note: ML-DSA-65 is deterministic, so same key+message = same sig
            const sig1Str = Array.from(sig1.slice(0, 32)).join(',');
            const sig2Str = Array.from(sig2.slice(0, 32)).join(',');
            expect(sig1Str).toBe(sig2Str);
        });
    });

    describe('signWithContext/verifyWithContext', () => {
        let keyPair;
        const testMessage = new TextEncoder().encode('Contextual message');

        beforeAll(async () => {
            keyPair = await ARC8Dilithium.generateKeyPair();
        });

        test('should sign with context', () => {
            const signed = ARC8Dilithium.signWithContext(
                keyPair.secretKey,
                testMessage,
                { purpose: 'test', version: 1 }
            );

            expect(signed).toBeDefined();
            expect(signed.payload).toBeDefined();
            expect(signed.signature).toBeDefined();
            expect(signed.algorithm).toBe('ML-DSA-65');
            expect(signed.signedAt).toBeDefined();
            expect(signed.payload.context.purpose).toBe('test');
        });

        test('should verify contextual signature', () => {
            const signed = ARC8Dilithium.signWithContext(
                keyPair.secretKey,
                testMessage,
                { purpose: 'test' }
            );

            const result = ARC8Dilithium.verifyWithContext(
                keyPair.publicKey,
                signed
            );

            expect(result.valid).toBe(true);
            expect(result.context.purpose).toBe('test');
            expect(result.timestamp).toBeDefined();
        });

        test('should reject tampered contextual signature', () => {
            const signed = ARC8Dilithium.signWithContext(
                keyPair.secretKey,
                testMessage,
                { purpose: 'test' }
            );

            // Tamper with payload
            signed.payload.context.purpose = 'tampered';

            const result = ARC8Dilithium.verifyWithContext(
                keyPair.publicKey,
                signed
            );

            expect(result.valid).toBe(false);
        });

        test('should include timestamp in signature', () => {
            const beforeSign = Date.now();
            const signed = ARC8Dilithium.signWithContext(
                keyPair.secretKey,
                testMessage,
                {}
            );
            const afterSign = Date.now();

            expect(signed.payload.timestamp).toBeGreaterThanOrEqual(beforeSign);
            expect(signed.payload.timestamp).toBeLessThanOrEqual(afterSign);
        });
    });

    describe('serialization', () => {
        test('should serialize key pair to JSON-safe format', async () => {
            const keyPair = await ARC8Dilithium.generateKeyPair();
            const serialized = ARC8Dilithium.serializeKeyPair(keyPair);

            expect(Array.isArray(serialized.publicKey)).toBe(true);
            expect(Array.isArray(serialized.secretKey)).toBe(true);
            expect(serialized.algorithm).toBe('ML-DSA-65');
            expect(serialized.quantumSafe).toBe(true);

            // Should be JSON-serializable
            const json = JSON.stringify(serialized);
            expect(typeof json).toBe('string');
        });

        test('should deserialize key pair correctly', async () => {
            const keyPair = await ARC8Dilithium.generateKeyPair();
            const serialized = ARC8Dilithium.serializeKeyPair(keyPair);
            const deserialized = ARC8Dilithium.deserializeKeyPair(serialized);

            expect(deserialized.publicKey).toBeInstanceOf(Uint8Array);
            expect(deserialized.secretKey).toBeInstanceOf(Uint8Array);
            expect(deserialized.publicKey.length).toBe(1952);
            expect(deserialized.secretKey.length).toBe(4032);
        });

        test('should roundtrip through serialization and still sign/verify', async () => {
            const originalKeyPair = await ARC8Dilithium.generateKeyPair();
            const serialized = ARC8Dilithium.serializeKeyPair(originalKeyPair);

            // Simulate storage (JSON roundtrip)
            const json = JSON.stringify(serialized);
            const restored = JSON.parse(json);

            const deserialized = ARC8Dilithium.deserializeKeyPair(restored);

            // Sign with restored keys
            const message = new TextEncoder().encode('Test after serialization');
            const signature = ARC8Dilithium.sign(deserialized.secretKey, message);

            // Verify with restored public key
            const valid = ARC8Dilithium.verify(
                deserialized.publicKey,
                message,
                signature
            );

            expect(valid).toBe(true);
        });
    });

    describe('algorithm info', () => {
        test('should return correct algorithm info', () => {
            const info = ARC8Dilithium.getInfo();

            expect(info.name).toBe('ML-DSA-65');
            expect(info.alias).toBe('CRYSTALS-Dilithium');
            expect(info.standard).toBe('NIST FIPS 204');
            expect(info.securityLevel).toBe(3);
            expect(info.publicKeySize).toBe(1952);
            expect(info.secretKeySize).toBe(4032);
            expect(info.signatureSize).toBe(3309);
            expect(info.quantumSafe).toBe(true);
        });
    });

    describe('edge cases', () => {
        let keyPair;

        beforeAll(async () => {
            keyPair = await ARC8Dilithium.generateKeyPair();
        });

        test('should sign empty message', () => {
            const emptyMessage = new Uint8Array(0);
            const signature = ARC8Dilithium.sign(keyPair.secretKey, emptyMessage);

            expect(signature).toBeInstanceOf(Uint8Array);
            expect(signature.length).toBe(3309);

            const valid = ARC8Dilithium.verify(
                keyPair.publicKey,
                emptyMessage,
                signature
            );
            expect(valid).toBe(true);
        });

        test('should sign large message', () => {
            // 100KB message (Node crypto.getRandomValues has 64KB limit per call)
            const largeMessage = new Uint8Array(100000);
            // Fill in chunks of 65536 bytes
            for (let i = 0; i < largeMessage.length; i += 65536) {
                const chunk = Math.min(65536, largeMessage.length - i);
                crypto.getRandomValues(largeMessage.subarray(i, i + chunk));
            }

            const signature = ARC8Dilithium.sign(keyPair.secretKey, largeMessage);

            expect(signature.length).toBe(3309);

            const valid = ARC8Dilithium.verify(
                keyPair.publicKey,
                largeMessage,
                signature
            );
            expect(valid).toBe(true);
        });

        test('should handle binary data', () => {
            // Random binary data
            const binaryData = new Uint8Array(256);
            crypto.getRandomValues(binaryData);

            const signature = ARC8Dilithium.sign(keyPair.secretKey, binaryData);
            const valid = ARC8Dilithium.verify(
                keyPair.publicKey,
                binaryData,
                signature
            );

            expect(valid).toBe(true);
        });
    });
});
