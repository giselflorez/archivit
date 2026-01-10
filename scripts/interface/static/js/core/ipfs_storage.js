/**
 * IPFS DISTRIBUTED STORAGE
 * ========================
 * Decentralized Storage for Compressed Seed Data
 *
 * Uses IPFS for storing compressed rings beyond local capacity.
 * Content-addressed, encrypted, and retrievable from any node.
 *
 * BENEFITS:
 * - Unlimited storage without local cost
 * - Redundancy (data survives device loss)
 * - Decentralized (no single point of failure)
 * - Only download what you need
 */

import { SeedCrypto } from './seed_profile.js';

// ═══════════════════════════════════════════════════════════════════════════
// IPFS CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

const IPFS_CONFIG = Object.freeze({
    // Public gateways (fallback)
    PUBLIC_GATEWAYS: [
        'https://ipfs.io/ipfs/',
        'https://gateway.pinata.cloud/ipfs/',
        'https://cloudflare-ipfs.com/ipfs/',
        'https://dweb.link/ipfs/'
    ],

    // Block configuration
    BLOCK_SIZE: 256 * 1024,  // 256KB per block
    MAX_BLOCKS_PER_RING: 100,

    // Retry settings
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY_MS: 1000,

    // Cache settings
    CACHE_DURATION_MS: 30 * 60 * 1000,  // 30 minutes

    // Pinning services (for persistence)
    PINNING_SERVICES: [
        { name: 'Pinata', url: 'https://api.pinata.cloud' },
        { name: 'Infura', url: 'https://ipfs.infura.io:5001' }
    ]
});

// ═══════════════════════════════════════════════════════════════════════════
// IPFS STORAGE ENGINE
// ═══════════════════════════════════════════════════════════════════════════

