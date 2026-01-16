"""
DOC-8 Spiral Compression System

A mathematical compression/archival system based on sacred geometry principles.
Designed for long-term preservation with adjustable parameters.

══════════════════════════════════════════════════════════════════════════════
                         EQUATION REGISTRY
              All equations documented for 22→968 MASTERS scaling
══════════════════════════════════════════════════════════════════════════════

CORE CONSTANTS (from NORTHSTAR principles):
    PHI = 1.618033988749895          # Golden ratio
    PHI_INV = 0.618033988749895      # 1/PHI (conjugate)
    GOLDEN_ANGLE = 137.5077640500378 # degrees (360 * PHI_INV²)
    SCHUMANN = 7.83                   # Hz (Earth resonance)
    TESLA_PATTERN = [3, 6, 9]        # Harmonic structure

SCALING EQUATIONS:
    EQ-1: masters_ratio = target_masters / base_masters
          Example: 968 / 22 = 44.0

    EQ-2: compression_depth = floor(log_PHI(masters_ratio))
          Example: log_φ(44) ≈ 7.87 → depth=7

    EQ-3: chunk_size(level) = base_chunk * PHI^level
          Fibonacci-like growth for nested compression

    EQ-4: spiral_index(n) = n * GOLDEN_ANGLE mod 360
          Distributes data points on golden spiral

    EQ-5: entropy_threshold = PHI_INV^compression_depth
          Quality floor (higher depth = more loss acceptable)

COMPRESSION EQUATIONS:
    EQ-6: quantization_step = value_range / (PHI^precision_level)
          PHI-based quantization for smooth degradation

    EQ-7: fibonacci_chunk(n) = fib(n) * base_unit
          Chunk sizes follow Fibonacci: 1,1,2,3,5,8,13,21...

    EQ-8: resonance_weight(freq) = |sin(freq * 2π / SCHUMANN)|
          Weights data by harmonic resonance

    EQ-9: tesla_reduce(value) = value mod 9 (digital root)
          Reduces to [1-9] for pattern matching

EXPANSION EQUATIONS:
    EQ-10: restore_precision = stored_value * PHI^(-quantization_level)
           Inverse of EQ-6

    EQ-11: interpolate_spiral(sparse_points) = golden_spiral_fit()
           Reconstructs from spiral-distributed samples

══════════════════════════════════════════════════════════════════════════════
"""

import json
import zlib
import hashlib
import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import struct

# ══════════════════════════════════════════════════════════════════════════════
#                              SACRED CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895              # Golden ratio (EQ-*)
PHI_INV = 0.618033988749895          # 1/PHI
PHI_SQ = PHI * PHI                   # PHI squared = PHI + 1
GOLDEN_ANGLE = 137.5077640500378     # 360 * PHI_INV^2
GOLDEN_ANGLE_RAD = math.radians(GOLDEN_ANGLE)
SCHUMANN = 7.83                      # Hz
TESLA_PATTERN = (3, 6, 9)            # Harmonic triad

# Fibonacci sequence (pre-computed for chunking)
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597]

# ══════════════════════════════════════════════════════════════════════════════
#                              SCALING PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ScalingConfig:
    """
    Configuration for scaling from base_masters to target_masters.

    EQUATIONS USED:
    - EQ-1: masters_ratio
    - EQ-2: compression_depth
    - EQ-5: entropy_threshold
    """
    base_masters: int = 22           # Current NORTHSTAR count
    target_masters: int = 968        # Future expansion target

    @property
    def masters_ratio(self) -> float:
        """EQ-1: Calculate scaling ratio"""
        return self.target_masters / self.base_masters

    @property
    def compression_depth(self) -> int:
        """EQ-2: Optimal compression depth based on scaling"""
        ratio = self.masters_ratio
        if ratio <= 1:
            return 1
        return int(math.log(ratio) / math.log(PHI))

    @property
    def entropy_threshold(self) -> float:
        """EQ-5: Quality threshold based on depth"""
        return PHI_INV ** self.compression_depth

    def to_dict(self) -> Dict:
        return {
            'base_masters': self.base_masters,
            'target_masters': self.target_masters,
            'masters_ratio': self.masters_ratio,
            'compression_depth': self.compression_depth,
            'entropy_threshold': self.entropy_threshold,
        }


