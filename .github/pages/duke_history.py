"""Generated validation snapshot; edit the sandbox source and run export_duke_validator.py.
Source: kakurai49/sandbox@47419e615aada02963da17bd97f422da7ab216d8/projects/agent2/src/agent_designer/learning_dashboard_history.py
Source SHA-256: 243121bc00e6c63edb1ba857db0607e40bc60a6515d4c2df48cb97b3f7a102af
"""

from __future__ import annotations
from datetime import date
from hashlib import sha256
import json
import re


SCHEMA = "learning-history/v1"


STAGES = {"motivation", "preparation", "experience", "review", "correction", "closure", "followup"}


STATUSES = {"reported", "recorded", "planned", "unconfirmed", "owner_closed"}


DATE_KINDS = {"occurred", "recorded", "planned", "unknown"}


HASH = re.compile(r"[a-f0-9]{64}\Z")


IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z")


def require(condition, message):
    if not condition:
        raise ValueError("Learning history: " + message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return sha256(canonical(value)).hexdigest()


def text(value, limit=2400):
    require(isinstance(value, str) and value.strip() and len(value) <= limit,
            "bounded text required")
    require(not any(ord(c) < 32 and c not in "\n\t" for c in value), "control character")
    return value


def check_date(value, kind):
    require(kind in DATE_KINDS, "unknown date kind")
    require((value is None) == (kind == "unknown"), "date meaning is required")
    if value is not None:
        require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "ISO date required")
        date.fromisoformat(value)


def validate_history(history):
    require(isinstance(history, dict) and set(history) == {"schema", "version", "coverage", "entries", "gaps", "notice"},
            "public history fields")
    require(history["schema"] == SCHEMA and history["coverage"] in {"reviewed", "partial"}, "history schema or coverage")
    require(isinstance(history["version"], str) and HASH.fullmatch(history["version"]), "history version")
    require(history["version"] == digest({k: v for k, v in history.items() if k != "version"}), "history version mismatch")
    require(isinstance(history["entries"], list) and len(history["entries"]) <= 160, "history entry budget")
    seen = set()
    for entry in history["entries"]:
        require(isinstance(entry, dict) and set(entry) == {"id", "date", "date_kind", "stage", "status", "title", "body", "source_labels", "source_hashes"},
                "public entry fields")
        require(isinstance(entry["id"], str) and IDENTIFIER.fullmatch(entry["id"]) and entry["id"] not in seen,
                "entry identity")
        seen.add(entry["id"])
        check_date(entry["date"], entry["date_kind"])
        require(entry["stage"] in STAGES and entry["status"] in STATUSES, "entry stage or status")
        require(entry["date_kind"] != "planned" or entry["status"] in {"planned", "unconfirmed"}, "plan cannot be achievement")
        text(entry["title"], 160)
        text(entry["body"])
        labels, hashes = entry["source_labels"], entry["source_hashes"]
        require(isinstance(labels, list) and isinstance(hashes, list) and 1 <= len(labels) == len(hashes) <= 12,
                "paired source references required")
        for label in labels:
            text(label, 160)
        require(all(isinstance(v, str) and HASH.fullmatch(v) for v in hashes), "source hashes required")
    require(isinstance(history["gaps"], list) and len(history["gaps"]) <= 30, "gap budget")
    for gap in history["gaps"]:
        text(gap, 700)
    text(history["notice"], 700)
    return history
