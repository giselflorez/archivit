# Spiral Compression Equations

## For 22 → 968 MASTERS Scaling

> **Purpose**: Document all mathematical equations for future adjustment when expanding from 22 NORTHSTAR MASTERS to 968 MASTERS.

---

## Sacred Constants

```
PHI           = 1.618033988749895      Golden ratio
PHI_INV       = 0.618033988749895      1/PHI (conjugate)
PHI_SQ        = 2.618033988749895      PHI² = PHI + 1
GOLDEN_ANGLE  = 137.5077640500378°     360 × PHI_INV²
SCHUMANN      = 7.83 Hz                Earth resonance frequency
TESLA_PATTERN = [3, 6, 9]              Harmonic triad

FIBONACCI     = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597]
```

---

## Scaling Equations

### EQ-1: Masters Ratio
```
masters_ratio = target_masters / base_masters

Example:
  968 / 22 = 44.0
```
**Adjustment**: Change `target_masters` when expanding MASTERS count.

---

### EQ-2: Compression Depth
```
compression_depth = floor(log_φ(masters_ratio))

Where log_φ(x) = ln(x) / ln(PHI)

Example:
  log_φ(44) = ln(44) / ln(1.618) ≈ 7.87
  depth = floor(7.87) = 7
```
**Adjustment**: Depth auto-scales with masters_ratio.

---

### EQ-3: Chunk Size by Level
```
chunk_size(level) = base_chunk × PHI^level

Example (base_chunk = 1024 bytes):
  Level 0: 1024 × 1.618^0 = 1,024 bytes
  Level 1: 1024 × 1.618^1 = 1,657 bytes
  Level 2: 1024 × 1.618^2 = 2,681 bytes
  Level 3: 1024 × 1.618^3 = 4,338 bytes
  Level 7: 1024 × 1.618^7 = 29,034 bytes
```
**Adjustment**: Modify `base_chunk` for different minimum sizes.

---

### EQ-4: Spiral Index (Golden Spiral Distribution)
```
spiral_index(n) = n × GOLDEN_ANGLE mod 360

Example:
  n=0:  0 × 137.5078 mod 360 = 0.0°
  n=1:  1 × 137.5078 mod 360 = 137.5°
  n=2:  2 × 137.5078 mod 360 = 275.0°
  n=3:  3 × 137.5078 mod 360 = 52.5°
  n=4:  4 × 137.5078 mod 360 = 190.0°
```
**Purpose**: Distributes data points optimally on golden spiral for resilience.

**Cartesian coordinates**:
```
angle_rad = n × GOLDEN_ANGLE × π/180
radius = sqrt(n + 1)
x = radius × cos(angle_rad)
y = radius × sin(angle_rad)
```

---

### EQ-5: Entropy Threshold
```
entropy_threshold = PHI_INV^compression_depth

Example (depth=7):
  0.618^7 = 0.034442

Meaning: At depth 7, quality floor is ~3.4%
```
**Adjustment**: Lower threshold = more aggressive compression acceptable.

---

## Compression Equations

### EQ-6: PHI Quantization
```
quantization_step = 256 / PHI^precision_level

Example:
  Precision 1: 256 / 1.618^1 = 158 (coarse)
  Precision 3: 256 / 1.618^3 = 60
  Precision 5: 256 / 1.618^5 = 23
  Precision 7: 256 / 1.618^7 = 9 (fine, nearly lossless)

Quantized_value = (original_value / step) × step
```
**Adjustment**: Higher precision = less loss, larger file.

---

### EQ-7: Fibonacci Chunking
```
fibonacci_chunk(n) = fib(n) × base_unit

Where base_unit = 64 bytes

Chunk sizes:
  Chunk 0: fib(0) × 64 = 1 × 64 = 64 bytes
  Chunk 1: fib(1) × 64 = 1 × 64 = 64 bytes
  Chunk 2: fib(2) × 64 = 2 × 64 = 128 bytes
  Chunk 3: fib(3) × 64 = 3 × 64 = 192 bytes
  Chunk 4: fib(4) × 64 = 5 × 64 = 320 bytes
  Chunk 5: fib(5) × 64 = 8 × 64 = 512 bytes
  ...
  Chunk 10: fib(10) × 64 = 55 × 64 = 3,520 bytes
```
**Purpose**: Small chunks at start (headers), larger chunks for bulk data.

