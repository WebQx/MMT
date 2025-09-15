#!/usr/bin/env python3
"""Generate strong secrets for production deployment.
Outputs a ready-to-paste .env snippet with:
 - INTERNAL_JWT_SECRET (>=48 chars)
 - ADMIN_API_KEY
 - Optional AES field encryption keys
 - Optional RSA keypair for internal JWT (if --rsa)
 - Optional vault-style base64 keys for rotation sets
Usage:
  python scripts/generate_secrets.py --all --rsa --encryption 2
"""
from __future__ import annotations
import argparse, secrets, base64, sys, textwrap
from pathlib import Path
from typing import List


def rand_token(length: int = 48) -> str:
    # urlsafe + ensure length
    t = secrets.token_urlsafe(length)
    # token_urlsafe(length) returns ~ 1.3 * length chars; trim/pad
    if len(t) < length:
        t += secrets.token_urlsafe(length - len(t))
    return t[:length]

def gen_aes_key() -> str:
    # 32 bytes (256-bit) base64
    return base64.b64encode(secrets.token_bytes(32)).decode()

def gen_rsa_keypair():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        print("[!] Install cryptography: pip install cryptography", file=sys.stderr)
        sys.exit(2)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv_pem, pub_pem


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rsa', action='store_true', help='Generate RSA key pair for internal JWT')
    p.add_argument('--encryption', type=int, default=0, help='Number of field encryption keys to generate (0 disables)')
    p.add_argument('--all', action='store_true', help='Generate a comprehensive recommended set (shorthand for --rsa --encryption 2)')
    args = p.parse_args()
    if args.all:
        args.rsa = True
        if args.encryption == 0:
            args.encryption = 2

    internal_jwt_secret = rand_token(48)
    admin_api_key = rand_token(40)

    encryption_lines: List[str] = []
    primary_id = None
    if args.encryption > 0:
        for i in range(1, args.encryption + 1):
            kid = f"k{i}"
            key = gen_aes_key()
            encryption_lines.append(f"{kid}:{key}")
        primary_id = 'k1'

    rsa_priv = rsa_pub = None
    if args.rsa:
        rsa_priv, rsa_pub = gen_rsa_keypair()

    # Build snippet
    snippet = []
    snippet.append('# --- Generated Secrets (DO NOT COMMIT) ---')
    snippet.append(f'INTERNAL_JWT_SECRET={internal_jwt_secret}')
    snippet.append(f'ADMIN_API_KEY={admin_api_key}')
    if encryption_lines:
        snippet.append(f'ENABLE_FIELD_ENCRYPTION=1')
        snippet.append(f'ENCRYPTION_KEYS={','.join(encryption_lines)}')
        snippet.append(f'PRIMARY_ENCRYPTION_KEY_ID={primary_id}')
    if rsa_priv and rsa_pub:
        snippet.append('USE_RSA_INTERNAL_JWT=1')
        snippet.append('INTERNAL_JWT_PRIVATE_KEY_PEM="""')
        snippet.append(rsa_priv.rstrip())
        snippet.append('"""')
        snippet.append('INTERNAL_JWT_PUBLIC_KEY_PEM="""')
        snippet.append(rsa_pub.rstrip())
        snippet.append('"""')
    out = '\n'.join(snippet)
    print(out)

if __name__ == '__main__':
    main()
