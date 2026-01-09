#!/usr/bin/env python3
"""
Code Obfuscation Tool - Protect source code from copying
Multi-layer protection against AI reconstruction
Copyright (c) 2026 WEB3GISEL. All Rights Reserved.
"""

import py_compile
import shutil
import subprocess
from pathlib import Path
import json
import sys


class CodeProtector:
    """Protect Python and JavaScript code from unauthorized copying"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.protected_dir = self.project_root / 'protected_build'

    def compile_python_to_bytecode(self, source_files: list):
        """Compile Python files to .pyc bytecode (harder to reverse engineer)"""
        print("\n" + "=" * 60)
        print("Compiling Python to Bytecode")
        print("=" * 60)

        compiled = []
        for source_file in source_files:
            source_path = self.project_root / source_file

            if not source_path.exists():
                print(f"⚠ Skipping {source_file} (not found)")
                continue

            # Create protected directory structure
            relative_path = source_path.relative_to(self.project_root)
            protected_path = self.protected_dir / relative_path.parent

            protected_path.mkdir(parents=True, exist_ok=True)

            # Compile to .pyc
            try:
                py_compile.compile(
                    str(source_path),
                    cfile=str(protected_path / f"{source_path.stem}.pyc"),
                    doraise=True
                )
                compiled.append(str(relative_path))
                print(f"✓ Compiled: {relative_path}")

                # Remove original .py file from protected build
                # (only .pyc remains)

            except py_compile.PyCompileError as e:
                print(f"✗ Failed to compile {source_file}: {e}")

        return compiled

    def obfuscate_javascript(self):
        """Obfuscate JavaScript using javascript-obfuscator"""
        print("\n" + "=" * 60)
        print("Obfuscating JavaScript")
        print("=" * 60)

        js_files = list(self.project_root.glob('**/*.js'))

        if not js_files:
            print("No JavaScript files found")
            return

        # Check if javascript-obfuscator is installed
        try:
            subprocess.run(['npx', '--version'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("⚠ npx not found - skipping JavaScript obfuscation")
            print("  Install Node.js to enable JS obfuscation")
            return

        for js_file in js_files:
            if 'node_modules' in str(js_file) or 'protected_build' in str(js_file):
                continue

            relative_path = js_file.relative_to(self.project_root)
            protected_path = self.protected_dir / relative_path

            protected_path.parent.mkdir(parents=True, exist_ok=True)

            # Obfuscate with high protection settings
            cmd = [
                'npx', 'javascript-obfuscator',
                str(js_file),
                '--output', str(protected_path),
                '--compact', 'true',
                '--control-flow-flattening', 'true',
                '--dead-code-injection', 'true',
                '--string-array', 'true',
                '--string-array-encoding', 'base64',
                '--unicode-escape-sequence', 'true'
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"✓ Obfuscated: {relative_path}")
            except subprocess.CalledProcessError as e:
                # Fallback: just copy the file
                shutil.copy2(js_file, protected_path)
                print(f"⚠ Copied (no obfuscation): {relative_path}")

    def minify_css(self):
        """Minify CSS files"""
        print("\n" + "=" * 60)
        print("Minifying CSS")
        print("=" * 60)

        css_files = list(self.project_root.glob('**/*.css'))

        for css_file in css_files:
            if 'protected_build' in str(css_file):
                continue

            relative_path = css_file.relative_to(self.project_root)
            protected_path = self.protected_dir / relative_path

            protected_path.parent.mkdir(parents=True, exist_ok=True)

            # Simple minification: remove comments and extra whitespace
            with open(css_file, 'r') as f:
                css_content = f.read()

            # Remove comments
            import re
            css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
            # Remove extra whitespace
            css_content = re.sub(r'\s+', ' ', css_content)
            css_content = css_content.replace(' {', '{').replace('{ ', '{')
            css_content = css_content.replace(' }', '}').replace('} ', '}')
            css_content = css_content.replace('; ', ';').replace(' ;', ';')

            with open(protected_path, 'w') as f:
                f.write(css_content)

            print(f"✓ Minified: {relative_path}")

    def copy_protected_files(self):
        """Copy non-code files to protected build"""
        print("\n" + "=" * 60)
        print("Copying Additional Files")
        print("=" * 60)

        # Copy essential files
        essential_files = [
            'requirements.txt',
            'README.md',
            'LICENSE',
            '.env.example'
        ]

        for file_name in essential_files:
            source = self.project_root / file_name
            if source.exists():
                shutil.copy2(source, self.protected_dir / file_name)
                print(f"✓ Copied: {file_name}")

        # Copy database folder structure (but not data)
        db_dir = self.protected_dir / 'db'
        db_dir.mkdir(exist_ok=True)

        # Copy knowledge_base structure
        kb_dir = self.protected_dir / 'knowledge_base'
        (kb_dir / 'processed').mkdir(parents=True, exist_ok=True)
        (kb_dir / 'media').mkdir(parents=True, exist_ok=True)

    def add_license_check(self):
        """Add license validation to main entry point"""
        print("\n" + "=" * 60)
        print("Adding License Protection")
        print("=" * 60)

        # Create protected launcher
        launcher_code = '''#!/usr/bin/env python3
"""
ARCHIV-IT - Protected Distribution
License validation required
"""

import sys
from pathlib import Path

# Add protection module to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from scripts.protection.license_manager import LicenseManager

    # Validate license before starting
    lm = LicenseManager()
    valid, message = lm.validate_license()

    if not valid:
        print("=" * 60)
        print("LICENSE VALIDATION FAILED")
        print("=" * 60)
        print(f"\\nReason: {message}")
        print(f"\\nHardware ID: {lm.hardware_id}")
        print("\\nPlease contact support for a valid license key.")
        print("=" * 60)
        sys.exit(1)

    print(f"✓ {message}")

    # Import and run main application
    from scripts.interface.visual_browser import app
    app.run(host='0.0.0.0', port=5001, debug=False)

except ImportError as e:
    print(f"Error: Missing required modules - {e}")
    sys.exit(1)
except PermissionError as e:
    print(f"Permission denied: {e}")
    sys.exit(1)
'''

        launcher_path = self.protected_dir / 'start_protected.py'
        with open(launcher_path, 'w') as f:
            f.write(launcher_code)

        launcher_path.chmod(0o755)
        print(f"✓ Created protected launcher: start_protected.py")

    def apply_anti_ai_protection(self):
        """Apply anti-AI protection layer"""
        print("\n" + "=" * 60)
        print("Applying Anti-AI Protection")
        print("=" * 60)

        # Import and run AI protection
        sys.path.insert(0, str(self.project_root))

        try:
            from scripts.protection.apply_ai_protection import protect_critical_files
            # This creates additionally protected versions
            protect_critical_files()
            print("✓ Anti-AI layer applied")
        except Exception as e:
            print(f"⚠ Anti-AI protection skipped: {e}")

    def create_protected_build(self):
        """Create complete protected build with multi-layer protection"""
        print("\n" + "=" * 60)
        print("WEB3GISEL - ARCHIV-IT Protection")
        print("=" * 60)
        print(f"\nProject: {self.project_root}")
        print(f"Output: {self.protected_dir}")

        # Clean previous build
        if self.protected_dir.exists():
            print("\nCleaning previous build...")
            shutil.rmtree(self.protected_dir)

        self.protected_dir.mkdir(parents=True)

        # Critical Python files to compile
        critical_files = [
            'scripts/interface/user_config_db.py',
            'scripts/processors/embeddings_generator.py',
            'scripts/search/semantic_search.py',
            'scripts/collectors/ethereum_tracker.py',
            'scripts/processors/visual_translator.py'
        ]

        # LAYER 1: AI-proof protection (strongest)
        self.apply_anti_ai_protection()

        # LAYER 2: Compile Python to bytecode
        self.compile_python_to_bytecode(critical_files)

        # LAYER 3: Obfuscate JavaScript
        self.obfuscate_javascript()

        # LAYER 4: Minify CSS
        self.minify_css()

        # LAYER 5: Copy other files
        self.copy_protected_files()

        # LAYER 6: Add license protection
        self.add_license_check()

        print("\n" + "=" * 60)
        print("✓ MULTI-LAYER PROTECTION COMPLETE")
        print("=" * 60)
        print(f"\nProtected build created at: {self.protected_dir}")
        print("\n🔒 Protection Layers Applied:")
        print("  1. Anti-AI reconstruction prevention")
        print("  2. Bytecode compilation")
        print("  3. JavaScript obfuscation")
        print("  4. CSS minification")
        print("  5. File structure protection")
        print("  6. Hardware-bound licensing")
        print("\nNext steps:")
        print("1. Generate license keys for testers")
        print("2. Distribute 'protected_build' folder only")
        print("3. Provide license.key to each tester")
        print("\n⚠️  NEVER distribute original source code")
        print("=" * 60)


if __name__ == '__main__':
    protector = CodeProtector()
    protector.create_protected_build()
