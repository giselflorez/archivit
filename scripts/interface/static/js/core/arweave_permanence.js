/**
 * ARWEAVE PERMANENCE SERVICE
 * Permanent storage via Arweave/Irys for provenance anchoring
 *
 * Uses Irys (formerly Bundlr) for cheaper, faster uploads
 * Falls back to direct Arweave if needed
 */

export class ArweavePermanenceService {
    constructor(config = {}) {
        this.config = {
            irysNode: config.irysNode || 'https://node2.irys.xyz',
            arweaveGateway: config.arweaveGateway || 'https://arweave.net',
            currency: config.currency || 'arweave',
            ...config
        };

        this.irys = null;
        this.initialized = false;
    }

    /**
     * Initialize with wallet/private key
     * @param {string|Uint8Array} key - Arweave private key or JWK
     */
    async initialize(key) {
        if (typeof window !== 'undefined') {
            // Browser: Use dynamic import
            const { WebIrys } = await import('@irys/sdk');
            this.irys = new WebIrys({
                url: this.config.irysNode,
                token: this.config.currency,
                wallet: { provider: window.arweaveWallet }
            });
        } else {
            // Node.js
            const Irys = (await import('@irys/sdk')).default;
            this.irys = new Irys({
                url: this.config.irysNode,
                token: this.config.currency,
                key: key
            });
        }

        await this.irys.ready();
        this.initialized = true;

        return {
            address: this.irys.address,
            balance: await this.getBalance()
        };
    }

    /**
     * Get current balance in AR
     */
    async getBalance() {
        if (!this.initialized) throw new Error('Not initialized');

        const balance = await this.irys.getLoadedBalance();
        return {
            atomic: balance.toString(),
            ar: this.irys.utils.fromAtomic(balance).toString()
        };
    }

    /**
     * Get price for upload in AR
     * @param {number} bytes - Size in bytes
     */
    async getPrice(bytes) {
        if (!this.initialized) throw new Error('Not initialized');

        const price = await this.irys.getPrice(bytes);
        return {
            atomic: price.toString(),
            ar: this.irys.utils.fromAtomic(price).toString(),
            usd: null // Would need price oracle
        };
    }

    /**
     * Fund Irys node (deposit AR for uploads)
     * @param {string} amount - Amount in AR
     */
    async fund(amount) {
        if (!this.initialized) throw new Error('Not initialized');

        const fundTx = await this.irys.fund(
            this.irys.utils.toAtomic(amount)
        );

        return {
            txId: fundTx.id,
            amount: amount
        };
    }

    /**
     * Upload data to Arweave via Irys
     * @param {string|Buffer|Uint8Array} data - Data to upload
     * @param {Array} tags - Arweave tags [{name, value}]
     * @returns {Object} - Upload result with transaction ID
     */
    async upload(data, tags = []) {
        if (!this.initialized) throw new Error('Not initialized');

        // Add ARC8 default tags
        const allTags = [
            { name: 'App-Name', value: 'ARC8' },
            { name: 'App-Version', value: '1.0.0' },
            { name: 'Unix-Time', value: Date.now().toString() },
            ...tags
        ];

        const receipt = await this.irys.upload(data, { tags: allTags });

        return {
            id: receipt.id,
            gateway: `${this.config.arweaveGateway}/${receipt.id}`,
            timestamp: receipt.timestamp,
            size: data.length || data.byteLength
        };
    }

    /**
     * Upload JSON data
     * @param {Object} data - JSON object
     * @param {Array} tags - Additional tags
     */
    async uploadJSON(data, tags = []) {
        const jsonString = JSON.stringify(data);
        const jsonTags = [
            { name: 'Content-Type', value: 'application/json' },
            ...tags
        ];

        return this.upload(jsonString, jsonTags);
    }

    /**
     * Create permanence anchor (small record linking to IPFS)
     * @param {Object} anchor - Anchor data
     */
    async createAnchor(anchor) {
        const anchorData = {
            type: 'ARC8_PERMANENCE_ANCHOR',
            version: '1.0.0',
            ipfs_cid: anchor.ipfsCid,
            content_hash: anchor.contentHash,
            size_bytes: anchor.sizeBytes,
            creator: anchor.creator,
            created_at: Date.now(),
            metadata: anchor.metadata || {}
        };

        const tags = [
            { name: 'Type', value: 'ARC8_ANCHOR' },
            { name: 'IPFS-CID', value: anchor.ipfsCid }
        ];

        return this.uploadJSON(anchorData, tags);
    }

    /**
     * Create provenance record
     * @param {Object} provenance - Provenance data
     */
    async createProvenanceRecord(provenance) {
        const record = {
            type: 'ARC8_PROVENANCE',
            version: '1.0.0',
            artwork: {
                title: provenance.title,
                ipfs_cid: provenance.ipfsCid,
                content_hash: provenance.contentHash
            },
            creator: {
                wallet: provenance.creatorWallet,
                pqs_vertex: provenance.pqsVertex || null
            },
            claims: provenance.claims || [],
            evidence: provenance.evidence || [],
            created_at: Date.now(),
            signatures: provenance.signatures || {}
        };

        const tags = [
            { name: 'Type', value: 'ARC8_PROVENANCE' },
            { name: 'Creator', value: provenance.creatorWallet },
            { name: 'IPFS-CID', value: provenance.ipfsCid }
        ];

        return this.uploadJSON(record, tags);
    }

