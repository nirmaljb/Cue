"""Standalone Neo4j connectivity checker.

Usage:
    python backend/scripts/check_neo4j.py
    python backend/scripts/check_neo4j.py --env-file /path/to/Neo4j-credentials.txt
"""

from __future__ import annotations

import argparse
import random
import struct
import logging
import os
import socket
import ssl
import sys
from pathlib import Path
from urllib.parse import urlparse

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ConfigurationError, Neo4jError, ServiceUnavailable


DEFAULT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_config(env_file: Path) -> dict[str, str]:
    file_values = parse_env_file(env_file)
    merged = {**file_values, **os.environ}

    return {
        "uri": merged.get("NEO4J_URI", ""),
        "user": merged.get("NEO4J_USER") or merged.get("NEO4J_USERNAME", ""),
        "password": merged.get("NEO4J_PASSWORD", ""),
        "database": merged.get("NEO4J_DATABASE", ""),
    }


def mask(value: str) -> str:
    if not value:
        return "<missing>"
    return f"<set, {len(value)} chars>"


def configure_certifi() -> str | None:
    if os.environ.get("SSL_CERT_FILE"):
        return os.environ["SSL_CERT_FILE"]

    paths = ssl.get_default_verify_paths()
    if paths.cafile and Path(paths.cafile).exists():
        return paths.cafile

    try:
        import certifi
    except ImportError:
        return None

    os.environ["SSL_CERT_FILE"] = certifi.where()
    return os.environ["SSL_CERT_FILE"]


def resolve_host(uri: str) -> tuple[str, list[str]]:
    parsed = urlparse(uri)
    host = parsed.hostname
    if not host:
        raise ValueError("NEO4J_URI does not contain a hostname")

    port = parsed.port or 7687
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addresses = sorted({info[4][0] for info in infos})
    return host, addresses


def encode_dns_name(host: str) -> bytes:
    return b"".join(bytes([len(part)]) + part.encode("ascii") for part in host.split(".")) + b"\0"


def skip_dns_name(packet: bytes, offset: int) -> int:
    while True:
        length = packet[offset]
        if length & 0xC0 == 0xC0:
            return offset + 2
        if length == 0:
            return offset + 1
        offset += length + 1


def public_dns_lookup(host: str, server: str = "1.1.1.1") -> list[str]:
    query_id = random.randint(0, 65535)
    question = encode_dns_name(host) + struct.pack("!HH", 1, 1)
    packet = struct.pack("!HHHHHH", query_id, 0x0100, 1, 0, 0, 0) + question

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)
        sock.sendto(packet, (server, 53))
        response, _ = sock.recvfrom(512)

    (
        response_id,
        _flags,
        question_count,
        answer_count,
        _authority_count,
        _additional_count,
    ) = struct.unpack("!HHHHHH", response[:12])
    if response_id != query_id:
        return []

    offset = 12
    for _ in range(question_count):
        offset = skip_dns_name(response, offset) + 4

    addresses = []
    for _ in range(answer_count):
        offset = skip_dns_name(response, offset)
        record_type, record_class, _ttl, record_length = struct.unpack(
            "!HHIH", response[offset : offset + 10]
        )
        offset += 10
        record_data = response[offset : offset + record_length]
        offset += record_length
        if record_type == 1 and record_class == 1 and record_length == 4:
            addresses.append(socket.inet_ntoa(record_data))

    return sorted(set(addresses))


def check_neo4j(config: dict[str, str], debug: bool) -> None:
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    uri = config["uri"]
    user = config["user"]
    password = config["password"]
    database = config["database"] or None

    missing = [
        name
        for name, value in (
            ("NEO4J_URI", uri),
            ("NEO4J_USER or NEO4J_USERNAME", user),
            ("NEO4J_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing required value(s): {', '.join(missing)}")

    ca_file = configure_certifi()

    print("Neo4j config", flush=True)
    print(f"  uri: {uri}", flush=True)
    print(f"  user: {user}", flush=True)
    print(f"  password: {mask(password)}", flush=True)
    print(f"  database: {database or '<driver default>'}", flush=True)
    print(f"  SSL_CERT_FILE: {ca_file or '<not configured>'}", flush=True)

    host, addresses = resolve_host(uri)
    print(f"  DNS: {host} -> {', '.join(addresses)}", flush=True)

    driver = GraphDatabase.driver(
        uri,
        auth=(user, password),
        connection_timeout=10,
        max_transaction_retry_time=5,
    )

    try:
        with driver.session(database=database) as session:
            result = session.run("RETURN 1 AS ok")
            ok = result.single(strict=True)["ok"]
        print(f"\nOK: Neo4j query succeeded: RETURN 1 AS ok -> {ok}", flush=True)
    finally:
        driver.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Neo4j Aura connectivity.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help=f"Path to .env or Neo4j credential download. Default: {DEFAULT_ENV_FILE}",
    )
    parser.add_argument("--debug", action="store_true", help="Enable Neo4j driver debug logs.")
    args = parser.parse_args()

    print(f"Reading credentials from: {args.env_file}", flush=True)
    config = get_config(args.env_file)

    try:
        check_neo4j(config, args.debug)
    except socket.gaierror as exc:
        uri = config.get("uri", "")
        host = urlparse(uri).hostname or "<unknown>"
        print(f"\nFAIL: system DNS lookup failed for {host}: {exc}", file=sys.stderr)
        try:
            public_addresses = public_dns_lookup(host)
        except Exception as dns_exc:
            print(f"Cloudflare DNS check also failed: {dns_exc}", file=sys.stderr)
        else:
            if public_addresses:
                print(
                    f"Cloudflare DNS resolves it to: {', '.join(public_addresses)}",
                    file=sys.stderr,
                )
                print(
                    "This points to a local DNS resolver issue, not bad Neo4j credentials.",
                    file=sys.stderr,
                )
            else:
                print("Cloudflare DNS did not return an A record either.", file=sys.stderr)
        return 2
    except AuthError as exc:
        print(f"\nFAIL: Authentication failed: {exc}", file=sys.stderr)
        return 3
    except ConfigurationError as exc:
        print(f"\nFAIL: Neo4j configuration error: {exc}", file=sys.stderr)
        return 4
    except ServiceUnavailable as exc:
        print(f"\nFAIL: Neo4j service unavailable: {exc}", file=sys.stderr)
        return 5
    except Neo4jError as exc:
        print(f"\nFAIL: Neo4j error: {exc}", file=sys.stderr)
        return 6
    except Exception as exc:
        print(f"\nFAIL: Unexpected error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
