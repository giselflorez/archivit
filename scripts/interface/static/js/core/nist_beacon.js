/**
 * NIST QUANTUM RANDOM BEACON INTEGRATION
 * ======================================
 *
 * Provides quantum-derived randomness and unforgeable timestamps
 * from the NIST Randomness Beacon (https://beacon.nist.gov)
 *
 * The beacon produces 512 bits of quantum-derived randomness every 60 seconds.
 * By including the beacon value in provenance records, we create timestamps
 * that are:
 *
 * 1. UNFORGEABLE - Cannot be backdated (beacon values are unpredictable)
 * 2. VERIFIABLE - Anyone can check against NIST's public record
 * 3. INSTITUTIONAL - NIST is trusted by governments and academia
 * 4. QUANTUM-DERIVED - Based on quantum random number generation
 *
 * @module nist_beacon
 * @version 1.0.0
 */

/**
 * NIST Beacon API Configuration
 */
const BEACON_CONFIG = {
    // NIST Beacon 2.0 API endpoints
    BASE_URL: 'https://beacon.nist.gov/beacon/2.0',

    // Endpoints
    LAST_PULSE: '/pulse/last',
    PULSE_BY_TIME: '/pulse/time/', // + Unix timestamp in ms
    PULSE_BY_INDEX: '/chain/1/pulse/', // + pulse index

    // Cache settings
    CACHE_DURATION_MS: 60000, // 1 minute (beacon updates every 60 seconds)

    // Retry settings
    MAX_RETRIES: 3,
    RETRY_DELAY_MS: 1000,

    // Timeout
    TIMEOUT_MS: 10000
};

/**
 * Beacon pulse structure (from NIST API)
 * @typedef {Object} BeaconPulse
 * @property {string} uri - Unique URI for this pulse
 * @property {string} version - Beacon version
 * @property {number} cipherSuite - Cryptographic suite used
 * @property {number} period - Time between pulses (ms)
 * @property {string} certificateId - Certificate identifier
 * @property {number} chainIndex - Chain index
 * @property {number} pulseIndex - Pulse index within chain
 * @property {string} timeStamp - ISO 8601 timestamp
 * @property {string} localRandomValue - Local random contribution
 * @property {Object} external - External entropy sources
 * @property {Array} listValues - List of random values
 * @property {string} precommitmentValue - Next pulse commitment
 * @property {number} statusCode - Status code
 * @property {string} signatureValue - Signature over pulse
 * @property {string} outputValue - Final 512-bit random output (hex)
 */

/**
 * NIST Beacon Client
 * Fetches and caches quantum random beacon pulses
 */
class NISTBeaconClient {

    constructor() {
        this.cache = {
            lastPulse: null,
            fetchedAt: 0
        };
        this.available = null; // Unknown until first fetch
    }

    /**
     * Check if beacon is reachable
     * @returns {Promise<boolean>}
     */
    async checkAvailability() {
        try {
            const response = await this._fetchWithTimeout(
                `${BEACON_CONFIG.BASE_URL}${BEACON_CONFIG.LAST_PULSE}`,
                { method: 'HEAD' }
            );
            this.available = response.ok;
            return this.available;
        } catch (error) {
            console.warn('[NIST-Beacon] Beacon not reachable:', error.message);
            this.available = false;
            return false;
        }
    }

