# Living Works & Temporal Framework
## Extracting Past States, Future Events, and Real-Time Reactivity

---

## The Core Insight

NFTs are not static snapshots. They exist in TIME:

```
        PAST                    PRESENT                   FUTURE
          │                        │                        │
    ┌─────┴─────┐            ┌─────┴─────┐            ┌─────┴─────┐
    │ Previous  │            │ Current   │            │ Scheduled │
    │ States    │────────────│ State     │────────────│ Events    │
    │ Iterations│            │ Live Feed │            │ Reveals   │
    └───────────┘            └───────────┘            └───────────┘
          │                        │                        │
    How did it                What is it              What will it
    look before?              right now?              become?
```

---

## Part 1: Extracting Past Iterations

### Types of Historical State Changes

#### 1. **Reveal Mechanisms**
Many NFTs start hidden and reveal later:
```
State 1: Placeholder image (pre-reveal)
State 2: Revealed artwork (post-reveal)
State 3+: Possible subsequent reveals
```

**How to detect:**
- Look for `Reveal` or `MetadataUpdate` events in contract logs
- Compare tokenURI at different block heights
- Check for `revealed` boolean in contract state

#### 2. **Dynamic Metadata Updates**
Some contracts allow metadata changes:
```solidity
// Common patterns in contracts:
function setTokenURI(uint256 tokenId, string memory uri)
function updateMetadata(uint256 tokenId)
function evolve(uint256 tokenId)
```

**How to detect:**
- Monitor `URI` events (ERC-1155) or custom `MetadataUpdate` events
- Track tokenURI() responses over time
- Look for `setBaseURI` transactions

#### 3. **On-Chain Attribute Evolution**
Some NFTs store mutable attributes directly on-chain:
```solidity
mapping(uint256 => uint256) public level;
mapping(uint256 => uint256) public experience;
mapping(uint256 => uint256) public lastFed;
```

**How to detect:**
- Identify state-changing functions in contract ABI
- Monitor transactions that call these functions
- Query historical state at different blocks

#### 4. **Generative Variations**
Art Blocks-style pieces generate different outputs:
```
Same token, different hash → different visual output
Historical outputs may exist as cached renders
```

**How to detect:**
- Check if contract stores generative hash
- Look for render services that cache outputs
- Monitor for re-render transactions

### Technical Implementation: Past State Extraction

```python
class HistoricalStateTracker:
    """
    Extract and archive historical states of NFTs
    """

    def get_token_uri_history(self, contract: str, token_id: int) -> List[Dict]:
        """
        Get all tokenURI values this NFT has had

        Method:
        1. Find all MetadataUpdate/URI events for this token
        2. For each event, query tokenURI at that block
        3. Fetch and archive the metadata at each state
        """
        history = []

        # Find metadata update events
        events = self.get_metadata_events(contract, token_id)

        for event in events:
            block = event['blockNumber']

            # Query tokenURI at historical block
            uri = self.call_at_block(
                contract,
                'tokenURI',
                [token_id],
                block
            )

            # Fetch metadata content
            metadata = self.fetch_metadata(uri)

            # Archive the state
            history.append({
                'block': block,
                'timestamp': self.get_block_timestamp(block),
                'token_uri': uri,
                'metadata': metadata,
                'image': metadata.get('image'),
                'state_type': self.classify_state_change(event)
            })

        return history

    def detect_reveal_pattern(self, contract: str) -> Dict:
        """
        Detect if contract uses reveal mechanism

        Patterns to look for:
        - revealed boolean storage
        - revealTime timestamp
        - placeholder → real URI switch
        """
        abi = self.get_contract_abi(contract)

        reveal_indicators = {
            'has_reveal_function': 'reveal' in [f['name'] for f in abi],
            'has_revealed_state': 'revealed' in self.get_storage_vars(contract),
            'has_reveal_time': 'revealTime' in self.get_storage_vars(contract),
            'has_placeholder': self.check_placeholder_pattern(contract)
        }

        return reveal_indicators

    def archive_generative_output(self, contract: str, token_id: int):
        """
        For generative works, archive the current visual output

        Many generative pieces render differently based on:
        - Token hash/seed
        - Current block/time
        - External data

        We need to capture point-in-time snapshots
        """
        # Get the generative hash/seed
        token_hash = self.get_token_hash(contract, token_id)

        # Capture current render
        render_url = self.get_render_url(contract, token_id)

        # Screenshot/archive the output
        visual_capture = self.capture_visual_state(render_url)

        return {
            'token_hash': token_hash,
            'captured_at': datetime.utcnow(),
            'block_height': self.get_current_block(),
            'visual_state': visual_capture,
            'render_url': render_url
        }
```

