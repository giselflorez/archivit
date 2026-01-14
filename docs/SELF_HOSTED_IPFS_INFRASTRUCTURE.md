# SELF-HOSTED IPFS INFRASTRUCTURE
## Maximum Sovereignty: Own Your Infrastructure

**Created:** 2026-01-13
**Status:** ARCHITECTURAL SPECIFICATION
**Classification:** CRITICAL - Enables true decentralization

---

## THE SOVEREIGNTY UPGRADE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   CURRENT: "Connects to decentralized infrastructure"                        ║
║   UPGRADE: "IS decentralized infrastructure"                                 ║
║                                                                              ║
║   By running your own IPFS node on your own hardware,                        ║
║   YOU become the infrastructure. No external dependencies.                   ║
║                                                                              ║
║   USER TAKES ALL — including the servers.                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## ARCHITECTURE OVERVIEW

### Three Sovereignty Tiers

| Tier | Description | External Dependency | Sovereignty |
|------|-------------|---------------------|-------------|
| **Tier 1: Cloud Pinning** | Pinata, Infura, web3.storage | HIGH - They store your data | Low |
| **Tier 2: Personal Node + Network** | Your IPFS node, connected to swarm | MEDIUM - Network for redundancy | Medium |
| **Tier 3: Air-Gapped Node** | Your IPFS node, offline mode | NONE - Fully self-contained | **Maximum** |

### Recommended: Tier 2.5 (Hybrid)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR SOVEREIGN INFRASTRUCTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    EXTERNAL HARD DRIVE                               │   │
│   │                    /Volumes/ARC8_SOVEREIGN                           │   │
│   │   ┌─────────────────────────────────────────────────────────────┐   │   │
│   │   │  /ipfs/                                                      │   │   │
│   │   │  ├── blocks/        # Content-addressed chunks               │   │   │
│   │   │  ├── datastore/     # LevelDB index                          │   │   │
│   │   │  └── keystore/      # Your node identity                     │   │   │
│   │   ├─────────────────────────────────────────────────────────────┤   │   │
│   │   │  /arc8_data/                                                 │   │   │
│   │   │  ├── knowledge_bank/    # Your sovereign archive             │   │   │
│   │   │  ├── media/             # Images, videos, documents          │   │   │
│   │   │  ├── backups/           # Versioned backups                  │   │   │
│   │   │  └── exports/           # Portable exports                   │   │   │
│   │   └─────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    YOUR IPFS NODE                                    │   │
│   │                    localhost:5001 (API)                              │   │
│   │                    localhost:8080 (Gateway)                          │   │
│   │                                                                      │   │
│   │    Mode: HYBRID (connected but self-sufficient)                      │   │
│   │    • Primary storage: YOUR external drive                            │   │
│   │    • Network: Optional redundancy only                               │   │
│   │    • Pinning: Everything stays on YOUR hardware                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│                                      ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    ARC-8 APPLICATION                                 │   │
│   │                                                                      │   │
│   │    Ring 0-2: Browser (localStorage/IndexedDB)                        │   │
│   │    Ring 3+:  YOUR IPFS Node → YOUR External Drive                    │   │
│   │                                                                      │   │
│   │    API calls go to localhost, not cloud                              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SETUP GUIDE

### Step 1: Prepare External Drive

```bash
# Format drive (if needed) - use APFS for Mac, ext4 for Linux
# Name it something meaningful
# Example: ARC8_SOVEREIGN

# Create directory structure
mkdir -p /Volumes/ARC8_SOVEREIGN/ipfs
mkdir -p /Volumes/ARC8_SOVEREIGN/arc8_data/knowledge_bank
mkdir -p /Volumes/ARC8_SOVEREIGN/arc8_data/media
mkdir -p /Volumes/ARC8_SOVEREIGN/arc8_data/backups
mkdir -p /Volumes/ARC8_SOVEREIGN/arc8_data/exports
```

### Step 2: Install IPFS

```bash
# macOS
brew install ipfs

# Linux
wget https://dist.ipfs.tech/kubo/v0.24.0/kubo_v0.24.0_linux-amd64.tar.gz
tar -xvzf kubo_v0.24.0_linux-amd64.tar.gz
cd kubo && sudo bash install.sh

# Verify
ipfs --version
```

### Step 3: Initialize IPFS on External Drive

```bash
# Set IPFS_PATH to external drive
export IPFS_PATH=/Volumes/ARC8_SOVEREIGN/ipfs

# Initialize node
ipfs init

# Verify location
ls -la /Volumes/ARC8_SOVEREIGN/ipfs/
# Should see: blocks, config, datastore, keystore, version
```

