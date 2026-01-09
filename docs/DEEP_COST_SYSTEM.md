# Deep Cost Management System

## Overview

A comprehensive, intelligent API cost management system that provides granular control, real-time tracking, budget enforcement, and optimization suggestions for all AI-powered media processing.

## 🎯 Key Features

### 1. **Service-Level Control**
- **Toggle each AI service independently**:
  - 🖼️ Vision Analysis (Claude Vision API)
  - 🎵 Audio Transcription (Whisper API)
  - 🎬 Video Frame Analysis
- **Choose vision AI models**:
  - Haiku ($0.003/image) - Fast, cost-effective
  - Sonnet ($0.015/image) - Balanced performance
  - Opus ($0.075/image) - Maximum capability

### 2. **Real-Time Cost Estimation**
- **Before import**, see exact costs for:
  - Number of images/audio/video files
  - Estimated processing time
  - Cache savings (already-processed content)
  - Per-service breakdown
  - Total cost projection

### 3. **Budget Management**
- Set monthly/weekly/daily budget limits
- Visual budget progress bars
- Automatic warnings at 80% threshold
- Budget enforcement (optional)
- Projected cost vs. remaining budget

### 4. **Intelligent Optimization**
- **Automatic suggestions** to reduce costs:
  - Switch to cheaper AI models
  - Use cached results
  - Batch process large jobs
  - Disable unnecessary services
- **Cache detection**: Saves money by not reprocessing

### 5. **Historical Tracking**
- SQLite database of all API usage
- Cost per document/session
- Usage analytics by service type
- Monthly spending reports

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│           Web Import Form                   │
│  ┌────────────────────────────────────────┐ │
│  │ URL: https://example.com               │ │
│  │ AI Processing Options:                 │ │
│  │ ☑ Vision Analysis [Haiku ▼]           │ │
│  │ ☑ Audio Transcription                 │ │
│  │ ☑ Video Frame Analysis                │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ 💰 Est. API Cost: $0.12                │ │
│  │ • 15 images × $0.003 = $0.05           │ │
│  │ • 2 audio (~6 min) = $0.04             │ │
│  │ • 1 video (10 frames) = $0.03          │ │
│  │                                         │ │
│  │ 💡 Suggestions:                        │ │
│  │ • Cache saved $0.02 on 7 images        │ │
│  │                                         │ │
│  │ Budget: $2.50 / $10.00 (25% used)      │ │
│  │ ▓▓▓░░░░░░░░░░░░░░░░░                  │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│       Cost Manager (cost_manager.py)        │
├─────────────────────────────────────────────┤
│  • Fetch page & analyze media               │
│  • Count: images, audio, video              │
│  • Check cache for processed items          │
│  • Calculate costs per service              │
│  • Generate optimization suggestions        │
│  • Check budget status                      │
│  • Return detailed breakdown                │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│     SQLite Database (cost_tracking.db)      │
├─────────────────────────────────────────────┤
│  Tables:                                    │
│  • jobs         - Actual API usage          │
│  • budgets      - User budget limits        │
│  • processed_cache - Avoid reprocessing     │
└─────────────────────────────────────────────┘
```

## 🔧 Technical Implementation

### Backend Components

**1. Cost Manager (`scripts/interface/cost_manager.py`)**

```python
from cost_manager import cost_manager

# Estimate web import costs
estimate = cost_manager.estimate_web_import(
    url="https://example.com",
    image_count=15,
    audio_files=[{'url': '...', 'estimated_duration_minutes': 3}],
    video_files=[{'url': '...', 'estimated_duration_seconds': 10}],
    vision_model='haiku',  # or 'sonnet', 'opus'
    enable_vision=True,
    enable_transcription=True,
    enable_video=True
)

# Estimate file upload costs
estimate = cost_manager.estimate_file_upload([
    {'path': 'image.jpg', 'type': 'jpg', 'size_bytes': 2048000},
    {'path': 'audio.mp3', 'type': 'mp3', 'size_bytes': 5120000, 'duration_seconds': 180}
])

# Record actual usage
cost_manager.record_job(
    service_type='vision_haiku',
    item_count=15,
    cost=0.045,
    document_id='abc123',
    metadata={'url': 'https://example.com'}
)

# Set budget
cost_manager.set_budget(period='monthly', limit=50.00, alert_threshold=0.8)

# Get usage stats
stats = cost_manager.get_usage_stats(period='monthly')
# Returns: {total_cost, by_service: {vision_haiku: {...}, ...}}
```

**2. Flask API Endpoint (`scripts/interface/visual_browser.py`)**

```python
@app.route('/api/estimate-costs', methods=['POST'])
def api_estimate_costs():
    # Fetch URL, count media, call cost_manager
    # Returns comprehensive cost breakdown