### Data Model for Historical States

```python
NFT_STATE_HISTORY = {
    'contract': '0x...',
    'token_id': 123,

    'states': [
        {
            'state_number': 0,
            'state_type': 'initial',
            'block': 14000000,
            'timestamp': '2022-01-15T00:00:00Z',
            'token_uri': 'ipfs://Qm.../hidden',
            'image': 'ipfs://Qm.../placeholder.png',
            'metadata': {
                'name': 'Unrevealed #123',
                'description': 'Awaiting reveal...'
            },
            'trigger': 'mint'
        },
        {
            'state_number': 1,
            'state_type': 'reveal',
            'block': 14500000,
            'timestamp': '2022-02-20T12:00:00Z',
            'token_uri': 'ipfs://Qm.../revealed',
            'image': 'ipfs://Qm.../artwork.png',
            'metadata': {
                'name': 'Cosmic Garden #123',
                'description': 'A generative exploration...',
                'attributes': [...]
            },
            'trigger': 'reveal_transaction',
            'trigger_tx': '0x...'
        },
        {
            'state_number': 2,
            'state_type': 'evolution',
            'block': 15000000,
            'timestamp': '2022-06-01T00:00:00Z',
            'changes': {
                'level': 1 -> 2,
                'experience': 0 -> 500
            },
            'trigger': 'owner_interaction'
        }
    ],

    'current_state': 2,
    'total_transitions': 2,
    'is_mutable': True,
    'mutability_type': ['reveal', 'evolution']
}
```

---

## Part 2: Detecting Future Timed Events

### Types of Scheduled Events

#### 1. **Timed Reveals**
```solidity
uint256 public revealTime = 1680000000; // Unix timestamp

function tokenURI(uint256 tokenId) public view returns (string) {
    if (block.timestamp < revealTime) {
        return placeholderURI;
    }
    return actualURI;
}
```

#### 2. **Phased Releases**
```solidity
uint256[] public phaseEndTimes = [1680000000, 1690000000, 1700000000];

function getCurrentPhase() public view returns (uint256) {
    for (uint i = 0; i < phaseEndTimes.length; i++) {
        if (block.timestamp < phaseEndTimes[i]) return i;
    }
    return phaseEndTimes.length;
}
```

#### 3. **Decay/Expiration**
```solidity
mapping(uint256 => uint256) public lastInteraction;
uint256 public decayPeriod = 30 days;

function getHealth(uint256 tokenId) public view returns (uint256) {
    uint256 elapsed = block.timestamp - lastInteraction[tokenId];
    if (elapsed > decayPeriod) return 0;
    return 100 - (elapsed * 100 / decayPeriod);
}
```

#### 4. **Seasonal/Cyclical Changes**
```solidity
function getSeason() public view returns (string) {
    uint256 dayOfYear = (block.timestamp / 1 days) % 365;
    if (dayOfYear < 91) return "spring";
    if (dayOfYear < 182) return "summer";
    if (dayOfYear < 273) return "autumn";
    return "winter";
}
```

### Technical Implementation: Future Event Detection