### Step 4: Configure for Sovereignty

```bash
# Set storage location permanently
export IPFS_PATH=/Volumes/ARC8_SOVEREIGN/ipfs

# OPTION A: Hybrid Mode (recommended)
# Connected to network for redundancy, but all data stays local
ipfs config --json Datastore.StorageMax '"100GB"'
ipfs config --json Swarm.ConnMgr.LowWater 50
ipfs config --json Swarm.ConnMgr.HighWater 200

# OPTION B: Air-Gapped Mode (maximum sovereignty)
# No network connection at all - pure local content-addressed storage
ipfs config --json Addresses.Swarm '[]'
ipfs config --json Bootstrap '[]'
ipfs config --json Discovery.MDNS.Enabled false
ipfs config --json Swarm.DisableNatPortMap true
```

### Step 5: Start Your Node

```bash
# Create startup script
cat > /Volumes/ARC8_SOVEREIGN/start_ipfs.sh << 'EOF'
#!/bin/bash
export IPFS_PATH=/Volumes/ARC8_SOVEREIGN/ipfs
ipfs daemon --enable-gc
EOF

chmod +x /Volumes/ARC8_SOVEREIGN/start_ipfs.sh

# Run it
/Volumes/ARC8_SOVEREIGN/start_ipfs.sh

# Verify
curl http://localhost:5001/api/v0/id
```

### Step 6: Configure ARC-8 to Use Local Node

Create/update `.env` file:

```bash
# ARC-8 IPFS Configuration
IPFS_API_URL=http://localhost:5001
IPFS_GATEWAY_URL=http://localhost:8080/ipfs/
IPFS_MODE=local  # 'local', 'hybrid', or 'cloud'
IPFS_STORAGE_PATH=/Volumes/ARC8_SOVEREIGN/arc8_data
```

---

## IPFS CONFIGURATION OPTIONS

### config.json Reference

```json
{
  "Identity": {
    "PeerID": "YOUR_UNIQUE_PEER_ID"
  },
  "Datastore": {
    "StorageMax": "100GB",
    "StorageGCWatermark": 90,
    "GCPeriod": "1h"
  },
  "Addresses": {
    "Swarm": [
      "/ip4/0.0.0.0/tcp/4001",
      "/ip6/::/tcp/4001"
    ],
    "API": "/ip4/127.0.0.1/tcp/5001",
    "Gateway": "/ip4/127.0.0.1/tcp/8080"
  },
  "Swarm": {
    "ConnMgr": {
      "Type": "basic",
      "LowWater": 50,
      "HighWater": 200,
      "GracePeriod": "20s"
    }
  },
  "Gateway": {
    "HTTPHeaders": {
      "Access-Control-Allow-Origin": ["http://localhost:5001"],
      "Access-Control-Allow-Methods": ["GET", "POST"]
    }
  }
}
```

### Mode Configurations

#### Hybrid Mode (Recommended)
```bash
# Connected to network but self-sufficient
# Benefits: Redundancy, can share with others, can access public content
# Your data: Stays on your drive, optionally replicated to network

ipfs config --json Swarm.ConnMgr.LowWater 50
ipfs config --json Swarm.ConnMgr.HighWater 200
ipfs config --json Reprovider.Strategy '"all"'
```

#### Air-Gapped Mode (Maximum Sovereignty)
```bash
# No network connection - pure local storage
# Benefits: Maximum privacy, no external dependencies
# Limitation: No redundancy unless you manage backups

ipfs config --json Addresses.Swarm '[]'
ipfs config --json Bootstrap '[]'
ipfs config --json Discovery.MDNS.Enabled false
ipfs config --json Routing.Type '"none"'
```

#### Selective Sharing Mode
```bash
# Connect only to trusted peers
# Benefits: Share with specific people, private network

ipfs config --json Bootstrap '[]'
ipfs config --json Peering.Peers '[
  {"ID": "TRUSTED_PEER_1", "Addrs": ["/ip4/x.x.x.x/tcp/4001"]},
  {"ID": "TRUSTED_PEER_2", "Addrs": ["/ip4/y.y.y.y/tcp/4001"]}
]'
```

---

## ARC-8 INTEGRATION

### Updated ipfs_storage.js Configuration

