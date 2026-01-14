/**
 * ARC-8 Kyber (ML-KEM-768) Unit Tests
 *
 * Tests for post-quantum key encapsulation mechanism
 * NIST FIPS 203 compliance
 */

import { ARC8Kyber } from '../kyber.js';

describe('ARC8Kyber', () => {

    describe('availability', () => {
        test('should check if Kyber is available', async () => {
            const available = await ARC8Kyber.isAvailable();
            expect(typeof available).toBe('boolean');
        });
    });

    describe('key generation', () => {
        test('should generate valid key pair', async () => {
            const keyPair = await ARC8Kyber.generateKeyPair();

            expect(keyPair).toBeDefined();
            expect(keyPair.publicKey).toBeInstanceOf(Uint8Array);
            expect(keyPair.secretKey).toBeInstanceOf(Uint8Array);
            expect(keyPair.algorithm).toBe('ML-KEM-768');
            expect(keyPair.quantumSafe).toBe(true);
            expect(keyPair.created).toBeDefined();
        });

        test('should generate correct key sizes (FIPS 203)', async () => {
            const keyPair = await ARC8Kyber.generateKeyPair();

            // ML-KEM-768 key sizes
            expect(keyPair.publicKey.length).toBe(1184);
            expect(keyPair.secretKey.length).toBe(2400);
        });

        test('should generate unique keys each time', async () => {
            const keyPair1 = await ARC8Kyber.generateKeyPair();
            const keyPair2 = await ARC8Kyber.generateKeyPair();

            // Keys should be different (extremely unlikely to match)
            const pk1Str = Array.from(keyPair1.publicKey.slice(0, 32)).join(',');
            const pk2Str = Array.from(keyPair2.publicKey.slice(0, 32)).join(',');
            expect(pk1Str).not.toBe(pk2Str);
        });
    });

    describe('encapsulation/decapsulation', () => {
        let keyPair;

        beforeAll(async () => {
            keyPair = await ARC8Kyber.generateKeyPair();
        });

        test('should encapsulate shared secret', () => {
            const result = ARC8Kyber.encapsulate(keyPair.publicKey);

            expect(result).toBeDefined();
            expect(result.ciphertext).toBeInstanceOf(Uint8Array);
            expect(result.sharedSecret).toBeInstanceOf(Uint8Array);
        });

        test('should generate correct encapsulation sizes', () => {
            const result = ARC8Kyber.encapsulate(keyPair.publicKey);

            // ML-KEM-768 sizes
            expect(result.ciphertext.length).toBe(1088);
            expect(result.sharedSecret.length).toBe(32);
        });

        test('should decapsulate to same shared secret', () => {
            const { ciphertext, sharedSecret: encapSecret } =
                ARC8Kyber.encapsulate(keyPair.publicKey);

            const decapSecret = ARC8Kyber.decapsulate(
                keyPair.secretKey,
                ciphertext
            );

            expect(decapSecret).toBeInstanceOf(Uint8Array);
            expect(decapSecret.length).toBe(32);

            // Shared secrets must match
            const encapStr = Array.from(encapSecret).join(',');
            const decapStr = Array.from(decapSecret).join(',');
            expect(encapStr).toBe(decapStr);
        });

        test('should produce different ciphertexts for same public key', () => {
            const result1 = ARC8Kyber.encapsulate(keyPair.publicKey);
            const result2 = ARC8Kyber.encapsulate(keyPair.publicKey);

            // Ciphertexts should be different (randomized)
            const ct1 = Array.from(result1.ciphertext.slice(0, 32)).join(',');
            const ct2 = Array.from(result2.ciphertext.slice(0, 32)).join(',');
            expect(ct1).not.toBe(ct2);
        });

        test('should fail decapsulation with wrong secret key', async () => {
            const { ciphertext } = ARC8Kyber.encapsulate(keyPair.publicKey);
            const otherKeyPair = await ARC8Kyber.generateKeyPair();

            // Decapsulating with wrong key produces different (invalid) secret
            const wrongSecret = ARC8Kyber.decapsulate(
                otherKeyPair.secretKey,
                ciphertext
            );
            const rightSecret = ARC8Kyber.decapsulate(
                keyPair.secretKey,
                ciphertext
            );

            const wrongStr = Array.from(wrongSecret).join(',');
            const rightStr = Array.from(rightSecret).join(',');
            expect(wrongStr).not.toBe(rightStr);
        });
    });

    describe('serialization', () => {
        test('should serialize key pair to JSON-safe format', async () => {
            const keyPair = await ARC8Kyber.generateKeyPair();
            const serialized = ARC8Kyber.serializeKeyPair(keyPair);

            expect(Array.isArray(serialized.publicKey)).toBe(true);
            expect(Array.isArray(serialized.secretKey)).toBe(true);
            expect(serialized.algorithm).toBe('ML-KEM-768');
            expect(serialized.quantumSafe).toBe(true);

            // Should be JSON-serializable
            const json = JSON.stringify(serialized);
            expect(typeof json).toBe('string');
        });

        test('should deserialize key pair correctly', async () => {
            const keyPair = await ARC8Kyber.generateKeyPair();
            const serialized = ARC8Kyber.serializeKeyPair(keyPair);
            const deserialized = ARC8Kyber.deserializeKeyPair(serialized);

            expect(deserialized.publicKey).toBeInstanceOf(Uint8Array);
            expect(deserialized.secretKey).toBeInstanceOf(Uint8Array);
            expect(deserialized.publicKey.length).toBe(1184);
            expect(deserialized.secretKey.length).toBe(2400);
        });

        test('should roundtrip through serialization', async () => {
            const originalKeyPair = await ARC8Kyber.generateKeyPair();
            const serialized = ARC8Kyber.serializeKeyPair(originalKeyPair);

            // Simulate storage (JSON roundtrip)
            const json = JSON.stringify(serialized);
            const restored = JSON.parse(json);

            const deserialized = ARC8Kyber.deserializeKeyPair(restored);

            // Encapsulate with original public key
            const { ciphertext, sharedSecret: encapSecret } =
                ARC8Kyber.encapsulate(originalKeyPair.publicKey);

            // Decapsulate with restored secret key
            const decapSecret = ARC8Kyber.decapsulate(
                deserialized.secretKey,
                ciphertext
            );

            // Secrets should match
            const encapStr = Array.from(encapSecret).join(',');
            const decapStr = Array.from(decapSecret).join(',');
            expect(encapStr).toBe(decapStr);
        });
    });

    describe('algorithm info', () => {
        test('should return correct algorithm info', () => {
            const info = ARC8Kyber.getInfo();

            expect(info.name).toBe('ML-KEM-768');
            expect(info.alias).toBe('CRYSTALS-Kyber');
            expect(info.standard).toBe('NIST FIPS 203');
            expect(info.securityLevel).toBe(3);
            expect(info.publicKeySize).toBe(1184);
            expect(info.secretKeySize).toBe(2400);
            expect(info.ciphertextSize).toBe(1088);
            expect(info.sharedSecretSize).toBe(32);
            expect(info.quantumSafe).toBe(true);
        });
    });
});