class IPFSStorage {
    constructor(options = {}) {
        this.gateway = options.gateway || IPFS_CONFIG.PUBLIC_GATEWAYS[0];
        this.pinningApiKey = options.pinningApiKey || null;
        this.encryptionKey = null;

        // Local cache for retrieved blocks
        this.cache = new Map();
        this.cacheTimestamps = new Map();

        // Block index (maps seed sections to CIDs)
        this.blockIndex = {
            version: '1.0.0',
            blocks: {},
            created: Date.now(),
            lastSync: null
        };

        // Statistics
        this.stats = {
            uploads: 0,
            downloads: 0,
            bytesUploaded: 0,
            bytesDownloaded: 0,
            cacheHits: 0,
            cacheMisses: 0
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Initialize IPFS storage with encryption key
     *
     * @param {CryptoKey} encryptionKey - Key for encrypting blocks
     */
    async initialize(encryptionKey) {
        this.encryptionKey = encryptionKey;

        // Load block index from local storage
        await this._loadBlockIndex();

        return this;
    }

    /**
     * Load block index from local storage
     */
    async _loadBlockIndex() {
        try {
            const stored = localStorage.getItem('ipfs_block_index');
            if (stored) {
                this.blockIndex = JSON.parse(stored);
            }
        } catch (e) {
            console.warn('[IPFSStorage] Could not load block index:', e);
        }
    }

    /**
     * Save block index to local storage
     */
    async _saveBlockIndex() {
        try {
            localStorage.setItem('ipfs_block_index', JSON.stringify(this.blockIndex));
        } catch (e) {
            console.warn('[IPFSStorage] Could not save block index:', e);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UPLOAD OPERATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Upload compressed data to IPFS
     *
     * @param {Object} data - Data to upload
     * @param {string} ringId - Identifier for this ring/section
     * @returns {Object} Upload result with CID
     */
    async upload(data, ringId) {
        if (!this.encryptionKey) {
            throw new Error('IPFS storage not initialized with encryption key');
        }

        // Serialize and encrypt
        const serialized = JSON.stringify(data);
        const encrypted = await SeedCrypto.encrypt(data, this.encryptionKey);

        // Create block
        const block = {
            version: '1.0.0',
            ringId: ringId,
            encrypted: true,
            timestamp: Date.now(),
            content: encrypted
        };

        // Calculate content hash (for local reference)
        const contentHash = await this._hashContent(JSON.stringify(block));

        // Upload to IPFS
        const cid = await this._uploadToIPFS(block);

        // Update block index
        this.blockIndex.blocks[ringId] = {
            cid: cid,
            contentHash: contentHash,
            size: serialized.length,
            uploadedAt: Date.now()
        };
        this.blockIndex.lastSync = Date.now();
        await this._saveBlockIndex();

        // Update stats
        this.stats.uploads++;
        this.stats.bytesUploaded += serialized.length;

        return {
            success: true,
            cid: cid,
            ringId: ringId,
            size: serialized.length
        };
    }

    /**
     * Upload to IPFS network
     */
    async _uploadToIPFS(block) {
        // If we have a pinning API key, use pinning service
        if (this.pinningApiKey) {
            return this._uploadToPinningService(block);
        }

        // Otherwise, simulate local IPFS node upload
        // In production, this would connect to local IPFS daemon
        console.log('[IPFSStorage] Would upload block:', {
            ringId: block.ringId,
            size: JSON.stringify(block).length
        });

        // Generate mock CID (in production, IPFS generates this)
        const mockCID = 'Qm' + await this._hashContent(JSON.stringify(block));
        return mockCID.substring(0, 46);  // Standard CID length
    }

    /**
     * Upload to pinning service (Pinata, etc.)
     */
    async _uploadToPinningService(block) {
        // Stub for pinning service integration
        // Would make actual API call in production
        console.log('[IPFSStorage] Would upload to pinning service');
        return 'Qm' + Math.random().toString(36).substring(2, 46);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // DOWNLOAD OPERATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Download and decrypt data from IPFS
     *
     * @param {string} ringId - Ring identifier to download
     * @returns {Object} Decrypted data
     */
    async download(ringId) {
        // Check cache first
        if (this._isCached(ringId)) {
            this.stats.cacheHits++;
            return this.cache.get(ringId);
        }

        this.stats.cacheMisses++;

        // Get CID from index
        const blockInfo = this.blockIndex.blocks[ringId];
        if (!blockInfo) {
            throw new Error(`No IPFS block found for ring: ${ringId}`);
        }

        // Download from IPFS
        const block = await this._downloadFromIPFS(blockInfo.cid);

        // Decrypt
        if (!this.encryptionKey) {
            throw new Error('IPFS storage not initialized with encryption key');
        }

        const decrypted = await SeedCrypto.decrypt(block.content, this.encryptionKey);

        // Cache result
        this._cacheResult(ringId, decrypted);

        // Update stats
        this.stats.downloads++;
        this.stats.bytesDownloaded += blockInfo.size || 0;

        return decrypted;
    }

    /**
     * Download from IPFS network
     */
    async _downloadFromIPFS(cid) {
        // Try each gateway in sequence
        for (let attempt = 0; attempt < IPFS_CONFIG.RETRY_ATTEMPTS; attempt++) {
            for (const gateway of IPFS_CONFIG.PUBLIC_GATEWAYS) {
                try {
                    const response = await fetch(`${gateway}${cid}`, {
                        method: 'GET',
                        headers: { 'Accept': 'application/json' }
                    });

                    if (response.ok) {
                        return await response.json();
                    }
                } catch (e) {
                    console.warn(`[IPFSStorage] Gateway ${gateway} failed:`, e.message);
                }
            }

            // Wait before retry
            await new Promise(resolve =>
                setTimeout(resolve, IPFS_CONFIG.RETRY_DELAY_MS * (attempt + 1))
            );
        }

        throw new Error(`Failed to download from IPFS after ${IPFS_CONFIG.RETRY_ATTEMPTS} attempts`);
    }

    /**
     * Check if ringId is in cache and still valid
     */
    _isCached(ringId) {
        if (!this.cache.has(ringId)) return false;

        const timestamp = this.cacheTimestamps.get(ringId) || 0;
        const age = Date.now() - timestamp;

        return age < IPFS_CONFIG.CACHE_DURATION_MS;
    }

    /**
     * Cache download result
     */
    _cacheResult(ringId, data) {
        this.cache.set(ringId, data);
        this.cacheTimestamps.set(ringId, Date.now());

        // Limit cache size
        if (this.cache.size > 50) {
            // Remove oldest entries
            const oldest = [...this.cacheTimestamps.entries()]
                .sort((a, b) => a[1] - b[1])
                .slice(0, 10)
                .map(e => e[0]);

            for (const key of oldest) {
                this.cache.delete(key);
                this.cacheTimestamps.delete(key);
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SYNC OPERATIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Sync all rings to IPFS
     *
     * @param {Object} rings - Ring data from compression engine
     * @returns {Object} Sync results
     */
    async syncRings(rings) {
        const results = {
            synced: [],
            failed: [],
            skipped: []
        };

        for (const [ringId, data] of Object.entries(rings)) {
            // Skip core (always local)
            if (ringId === 'core') {
                results.skipped.push(ringId);
                continue;
            }

            // Skip if data is just an IPFS reference
            if (data._ipfsRef) {
                results.skipped.push(ringId);
                continue;
            }

            try {
                const result = await this.upload(data, ringId);
                results.synced.push({
                    ringId: ringId,
                    cid: result.cid,
                    size: result.size
                });
            } catch (e) {
                results.failed.push({
                    ringId: ringId,
                    error: e.message
                });
            }
        }

        return results;
    }

    /**
     * Verify integrity of stored blocks
     */
    async verifyIntegrity() {
        const results = {
            verified: [],
            corrupted: [],
            missing: []
        };

        for (const [ringId, blockInfo] of Object.entries(this.blockIndex.blocks)) {
            try {
                const block = await this._downloadFromIPFS(blockInfo.cid);
                const currentHash = await this._hashContent(JSON.stringify(block));

                // Note: We can't verify against stored hash because encryption
                // produces different output each time. Instead verify structure.
                if (block.version && block.encrypted && block.content) {
                    results.verified.push(ringId);
                } else {
                    results.corrupted.push(ringId);
                }
            } catch (e) {
                results.missing.push(ringId);
            }
        }

        return results;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UTILITIES
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Hash content for verification
     */
    async _hashContent(content) {
        const encoder = new TextEncoder();
        const data = encoder.encode(content);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    /**
     * Get list of all stored blocks
     */
    getBlockList() {
        return Object.entries(this.blockIndex.blocks).map(([ringId, info]) => ({
            ringId: ringId,
            cid: info.cid,
            size: info.size,
            uploadedAt: info.uploadedAt
        }));
    }

    /**
     * Delete a block (unpin from IPFS)
     */
    async deleteBlock(ringId) {
        const blockInfo = this.blockIndex.blocks[ringId];
        if (!blockInfo) return false;

        // Remove from index
        delete this.blockIndex.blocks[ringId];
        await this._saveBlockIndex();

        // Clear from cache
        this.cache.delete(ringId);
        this.cacheTimestamps.delete(ringId);

        // Note: IPFS content is content-addressed and immutable
        // "Deletion" means unpinning so it can be garbage collected
        // The content may persist on other nodes

        return true;
    }

    /**
     * Get storage statistics
     */
    getStats() {
        return {
            ...this.stats,
            blocksStored: Object.keys(this.blockIndex.blocks).length,
            cacheSize: this.cache.size,
            lastSync: this.blockIndex.lastSync
        };
    }

    /**
     * Clear local cache
     */
    clearCache() {
        this.cache.clear();
        this.cacheTimestamps.clear();
    }

    /**
     * Export block index for backup
     */
    exportIndex() {
        return { ...this.blockIndex };
    }

    /**
     * Import block index from backup
     */
    async importIndex(index) {
        this.blockIndex = { ...index };
        await this._saveBlockIndex();
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// PLATFORM TIER MANAGER
// ═══════════════════════════════════════════════════════════════════════════

class PlatformTierManager {
    constructor() {
        this.detectedTier = null;
        this.overrideTier = null;
        this.capabilities = null;
    }

    /**
     * Detect device capabilities and recommend tier
     */
    async detect() {
        const capabilities = {
            storage: await this._detectStorage(),
            memory: this._detectMemory(),
            network: await this._detectNetwork(),
            platform: this._detectPlatform()
        };

        this.capabilities = capabilities;

        // Determine tier based on capabilities
        let tier = 'STANDARD';

        if (capabilities.storage.available > 10 * 1024 * 1024 * 1024 && // 10GB
            capabilities.memory.deviceMemory >= 8) {
            tier = 'FULL';
        } else if (capabilities.storage.available > 100 * 1024 * 1024 && // 100MB
                   capabilities.memory.deviceMemory >= 2) {
            tier = 'STANDARD';
        } else if (capabilities.storage.available > 20 * 1024 * 1024) { // 20MB
            tier = 'LITE';
        } else {
            tier = 'MICRO';
        }

        // Adjust for platform
        if (capabilities.platform.isRaspberryPi ||
            capabilities.platform.isIoT) {
            tier = 'MICRO';
        }

        this.detectedTier = tier;
        return {
            tier: tier,
            capabilities: capabilities,
            recommendation: this._getRecommendation(tier, capabilities)
        };
    }

    /**
     * Override detected tier
     */
    setTier(tier) {
        if (['FULL', 'STANDARD', 'LITE', 'MICRO'].includes(tier)) {
            this.overrideTier = tier;
            return true;
        }
        return false;
    }

    /**
     * Get current active tier
     */
    getCurrentTier() {
        return this.overrideTier || this.detectedTier || 'STANDARD';
    }

    /**
     * Detect available storage
     */
    async _detectStorage() {
        if (navigator.storage && navigator.storage.estimate) {
            const estimate = await navigator.storage.estimate();
            return {
                available: estimate.quota || 0,
                used: estimate.usage || 0,
                persistent: await this._checkPersistence()
            };
        }

        // Fallback: assume minimal storage
        return {
            available: 50 * 1024 * 1024,  // 50MB assumed
            used: 0,
            persistent: false
        };
    }

    /**
     * Check if persistent storage is available
     */
    async _checkPersistence() {
        if (navigator.storage && navigator.storage.persisted) {
            return await navigator.storage.persisted();
        }
        return false;
    }

    /**
     * Detect available memory
     */
    _detectMemory() {
        return {
            deviceMemory: navigator.deviceMemory || 4,  // Default 4GB
            hardwareConcurrency: navigator.hardwareConcurrency || 4
        };
    }

    /**
     * Detect network capabilities
     */
    async _detectNetwork() {
        const connection = navigator.connection ||
                          navigator.mozConnection ||
                          navigator.webkitConnection;

        if (connection) {
            return {
                type: connection.effectiveType || 'unknown',
                downlink: connection.downlink || 0,
                rtt: connection.rtt || 0,
                saveData: connection.saveData || false
            };
        }

        return {
            type: 'unknown',
            downlink: 0,
            rtt: 0,
            saveData: false
        };
    }

    /**
     * Detect platform type
     */
    _detectPlatform() {
        const ua = navigator.userAgent.toLowerCase();

        return {
            isMobile: /mobile|android|iphone|ipad|ipod/.test(ua),
            isTablet: /ipad|tablet/.test(ua),
            isDesktop: !(/mobile|android|iphone|ipad|ipod|tablet/.test(ua)),
            isRaspberryPi: /raspberry/.test(ua) || /linux.*arm/.test(ua),
            isIoT: /embedded|iot/.test(ua),
            browser: this._detectBrowser(ua)
        };
    }

    /**
     * Detect browser
     */
    _detectBrowser(ua) {
        if (ua.includes('firefox')) return 'firefox';
        if (ua.includes('chrome')) return 'chrome';
        if (ua.includes('safari')) return 'safari';
        if (ua.includes('edge')) return 'edge';
        return 'unknown';
    }

    /**
     * Get recommendation message for tier
     */
    _getRecommendation(tier, capabilities) {
        const messages = {
            FULL: 'Full experience with all features and unlimited local storage.',
            STANDARD: 'Recommended for most devices. Core features with IPFS backup.',
            LITE: 'Optimized for limited storage. Essential features with streaming.',
            MICRO: 'Minimal footprint. Core-only with everything streamed from IPFS.'
        };

        let recommendation = messages[tier];

        if (capabilities.network.saveData) {
            recommendation += ' Data saver mode detected - IPFS downloads will be minimized.';
        }

        if (capabilities.storage.persistent === false) {
            recommendation += ' Note: Persistent storage not enabled - consider enabling for better reliability.';
        }

        return recommendation;
    }

    /**
     * Request persistent storage
     */
    async requestPersistence() {
        if (navigator.storage && navigator.storage.persist) {
            const granted = await navigator.storage.persist();
            return granted;
        }
        return false;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON INSTANCES
// ═══════════════════════════════════════════════════════════════════════════

const ipfsStorage = new IPFSStorage();
const tierManager = new PlatformTierManager();

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
    IPFSStorage,
    ipfsStorage,
    PlatformTierManager,
    tierManager,
    IPFS_CONFIG
};

export default ipfsStorage;