```

**3. Database Schema (`db/cost_tracking.db`)**

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    service_type TEXT NOT NULL,
    item_count INTEGER NOT NULL,
    actual_cost REAL NOT NULL,
    document_id TEXT,
    metadata TEXT
);

CREATE TABLE budgets (
    period TEXT PRIMARY KEY,
    limit_amount REAL NOT NULL,
    alert_threshold REAL DEFAULT 0.8,
    created_at TEXT NOT NULL
);

CREATE TABLE processed_cache (
    content_hash TEXT PRIMARY KEY,
    service_type TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    document_id TEXT,
    cost REAL
);
```

### Frontend Components

**1. Service Toggles (`templates/add_content.html`)**

```html
<!-- Vision Analysis with model selection -->
<label>
    <input type="checkbox" id="enable_vision" checked>
    🖼️ Vision Analysis
</label>
<select id="vision_model">
    <option value="haiku">Haiku ($0.003/img)</option>
    <option value="sonnet">Sonnet ($0.015/img)</option>
    <option value="opus">Opus ($0.075/img)</option>
</select>

<!-- Audio Transcription -->
<label>
    <input type="checkbox" id="enable_transcription" checked>
    🎵 Audio Transcription ($0.006/min)
</label>

<!-- Video Analysis -->
<label>
    <input type="checkbox" id="enable_video" checked>
    🎬 Video Frame Analysis ($0.003/frame)
</label>
```

**2. Cost Display with Suggestions**

```javascript
// Real-time cost estimation
async function estimateCosts() {
    const response = await fetch('/api/estimate-costs', {
        method: 'POST',
        body: JSON.stringify({
            url: url,
            enable_vision: true,
            enable_transcription: true,
            enable_video: true,
            vision_model: 'haiku'
        })
    });

    const data = await response.json();
    // data contains: estimates[], total_cost, suggestions[], budget_status
    displayCostEstimate(data);
}

// Triggers on: URL blur, checkbox change, model selection
```

## 💡 Optimization Strategies

### 1. **Smart Model Selection**
```
15 images × Opus ($0.075)  = $1.13
15 images × Sonnet ($0.015) = $0.23  (80% savings)
15 images × Haiku ($0.003)  = $0.05  (96% savings)

→ Use Haiku for: Product images, social media, NFT art
→ Use Sonnet for: Complex diagrams, technical drawings
→ Use Opus for: Advanced analysis, research documents
```

### 2. **Cache Utilization**
```
First import:  15 images × $0.003 = $0.05
Second import:  7 cached + 8 new × $0.003 = $0.02 (60% savings)

Cache saves: $0.03
```

### 3. **Service Disabling**
```
All services:     $0.12
Text only:        $0.00 (100% savings)
Vision only:      $0.05 (58% savings)
Transcription only: $0.04 (67% savings)
```

### 4. **Batch Processing**
```
1 page × 15 images = $0.05
Crawl 5 pages × 15 images = $0.25

→ Process critical pages first
→ Queue bulk operations
→ Monitor cumulative costs
```

## 📈 Cost Tracking & Analytics

### Usage Stats API

```python
# Get monthly usage
stats = cost_manager.get_usage_stats(period='monthly')
print(f"Total spent: ${stats['total_cost']:.2f}")
print(f"Jobs run: {stats['total_jobs']}")

# Per-service breakdown
for service, data in stats['by_service'].items():
    print(f"{service}: ${data['total_cost']:.2f} ({data['item_count']} items)")
```

### Expected Output

```
Total spent: $45.67
Jobs run: 127

By Service:
  vision_haiku: $23.45 (7,816 images)
  transcription_whisper: $18.22 (3,037 minutes)
  video_analysis: $4.00 (1,334 frames)
```

## ⚙️ Configuration

### Set Monthly Budget

```python
# Set $100 monthly budget, alert at 80%
cost_manager.set_budget(period='monthly', limit=100.00, alert_threshold=0.8)
```

### Budget Enforcement Modes

**1. Warning Only (Default)**
- Shows alerts when approaching limit
- Allows imports to proceed
- User makes final decision

**2. Hard Limit (Future)**
- Blocks imports that exceed budget
- Requires budget increase to proceed

### Pricing Configuration

Update in `cost_manager.py`:

```python
PRICING = {
    ServiceType.VISION_HAIKU: {
        'cost_per_image': 0.003,
        'cost_per_1k_tokens': 0.001
    },
    # ... update as API pricing changes
}
```

## 🎯 Use Cases

### Use Case 1: NFT Artist Portfolio

**Scenario**: Import SuperRare artist page with 50 NFT images

**Cost Without Optimization**:
```
50 images × Sonnet ($0.015) = $0.75
```