```javascript
// scripts/interface/static/js/core/ipfs_storage.js

const IPFS_CONFIG = Object.freeze({
    // Sovereignty modes
    MODES: {
        LOCAL: {
            name: 'Local Node',
            api: 'http://localhost:5001',
            gateway: 'http://localhost:8080/ipfs/',
            pinning: 'local',
            sovereignty: 'maximum'
        },
        HYBRID: {
            name: 'Hybrid',
            api: 'http://localhost:5001',
            gateway: 'http://localhost:8080/ipfs/',
            pinning: 'local+remote',
            fallbackGateways: [
                'https://ipfs.io/ipfs/',
                'https://dweb.link/ipfs/'
            ],
            sovereignty: 'high'
        },
        CLOUD: {
            name: 'Cloud Pinning',
            api: null,  // No local node
            gateway: 'https://gateway.pinata.cloud/ipfs/',
            pinning: 'remote',
            sovereignty: 'medium'
        }
    },

    // Current mode (loaded from user config)
    currentMode: 'HYBRID',

    // Local node detection
    async detectLocalNode() {
        try {
            const response = await fetch('http://localhost:5001/api/v0/id', {
                method: 'POST',
                timeout: 2000
            });
            return response.ok;
        } catch {
            return false;
        }
    },

    // Auto-select best mode
    async autoSelectMode() {
        const hasLocalNode = await this.detectLocalNode();
        if (hasLocalNode) {
            return 'LOCAL';
        }
        return 'CLOUD';
    }
});
```

### Ring 3+ Storage Flow

```javascript
class SovereignStorage {
    constructor(mode = 'HYBRID') {
        this.mode = IPFS_CONFIG.MODES[mode];
        this.localApi = this.mode.api;
    }

    /**
     * Store data to IPFS (your node or cloud)
     */
    async store(data, options = {}) {
        const encrypted = await this.encrypt(data);

        if (this.localApi) {
            // Store to YOUR local node
            return await this.storeLocal(encrypted);
        } else {
            // Fallback to cloud pinning
            return await this.storeCloud(encrypted);
        }
    }

    /**
     * Store to local IPFS node (YOUR external drive)
     */
    async storeLocal(data) {
        const formData = new FormData();
        formData.append('file', new Blob([data]));

        const response = await fetch(`${this.localApi}/api/v0/add`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        // Pin locally to prevent garbage collection
        await fetch(`${this.localApi}/api/v0/pin/add?arg=${result.Hash}`, {
            method: 'POST'
        });

        return {
            cid: result.Hash,
            size: result.Size,
            storage: 'local',
            location: 'YOUR_EXTERNAL_DRIVE'
        };
    }

    /**
     * Retrieve from IPFS (local first, then network)
     */
    async retrieve(cid) {
        // Try local node first
        if (this.localApi) {
            try {
                const response = await fetch(
                    `${this.mode.gateway}${cid}`,
                    { timeout: 5000 }
                );
                if (response.ok) {
                    return await response.arrayBuffer();
                }
            } catch {
                console.log('Local retrieval failed, trying network...');
            }
        }

        // Fallback to public gateways
        for (const gateway of this.mode.fallbackGateways || []) {
            try {
                const response = await fetch(`${gateway}${cid}`);
                if (response.ok) {
                    return await response.arrayBuffer();
                }
            } catch {
                continue;
            }
        }

        throw new Error(`Could not retrieve ${cid} from any source`);
    }
}
```

---

## LAUNCHD SERVICE (macOS Auto-Start)

### Create Launch Agent

```bash
cat > ~/Library/LaunchAgents/com.arc8.ipfs.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.arc8.ipfs</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/ipfs</string>
        <string>daemon</string>
        <string>--enable-gc</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>IPFS_PATH</key>
        <string>/Volumes/ARC8_SOVEREIGN/ipfs</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>PathState</key>
        <dict>
            <key>/Volumes/ARC8_SOVEREIGN</key>
            <true/>
        </dict>
    </dict>

    <key>StandardOutPath</key>
    <string>/Volumes/ARC8_SOVEREIGN/logs/ipfs.log</string>

    <key>StandardErrorPath</key>
    <string>/Volumes/ARC8_SOVEREIGN/logs/ipfs.error.log</string>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.arc8.ipfs.plist

# Check status
launchctl list | grep ipfs
```

### Linux systemd Service

```bash
sudo cat > /etc/systemd/system/arc8-ipfs.service << 'EOF'
[Unit]
Description=ARC-8 IPFS Node
After=network.target
RequiresMountsFor=/mnt/arc8_sovereign

[Service]
Type=simple
User=your_username
Environment="IPFS_PATH=/mnt/arc8_sovereign/ipfs"
ExecStart=/usr/local/bin/ipfs daemon --enable-gc
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable arc8-ipfs
sudo systemctl start arc8-ipfs
```

---

## BACKUP STRATEGY

### The 3-2-1 Sovereign Backup Rule