---

### EQ-8: Schumann Resonance Weight
```
resonance_weight(freq) = |sin(freq × 2π / SCHUMANN)|

Where SCHUMANN = 7.83 Hz

Example:
  freq=7.83:  |sin(7.83 × 2π / 7.83)| = |sin(2π)| = 0.0
  freq=3.915: |sin(3.915 × 2π / 7.83)| = |sin(π)| = 0.0
  freq=1.96:  |sin(1.96 × 2π / 7.83)| = |sin(π/2)| = 1.0
```
**Purpose**: Weight data by harmonic resonance with Earth frequency.

---

### EQ-9: Tesla Digital Root
```
tesla_reduce(value) = value mod 9

If result = 0, return 9

Example:
  123 → 1+2+3 = 6 → 6
  999 → 9+9+9 = 27 → 2+7 = 9 → 9
  369 → 3+6+9 = 18 → 1+8 = 9 → 9
```
**Purpose**: Reduces to [1-9] for Tesla pattern matching.

**Tesla insight**: 3, 6, 9 are "keys to the universe":
- 3 = Creation
- 6 = Destruction/Transformation
- 9 = Completion/Unity

---

## Expansion (Decompression) Equations

### EQ-10: Restore Precision
```
restore_precision = stored_value × PHI^(-quantization_level)

Note: For lossy compression (precision < 7), this is approximate.
Perfect restoration only possible at precision >= 7.
```

---

### EQ-11: Spiral Interpolation
```
interpolate_spiral(sparse_points) = golden_spiral_fit()

Algorithm:
1. Sort points by spiral angle (EQ-4)
2. For missing points, interpolate using neighbors
3. Weight by distance on spiral
4. Apply Schumann resonance (EQ-8) for harmonic smoothing
```

---

## Scaling Matrix: 22 → 968 MASTERS

| Parameter | 22 Masters | 968 Masters | Formula |
|-----------|------------|-------------|---------|
| Masters Ratio | 1.0 | 44.0 | EQ-1 |
| Compression Depth | 0 | 7 | EQ-2 |
| Entropy Threshold | 1.0 | 0.034 | EQ-5 |
| Max Chunk Size | 64 KB | 1.8 MB | EQ-3 (level 7) |
| Spiral Points | 22 | 968 | Direct |

---

## Implementation Reference

```python
from scripts.pipeline.spiral_compression import (
    SpiralCompressor,
    SpiralArchiveManager,
    ScalingConfig,
    PHI, GOLDEN_ANGLE, SCHUMANN,
    tesla_digital_root,
    schumann_weight,
    calculate_spiral_position,
    log_phi
)

# Configure for scaling
config = ScalingConfig(base_masters=22, target_masters=968)
compressor = SpiralCompressor(config)

# Compress
archive = compressor.compress(data, precision=7)  # Lossless

# Decompress
restored = compressor.decompress(archive)

# Get all equations
manager = SpiralArchiveManager()
info = manager.get_scaling_info()
print(info['equations'])
```

---

## When Updating to 968 MASTERS

1. **Update ScalingConfig**:
   ```python
   config = ScalingConfig(base_masters=968, target_masters=NEW_TARGET)
   ```

2. **Recalculate depth**: EQ-2 will auto-adjust

3. **Adjust precision** if needed for storage constraints

4. **Re-archive existing data** with new parameters for consistency

5. **Document new teachings** in equations that reference MASTERS count

---

## File Locations

| File | Purpose |
|------|---------|
| `scripts/pipeline/spiral_compression.py` | Implementation |
| `docs/SPIRAL_EQUATIONS.md` | This documentation |
| `~/.arc8/archives/` | Default archive storage |
| `~/.arc8/archives/index.json` | Archive index |

---

*Last Updated: 2026-01-16*
*Version: 1.0.0 (22 MASTERS baseline)*