```python
class FutureEventDetector:
    """
    Detect scheduled events encoded in contracts and metadata
    """

    def analyze_contract_for_time_logic(self, contract: str) -> Dict:
        """
        Parse contract for time-dependent logic

        Look for:
        - Timestamp comparisons (block.timestamp < X)
        - Time storage variables (revealTime, endTime, etc.)
        - Phase/stage logic
        """
        bytecode = self.get_contract_bytecode(contract)
        abi = self.get_contract_abi(contract)

        # Known time-related function selectors
        time_functions = self.find_time_functions(abi)

        # Look for timestamp storage
        time_vars = []
        for var in ['revealTime', 'endTime', 'startTime', 'phaseEnd',
                    'unlockTime', 'expirationTime', 'decayStart']:
            if self.has_storage_var(contract, var):
                value = self.read_storage_var(contract, var)
                if value > 0:
                    time_vars.append({
                        'name': var,
                        'timestamp': value,
                        'date': datetime.fromtimestamp(value),
                        'is_future': value > time.time()
                    })

        return {
            'has_time_logic': len(time_vars) > 0,
            'time_variables': time_vars,
            'future_events': [v for v in time_vars if v['is_future']],
            'time_functions': time_functions
        }

    def extract_metadata_time_events(self, metadata: Dict) -> List[Dict]:
        """
        Extract time-based events from NFT metadata

        Common patterns:
        - reveal_date
        - unlock_time
        - phase_end
        - edition_close
        - auction_end
        """
        events = []

        time_fields = [
            'reveal_date', 'reveal_time', 'unlock_date', 'unlock_time',
            'phase_end', 'edition_close', 'auction_end', 'expiration',
            'decay_start', 'next_phase', 'scheduled_update'
        ]

        for field in time_fields:
            if field in metadata:
                events.append({
                    'event_type': field,
                    'timestamp': self.parse_time(metadata[field]),
                    'raw_value': metadata[field]
                })

        # Check attributes for time data
        for attr in metadata.get('attributes', []):
            if 'time' in attr.get('trait_type', '').lower():
                events.append({
                    'event_type': attr['trait_type'],
                    'value': attr['value']
                })

        return events

    def build_event_calendar(self, nfts: List[Dict]) -> Dict:
        """
        Build calendar of upcoming events across all tracked NFTs
        """
        calendar = defaultdict(list)

        for nft in nfts:
            contract_events = self.analyze_contract_for_time_logic(nft['contract'])
            metadata_events = self.extract_metadata_time_events(nft['metadata'])

            for event in contract_events['future_events'] + metadata_events:
                if event.get('timestamp') and event['timestamp'] > time.time():
                    date_key = datetime.fromtimestamp(event['timestamp']).date()
                    calendar[date_key].append({
                        'nft': nft,
                        'event': event
                    })

        return dict(calendar)
```

### Data Model for Future Events

```python
NFT_SCHEDULED_EVENTS = {
    'contract': '0x...',
    'token_id': 123,

    'upcoming_events': [
        {
            'event_type': 'reveal',
            'scheduled_time': '2026-02-15T00:00:00Z',
            'source': 'contract_storage',
            'variable': 'revealTime',
            'description': 'Artwork will be revealed',
            'countdown_seconds': 3456000
        },
        {
            'event_type': 'phase_change',
            'scheduled_time': '2026-06-01T00:00:00Z',
            'source': 'metadata',
            'field': 'phase_2_start',
            'description': 'Phase 2 begins - new attributes unlock'
        },
        {
            'event_type': 'decay_threshold',
            'scheduled_time': '2026-03-01T00:00:00Z',
            'source': 'contract_logic',
            'description': 'Will enter decay state if not interacted with'
        }
    ],

    'recurring_events': [
        {
            'event_type': 'seasonal_change',
            'pattern': 'quarterly',
            'next_occurrence': '2026-03-20T00:00:00Z',
            'description': 'Visual changes with seasons'
        }
    ],

    'conditional_events': [
        {
            'event_type': 'evolution',
            'condition': 'experience >= 1000',
            'current_value': 750,
            'description': 'Will evolve when experience threshold reached'
        }
    ]
}
```

---

## Part 3: Tracking Live Reactive Pieces