```
3 copies of your data:
├── Copy 1: External drive (primary IPFS node)
├── Copy 2: Second external drive (cloned)
└── Copy 3: Optional cloud pin (encrypted)

2 different storage types:
├── SSD (fast access)
└── HDD (archival)

1 off-site backup:
└── Either encrypted cloud OR physical drive at different location
```

### Automated Backup Script

```bash
#!/bin/bash
# /Volumes/ARC8_SOVEREIGN/backup.sh

SOURCE="/Volumes/ARC8_SOVEREIGN"
BACKUP="/Volumes/ARC8_BACKUP"
DATE=$(date +%Y-%m-%d)

# Rsync with checksums
rsync -avz --checksum \
    --exclude='ipfs/blocks' \
    "$SOURCE/" "$BACKUP/arc8_$DATE/"

# Export IPFS pins list
export IPFS_PATH=/Volumes/ARC8_SOVEREIGN/ipfs
ipfs pin ls --type=recursive > "$BACKUP/arc8_$DATE/pins.txt"

# Verify backup
echo "Backup complete: $BACKUP/arc8_$DATE"
du -sh "$BACKUP/arc8_$DATE"
```

---

## HARDWARE RECOMMENDATIONS

### Minimum Setup
| Component | Specification | Purpose |
|-----------|--------------|---------|
| External SSD | 500GB USB 3.0 | Primary IPFS storage |
| RAM | 8GB | IPFS daemon |
| CPU | Any modern | Content addressing |

### Recommended Setup
| Component | Specification | Purpose |
|-----------|--------------|---------|
| External SSD | 2TB NVMe enclosure | Primary + room to grow |
| Backup HDD | 4TB | Secondary backup |
| RAM | 16GB+ | Comfortable headroom |
| UPS | 600VA | Prevent corruption |

### Maximum Sovereignty Setup
| Component | Specification | Purpose |
|-----------|--------------|---------|
| NAS (Synology/QNAP) | 4-bay, 8TB+ | Redundant storage |
| RAID | RAID 5 or 6 | Fault tolerance |
| UPS | 1500VA | Extended runtime |
| Offsite drive | Rotated monthly | Disaster recovery |

---

## SOVEREIGNTY CHECKLIST

### Setup Verification
- [ ] External drive mounted and accessible
- [ ] IPFS_PATH points to external drive
- [ ] IPFS node initializes correctly
- [ ] IPFS daemon starts and stays running
- [ ] Gateway accessible at localhost:8080
- [ ] API accessible at localhost:5001
- [ ] ARC-8 detects local node
- [ ] Test pin/retrieve cycle works

### Ongoing Maintenance
- [ ] Monitor disk space (80% threshold)
- [ ] Run garbage collection monthly
- [ ] Verify backups quarterly
- [ ] Update IPFS annually (or as needed)
- [ ] Test restore procedure annually

### Security Checklist
- [ ] External drive encrypted (FileVault/LUKS)
- [ ] IPFS API bound to localhost only
- [ ] No sensitive data in public IPFS (air-gap mode)
- [ ] Backup drives secured physically
- [ ] Recovery phrase stored safely (if using IPFS key)

---

## TROUBLESHOOTING

### Node Won't Start
```bash
# Check if drive is mounted
ls /Volumes/ARC8_SOVEREIGN

# Check IPFS_PATH
echo $IPFS_PATH

# Check for lock file
ls -la /Volumes/ARC8_SOVEREIGN/ipfs/repo.lock
# Remove if stale: rm /Volumes/ARC8_SOVEREIGN/ipfs/repo.lock

# Check logs
tail -100 /Volumes/ARC8_SOVEREIGN/logs/ipfs.error.log
```

### Slow Performance
```bash
# Check connection count
ipfs swarm peers | wc -l

# Reduce connections for air-gapped feel
ipfs config --json Swarm.ConnMgr.HighWater 50

# Enable garbage collection
ipfs repo gc
```

### Drive Disconnected While Running
```bash
# IPFS will error - this is expected
# Reconnect drive, then:
ipfs repo fsck
ipfs daemon
```

---

## THE SOVEREIGNTY PROMISE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   WITH THIS SETUP:                                                           ║
║                                                                              ║
║   • Your data lives on YOUR hardware                                         ║
║   • Your node runs on YOUR machine                                           ║
║   • Your backups are in YOUR control                                         ║
║   • Your network participation is YOUR choice                                ║
║                                                                              ║
║   No cloud provider can:                                                     ║
║   • Delete your data                                                         ║
║   • Deny you access                                                          ║
║   • Charge you more                                                          ║
║   • Shut down and lose everything                                            ║
║                                                                              ║
║   USER TAKES ALL — including the infrastructure.                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

*Last Updated: 2026-01-13*
*Status: Ready for Implementation*
