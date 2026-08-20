"""Canonical serialization and SHA-256 cryptographic hashing."""

import hashlib
import json
from datetime import date, datetime
from typing import Any
import uuid


def json_serializer(obj: Any) -> Any:
    """Helper for non-standard JSON types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return obj.model_dump()
    return str(obj)


def canonical_json_dumps(data: Any) -> str:
    """Returns a deterministic, sorted, compact JSON string."""
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(',', ':'),
        default=json_serializer
    )


def sha256_hash(text: str) -> str:
    """Calculates SHA-256 hexadecimal digest for given text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def hash_canonical_payload(payload: Any) -> str:
    """Computes SHA-256 hash of canonically serialized JSON payload."""
    canonical_str = canonical_json_dumps(payload)
    return sha256_hash(canonical_str)


def calculate_current_hash(
    previous_hash: str,
    payload_hash: str,
    entity_type: str,
    entity_id: str,
    action: str
) -> str:
    """Computes the hash-chain node hash combining previous_hash and current metadata."""
    combined_raw = f"{previous_hash}|{payload_hash}|{entity_type}|{entity_id}|{action}"
    return sha256_hash(combined_raw)

