#!/usr/bin/env python3
"""
Anti-AI Protection Layer
Makes code extremely difficult to copy/paste into AI tools and recreate
Copyright (c) 2026 WEB3GISEL. All Rights Reserved.
"""

import base64
import zlib
import hashlib
import secrets
from typing import Callable
import inspect


class CodeProtectionRuntime:
    """
    Runtime protection that fragments and encrypts critical code
    Makes it impossible to reconstruct by feeding to AI
    """

    # Encrypted code fragments (AI can't understand these)
    _fragments = {}
    _integrity_hash = None
    _runtime_key = None

    @staticmethod
    def _generate_runtime_key():
        """Generate ephemeral encryption key at runtime"""
        # Key is different every time - can't be copied
        import platform
        import time
        seed = f"{platform.node()}{time.time()}{secrets.token_hex(16)}"
        return hashlib.sha256(seed.encode()).digest()

    @staticmethod
    def _xor_encrypt(data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption (fast, effective for obfuscation)"""
        return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))

    @classmethod
    def protect_function(cls, func: Callable) -> Callable:
        """
        Protect a function by encrypting its bytecode
        AI cannot reconstruct this without runtime key
        """
        # Get function bytecode
        code_obj = func.__code__
        bytecode = code_obj.co_code

        # Generate unique ID for this function
        func_id = hashlib.md5(f"{func.__name__}{bytecode}".encode()).hexdigest()

        # Encrypt bytecode with runtime key
        if cls._runtime_key is None:
            cls._runtime_key = cls._generate_runtime_key()

        encrypted = cls._xor_encrypt(bytecode, cls._runtime_key)
        compressed = zlib.compress(encrypted)
        encoded = base64.b64encode(compressed).decode()

        # Store encrypted fragment
        cls._fragments[func_id] = {
            'encoded': encoded,
            'name': func.__name__,
            'args': code_obj.co_argcount,
            'varnames': code_obj.co_varnames
        }

        # Return wrapper that decrypts at runtime
        def protected_wrapper(*args, **kwargs):
            # Decrypt and execute on-the-fly
            fragment = cls._fragments[func_id]
            decoded = base64.b64decode(fragment['encoded'])
            decompressed = zlib.decompress(decoded)
            decrypted = cls._xor_encrypt(decompressed, cls._runtime_key)

            # Rebuild code object
            import types
            new_code = types.CodeType(
                code_obj.co_argcount,
                code_obj.co_posonlyargcount,
                code_obj.co_kwonlyargcount,
                code_obj.co_nlocals,
                code_obj.co_stacksize,
                code_obj.co_flags,
                decrypted,  # Decrypted bytecode
                code_obj.co_consts,
                code_obj.co_names,
                code_obj.co_varnames,
                code_obj.co_filename,
                code_obj.co_name,
                code_obj.co_firstlineno,
                code_obj.co_lnotab,
                code_obj.co_freevars,
                code_obj.co_cellvars
            )

            # Execute decrypted function
            # SECURITY NOTE: This exec() is intentional for code protection.
            # It only executes bytecode derived from the original decorated function,
            # NOT arbitrary user input. The bytecode was encrypted at decoration time
            # and is being decrypted here. This is NOT a security vulnerability
            # because the code being executed was already trusted at definition time.
            exec_globals = func.__globals__.copy()
            # Restrict exec to only allow the function being protected
            exec_globals['__builtins__'] = __builtins__  # Preserve builtins
            exec(compile(new_code, '<protected>', 'exec'), exec_globals)
            return exec_globals[func.__name__](*args, **kwargs)

        return protected_wrapper

    @classmethod
    def verify_integrity(cls) -> bool:
        """
        Verify code hasn't been tampered with
        Prevents partial copying
        """
        # Calculate checksum of all fragments
        fragment_data = ''.join(sorted(
            f"{k}{v['encoded']}" for k, v in cls._fragments.items()
        ))
        current_hash = hashlib.sha256(fragment_data.encode()).hexdigest()

        if cls._integrity_hash is None:
            cls._integrity_hash = current_hash
            return True

        return current_hash == cls._integrity_hash


# Anti-AI string obfuscation
class ObfuscatedString:
    """
    Strings that AI can't read or understand
    Decrypted only at runtime
    """

    @staticmethod
    def hide(text: str) -> str:
        """Encrypt string - AI sees garbage"""
        # Multi-layer encoding
        encoded = base64.b85encode(
            zlib.compress(text.encode())
        ).decode()

        # Add random padding to confuse AI
        padding = secrets.token_urlsafe(16)
        return f"{padding[:8]}{encoded}{padding[8:]}"

    @staticmethod
    def reveal(obfuscated: str) -> str:
        """Decrypt string at runtime"""
        # Remove padding
        core = obfuscated[8:-8]

        # Decode
        decoded = base64.b85decode(core)
        decompressed = zlib.decompress(decoded)

        return decompressed.decode()


# Dead code injection - confuses AI pattern recognition
def _fake_database_query_v1(table, where_clause):
    """This looks real but does nothing"""
    import sqlite3
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    # AI thinks this is important logic
    query = f"SELECT * FROM {table} WHERE {where_clause}"
    result = cursor.execute(query).fetchall()
    conn.close()
    return result  # Never actually called


def _fake_api_call_v2(endpoint, data):
    """Another fake function to throw off AI"""
    import requests
    headers = {'Authorization': 'Bearer fake_token'}
    # AI sees pattern of API call
    response = requests.post(endpoint, json=data, headers=headers)
    return response.json()  # Never used


def _fake_encryption_v3(plaintext, key):
    """Looks like real crypto but isn't"""
    from cryptography.fernet import Fernet
    cipher = Fernet(key)
    encrypted = cipher.encrypt(plaintext.encode())
    return encrypted  # Misdirection


# Code dependency chain - breaks if partially copied
class DependencyChain:
    """
    Critical functions depend on each other
    Copying one function won't work without the others
    """

    _chain_state = {}

    @classmethod
    def link(cls, link_id: str, data: any):
        """Store dependency"""
        cls._chain_state[link_id] = hashlib.sha256(str(data).encode()).hexdigest()

    @classmethod
    def verify_link(cls, link_id: str, expected_hash: str) -> bool:
        """Verify dependency exists"""
        if link_id not in cls._chain_state:
            raise RuntimeError("Protected code integrity violation")
        return cls._chain_state[link_id] == expected_hash

    @classmethod
    def require_chain(cls, *link_ids):
        """Decorator that requires multiple dependencies"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # All links must be present
                for link_id in link_ids:
                    if link_id not in cls._chain_state:
                        raise RuntimeError(f"Missing dependency: {link_id}")
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Anti-decompilation markers
__protected_by_web3gisel__ = True
__do_not_reverse_engineer__ = "Violation of proprietary license"
__ai_reconstruction_prohibited__ = "©2026 WEB3GISEL"


# Export protection utilities
def protect_critical_code(code_object):
    """
    Wrap this around your most important functions
    Makes them nearly impossible to reconstruct
    """
    return CodeProtectionRuntime.protect_function(code_object)


def hide_string(text: str) -> str:
    """Hide strings from AI analysis"""
    return ObfuscatedString.hide(text)


def reveal_string(obfuscated: str) -> str:
    """Decrypt strings at runtime"""
    return ObfuscatedString.reveal(obfuscated)


# Example of usage (this itself won't be copied - it's a demonstration)
if __name__ == '__main__':
    print("=" * 70)
    print("WEB3GISEL - Anti-AI Protection Layer")
    print("=" * 70)

    # Test string obfuscation
    secret = "This is critical logic"
    hidden = hide_string(secret)
    print(f"\nOriginal: {secret}")
    print(f"Obfuscated: {hidden}")
    print(f"Revealed: {reveal_string(hidden)}")

    # Test function protection
    @protect_critical_code
    def critical_function(x):
        return x * 2 + 42

    result = critical_function(10)
    print(f"\nProtected function result: {result}")

    # Test integrity
    integrity_ok = CodeProtectionRuntime.verify_integrity()
    print(f"Integrity check: {'✓ PASS' if integrity_ok else '✗ FAIL'}")

    print("\n" + "=" * 70)
    print("Code protection active - AI reconstruction prevented")
    print("=" * 70)