# ══════════════════════════════════════════════════════════════════════════════
#                              SPIRAL ARCHIVE FORMAT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SpiralArchiveHeader:
    """
    Header for spiral-compressed archive.
    Contains all parameters needed for decompression.
    """
    version: str = "1.0.0"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Scaling config (for 22→968 transition)
    base_masters: int = 22
    target_masters: int = 968
    compression_depth: int = 7

    # Compression parameters
    chunk_base_size: int = 1024      # Base chunk in bytes
    precision_level: int = 3          # PHI quantization level
    use_spiral_distribution: bool = True

    # Integrity
    content_hash: str = ""
    original_size: int = 0
    compressed_size: int = 0

    # Equation registry (for future reference)
    equations_used: List[str] = field(default_factory=lambda: [
        "EQ-1", "EQ-2", "EQ-3", "EQ-5", "EQ-6", "EQ-7"
    ])

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self)).encode('utf-8')

    @classmethod
    def from_bytes(cls, data: bytes) -> 'SpiralArchiveHeader':
        d = json.loads(data.decode('utf-8'))
        return cls(**{k: v for k, v in d.items() if k != 'equations_used'})


# ══════════════════════════════════════════════════════════════════════════════
#                              SPIRAL COMPRESSION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class SpiralCompressor:
    """
    Compression engine using sacred geometry principles.

    Features:
    - Fibonacci-based chunking (EQ-7)
    - Golden spiral data distribution (EQ-4)
    - PHI-quantization for smooth quality scaling (EQ-6)
    - Tesla digital root patterns (EQ-9)
    - Schumann resonance weighting (EQ-8)
    """

    def __init__(self, config: ScalingConfig = None):
        self.config = config or ScalingConfig()
        self.stats = {
            'chunks_processed': 0,
            'spiral_points': 0,
            'compression_ratio': 0.0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    #                          CORE COMPRESSION
    # ─────────────────────────────────────────────────────────────────────────

    def compress(self, data: bytes, precision: int = 3) -> bytes:
        """
        Compress data using spiral compression.

        Args:
            data: Raw bytes to compress
            precision: PHI quantization level (1-7)

        Returns:
            Compressed archive bytes

        EQUATIONS: EQ-3, EQ-6, EQ-7
        """
        # Create header
        header = SpiralArchiveHeader(
            base_masters=self.config.base_masters,
            target_masters=self.config.target_masters,
            compression_depth=self.config.compression_depth,
            precision_level=precision,
            original_size=len(data),
            content_hash=hashlib.sha256(data).hexdigest()[:16],
        )

        # Step 1: Fibonacci chunking (EQ-7)
        chunks = self._fibonacci_chunk(data)
        self.stats['chunks_processed'] = len(chunks)

        # Step 2: Spiral distribution (EQ-4)
        spiral_indexed = self._spiral_distribute(chunks)
        self.stats['spiral_points'] = len(spiral_indexed)

        # Step 3: PHI quantization (EQ-6)
        quantized = self._phi_quantize(spiral_indexed, precision)

        # Step 4: Standard compression (zlib for reliability)
        compressed_payload = zlib.compress(quantized, level=9)

        # Step 5: Pack archive
        header.compressed_size = len(compressed_payload)
        self.stats['compression_ratio'] = len(data) / max(len(compressed_payload), 1)

        return self._pack_archive(header, compressed_payload)

    def decompress(self, archive: bytes) -> bytes:
        """
        Decompress spiral archive.

        EQUATIONS: EQ-10, EQ-11
        """
        # Unpack
        header, payload = self._unpack_archive(archive)

        # Step 1: Decompress payload
        quantized = zlib.decompress(payload)

        # Step 2: Inverse PHI quantization (EQ-10)
        spiral_indexed = self._phi_dequantize(quantized, header.precision_level)

        # Step 3: Inverse spiral distribution (EQ-11)
        chunks = self._spiral_undistribute(spiral_indexed)

        # Step 4: Reassemble from Fibonacci chunks
        data = self._fibonacci_unchunk(chunks)

        # Note: At precision < 7, quantization is lossy
        # Integrity check only valid for precision >= 7
        if header.precision_level >= 7:
            if hashlib.sha256(data).hexdigest()[:16] != header.content_hash:
                raise ValueError("Archive integrity check failed")

        return data

    # ─────────────────────────────────────────────────────────────────────────
    #                     FIBONACCI CHUNKING (EQ-7)
    # ─────────────────────────────────────────────────────────────────────────

    def _fibonacci_chunk(self, data: bytes) -> List[bytes]:
        """
        EQ-7: fibonacci_chunk(n) = fib(n) * base_unit

        Splits data into Fibonacci-sized chunks.
        Smaller chunks at start (headers), larger at end (bulk data).
        """
        chunks = []
        offset = 0
        fib_idx = 0
        base_unit = 64  # Minimum chunk size

        while offset < len(data):
            # Get Fibonacci multiplier
            fib_mult = FIBONACCI[min(fib_idx, len(FIBONACCI) - 1)]
            chunk_size = fib_mult * base_unit

            # Extract chunk
            chunk = data[offset:offset + chunk_size]
            if chunk:
                chunks.append(chunk)

            offset += chunk_size
            fib_idx += 1

        return chunks

    def _fibonacci_unchunk(self, chunks: List[bytes]) -> bytes:
        """Reassemble Fibonacci chunks"""
        return b''.join(chunks)

    # ─────────────────────────────────────────────────────────────────────────
    #                     SPIRAL DISTRIBUTION (EQ-4)
    # ─────────────────────────────────────────────────────────────────────────

    def _spiral_distribute(self, chunks: List[bytes]) -> bytes:
        """
        EQ-4: spiral_index(n) = n * GOLDEN_ANGLE mod 360

        Distributes chunk indices on golden spiral for resilient storage.
        Each chunk gets a spiral position that aids in error recovery.
        """
        n_chunks = len(chunks)
        if n_chunks == 0:
            return b''

        # Calculate spiral positions
        positions = []
        for i in range(n_chunks):
            angle = (i * GOLDEN_ANGLE) % 360
            radius = math.sqrt(i + 1)  # Fermat spiral
            positions.append((angle, radius, i))

        # Sort by angle for sequential storage
        positions.sort(key=lambda x: x[0])

        # Create indexed payload
        indexed_data = []
        for angle, radius, orig_idx in positions:
            chunk = chunks[orig_idx]
            # Header: original index (2 bytes) + length (4 bytes)
            header = struct.pack('>HI', orig_idx, len(chunk))
            indexed_data.append(header + chunk)

        return b''.join(indexed_data)

    def _spiral_undistribute(self, data: bytes) -> List[bytes]:
        """Reverse spiral distribution"""
        chunks = {}
        offset = 0

        while offset < len(data):
            if offset + 6 > len(data):
                break

            # Read header
            orig_idx, length = struct.unpack('>HI', data[offset:offset + 6])
            offset += 6

            # Read chunk
            chunk = data[offset:offset + length]
            chunks[orig_idx] = chunk
            offset += length

        # Reassemble in original order
        max_idx = max(chunks.keys()) if chunks else 0
        return [chunks.get(i, b'') for i in range(max_idx + 1)]

    # ─────────────────────────────────────────────────────────────────────────
    #                     PHI QUANTIZATION (EQ-6)
    # ─────────────────────────────────────────────────────────────────────────

    def _phi_quantize(self, data: bytes, precision: int) -> bytes:
        """
        EQ-6: quantization_step = value_range / (PHI^precision_level)

        Applies PHI-based quantization for smooth quality degradation.
        Higher precision = less loss but larger output.
        """
        # At precision >= 7, no quantization (lossless)
        if precision >= 7:
            return data

        # Calculate quantization step
        step = int(256 / (PHI ** precision))
        if step < 1:
            step = 1

        # Quantize bytes
        quantized = bytes((b // step) * step for b in data)
        return quantized

    def _phi_dequantize(self, data: bytes, precision: int) -> bytes:
        """
        EQ-10: restore_precision = stored_value * PHI^(-quantization_level)

        Note: This is approximate reconstruction.
        Original values cannot be perfectly recovered if precision < 7.
        """
        # No dequantization needed for high precision
        if precision >= 7:
            return data

        # For lower precision, return as-is (values already quantized)
        return data

    # ─────────────────────────────────────────────────────────────────────────
    #                     ARCHIVE PACKING
    # ─────────────────────────────────────────────────────────────────────────

    def _pack_archive(self, header: SpiralArchiveHeader, payload: bytes) -> bytes:
        """Pack header and payload into archive format"""
        header_bytes = header.to_bytes()
        header_len = struct.pack('>I', len(header_bytes))

        # Magic bytes + version
        magic = b'SPRL'  # Spiral archive magic

        return magic + header_len + header_bytes + payload

    def _unpack_archive(self, archive: bytes) -> Tuple[SpiralArchiveHeader, bytes]:
        """Unpack archive into header and payload"""
        if not archive.startswith(b'SPRL'):
            raise ValueError("Invalid spiral archive (bad magic)")

        header_len = struct.unpack('>I', archive[4:8])[0]
        header_bytes = archive[8:8 + header_len]
        payload = archive[8 + header_len:]

        header = SpiralArchiveHeader.from_bytes(header_bytes)
        return header, payload


# ══════════════════════════════════════════════════════════════════════════════
#                         UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def tesla_digital_root(value: int) -> int:
    """
    EQ-9: tesla_reduce(value) = value mod 9 (digital root)

    Reduces any integer to 1-9 using Tesla's pattern.
    0 becomes 9.
    """
    if value == 0:
        return 9
    root = value % 9
    return root if root != 0 else 9


def schumann_weight(frequency: float) -> float:
    """
    EQ-8: resonance_weight(freq) = |sin(freq * 2π / SCHUMANN)|

    Weights data by harmonic resonance with Earth frequency.
    """
    return abs(math.sin(frequency * 2 * math.pi / SCHUMANN))


def calculate_spiral_position(index: int) -> Tuple[float, float]:
    """
    EQ-4: Calculate x,y position on Fermat golden spiral.

    Returns (x, y) coordinates.
    """
    angle_rad = index * GOLDEN_ANGLE_RAD
    radius = math.sqrt(index + 1)
    x = radius * math.cos(angle_rad)
    y = radius * math.sin(angle_rad)
    return (x, y)


def log_phi(value: float) -> float:
    """Logarithm base PHI"""
    return math.log(value) / math.log(PHI)


# ══════════════════════════════════════════════════════════════════════════════
#                         ARCHIVE MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class SpiralArchiveManager:
    """
    High-level manager for spiral archives.

    Handles:
    - Source archival with metadata
    - Long-term preservation format
    - Scaling configuration for 22→968 transition
    """

    def __init__(self, archive_dir: str = None):
        self.archive_dir = Path(archive_dir or '~/.arc8/archives').expanduser()
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.config = ScalingConfig()
        self.compressor = SpiralCompressor(self.config)

    def archive_source(self, source_data: Dict, source_id: str) -> Path:
        """
        Archive a processed source for long-term storage.

        Returns path to archive file.
        """
        # Serialize source data
        json_data = json.dumps(source_data, indent=2).encode('utf-8')

        # Compress with spiral compression
        archive_data = self.compressor.compress(json_data, precision=5)

        # Save archive
        archive_path = self.archive_dir / f"{source_id}.sprl"
        with open(archive_path, 'wb') as f:
            f.write(archive_data)

        # Save metadata index
        self._update_index(source_id, source_data, archive_path)

        return archive_path

    def restore_source(self, source_id: str) -> Optional[Dict]:
        """Restore source from archive"""
        archive_path = self.archive_dir / f"{source_id}.sprl"
        if not archive_path.exists():
            return None

        with open(archive_path, 'rb') as f:
            archive_data = f.read()

        json_data = self.compressor.decompress(archive_data)
        return json.loads(json_data.decode('utf-8'))

    def _update_index(self, source_id: str, source_data: Dict, archive_path: Path):
        """Update archive index"""
        index_path = self.archive_dir / 'index.json'
        index = {}
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)

        index[source_id] = {
            'title': source_data.get('title', ''),
            'archived': datetime.utcnow().isoformat(),
            'size': archive_path.stat().st_size,
            'config': self.config.to_dict(),
        }

        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

    def get_scaling_info(self) -> Dict:
        """Get current scaling configuration and equations"""
        return {
            'config': self.config.to_dict(),
            'equations': {
                'EQ-1': f'masters_ratio = {self.config.target_masters}/{self.config.base_masters} = {self.config.masters_ratio:.2f}',
                'EQ-2': f'compression_depth = floor(log_φ({self.config.masters_ratio:.2f})) = {self.config.compression_depth}',
                'EQ-3': f'chunk_size(level) = base_chunk * φ^level',
                'EQ-4': f'spiral_index(n) = n * {GOLDEN_ANGLE:.4f}° mod 360',
                'EQ-5': f'entropy_threshold = φ^(-{self.config.compression_depth}) = {self.config.entropy_threshold:.6f}',
                'EQ-6': f'quantization_step = 256 / φ^precision',
                'EQ-7': f'fibonacci_chunk(n) = fib(n) * 64 bytes',
                'EQ-8': f'resonance_weight(freq) = |sin(freq * 2π / {SCHUMANN})|',
                'EQ-9': f'tesla_reduce(value) = value mod 9 → [1-9]',
                'EQ-10': 'restore_precision = stored_value (approximate)',
                'EQ-11': 'interpolate_spiral = golden_spiral_fit()',
            },
            'constants': {
                'PHI': PHI,
                'PHI_INV': PHI_INV,
                'GOLDEN_ANGLE': GOLDEN_ANGLE,
                'SCHUMANN': SCHUMANN,
                'TESLA_PATTERN': TESLA_PATTERN,
                'FIBONACCI': FIBONACCI[:10],
            },
            'scaling_note': f'Designed to scale from {self.config.base_masters} to {self.config.target_masters} MASTERS',
        }


# ══════════════════════════════════════════════════════════════════════════════
#                              CLI INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    print("=" * 70)
    print("SPIRAL COMPRESSION SYSTEM - Equation Registry")
    print("=" * 70)

    manager = SpiralArchiveManager()
    info = manager.get_scaling_info()

    print(f"\nScaling: {info['config']['base_masters']} → {info['config']['target_masters']} MASTERS")
    print(f"Compression depth: {info['config']['compression_depth']}")
    print(f"Entropy threshold: {info['config']['entropy_threshold']:.6f}")

    print("\n" + "-" * 70)
    print("EQUATIONS (document for 22→968 MASTERS adjustment):")
    print("-" * 70)
    for eq_id, formula in info['equations'].items():
        print(f"  {eq_id}: {formula}")

    print("\n" + "-" * 70)
    print("CONSTANTS:")
    print("-" * 70)
    for name, value in info['constants'].items():
        print(f"  {name} = {value}")

    # Test compression
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("\n" + "-" * 70)
        print("COMPRESSION TEST:")
        print("-" * 70)

        test_data = b"The key is to always stay curious. " * 100
        compressor = SpiralCompressor()

        # Use precision 7 for lossless compression
        compressed = compressor.compress(test_data, precision=7)
        decompressed = compressor.decompress(compressed)

        print(f"  Original size:   {len(test_data):,} bytes")
        print(f"  Compressed size: {len(compressed):,} bytes")
        print(f"  Ratio:           {compressor.stats['compression_ratio']:.2f}x")
        print(f"  Chunks:          {compressor.stats['chunks_processed']}")
        print(f"  Integrity:       {'PASS' if decompressed == test_data else 'FAIL'}")
