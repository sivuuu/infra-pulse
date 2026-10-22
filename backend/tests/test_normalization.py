import pytest
from runtime.podman_adapter import parse_bytes, parse_percent

def test_parse_bytes_various_units():
    assert parse_bytes("0B") == 0
    assert parse_bytes("500B") == 500
    assert parse_bytes("1.5kB") == 1500
    assert parse_bytes("10KiB") == 10240
    assert parse_bytes("12.5MB") == 12500000
    assert parse_bytes("4MiB") == 4 * 1024 * 1024
    assert parse_bytes("2GB") == 2000000000
    assert parse_bytes("1GiB") == 1073741824

def test_parse_bytes_invalid_or_none():
    assert parse_bytes(None) is None
    assert parse_bytes("--") is None
    assert parse_bytes("") is None
    assert parse_bytes("invalid_text") == 0

def test_parse_percent():
    assert parse_percent("0.00%") == 0.0
    assert parse_percent("14.5%") == 14.5
    assert parse_percent("99.99%") == 99.99
    assert parse_percent(None) is None
    assert parse_percent("--") is None
    assert parse_percent("unknown") == 0.0
