#!/usr/bin/env python3
"""
NFT-8 4D Connections Visualizer

Generate interactive 3D/4D visualizations of NFT connections:
- Artist's mints across platforms
- Collector networks
- Cross-chain relationships
- Time-based evolution (4th dimension)

Uses Three.js for WebGL rendering.
"""

import json
import hashlib
import math
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# PHI - Golden Ratio
PHI = 1.618033988749895
GOLDEN_ANGLE = 137.5077640500378


def generate_connections_html(
    profile_data: Dict,
    title: str = "NFT Connections",
    output_path: Path = None
) -> str:
    """
    Generate interactive 4D visualization HTML

    Args:
        profile_data: Artist profile data from ArtistWalletProfiler
        title: Page title
        output_path: Optional path to save HTML file

    Returns:
        HTML string
    """

    # Extract data
    mints = profile_data.get('all_mints', [])
    collectors = profile_data.get('all_collectors', profile_data.get('top_collectors', []))
    wallets = profile_data.get('wallets', [])
    platforms = list(profile_data.get('mints_by_platform', {}).keys())
    networks = list(profile_data.get('mints_by_network', {}).keys())

    # Color scheme for platforms
    platform_colors = {
        'SuperRare': '#ff3366',
        'Foundation': '#1e1e1e',
        'Art Blocks': '#ff9900',
        'OpenSea': '#2081e2',
        'Rarible': '#feda03',
        'Objkt': '#0066ff',
        'fxhash': '#00ff88',
        'Hic et Nunc': '#00f5ff',
        'Teia': '#9966ff',
        'Known Origin': '#ec6a5e',
        'Nifty Gateway': '#0052ff',
        'Zora': '#ff6600',
        'Manifold': '#ffcc00',
        'ethereum': '#627eea',
        'polygon': '#8247e5',
        'tezos': '#2c7df7',
        'solana': '#14f195',
        'bitcoin': '#f7931a',
        'Unknown': '#888888',
    }

    # Build nodes data
    nodes = []
    edges = []

    # Add wallet nodes
    for i, wallet in enumerate(wallets):
        addr = wallet.get('address', '')
        network = wallet.get('network', 'unknown')
        nodes.append({
            'id': f"wallet_{i}",
            'type': 'wallet',
            'label': addr[:8] + '...' + addr[-4:],
            'address': addr,
            'network': network,
            'color': platform_colors.get(network, '#ffffff'),
            'size': 2.0,
            'x': math.cos(i * GOLDEN_ANGLE * math.pi / 180) * 5,
            'y': math.sin(i * GOLDEN_ANGLE * math.pi / 180) * 5,
            'z': 0
        })

    # Add mint nodes (positioned in spiral)
    for i, mint in enumerate(mints[:200]):  # Limit for performance
        platform = mint.get('platform', 'Unknown')
        network = mint.get('network', 'unknown')

        # Spiral positioning using golden angle
        angle = i * GOLDEN_ANGLE * math.pi / 180
        radius = math.sqrt(i + 1) * 1.5
        height = (i / len(mints)) * 10 - 5  # Spread vertically by index (time)

        nodes.append({
            'id': f"mint_{i}",
            'type': 'mint',
            'label': mint.get('name', f"#{mint.get('token_id', i)}")[:20],
            'platform': platform,
            'network': network,
            'contract': mint.get('contract_address', ''),
            'token_id': mint.get('token_id', ''),
            'color': platform_colors.get(platform, platform_colors.get(network, '#ffffff')),
            'size': 1.0,
            'x': math.cos(angle) * radius,
            'y': height,
            'z': math.sin(angle) * radius
        })

        # Connect mint to its wallet
        minter_addr = mint.get('minter_address', '')
        for j, wallet in enumerate(wallets):
            if wallet.get('address', '').lower() == minter_addr.lower():
                edges.append({
                    'source': f"wallet_{j}",
                    'target': f"mint_{i}",
                    'type': 'minted'
                })
                break

    # Add collector nodes (outer ring)
    for i, collector in enumerate(collectors[:50]):  # Limit
        addr = collector.get('address', '')
        pieces = collector.get('total_pieces', 1)

        angle = i * GOLDEN_ANGLE * math.pi / 180
        radius = 15 + math.sqrt(i) * 2

        nodes.append({
            'id': f"collector_{i}",
            'type': 'collector',
            'label': addr[:6] + '...',
            'address': addr,
            'pieces': pieces,
            'color': '#54a876',  # Emerald for collectors
            'size': 0.5 + math.log(pieces + 1) * 0.3,
            'x': math.cos(angle) * radius,
            'y': (i % 10) - 5,
            'z': math.sin(angle) * radius
        })

        # Connect collector to their acquired mints
        acquired = collector.get('nfts_acquired', [])
        for acq in acquired[:10]:  # Limit connections
            contract = acq.get('contract', '')
            token_id = str(acq.get('token_id', ''))

            # Find matching mint
            for j, mint in enumerate(mints[:200]):
                if (mint.get('contract_address', '').lower() == contract.lower() and
                    str(mint.get('token_id', '')) == token_id):
                    edges.append({
                        'source': f"mint_{j}",
                        'target': f"collector_{i}",
                        'type': 'collected'
                    })
                    break

    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - NFT-8 4D Visualization</title>
    <style>
        :root {{
            --void: #030308;
            --cosmic: #0a0a12;
            --panel: #0e0e18;
            --border: rgba(255,255,255,0.06);
            --gold: #d4a574;
            --emerald: #54a876;
            --rose: #ba6587;
            --violet: #7865ba;
            --text: #f0ece7;
            --text-dim: #9a9690;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: var(--void);
            color: var(--text);
            font-family: 'Inter', -apple-system, sans-serif;
            overflow: hidden;
        }}

        #container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}

        #canvas {{
            width: 100%;
            height: 100%;
        }}

        .info-panel {{
            position: fixed;
            top: 20px;
            left: 20px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            max-width: 300px;
            z-index: 100;
        }}

        .info-panel h1 {{
            font-size: 1rem;
            font-weight: 300;
            letter-spacing: 0.2em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #5aa8b9, #7865ba, #ba6587);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.5rem;
            font-weight: 200;
            color: var(--gold);
        }}

        .stat-label {{
            font-size: 0.6rem;
            color: var(--text-dim);
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}

        .legend {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid var(--border);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 5px 0;
            font-size: 0.7rem;
            color: var(--text-dim);
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}

        .tooltip {{
            position: fixed;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 200;
            max-width: 250px;
        }}

        .tooltip.visible {{
            opacity: 1;
        }}

        .tooltip h3 {{
            font-size: 0.8rem;
            font-weight: 400;
            margin-bottom: 5px;
            color: var(--gold);
        }}

        .tooltip p {{
            font-size: 0.65rem;
            color: var(--text-dim);
            margin: 3px 0;
        }}

        .controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}

        .controls button {{
            background: var(--panel);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 0.7rem;
            letter-spacing: 0.1em;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .controls button:hover {{
            background: var(--cosmic);
            border-color: var(--gold);
        }}

        .controls button.active {{
            border-color: var(--gold);
            color: var(--gold);
        }}
    </style>
</head>
<body>
    <div id="container">
        <canvas id="canvas"></canvas>
    </div>

    <div class="info-panel">
        <h1>{title.upper()}</h1>
        <p style="font-size: 0.65rem; color: var(--text-dim);">
            Interactive 4D NFT Connection Map
        </p>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(mints)}</div>
                <div class="stat-label">Mints</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(collectors)}</div>
                <div class="stat-label">Collectors</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(wallets)}</div>
                <div class="stat-label">Wallets</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(platforms)}</div>
                <div class="stat-label">Platforms</div>
            </div>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: var(--gold);"></div>
                <span>Artist Wallets</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: var(--violet);"></div>
                <span>NFT Mints</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: var(--emerald);"></div>
                <span>Collectors</span>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip">
        <h3 id="tooltip-title">Node</h3>
        <p id="tooltip-info"></p>
    </div>

    <div class="controls">
        <button onclick="toggleRotation()" id="rotateBtn" class="active">AUTO-ROTATE</button>
        <button onclick="resetCamera()">RESET VIEW</button>
        <button onclick="toggleConnections()" id="connectBtn" class="active">CONNECTIONS</button>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        // Node and edge data
        const nodesData = {json.dumps(nodes)};
        const edgesData = {json.dumps(edges)};

        // Three.js setup
        const container = document.getElementById('container');
        const canvas = document.getElementById('canvas');
        const tooltip = document.getElementById('tooltip');

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x030308);

        const camera = new THREE.PerspectiveCamera(
            60,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        camera.position.set(20, 15, 25);

        const renderer = new THREE.WebGLRenderer({{
            canvas: canvas,
            antialias: true
        }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Controls
        const controls = new THREE.OrbitControls(camera, canvas);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.5;

        // Lights
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        scene.add(ambientLight);

        const pointLight1 = new THREE.PointLight(0x5aa8b9, 1, 100);
        pointLight1.position.set(20, 20, 20);
        scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0xba6587, 0.8, 100);
        pointLight2.position.set(-20, -10, -20);
        scene.add(pointLight2);

        // Create nodes
        const nodeObjects = [];
        const nodeMeshMap = {{}};

        nodesData.forEach(node => {{
            const size = node.size || 1;
            const geometry = node.type === 'wallet'
                ? new THREE.OctahedronGeometry(size)
                : node.type === 'collector'
                    ? new THREE.TetrahedronGeometry(size * 0.8)
                    : new THREE.SphereGeometry(size * 0.5, 16, 16);

            const material = new THREE.MeshPhongMaterial({{
                color: new THREE.Color(node.color),
                emissive: new THREE.Color(node.color),
                emissiveIntensity: 0.3,
                transparent: true,
                opacity: 0.9
            }});

            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(node.x, node.y, node.z);
            mesh.userData = node;

            scene.add(mesh);
            nodeObjects.push(mesh);
            nodeMeshMap[node.id] = mesh;
        }});

        // Create edges
        const edgeLines = [];
        let showConnections = true;

        edgesData.forEach(edge => {{
            const sourceNode = nodeMeshMap[edge.source];
            const targetNode = nodeMeshMap[edge.target];

            if (sourceNode && targetNode) {{
                const points = [
                    sourceNode.position.clone(),
                    targetNode.position.clone()
                ];

                const geometry = new THREE.BufferGeometry().setFromPoints(points);
                const material = new THREE.LineBasicMaterial({{
                    color: edge.type === 'minted' ? 0xd4a574 : 0x54a876,
                    transparent: true,
                    opacity: 0.2
                }});

                const line = new THREE.Line(geometry, material);
                scene.add(line);
                edgeLines.push(line);
            }}
        }});

        // Raycaster for interaction
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        function onMouseMove(event) {{
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(nodeObjects);

            if (intersects.length > 0) {{
                const node = intersects[0].object.userData;

                document.getElementById('tooltip-title').textContent = node.label || 'Node';

                let info = '';
                if (node.type === 'wallet') {{
                    info = `Network: ${{node.network}}<br>Address: ${{node.address}}`;
                }} else if (node.type === 'mint') {{
                    info = `Platform: ${{node.platform}}<br>Network: ${{node.network}}<br>Token: ${{node.token_id}}`;
                }} else if (node.type === 'collector') {{
                    info = `Pieces: ${{node.pieces}}<br>Address: ${{node.address}}`;
                }}

                document.getElementById('tooltip-info').innerHTML = info;
                tooltip.classList.add('visible');
                tooltip.style.left = event.clientX + 15 + 'px';
                tooltip.style.top = event.clientY + 15 + 'px';

                // Highlight node
                intersects[0].object.material.emissiveIntensity = 0.8;
            }} else {{
                tooltip.classList.remove('visible');
                nodeObjects.forEach(obj => {{
                    obj.material.emissiveIntensity = 0.3;
                }});
            }}
        }}

        window.addEventListener('mousemove', onMouseMove);

        // Window resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        // Control functions
        function toggleRotation() {{
            controls.autoRotate = !controls.autoRotate;
            document.getElementById('rotateBtn').classList.toggle('active');
        }}

        function resetCamera() {{
            camera.position.set(20, 15, 25);
            controls.target.set(0, 0, 0);
        }}

        function toggleConnections() {{
            showConnections = !showConnections;
            edgeLines.forEach(line => {{
                line.visible = showConnections;
            }});
            document.getElementById('connectBtn').classList.toggle('active');
        }}

        // Time-based animation (4th dimension)
        let time = 0;

        function animate() {{
            requestAnimationFrame(animate);

            time += 0.001;

            // Subtle node animation
            nodeObjects.forEach((obj, i) => {{
                if (obj.userData.type === 'mint') {{
                    obj.position.y += Math.sin(time * 2 + i * 0.1) * 0.002;
                }}
            }});

            controls.update();
            renderer.render(scene, camera);
        }}

        animate();
    </script>
</body>
</html>'''

    if output_path:
        with open(output_path, 'w') as f:
            f.write(html)

    return html


def generate_from_profile_file(profile_path: Path, output_path: Path = None) -> str:
    """Generate visualization from saved profile JSON"""
    with open(profile_path) as f:
        profile_data = json.load(f)

    title = profile_data.get('display_name', 'Artist') + ' NFT Network'

    if not output_path:
        output_path = profile_path.parent / f"{profile_path.stem}_visualization.html"

    return generate_connections_html(profile_data, title, output_path)


# CLI
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("""
NFT-8 4D Connections Visualizer

Generate interactive 3D/4D visualizations of NFT connections.

Usage:
  python nft_connections_visualizer.py <profile.json> [output.html]

Example:
  python nft_connections_visualizer.py ./profiles/artist_123_profile.json
        """)
        sys.exit(0)

    profile_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        sys.exit(1)

    html_path = generate_from_profile_file(profile_path, output_path)
    print(f"Generated visualization: {html_path}")