    /**
     * Get the latest beacon pulse
     * @param {boolean} forceRefresh - Bypass cache
     * @returns {Promise<BeaconPulse|null>}
     */
    async getLatestPulse(forceRefresh = false) {
        // Check cache
        const now = Date.now();
        if (!forceRefresh &&
            this.cache.lastPulse &&
            (now - this.cache.fetchedAt) < BEACON_CONFIG.CACHE_DURATION_MS) {
            console.log('[NIST-Beacon] Returning cached pulse');
            return this.cache.lastPulse;
        }

        // Fetch new pulse
        try {
            const response = await this._fetchWithRetry(
                `${BEACON_CONFIG.BASE_URL}${BEACON_CONFIG.LAST_PULSE}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            const pulse = data.pulse;

            // Update cache
            this.cache.lastPulse = pulse;
            this.cache.fetchedAt = now;
            this.available = true;

            console.log('[NIST-Beacon] Fetched pulse:', {
                pulseIndex: pulse.pulseIndex,
                timestamp: pulse.timeStamp,
                outputValuePreview: pulse.outputValue.substring(0, 16) + '...'
            });

            return pulse;

        } catch (error) {
            console.error('[NIST-Beacon] Failed to fetch pulse:', error.message);
            this.available = false;

            // Return stale cache if available
            if (this.cache.lastPulse) {
                console.warn('[NIST-Beacon] Returning stale cached pulse');
                return this.cache.lastPulse;
            }

            return null;
        }
    }

    /**
     * Get pulse by specific timestamp
     * @param {number} timestamp - Unix timestamp in milliseconds
     * @returns {Promise<BeaconPulse|null>}
     */
    async getPulseByTime(timestamp) {
        try {
            const response = await this._fetchWithRetry(
                `${BEACON_CONFIG.BASE_URL}${BEACON_CONFIG.PULSE_BY_TIME}${timestamp}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data.pulse;

        } catch (error) {
            console.error('[NIST-Beacon] Failed to fetch pulse by time:', error.message);
            return null;
        }
    }

    /**
     * Verify a beacon pulse is authentic
     * @param {BeaconPulse} pulse - Pulse to verify
     * @returns {Promise<Object>} Verification result
     */
    async verifyPulse(pulse) {
        if (!pulse || !pulse.pulseIndex) {
            return { valid: false, error: 'Invalid pulse object' };
        }

        try {
            // Fetch the same pulse from NIST to compare
            const response = await this._fetchWithRetry(
                `${BEACON_CONFIG.BASE_URL}${BEACON_CONFIG.PULSE_BY_INDEX}${pulse.pulseIndex}`
            );

            if (!response.ok) {
                return { valid: false, error: `Could not fetch reference pulse: HTTP ${response.status}` };
            }

            const data = await response.json();
            const referencePulse = data.pulse;

            // Compare critical fields
            const valid = (
                pulse.outputValue === referencePulse.outputValue &&
                pulse.timeStamp === referencePulse.timeStamp &&
                pulse.signatureValue === referencePulse.signatureValue
            );

            return {
                valid,
                pulseIndex: pulse.pulseIndex,
                timestamp: pulse.timeStamp,
                verifiedAt: new Date().toISOString(),
                verificationSource: 'NIST Beacon 2.0 API'
            };

        } catch (error) {
            return { valid: false, error: error.message };
        }
    }

    /**
     * Create a timestamp anchor using the beacon
     * @param {string|Uint8Array} data - Data to anchor
     * @returns {Promise<Object>} Timestamp anchor
     */
    async createTimestampAnchor(data) {
        const pulse = await this.getLatestPulse();

        if (!pulse) {
            console.warn('[NIST-Beacon] No beacon available, using local timestamp only');
            return {
                anchored: false,
                localTimestamp: Date.now(),
                localISO: new Date().toISOString(),
                reason: 'NIST Beacon unavailable'
            };
        }

        // Hash the data
        const dataBytes = typeof data === 'string'
            ? new TextEncoder().encode(data)
            : data;
        const hashBuffer = await crypto.subtle.digest('SHA-384', dataBytes);
        const dataHash = Array.from(new Uint8Array(hashBuffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');

        // Create anchor combining data hash with beacon
        const anchorData = `${dataHash}:${pulse.outputValue}`;
        const anchorHashBuffer = await crypto.subtle.digest('SHA-384',
            new TextEncoder().encode(anchorData));
        const anchorHash = Array.from(new Uint8Array(anchorHashBuffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');

        return {
            anchored: true,
            anchor: {
                dataHash,
                anchorHash,
                beaconPulse: {
                    pulseIndex: pulse.pulseIndex,
                    outputValue: pulse.outputValue,
                    timeStamp: pulse.timeStamp,
                    uri: pulse.uri
                }
            },
            localTimestamp: Date.now(),
            localISO: new Date().toISOString(),
            verificationUrl: `https://beacon.nist.gov/beacon/2.0/chain/1/pulse/${pulse.pulseIndex}`
        };
    }

    /**
     * Get beacon status
     * @returns {Object}
     */
    getStatus() {
        return {
            available: this.available,
            cached: !!this.cache.lastPulse,
            cacheAge: this.cache.lastPulse
                ? Date.now() - this.cache.fetchedAt
                : null,
            lastPulseIndex: this.cache.lastPulse?.pulseIndex || null,
            lastPulseTime: this.cache.lastPulse?.timeStamp || null
        };
    }

    // ─────────────────────────────────────────────────────────────────────────
    // PRIVATE METHODS
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Fetch with timeout
     * @private
     */
    async _fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeout = setTimeout(
            () => controller.abort(),
            BEACON_CONFIG.TIMEOUT_MS
        );

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            return response;
        } finally {
            clearTimeout(timeout);
        }
    }

    /**
     * Fetch with retry
     * @private
     */
    async _fetchWithRetry(url, options = {}) {
        let lastError;

        for (let attempt = 1; attempt <= BEACON_CONFIG.MAX_RETRIES; attempt++) {
            try {
                return await this._fetchWithTimeout(url, options);
            } catch (error) {
                lastError = error;
                console.warn(`[NIST-Beacon] Attempt ${attempt} failed:`, error.message);

                if (attempt < BEACON_CONFIG.MAX_RETRIES) {
                    await new Promise(resolve =>
                        setTimeout(resolve, BEACON_CONFIG.RETRY_DELAY_MS * attempt)
                    );
                }
            }
        }

        throw lastError;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCE
// ═══════════════════════════════════════════════════════════════════════════

const nistBeacon = new NISTBeaconClient();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export { NISTBeaconClient, nistBeacon, BEACON_CONFIG };
export default nistBeacon;
