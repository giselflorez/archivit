/**
 * SEED PROFILE ENGINE
 * ====================
 * The North Star Implementation
 *
 * A living data structure that represents the user's digital identity.
 * Stored locally. Encrypted. Owned by the user. Forever.
 */

// Version for migration compatibility
const SEED_VERSION = '1.0.0';

// Encryption utilities (uses Web Crypto API)
const SeedCrypto = {
    async generateKey() {
        return await crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );
    },

    async exportKey(key) {
        const exported = await crypto.subtle.exportKey('raw', key);
        return btoa(String.fromCharCode(...new Uint8Array(exported)));
    },

    async importKey(keyString) {
        const keyData = Uint8Array.from(atob(keyString), c => c.charCodeAt(0));
        return await crypto.subtle.importKey(
            'raw',
            keyData,
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );
    },

    async encrypt(data, key) {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const encoded = new TextEncoder().encode(JSON.stringify(data));
        const ciphertext = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            key,
            encoded
        );
        return {
            iv: btoa(String.fromCharCode(...iv)),
            data: btoa(String.fromCharCode(...new Uint8Array(ciphertext)))
        };
    },

    async decrypt(encrypted, key) {
        const iv = Uint8Array.from(atob(encrypted.iv), c => c.charCodeAt(0));
        const ciphertext = Uint8Array.from(atob(encrypted.data), c => c.charCodeAt(0));
        const decrypted = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            key,
            ciphertext
        );
        return JSON.parse(new TextDecoder().decode(decrypted));
    },

    generateEntropy() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
    }
};

/**
 * SEED SCHEMA
 * The complete structure of a user's digital identity
 */
