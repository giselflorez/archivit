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

## Dynamic Effects & Streaming

### Frame-by-Frame Model Streaming

For dynamic effects, run a PyTorch model over time (predicting future flows or anomalies) and stream outputs frame-by-frame to WebGPU:

```python
# Backend: Stream predictions to frontend
import asyncio
import websockets
import torch

async def stream_flow_predictions(model, data_loader, websocket):
    """Stream frame-by-frame predictions to WebGPU client"""
    for batch in data_loader:
        # Run model prediction
        with torch.no_grad():
            flow_pred = model(batch)
            anomaly_scores = detect_anomalies(flow_pred)

        # Pack into compact buffer
        frame_data = {
            'flows': flow_pred.numpy().tobytes(),      # Float32 array
            'anomalies': anomaly_scores.numpy().tobytes(),
            'timestamp': time.time()
        }

        # Stream to WebGPU client
        await websocket.send(msgpack.packb(frame_data))
        await asyncio.sleep(1/60)  # 60fps target
```

```typescript
// Frontend: Update buffers without recomputing geometry
class FlowAnimator {
    private flowBuffer: GPUBuffer;
    private anomalyBuffer: GPUBuffer;

    async onFrame(frameData: ArrayBuffer) {
        // Only update the small control buffers
        // Geometry stays static - shaders read these buffers
        this.device.queue.writeBuffer(this.flowBuffer, 0, frameData.flows);
        this.device.queue.writeBuffer(this.anomalyBuffer, 0, frameData.anomalies);
        // Shader animates tubes based on buffer values
    }
}
```

**Key Insight:** WebGPU only updates small buffers controlling animation parameters. Geometry is computed once. This enables smooth 60fps even with complex ML predictions.

---

## Non-ML Alternative (Lightweight Prototype)

For a purely visual, non-ML prototype, use Python + NumPy without PyTorch:

### Option A: NumPy + Open3D

```python
import numpy as np
import open3d as o3d
from waymo_open_dataset import dataset_pb2

class CollectorFlowGenerator:
    """Generate flow data without ML - pure computation"""

    def compute_flow_metrics(self, transactions):
        """Compute per-edge flow from transaction history"""
        flows = {}
        for tx in transactions:
            edge = (tx['from'], tx['to'])
            if edge not in flows:
                flows[edge] = {'volume': 0, 'recency': 0, 'value': 0}

            flows[edge]['volume'] += 1
            flows[edge]['recency'] = max(flows[edge]['recency'], tx['timestamp'])
            flows[edge]['value'] += tx['value']

        # Normalize to 0-1 scalars
        return self.normalize_flows(flows)

    def export_for_webgpu(self, flows):
        """Export as binary buffer for WebGPU"""
        # Pack as Float32Array: [edge_id, flow, recency, value] per edge
        data = np.array([
            [e, f['volume'], f['recency'], f['value']]
            for e, f in enumerate(flows.values())
        ], dtype=np.float32)
        return data.tobytes()
```

### Option B: Adapt MMDetection3D Patterns

MMDetection3D pipelines show robust data handling patterns - adapt their dataset code even without training models:

```python
# Inspired by MMDetection3D data pipeline
class ArchivitDataPipeline:
    """Robust data handling adapted from MMDetection3D patterns"""

    def __init__(self):
        self.transforms = [
            LoadCollectorGraph(),      # Load from blockchain
            NormalizeTransactions(),   # Clean and normalize
            ComputeFlowMetrics(),      # Calculate per-edge flows
            PackForVisualization(),    # Prepare for WebGPU
        ]

    def __call__(self, data):
        for transform in self.transforms:
            data = transform(data)
        return data

class LoadCollectorGraph:
    """Load collector network from indexed blockchain data"""

    def __call__(self, data):
        # Load from local database (ARCHIV-IT pattern)
        data['nodes'] = self.load_collectors()
        data['edges'] = self.load_transactions()
        return data

class ComputeFlowMetrics:
    """Compute flow/pressure per edge"""

    def __call__(self, data):
        edges = data['edges']
        data['flow'] = self.calculate_flow(edges)
        data['pressure'] = self.calculate_pressure(edges)
        return data
```

---

## Streaming API Architecture

Connect PyTorch/NumPy backend to WebGPU frontend via streaming API:

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Data       │ →  │  Compute    │ →  │  Stream     │    │
│  │  Pipeline   │    │  Flow/ML    │    │  Server     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket / Binary
                              │ (msgpack, protobuf, or raw Float32)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    WebGPU Frontend                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Receive    │ →  │  Update     │ →  │  Render     │    │
│  │  Buffers    │    │  GPU Buffers│    │  Frame      │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Protocol Options

| Protocol | Pros | Cons | Best For |
|----------|------|------|----------|
| WebSocket + msgpack | Low latency, compact | Requires server | Real-time streaming |
| HTTP + JSON | Simple, debuggable | Higher overhead | Static/infrequent updates |
| WebSocket + protobuf | Very compact, typed | Setup complexity | High-frequency data |
| SharedArrayBuffer | Zero-copy (same machine) | Security restrictions | Local development |

### Recommended: WebSocket + Binary Float32

```python
# Backend
async def send_frame(ws, flow_data: np.ndarray):
    # Send raw Float32 bytes - no serialization overhead
    await ws.send(flow_data.astype(np.float32).tobytes())
```

```typescript
// Frontend
ws.onmessage = (event: MessageEvent) => {
    const flowData = new Float32Array(event.data);
    device.queue.writeBuffer(flowBuffer, 0, flowData);
};
```

---

## Summary: Best of Both Worlds

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Data/ML | PyTorch or NumPy | Load data, compute flow/pressure, run predictions |
| Transport | WebSocket + Binary | Stream compact buffers at 60fps |
| Visualization | WebGPU | Render arteries, animate flow, handle interaction |

**PyTorch** is the strong choice for:
- ML models (anomaly detection, predictions)
- Graph neural networks
- Embedding computations
- Complex flow/pressure logic

**NumPy** is sufficient for:
- Non-ML prototypes
- Simple flow calculations
- Quick iteration without GPU

**WebGPU** handles:
- Interactive 3D rendering
- Artery/bloodflow animation
- Real-time buffer updates
- User interaction

Connecting them via a small streaming API gives you the best of both worlds.

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