### Types of Reactivity

#### 1. **Oracle-Fed Data**
Works that display external data:
```
- Price feeds (ETH, BTC, stocks)
- Weather data
- Social metrics (follower counts, etc.)
- Sports scores
- Astronomical data (moon phase, etc.)
```

#### 2. **Time-Responsive**
Works that change based on time:
```
- Day/night cycles
- Seasonal variations
- Anniversary states
- Age-based evolution
- Real-time clocks
```

#### 3. **Chain-State Responsive**
Works that reflect blockchain state:
```
- Current block number/hash
- Gas price visualization
- Network congestion
- Holder count
- Transaction volume
```

#### 4. **Interaction-Responsive**
Works that respond to engagement:
```
- View count
- Owner interactions
- Community votes
- Cumulative interactions
```

#### 5. **Owner-Responsive**
Works that change based on holder:
```
- Different for each owner
- Reflects owner's other holdings
- Changes on transfer
```

### Technical Implementation: Live State Tracking

```python
class LiveWorkTracker:
    """
    Track and archive states of reactive/living NFTs
    """

    def identify_reactivity_type(self, contract: str, metadata: Dict) -> Dict:
        """
        Determine what type of reactivity this work has
        """
        reactivity = {
            'is_reactive': False,
            'types': [],
            'data_sources': [],
            'update_frequency': None
        }

        # Check for oracle usage in contract
        oracles = self.detect_oracle_usage(contract)
        if oracles:
            reactivity['is_reactive'] = True
            reactivity['types'].append('oracle_fed')
            reactivity['data_sources'].extend(oracles)

        # Check for time-based logic
        if self.has_time_based_visuals(contract):
            reactivity['is_reactive'] = True
            reactivity['types'].append('time_responsive')

        # Check for block-based logic
        if self.uses_block_data(contract):
            reactivity['is_reactive'] = True
            reactivity['types'].append('chain_state')

        # Check metadata for reactivity hints
        if 'animation_url' in metadata:
            # Likely interactive/animated
            reactivity['is_reactive'] = True
            reactivity['types'].append('interactive')

        # Determine update frequency
        reactivity['update_frequency'] = self.estimate_update_frequency(
            reactivity['types']
        )

        return reactivity

    def capture_live_state(self, contract: str, token_id: int) -> Dict:
        """
        Capture current state of a reactive work

        For works that change, we need to snapshot:
        - Current visual output
        - Current data values
        - Timestamp of capture
        - Any relevant chain state
        """
        state = {
            'captured_at': datetime.utcnow().isoformat(),
            'block_height': self.get_current_block(),
            'chain_state': {
                'gas_price': self.get_gas_price(),
                'eth_price': self.get_eth_price()
            }
        }

        # Get current metadata
        metadata = self.get_current_metadata(contract, token_id)
        state['metadata'] = metadata

        # If has animation_url, capture the rendered state
        if 'animation_url' in metadata:
            state['visual_capture'] = self.screenshot_animation(
                metadata['animation_url']
            )

        # If uses oracles, capture current oracle values
        oracles = self.detect_oracle_usage(contract)
        if oracles:
            state['oracle_values'] = {
                oracle: self.get_oracle_value(oracle)
                for oracle in oracles
            }

        return state

    def setup_state_monitoring(self, contract: str, token_id: int) -> Dict:
        """
        Configure ongoing monitoring for a reactive work

        Returns monitoring configuration to track state changes
        """
        reactivity = self.identify_reactivity_type(contract, {})

        monitoring = {
            'contract': contract,
            'token_id': token_id,
            'capture_schedule': []
        }

        if 'time_responsive' in reactivity['types']:
            # Capture at different times of day
            monitoring['capture_schedule'].append({
                'type': 'time_of_day',
                'times': ['06:00', '12:00', '18:00', '00:00']
            })

        if 'oracle_fed' in reactivity['types']:
            # Capture when oracle values change significantly
            monitoring['capture_schedule'].append({
                'type': 'oracle_change',
                'threshold': 0.05,  # 5% change triggers capture
                'oracles': reactivity['data_sources']
            })

        if 'chain_state' in reactivity['types']:
            # Capture periodically
            monitoring['capture_schedule'].append({
                'type': 'periodic',
                'interval_hours': 4
            })

        return monitoring
```