function createEmptySeed() {
    return {
        version: SEED_VERSION,

        // ═══════════════════════════════════════════════════════════
        // LAYER 1: GENESIS CORE (Immutable after creation)
        // ═══════════════════════════════════════════════════════════
        genesis: {
            created_at: null,
            device_fingerprint: null,
            entropy_seed: null,
            root_signature: null,
            interaction_count_at_lock: 100  // Locks after 100 interactions
        },

        // ═══════════════════════════════════════════════════════════
        // LAYER 2: BEHAVIORAL FINGERPRINT (Evolving)
        // ═══════════════════════════════════════════════════════════
        behavioral: {
            temporal: {
                active_hours: new Array(24).fill(0),  // Hour distribution
                active_days: new Array(7).fill(0),     // Day distribution
                response_latencies: [],                 // Time to respond (ms)
                session_durations: [],                  // How long they stay
                creation_intervals: []                  // Time between creations
            },
            linguistic: {
                vocabulary_size: 0,
                unique_words: new Set(),
                avg_sentence_length: 0,
                punctuation_frequency: {},
                emoji_usage: {},
                capitalization_style: 'mixed',  // 'lower', 'upper', 'mixed', 'title'
                formality_score: 0.5            // 0 = casual, 1 = formal
            },
            aesthetic: {
                color_histogram: {},            // RGB buckets
                brightness_preference: 0.5,     // 0 = dark, 1 = bright
                saturation_preference: 0.5,     // 0 = muted, 1 = vivid
                composition_patterns: [],       // Rule of thirds, centered, etc.
                subject_preferences: {}         // People, nature, abstract, etc.
            },
            social: {
                response_rate: 0,               // % of messages responded to
                initiation_rate: 0,             // % of conversations started
                avg_connection_depth: 0,        // Interactions per connection
                community_role: 'observer',     // observer, participant, leader
                sharing_frequency: 0
            }
        },

        // ═══════════════════════════════════════════════════════════
        // LAYER 3: KNOWLEDGE GRAPH (Expanding)
        // ═══════════════════════════════════════════════════════════
        knowledge: {
            topics: {},  // topic -> {weight, depth, last_touched, first_seen}
            entities: {
                people: {},   // name -> {relationship, frequency, sentiment}
                places: {},   // location -> {significance, visits, sentiment}
                things: {}    // item -> {attachment, mentions, context}
            },
            narratives: [],   // Recurring story patterns
            questions: [],    // Questions they ask (curiosity map)
            expertise: {}     // Topics they explain to others
        },

        // ═══════════════════════════════════════════════════════════
        // LAYER 4: CREATION DNA (Learned patterns)
        // ═══════════════════════════════════════════════════════════
        creation_dna: {
            preferred_formats: {},     // format -> usage count
            editing_patterns: {
                crop_tendencies: [],
                color_adjustments: [],
                filter_preferences: [],
                revision_count_avg: 0
            },
            output_templates: [],      // Learned structural patterns
            signature_elements: [],    // Recurring personal touches
            time_to_publish: [],       // How long from start to publish
            perfectionism_score: 0.5   // 0 = ships fast, 1 = refines forever
        },

        // ═══════════════════════════════════════════════════════════
        // LAYER 5: ALGORITHM WEIGHTS (Personal ranking)
        // ═══════════════════════════════════════════════════════════
        algorithm: {
            content_ranking: {
                recency: 0.3,
                relationship_depth: 0.4,
                topic_relevance: 0.2,
                emotional_resonance: 0.1
            },
            engagement_triggers: [],    // What makes them interact
            suppression_patterns: [],   // What they skip/hide
            discovery_mode: 'balanced', // 'familiar', 'balanced', 'exploratory'
            notification_preferences: {
                frequency: 'normal',    // 'minimal', 'normal', 'all'
                quiet_hours: []
            }
        },

        // ═══════════════════════════════════════════════════════════
        // LAYER 6: APP GENOME (Generative capability)
        // ═══════════════════════════════════════════════════════════
        app_genome: {
            ui_preferences: {
                color_scheme: 'dark',
                density: 'comfortable',  // 'compact', 'comfortable', 'spacious'
                animation_level: 'full', // 'none', 'reduced', 'full'
                font_size: 'medium'
            },
            workflow_patterns: [],       // How they navigate apps
            component_affinities: {},    // Which UI components they prefer
            generated_apps: [],          // Apps created from this seed
            exportable_modules: []       // Reusable pieces
        },

        // ═══════════════════════════════════════════════════════════
        // METADATA
        // ═══════════════════════════════════════════════════════════
        meta: {
            total_interactions: 0,
            last_updated: null,
            last_backup: null,
            consent_log: [],             // Record of all consent decisions
            data_sources: []             // Where data came from
        }
    };
}

/**
 * SEED PROFILE ENGINE
 * Main class for managing the user's seed
 */
class SeedProfileEngine {
    constructor() {
        this.seed = null;
        this.encryptionKey = null;
        this.isInitialized = false;
        this.pendingQueue = [];          // Items awaiting consent
        this.autoApproveRules = [];      // Patterns to auto-approve
        this.listeners = new Map();      // Event listeners

        this.DB_NAME = 'SeedProfileDB';
        this.STORE_NAME = 'seed';
    }

    // ═══════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════

    async initialize() {
        // Open IndexedDB
        this.db = await this._openDatabase();

        // Try to load existing seed
        const existingSeed = await this._loadFromStorage();

        if (existingSeed) {
            // Prompt for key to decrypt
            this.seed = existingSeed;
            this.isInitialized = true;
            this._emit('loaded', { seed: this.seed });
        } else {
            // Create new seed
            await this.createNewSeed();
        }

        return this.seed;
    }

    async createNewSeed() {
        // Generate encryption key
        this.encryptionKey = await SeedCrypto.generateKey();

        // Create empty seed
        this.seed = createEmptySeed();

        // Initialize genesis
        this.seed.genesis.created_at = Date.now();
        this.seed.genesis.entropy_seed = SeedCrypto.generateEntropy();
        this.seed.genesis.device_fingerprint = await this._generateDeviceFingerprint();

        // Save
        await this._saveToStorage();

        this.isInitialized = true;
        this._emit('created', { seed: this.seed });

        // Return the key for user to store safely
        const exportedKey = await SeedCrypto.exportKey(this.encryptionKey);

        return {
            seed: this.seed,
            key: exportedKey  // User MUST save this
        };
    }

