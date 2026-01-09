# PyTorch + WebGPU Architecture for ARCHIV-IT

**Status:** Technical Direction Document
**Date:** January 9, 2026
**Category:** Future Architecture / IT-R8 Integration

---

## Overview

Two-layer architecture separating ML processing from visualization:

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: PyTorch Backend                 │
│  (Python/Server - ML, embeddings, predictions, analysis)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ JSON / Binary Buffers
                              │ (compact tensors, scalars)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 LAYER 2: WebGPU Frontend                    │
│  (TypeScript/Browser - 3D rendering, interaction, animation)│
└─────────────────────────────────────────────────────────────┘
```

---

## Application to ARCHIV-IT / IT-R8

### Current Visualizations (Upgrade Path)

| Feature | Current | With PyTorch+WebGPU |
|---------|---------|---------------------|
| Semantic Network | D3.js force layout | ML-learned embeddings + WebGPU rendering |
| Edition Constellation | Canvas 2D | True 3D WebGPU with flow dynamics |
| Point Cloud | Three.js | Native WebGPU with millions of particles |
| Tag Network | D3.js | Embedding-based clustering + GPU layout |

### New Capabilities

**1. Artery/Bloodflow Visualization for Provenance**
- NFT transfers as "blood flow" through collector network arteries
- Tube radius = transaction volume
- Pulse speed = recency of activity
- Color = value flow (ETH/USD)

**2. ML-Powered Features**
- Learned embeddings for artwork similarity
- Anomaly detection for wash trading (real-time)
- Predictive collector behavior
- Style clustering from image embeddings

**3. Real-Time Streaming**
- PyTorch runs predictions frame-by-frame
- WebGPU updates buffers (not geometry)
- Smooth 60fps animations on complex data

---

## Technical Stack

### Backend (PyTorch)

```python
# Example: Compute flow metrics for collector network
import torch
from torch_geometric.data import Data

class CollectorFlowModel(torch.nn.Module):
    """Compute flow/importance per edge in collector graph"""

    def forward(self, edge_index, edge_attr):
        # edge_attr: [transaction_count, avg_value, recency, hold_time]
        # Output: flow_scalar per edge (0-1)
        ...
        return flow_scalars, importance_scores
```

**Key Libraries:**
- `torch` - Core ML
- `torch_geometric` - Graph neural networks
- `transformers` - Text embeddings for metadata
- `clip` - Image embeddings for artwork
- `open3d` - Point cloud processing

### Frontend (WebGPU)

```typescript
// Example: Update flow animation from PyTorch output
async function updateFlowBuffers(flowData: Float32Array) {
    // flowData from PyTorch model
    device.queue.writeBuffer(flowBuffer, 0, flowData);
    // Shader reads flowBuffer, animates tube pulses
}
```

**Key Libraries:**
- Native WebGPU API
- `wgpu-matrix` - Math utilities
- `@webgpu/types` - TypeScript types

---

## Data Pipeline

```
Blockchain Data (Alchemy, etc.)
        │
        ▼
   PyTorch Dataloader
        │
        ▼
┌───────────────────────────┐
│   Feature Extraction      │
│ - Transaction patterns    │
│ - Collector embeddings    │
│ - Artwork similarity      │
│ - Temporal dynamics       │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   ML Models               │
│ - Flow prediction         │
│ - Anomaly detection       │
│ - Clustering              │
│ - Recommendations         │
└───────────────────────────┘
        │
        ▼
   Compact Output
   (scalars, embeddings)
        │
        ▼
┌───────────────────────────┐
│   WebGPU Visualization    │
│ - Artery/bloodflow render │
│ - Real-time updates       │
│ - Interactive 3D          │
└───────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Backend ML Pipeline
- [ ] Set up PyTorch environment
- [ ] Create collector graph dataloader
- [ ] Implement flow metric computation
- [ ] Export to JSON/binary format

### Phase 2: WebGPU Renderer
- [ ] Basic WebGPU initialization
- [ ] Tube/artery geometry shader
- [ ] Flow animation shader
- [ ] Buffer update from backend

### Phase 3: Integration
- [ ] WebSocket connection for real-time updates
- [ ] Fallback to WebGL for unsupported browsers
- [ ] Performance optimization

### Phase 4: Advanced ML
- [ ] Graph neural network for collector behavior
- [ ] CLIP embeddings for artwork similarity
- [ ] Anomaly detection model training
- [ ] Predictive analytics

---

## IP Considerations

This architecture enables novel innovations:

1. **Artery/Bloodflow Provenance Visualization**
   - Novel visual metaphor for ownership flow
   - ML-driven dynamics (not just static graphs)
   - Potential trademark: "Provenance Flow" or "Chain Arteries"

2. **Real-Time ML Fraud Detection**
   - Streaming anomaly detection
   - Visual alerts in 3D space
   - Patent potential for method

3. **Embedding-Based Discovery**
   - Artwork similarity through learned embeddings
   - Collector taste matching
   - Novel recommendation system

---

## Resource Requirements

**Development:**
- PyTorch expertise
- WebGPU shader programming
- Graph ML knowledge

**Runtime:**
- Server with GPU (for PyTorch inference)
- Modern browser with WebGPU support
- WebSocket for real-time streaming

**Fallback:**
- WebGL 2.0 for older browsers
- CPU inference for small datasets

---

## References

- WebGPU Spec: https://www.w3.org/TR/webgpu/
- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/
- torch_waymo: (for dataloader patterns)
- Open3D PyTorch: https://www.open3d.org/

---

## Next Steps

1. Prototype basic WebGPU renderer for existing semantic network
2. Create PyTorch dataloader for collector graph
3. Implement simple flow metric computation
4. Connect backend to frontend via WebSocket
5. Iterate on visual design for artery metaphor

---

*This architecture represents a significant technical evolution for ARCHIV-IT and positions IT-R8 as a next-generation visualization platform.*