### Data Model for Live Reactive Works

```python
REACTIVE_WORK_STATE = {
    'contract': '0x...',
    'token_id': 123,

    'reactivity_profile': {
        'types': ['oracle_fed', 'time_responsive'],
        'data_sources': [
            {
                'type': 'chainlink_oracle',
                'feed': 'ETH/USD',
                'address': '0x...'
            },
            {
                'type': 'time',
                'granularity': 'hour',
                'affects': 'color_palette'
            }
        ],
        'update_frequency': 'real_time',
        'deterministic': False  # Same inputs don't always = same output
    },

    'state_archive': [
        {
            'capture_id': 'state_001',
            'timestamp': '2026-01-06T00:00:00Z',
            'block': 24170000,
            'inputs': {
                'eth_price': 2847.50,
                'hour': 0,
                'gas_price': 25
            },
            'visual_hash': 'abc123...',  # Hash of visual output
            'visual_url': 'archive/state_001.png',
            'metadata_snapshot': {...}
        },
        {
            'capture_id': 'state_002',
            'timestamp': '2026-01-06T06:00:00Z',
            'block': 24172000,
            'inputs': {
                'eth_price': 2890.00,
                'hour': 6,
                'gas_price': 18
            },
            'visual_hash': 'def456...',
            'visual_url': 'archive/state_002.png',
            'changes_from_previous': {
                'eth_price': '+1.5%',
                'visual_similarity': 0.85
            }
        }
    ],

    'monitoring_config': {
        'active': True,
        'next_capture': '2026-01-06T12:00:00Z',
        'capture_conditions': [
            {'type': 'time_interval', 'hours': 6},
            {'type': 'oracle_delta', 'threshold': 0.05},
            {'type': 'transfer_event'}
        ]
    }
}
```

---

## Part 4: Visualization Framework

### How This Appears in the Point Cloud

#### Temporal Dimension

```
Point Cloud with Time Axis:

      PAST ←───────────────────────────→ FUTURE
        │                                    │
        │    ○ ─── ○ ─── ◉ ─── ○ ─── ○     │
        │    │     │     │     │     │     │
        │  state  state current future future│
        │    1     2   state  event  event  │
        │                                    │
        │         Timeline Trail            │
        └────────────────────────────────────┘
```

Each NFT node can be "expanded" to show its temporal existence:
- Past states appear as faded connected nodes
- Current state is the primary node
- Future events appear as pulsing indicators
- Timeline trail shows the work's life

#### State Change Visualization

```
Static Work:          Living Work:
    ●                     ◉ ← (pulsing)
    │                     │
  (fixed)            (breathing animation
                      based on reactivity)
```

Living works visually breathe/pulse to indicate their reactive nature.

#### Event Indicators

```
Upcoming Events:

    ◉ ─────── ⏱ REVEAL in 5 days
    │
    └── ⏱ PHASE 2 in 30 days

Decay Warning:

    ◉ ← (dimming if approaching decay)
```

### Data Structure for Visualization

```python
VISUALIZATION_NODE = {
    'id': 'nft_abc123',
    'type': 'nft',

    # Spatial position (force-directed)
    'x': 0, 'y': 0, 'z': 0,

    # Visual properties
    'color': '#627EEA',  # Blockchain color
    'size': 15,
    'opacity': 1.0,

    # Temporal properties
    'temporal': {
        'is_living': True,
        'pulse_rate': 0.5,  # Animation speed
        'has_history': True,
        'history_depth': 3,  # Number of past states
        'has_future_events': True,
        'next_event_days': 5
    },

    # Expandable timeline
    'timeline': {
        'states': [
            {'time': -60, 'type': 'mint', 'label': 'Created'},
            {'time': -30, 'type': 'reveal', 'label': 'Revealed'},
            {'time': 0, 'type': 'current', 'label': 'Now'},
            {'time': 5, 'type': 'future', 'label': 'Phase 2'},
        ],
        'expanded': False
    },

    # Live feed (for reactive works)
    'live_feed': {
        'active': True,
        'data_source': 'ETH/USD Oracle',
        'current_value': 2847.50,
        'last_update': '2026-01-06T02:30:00Z'
    }
}
```