    async unlock(keyString) {
        try {
            this.encryptionKey = await SeedCrypto.importKey(keyString);
            const encrypted = await this._loadEncryptedSeed();
            this.seed = await SeedCrypto.decrypt(encrypted, this.encryptionKey);
            this.isInitialized = true;
            this._emit('unlocked', { seed: this.seed });
            return true;
        } catch (e) {
            console.error('Failed to unlock seed:', e);
            return false;
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // CONSENT GATEWAY
    // ═══════════════════════════════════════════════════════════════

    /**
     * Queue data for consent review
     * Nothing enters the seed without going through here
     */
    queueForConsent(data) {
        const item = {
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            source: data.source,         // 'screen_capture', 'import', 'creation', etc.
            raw_data: data.raw,          // Original data (can be deleted after)
            extracted_patterns: data.patterns,  // What we learned
            preview: data.preview,       // Human-readable summary
            category: data.category,     // For auto-approve matching
            status: 'pending'
        };

        // Check auto-approve rules
        const autoRule = this.autoApproveRules.find(rule =>
            rule.category === item.category &&
            this._matchesRule(item, rule)
        );

        if (autoRule) {
            item.status = 'auto_approved';
            item.approved_by_rule = autoRule.id;
            this._processApprovedItem(item);
            this._emit('auto_approved', { item, rule: autoRule });
        } else {
            this.pendingQueue.push(item);
            this._emit('queued', { item, queueLength: this.pendingQueue.length });
        }

        return item.id;
    }

    /**
     * Get pending items for review
     */
    getPendingItems() {
        return this.pendingQueue.filter(item => item.status === 'pending');
    }

    /**
     * Approve an item - add its patterns to the seed
     */
    async approveItem(itemId, modifications = null) {
        const item = this.pendingQueue.find(i => i.id === itemId);
        if (!item) return false;

        if (modifications) {
            item.extracted_patterns = { ...item.extracted_patterns, ...modifications };
        }

        item.status = 'approved';
        item.approved_at = Date.now();

        await this._processApprovedItem(item);

        // Log consent
        this.seed.meta.consent_log.push({
            item_id: itemId,
            action: 'approved',
            timestamp: Date.now(),
            patterns_added: Object.keys(item.extracted_patterns)
        });

        await this._saveToStorage();
        this._emit('approved', { item });

        return true;
    }

    /**
     * Reject an item - never train on this
     */
    rejectItem(itemId, deleteRaw = true) {
        const index = this.pendingQueue.findIndex(i => i.id === itemId);
        if (index === -1) return false;

        const item = this.pendingQueue[index];
        item.status = 'rejected';

        if (deleteRaw) {
            item.raw_data = null;  // True deletion
        }

        // Log consent
        this.seed.meta.consent_log.push({
            item_id: itemId,
            action: 'rejected',
            timestamp: Date.now(),
            raw_deleted: deleteRaw
        });

        // Remove from queue
        this.pendingQueue.splice(index, 1);

        this._emit('rejected', { itemId });
        return true;
    }

    /**
     * Add auto-approve rule
     */
    addAutoApproveRule(rule) {
        const newRule = {
            id: crypto.randomUUID(),
            created_at: Date.now(),
            category: rule.category,
            conditions: rule.conditions,
            description: rule.description
        };

        this.autoApproveRules.push(newRule);
        this._emit('rule_added', { rule: newRule });

        return newRule.id;
    }

    // ═══════════════════════════════════════════════════════════════
    // SEED TRAINING
    // ═══════════════════════════════════════════════════════════════

    async _processApprovedItem(item) {
        const patterns = item.extracted_patterns;

        // Update behavioral patterns
        if (patterns.temporal) {
            this._updateTemporal(patterns.temporal);
        }

        if (patterns.linguistic) {
            this._updateLinguistic(patterns.linguistic);
        }

        if (patterns.aesthetic) {
            this._updateAesthetic(patterns.aesthetic);
        }

        if (patterns.topics) {
            this._updateTopics(patterns.topics);
        }

        if (patterns.entities) {
            this._updateEntities(patterns.entities);
        }

        if (patterns.creation) {
            this._updateCreationDNA(patterns.creation);
        }

        // Increment interaction count
        this.seed.meta.total_interactions++;
        this.seed.meta.last_updated = Date.now();

        // Check if genesis should lock
        if (this.seed.meta.total_interactions === this.seed.genesis.interaction_count_at_lock) {
            this._lockGenesis();
        }

        // Log data source
        if (!this.seed.meta.data_sources.includes(item.source)) {
            this.seed.meta.data_sources.push(item.source);
        }
    }

    _updateTemporal(temporal) {
        const t = this.seed.behavioral.temporal;

        if (temporal.hour !== undefined) {
            t.active_hours[temporal.hour]++;
        }
        if (temporal.day !== undefined) {
            t.active_days[temporal.day]++;
        }
        if (temporal.response_latency !== undefined) {
            t.response_latencies.push(temporal.response_latency);
            // Keep last 1000
            if (t.response_latencies.length > 1000) {
                t.response_latencies.shift();
            }
        }
        if (temporal.session_duration !== undefined) {
            t.session_durations.push(temporal.session_duration);
            if (t.session_durations.length > 100) {
                t.session_durations.shift();
            }
        }
    }

    _updateLinguistic(linguistic) {
        const l = this.seed.behavioral.linguistic;

        if (linguistic.words) {
            linguistic.words.forEach(word => {
                if (!l.unique_words.has) {
                    // Convert to Set if needed (JSON doesn't preserve Sets)
                    l.unique_words = new Set(l.unique_words);
                }
                l.unique_words.add(word.toLowerCase());
            });
            l.vocabulary_size = l.unique_words.size;
        }

        if (linguistic.sentence_length !== undefined) {
            const count = this.seed.meta.total_interactions;
            l.avg_sentence_length = (l.avg_sentence_length * count + linguistic.sentence_length) / (count + 1);
        }

        if (linguistic.emojis) {
            linguistic.emojis.forEach(emoji => {
                l.emoji_usage[emoji] = (l.emoji_usage[emoji] || 0) + 1;
            });
        }
    }

    _updateAesthetic(aesthetic) {
        const a = this.seed.behavioral.aesthetic;

        if (aesthetic.dominant_colors) {
            aesthetic.dominant_colors.forEach(color => {
                const key = `${Math.floor(color.r/16)}-${Math.floor(color.g/16)}-${Math.floor(color.b/16)}`;
                a.color_histogram[key] = (a.color_histogram[key] || 0) + 1;
            });
        }

        if (aesthetic.brightness !== undefined) {
            const count = this.seed.meta.total_interactions;
            a.brightness_preference = (a.brightness_preference * count + aesthetic.brightness) / (count + 1);
        }

        if (aesthetic.subject) {
            a.subject_preferences[aesthetic.subject] = (a.subject_preferences[aesthetic.subject] || 0) + 1;
        }
    }

    _updateTopics(topics) {
        const k = this.seed.knowledge.topics;
        const now = Date.now();

        topics.forEach(topic => {
            if (!k[topic.name]) {
                k[topic.name] = {
                    weight: 0,
                    depth: 0,
                    first_seen: now,
                    last_touched: now,
                    mentions: 0
                };
            }

            k[topic.name].weight = Math.min(1, k[topic.name].weight + (topic.confidence || 0.1));
            k[topic.name].depth = Math.max(k[topic.name].depth, topic.depth || 1);
            k[topic.name].last_touched = now;
            k[topic.name].mentions++;
        });
    }

    _updateEntities(entities) {
        const e = this.seed.knowledge.entities;

        if (entities.people) {
            entities.people.forEach(person => {
                if (!e.people[person.name]) {
                    e.people[person.name] = {
                        relationship: person.relationship || 'unknown',
                        frequency: 0,
                        sentiment: 0.5,
                        first_mentioned: Date.now()
                    };
                }
                e.people[person.name].frequency++;
                if (person.sentiment !== undefined) {
                    e.people[person.name].sentiment =
                        (e.people[person.name].sentiment + person.sentiment) / 2;
                }
            });
        }

        if (entities.places) {
            entities.places.forEach(place => {
                if (!e.places[place.name]) {
                    e.places[place.name] = {
                        significance: 0,
                        visits: 0,
                        sentiment: 0.5
                    };
                }
                e.places[place.name].visits++;
                e.places[place.name].significance = Math.min(1,
                    e.places[place.name].significance + 0.1);
            });
        }
    }

    _updateCreationDNA(creation) {
        const c = this.seed.creation_dna;

        if (creation.format) {
            c.preferred_formats[creation.format] = (c.preferred_formats[creation.format] || 0) + 1;
        }

        if (creation.time_to_publish) {
            c.time_to_publish.push(creation.time_to_publish);
            if (c.time_to_publish.length > 100) {
                c.time_to_publish.shift();
            }
        }

        if (creation.revision_count !== undefined) {
            const count = Object.values(c.preferred_formats).reduce((a, b) => a + b, 0);
            c.editing_patterns.revision_count_avg =
                (c.editing_patterns.revision_count_avg * count + creation.revision_count) / (count + 1);
        }
    }

    _lockGenesis() {
        // Generate root signature from behavioral patterns
        const behavioralString = JSON.stringify(this.seed.behavioral);
        // Simple hash (in production, use proper cryptographic hash)
        let hash = 0;
        for (let i = 0; i < behavioralString.length; i++) {
            const char = behavioralString.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        this.seed.genesis.root_signature = Math.abs(hash).toString(16);
        this._emit('genesis_locked', { signature: this.seed.genesis.root_signature });
    }

    // ═══════════════════════════════════════════════════════════════
    // ALGORITHM ACCESS
    // ═══════════════════════════════════════════════════════════════

    /**
     * Get content ranking weights for the spiral algorithm
     */
    getContentRanking() {
        return { ...this.seed.algorithm.content_ranking };
    }

    /**
     * Update algorithm weights
     */
    updateAlgorithm(weights) {
        Object.assign(this.seed.algorithm.content_ranking, weights);
        this._saveToStorage();
        this._emit('algorithm_updated', { weights });
    }

    /**
     * Get topic relevance for a piece of content
     */
    getTopicRelevance(topics) {
        let relevance = 0;
        topics.forEach(topic => {
            if (this.seed.knowledge.topics[topic]) {
                relevance += this.seed.knowledge.topics[topic].weight;
            }
        });
        return Math.min(1, relevance / topics.length);
    }

    /**
     * Get relationship depth with an entity
     */
    getRelationshipDepth(name) {
        const person = this.seed.knowledge.entities.people[name];
        if (!person) return 0;
        return Math.min(1, person.frequency / 100);  // Normalize
    }

    // ═══════════════════════════════════════════════════════════════
    // EXPORT & PORTABILITY
    // ═══════════════════════════════════════════════════════════════

    /**
     * Export seed as encrypted package
     */
    async exportSeed() {
        if (!this.encryptionKey) {
            throw new Error('Seed must be unlocked to export');
        }

        const encrypted = await SeedCrypto.encrypt(this.seed, this.encryptionKey);
        const exportedKey = await SeedCrypto.exportKey(this.encryptionKey);

        return {
            version: SEED_VERSION,
            encrypted_seed: encrypted,
            key: exportedKey,
            exported_at: Date.now(),
            checksum: this._generateChecksum(this.seed)
        };
    }

    /**
     * Export seed as JSON (unencrypted - for full transparency)
     */
    exportSeedPlaintext() {
        return JSON.parse(JSON.stringify(this.seed, (key, value) => {
            if (value instanceof Set) {
                return Array.from(value);
            }
            return value;
        }));
    }

    /**
     * Import seed from export package
     */
    async importSeed(exportPackage) {
        const key = await SeedCrypto.importKey(exportPackage.key);
        const seed = await SeedCrypto.decrypt(exportPackage.encrypted_seed, key);

        // Verify checksum
        if (this._generateChecksum(seed) !== exportPackage.checksum) {
            throw new Error('Seed checksum mismatch - data may be corrupted');
        }

        this.seed = seed;
        this.encryptionKey = key;
        await this._saveToStorage();
        this.isInitialized = true;

        this._emit('imported', { seed: this.seed });
        return true;
    }

    /**
     * Delete everything - true sovereignty includes the right to be forgotten
     */
    async deleteSeed() {
        // Clear IndexedDB
        await this._clearStorage();

        // Clear in-memory
        this.seed = null;
        this.encryptionKey = null;
        this.isInitialized = false;
        this.pendingQueue = [];

        this._emit('deleted', {});
        return true;
    }

    // ═══════════════════════════════════════════════════════════════
    // STORAGE
    // ═══════════════════════════════════════════════════════════════

    async _openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.DB_NAME, 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(this.STORE_NAME)) {
                    db.createObjectStore(this.STORE_NAME, { keyPath: 'id' });
                }
            };
        });
    }

    async _saveToStorage() {
        if (!this.encryptionKey) return;

        const encrypted = await SeedCrypto.encrypt(this.seed, this.encryptionKey);

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.STORE_NAME], 'readwrite');
            const store = transaction.objectStore(this.STORE_NAME);

            const request = store.put({
                id: 'primary_seed',
                encrypted: encrypted,
                updated_at: Date.now()
            });

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    async _loadFromStorage() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.STORE_NAME], 'readonly');
            const store = transaction.objectStore(this.STORE_NAME);

            const request = store.get('primary_seed');

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async _loadEncryptedSeed() {
        const data = await this._loadFromStorage();
        return data ? data.encrypted : null;
    }

    async _clearStorage() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.STORE_NAME], 'readwrite');
            const store = transaction.objectStore(this.STORE_NAME);

            const request = store.clear();

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    // ═══════════════════════════════════════════════════════════════
    // UTILITIES
    // ═══════════════════════════════════════════════════════════════

    async _generateDeviceFingerprint() {
        const components = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset(),
            navigator.hardwareConcurrency || 'unknown'
        ];

        const text = components.join('|');
        const encoder = new TextEncoder();
        const data = encoder.encode(text);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    _generateChecksum(seed) {
        const str = JSON.stringify(seed);
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }

    _matchesRule(item, rule) {
        if (!rule.conditions) return true;

        return rule.conditions.every(condition => {
            switch (condition.type) {
                case 'source_equals':
                    return item.source === condition.value;
                case 'category_equals':
                    return item.category === condition.value;
                case 'pattern_contains':
                    return JSON.stringify(item.extracted_patterns).includes(condition.value);
                default:
                    return false;
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (!this.listeners.has(event)) return;
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }

    _emit(event, data) {
        if (!this.listeners.has(event)) return;
        this.listeners.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (e) {
                console.error(`Error in ${event} listener:`, e);
            }
        });
    }
}

// Singleton instance
const seedEngine = new SeedProfileEngine();

// Export
export { SeedProfileEngine, seedEngine, SeedCrypto, createEmptySeed, SEED_VERSION };
export default seedEngine;