**Cost With Optimization**:
```
1. Switch to Haiku: 50 × $0.003 = $0.15 (80% savings)
2. 20 already cached: (50-20) × $0.003 = $0.09 (88% savings)
```

**Suggested Settings**:
- ✅ Vision Analysis: Haiku (NFTs are visual, need analysis)
- ❌ Audio Transcription (no audio on NFT pages)
- ❌ Video Analysis (use only for video NFTs)

---

### Use Case 2: Podcast Archive

**Scenario**: Import 10 podcast episodes, 45 minutes each

**Cost**:
```
10 episodes × 45 min × $0.006/min = $2.70
```

**Optimization**:
```
- Import audio transcription only
- Disable vision and video
- Batch import during off-peak hours
```

**Suggested Settings**:
- ❌ Vision Analysis (no images)
- ✅ Audio Transcription (primary content)
- ❌ Video Analysis (no videos)

---

### Use Case 3: Research Paper with Diagrams

**Scenario**: PDF with 12 complex diagrams, no audio/video

**Cost Without Optimization**:
```
12 diagrams × Opus ($0.075) = $0.90
```

**Cost With Optimization**:
```
12 diagrams × Sonnet ($0.015) = $0.18 (80% savings)
```

**Suggested Settings**:
- ✅ Vision Analysis: Sonnet (complex diagrams need good analysis)
- ❌ Audio Transcription (no audio)
- ❌ Video Analysis (no video)

---

## 📊 Cost Comparison Table

| Media Type | Quantity | Haiku | Sonnet | Opus | Whisper | Recommended |
|------------|----------|-------|--------|------|---------|-------------|
| NFT Portfolio | 50 images | $0.15 | $0.75 | $3.75 | N/A | **Haiku** |
| Podcast | 45 min | N/A | N/A | N/A | $0.27 | **Whisper** |
| Tutorial Video | 10 frames | $0.03 | $0.15 | $0.75 | N/A | **Haiku** |
| Research PDF | 12 diagrams | $0.04 | $0.18 | $0.90 | N/A | **Sonnet** |
| Blog Post | 5 images + 1 audio (10min) | $0.02 | $0.08 | $0.38 | $0.06 | **Haiku + Whisper** |

---

## 🔮 Future Enhancements

### Phase 1 (Implemented)
- [x] Service-level toggles
- [x] Model selection
- [x] Real-time cost estimation
- [x] Budget tracking
- [x] Optimization suggestions
- [x] Database logging

### Phase 2 (Planned)
- [ ] Per-document cost display in archive
- [ ] Monthly cost analytics dashboard
- [ ] Budget enforcement (hard limits)
- [ ] Cost trends and forecasting
- [ ] Batch queue with cost preview
- [ ] API quota warnings

### Phase 3 (Future)
- [ ] Smart auto-model selection (ML-based)
- [ ] Cost-aware processing priority
- [ ] Multi-user cost allocation
- [ ] Export cost reports (CSV/PDF)
- [ ] Integration with billing systems
- [ ] Cost alerts via email/webhook

---

## 📝 Best Practices

### 1. **Always Check Estimate First**
- Enter URL and wait for cost preview
- Review suggestions before importing
- Adjust settings if cost is too high

### 2. **Use Appropriate Models**
- **Haiku**: Simple images, NFTs, social media
- **Sonnet**: Complex documents, technical diagrams
- **Opus**: Maximum accuracy, research analysis

### 3. **Disable Unused Services**
- Text-only articles: Disable all AI processing
- Audio content: Disable vision and video
- Visual content: Disable transcription

### 4. **Set and Monitor Budgets**
- Start with monthly budget
- Review usage weekly
- Adjust limits based on needs

### 5. **Leverage Cache**
- Re-importing same content = $0 cost
- Archive grows smarter over time
- Cache persists across sessions

---

## 🚨 Troubleshooting

### High Costs

**Problem**: Import estimated at $20+

**Solutions**:
1. Disable unnecessary services
2. Switch to Haiku model
3. Import one page instead of crawling
4. Process in smaller batches

### Budget Exceeded

**Problem**: "Budget exceeded" warning

**Solutions**:
1. Increase monthly budget
2. Wait for next billing period
3. Process only essential content
4. Review and delete unused documents

### Inaccurate Estimates

**Problem**: Actual cost different from estimate

**Solutions**:
1. Estimates are based on averages
2. Actual file sizes may vary
3. Network errors can cause retries
4. Review logs for details

---

## 📞 Support

For cost management questions:
- Check pricing updates: [Anthropic](https://anthropic.com/pricing) | [OpenAI](https://openai.com/pricing)
- Report issues: GitHub Issues
- Documentation: `/docs/API_COST_ESTIMATION.md`

---

**Last Updated**: January 3, 2026
**Version**: 2.0 (Deep Cost System)