---

## Part 5: Implementation Architecture

### Database Schema Additions

```sql
-- Historical states table
CREATE TABLE nft_states (
    id INTEGER PRIMARY KEY,
    nft_id INTEGER REFERENCES nft_mints(id),
    state_number INTEGER,
    block_number INTEGER,
    timestamp DATETIME,
    state_type TEXT,  -- 'initial', 'reveal', 'evolution', 'decay'
    token_uri TEXT,
    metadata_json TEXT,
    image_archive_path TEXT,
    trigger_type TEXT,  -- 'mint', 'transaction', 'time', 'oracle'
    trigger_tx_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled events table
CREATE TABLE nft_scheduled_events (
    id INTEGER PRIMARY KEY,
    nft_id INTEGER REFERENCES nft_mints(id),
    event_type TEXT,
    scheduled_time DATETIME,
    source TEXT,  -- 'contract', 'metadata', 'inferred'
    description TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reactivity profiles table
CREATE TABLE nft_reactivity (
    id INTEGER PRIMARY KEY,
    nft_id INTEGER REFERENCES nft_mints(id),
    is_reactive BOOLEAN DEFAULT FALSE,
    reactivity_types TEXT,  -- JSON array
    data_sources TEXT,  -- JSON array
    update_frequency TEXT,
    monitoring_active BOOLEAN DEFAULT FALSE,
    last_capture DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Live state captures table
CREATE TABLE nft_live_captures (
    id INTEGER PRIMARY KEY,
    nft_id INTEGER REFERENCES nft_mints(id),
    capture_timestamp DATETIME,
    block_height INTEGER,
    input_state TEXT,  -- JSON of oracle values, time, etc.
    visual_hash TEXT,
    visual_archive_path TEXT,
    metadata_snapshot TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

```
GET /api/nft/{contract}/{token_id}/history
    → Returns all historical states

GET /api/nft/{contract}/{token_id}/events
    → Returns upcoming scheduled events

GET /api/nft/{contract}/{token_id}/live
    → Returns current live state (for reactive works)

GET /api/calendar
    → Returns calendar of all upcoming events

POST /api/nft/{contract}/{token_id}/capture
    → Triggers immediate state capture

GET /api/network/temporal
    → Returns network with temporal data for visualization
```

---

## Summary: The Living Work Model

```
                    ┌─────────────────────────────────────────┐
                    │           NFT AS LIVING ENTITY          │
                    │                                         │
                    │   PAST          PRESENT        FUTURE   │
                    │    │              │              │       │
                    │    ▼              ▼              ▼       │
                    │  ┌───┐         ┌───┐         ┌───┐     │
                    │  │ 📜│ ──────▶ │ 🔮│ ──────▶ │ ⏰│     │
                    │  │   │         │   │         │   │     │
                    │  └───┘         └───┘         └───┘     │
                    │ History      Live State    Scheduled   │
                    │                 │                       │
                    │                 ▼                       │
                    │            ┌────────┐                  │
                    │            │ 📡     │                  │
                    │            │ Feeds  │                  │
                    │            └────────┘                  │
                    │           Data Sources                 │
                    │                                         │
                    └─────────────────────────────────────────┘

What we track:
- Every state the work has been in
- Every state change trigger
- Current live state (if reactive)
- All data sources feeding it
- All scheduled future events
- Decay/health status
```

This framework treats artworks as they truly are: temporal entities with pasts, presents, and futures - not static objects that merely transfer between wallets.