    /**
     * Fetch data from Arweave
     * @param {string} txId - Transaction ID
     */
    async fetch(txId) {
        const gateways = [
            this.config.arweaveGateway,
            'https://ar-io.net',
            'https://arweave.dev'
        ];

        for (const gateway of gateways) {
            try {
                const response = await fetch(`${gateway}/${txId}`);
                if (response.ok) {
                    return {
                        data: await response.text(),
                        gateway: gateway
                    };
                }
            } catch (e) {
                continue;
            }
        }

        throw new Error('Failed to fetch from all gateways');
    }

    /**
     * Fetch and parse JSON from Arweave
     * @param {string} txId - Transaction ID
     */
    async fetchJSON(txId) {
        const result = await this.fetch(txId);
        return {
            data: JSON.parse(result.data),
            gateway: result.gateway
        };
    }

    /**
     * Verify anchor matches IPFS content
     * @param {string} txId - Arweave transaction ID
     * @param {string} ipfsCid - Expected IPFS CID
     */
    async verifyAnchor(txId, ipfsCid) {
        const { data } = await this.fetchJSON(txId);

        return {
            valid: data.ipfs_cid === ipfsCid,
            anchor: data,
            ipfsCid: data.ipfs_cid,
            expected: ipfsCid
        };
    }
}

/**
 * Hybrid IPFS + Arweave service
 * Combines fast IPFS uploads with permanent Arweave anchoring
 */
export class HybridPermanenceService {
    constructor(ipfsService, arweaveService) {
        this.ipfs = ipfsService;
        this.arweave = arweaveService;
    }

    /**
     * Upload with hybrid permanence
     * @param {*} content - Content to upload
     * @param {string} tier - TEMPORARY | STANDARD | PERMANENT | ARCHIVAL
     */
    async upload(content, tier = 'STANDARD') {
        const result = {
            tier,
            ipfs: null,
            arweave: null,
            proof: null
        };

        // Step 1: Upload to IPFS (fast)
        const ipfsResult = await this.ipfs.add(content);
        result.ipfs = {
            cid: ipfsResult.cid.toString(),
            size: ipfsResult.size
        };

        // Step 2: Calculate content hash
        const contentHash = await this._hashContent(content);

        // Step 3: Arweave based on tier
        if (tier === 'TEMPORARY') {
            // No Arweave for temporary content
            result.arweave = null;
        } else if (tier === 'STANDARD') {
            // Anchor only (small record pointing to IPFS)
            const anchor = await this.arweave.createAnchor({
                ipfsCid: result.ipfs.cid,
                contentHash: contentHash,
                sizeBytes: result.ipfs.size
            });
            result.arweave = {
                type: 'anchor',
                txId: anchor.id,
                gateway: anchor.gateway
            };
        } else if (tier === 'PERMANENT' || tier === 'ARCHIVAL') {
            // Full content to Arweave
            const fullUpload = await this.arweave.upload(content);
            result.arweave = {
                type: 'full',
                txId: fullUpload.id,
                gateway: fullUpload.gateway
            };
        }

        // Step 4: Generate unified proof
        result.proof = {
            arc8_uri: `arc8://${result.ipfs.cid}${result.arweave ? `?ar=${result.arweave.txId}` : ''}`,
            ipfs_cid: result.ipfs.cid,
            arweave_tx: result.arweave?.txId || null,
            content_hash: contentHash,
            tier: tier,
            created_at: Date.now()
        };

        return result;
    }

    /**
     * Retrieve content with fallback
     * @param {Object} proof - Proof object from upload
     */
    async retrieve(proof) {
        // Try IPFS first (faster)
        try {
            const ipfsContent = await this.ipfs.cat(proof.ipfs_cid);
            return {
                source: 'ipfs',
                data: ipfsContent
            };
        } catch (e) {
            // IPFS failed, try Arweave
        }

        // Try Arweave if available
        if (proof.arweave_tx) {
            try {
                const arweaveContent = await this.arweave.fetch(proof.arweave_tx);
                return {
                    source: 'arweave',
                    data: arweaveContent.data
                };
            } catch (e) {
                // Arweave also failed
            }
        }

        throw new Error('Content unavailable from all sources');
    }

    /**
     * Verify content integrity
     * @param {Object} proof - Proof object
     * @param {*} content - Content to verify
     */
    async verify(proof, content) {
        const contentHash = await this._hashContent(content);

        return {
            hashMatch: contentHash === proof.content_hash,
            expectedHash: proof.content_hash,
            actualHash: contentHash
        };
    }

    async _hashContent(content) {
        const encoder = new TextEncoder();
        const data = typeof content === 'string' ? encoder.encode(content) : content;
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
}

// Export for use
export const arweavePermanence = new ArweavePermanenceService();
