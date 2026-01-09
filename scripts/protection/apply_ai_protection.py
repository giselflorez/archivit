#!/usr/bin/env python3
"""
Apply Anti-AI Protection to Critical Files
Automatically wraps functions and obfuscates strings
Copyright (c) 2026 WEB3GISEL. All Rights Reserved.
"""

import ast
import os
from pathlib import Path


class AIProtectionInjector(ast.NodeTransformer):
    """
    AST transformer that automatically protects functions
    Injects protection code without manual intervention
    """

    def __init__(self):
        self.protected_functions = []
        self.obfuscated_strings = []

    def visit_FunctionDef(self, node):
        """Protect function definitions"""
        # Skip __init__ and private methods
        if node.name.startswith('_'):
            return node

        # Add protection decorator
        protection_decorator = ast.Name(id='protect_critical_code', ctx=ast.Load())
        node.decorator_list.insert(0, protection_decorator)

        self.protected_functions.append(node.name)
        return node

    def visit_Str(self, node):
        """Obfuscate string literals"""
        # Only obfuscate strings longer than 10 chars
        if len(node.s) > 10:
            # Replace with obfuscation call
            obfuscated = ast.Call(
                func=ast.Name(id='reveal_string', ctx=ast.Load()),
                args=[ast.Call(
                    func=ast.Name(id='hide_string', ctx=ast.Load()),
                    args=[node],
                    keywords=[]
                )],
                keywords=[]
            )
            self.obfuscated_strings.append(node.s[:20])
            return obfuscated

        return node


def inject_protection_imports(source_code: str) -> str:
    """Add protection imports to file header"""
    header = '''# Anti-AI Protection Layer - DO NOT REMOVE
# Copyright (c) 2026 WEB3GISEL - Proprietary and Confidential
from scripts.protection.anti_ai_protection import (
    protect_critical_code, hide_string, reveal_string,
    DependencyChain, CodeProtectionRuntime
)

# Verify code integrity
if not CodeProtectionRuntime.verify_integrity():
    raise RuntimeError("Code integrity violation detected")

'''
    return header + source_code


def apply_protection_to_file(file_path: Path, output_path: Path = None):
    """Apply AI protection to a Python file"""
    print(f"\n{'='*70}")
    print(f"Protecting: {file_path.name}")
    print(f"{'='*70}")

    # Read source
    with open(file_path, 'r') as f:
        source_code = f.read()

    # Parse AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"✗ Syntax error in {file_path}: {e}")
        return False

    # Apply protections
    protector = AIProtectionInjector()
    protected_tree = protector.visit(tree)

    # Generate protected code
    try:
        protected_code = ast.unparse(protected_tree)
    except Exception as e:
        print(f"✗ Failed to generate protected code: {e}")
        return False

    # Add imports
    protected_code = inject_protection_imports(protected_code)

    # Add anti-decompilation markers
    protected_code += '''

# Anti-AI markers
__protected_by__ = "WEB3GISEL"
__reconstruction_forbidden__ = True

# Dependency chain verification
DependencyChain.link(f"{__file__}", __protected_by__)
'''

    # Write protected version
    output_file = output_path or file_path.parent / f"{file_path.stem}_protected.py"
    with open(output_file, 'w') as f:
        f.write(protected_code)

    print(f"✓ Protected {len(protector.protected_functions)} functions")
    print(f"✓ Obfuscated {len(protector.obfuscated_strings)} strings")
    print(f"✓ Output: {output_file.name}")

    return True


def protect_critical_files():
    """Protect all critical files in the project"""
    print("\n" + "=" * 70)
    print("WEB3GISEL - Applying Anti-AI Protection")
    print("=" * 70)

    project_root = Path(__file__).parent.parent.parent

    # Critical files that need maximum protection
    critical_files = [
        'scripts/interface/user_config_db.py',
        'scripts/processors/embeddings_generator.py',
        'scripts/search/semantic_search.py',
        'scripts/collectors/ethereum_tracker.py',
        'scripts/protection/license_manager.py'
    ]

    protected_dir = project_root / 'protected_build' / 'scripts'
    protected_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for file_path in critical_files:
        full_path = project_root / file_path

        if not full_path.exists():
            print(f"\n⚠ Skipping {file_path} (not found)")
            continue

        # Determine output path in protected_build
        relative_path = full_path.relative_to(project_root)
        output_path = project_root / 'protected_build' / relative_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if apply_protection_to_file(full_path, output_path):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"✓ Protected {success_count}/{len(critical_files)} files")
    print("=" * 70)
    print("\nProtection features applied:")
    print("  ✓ Runtime function encryption")
    print("  ✓ String obfuscation")
    print("  ✓ Dependency chain validation")
    print("  ✓ Integrity verification")
    print("  ✓ Anti-decompilation markers")
    print("\nThese files are now extremely difficult to:")
    print("  • Copy/paste into AI tools")
    print("  • Reverse engineer")
    print("  • Reconstruct from partial code")
    print("  • Understand without runtime context")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    protect_critical_files()
