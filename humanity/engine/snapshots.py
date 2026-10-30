"""Versioned, validated JSON storage compatible with the original web worlds."""

import json
import math
import os
import types
from functools import lru_cache
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Union, get_args, get_origin, get_type_hints

from .models import (Beliefs, Conditions, Emotions, Needs, Personality, Position,
                     Relationship, Values, World)

MAX_SNAPSHOT_BYTES = 32_000_000
SAFE_INTEGER = 9_007_199_254_740_991


@lru_cache(maxsize=64)
def model_fields(model):
    return fields(model)


@lru_cache(maxsize=64)
def model_hints(model):
    return get_type_hints(model)


def camel_case(name: str) -> str:
    first, *rest = name.split("_")
    return first + "".join(word.title() for word in rest)


def to_wire(value):
    if is_dataclass(value):
        result = {}
        for f in model_fields(type(value)):
            item = getattr(value, f.name)
            if item is None and f.metadata.get("omit_none"):
                continue
            result[camel_case(f.name)] = to_wire(item)
        return result
    if isinstance(value, dict):
        # Extension namespaces and person IDs are arbitrary keys; never rename them.
        return {key: to_wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_wire(item) for item in value]
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        # Canonical JSON: restoring a typed float must not turn 0 into 0.0.
        return int(value)
    return value


def _decode(model, value, path="world"):
    if model is Any:
        return value
    origin = get_origin(model)
    if origin in (Union, types.UnionType):
        if value is None and type(None) in get_args(model):
            return None
        for choice in get_args(model):
            if choice is type(None):
                continue
            try:
                return _decode(choice, value, path)
            except (ValueError, TypeError):
                continue
        raise ValueError(f"Invalid value at {path}")
    if is_dataclass(model):
        if not isinstance(value, dict):
            raise ValueError(f"Expected object at {path}")
        hints = model_hints(model)
        result = {}
        for f in model_fields(model):
            key = camel_case(f.name)
            if key in value:
                result[f.name] = _decode(hints[f.name], value[key], f"{path}.{key}")
            elif f.default is MISSING and f.default_factory is MISSING:
                raise ValueError(f"Missing {path}.{key}")
        return model(**result)
    if origin is list:
        if not isinstance(value, list):
            raise ValueError(f"Expected array at {path}")
        return [_decode(get_args(model)[0], item, path) for item in value]
    if origin is dict:
        if not isinstance(value, dict):
            raise ValueError(f"Expected object at {path}")
        return {str(key): _decode(get_args(model)[1], item, path) for key, item in value.items()}
    if model is bool:
        if type(value) is not bool:
            raise ValueError(f"Expected boolean at {path}")
    elif model in (int, float):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"Expected finite number at {path}")
        if model is int and (not float(value).is_integer() or abs(value) > SAFE_INTEGER):
            raise ValueError(f"Expected safe integer at {path}")
        return model(value)
    elif model is str and (not isinstance(value, str) or len(value) > 100_000):
        raise ValueError(f"Expected bounded string at {path}")
    return value


def _unit_record(record):
    return all(0 <= getattr(record, f.name) <= 1 for f in fields(record))


def validate_world(world: World):
    if world.schema_version != 1 or len(world.seed) >= 200:
        raise ValueError("Unsupported world schema or seed")
    if not 2 <= len(world.agents) <= 300 or not 0 <= world.rng <= 0xFFFFFFFF or world.tick < 0:
        raise ValueError("Invalid population, random state, or clock")
    if world.next_event_id < 1 or world.next_memory_id < 1:
        raise ValueError("Invalid event or memory sequence")
    if not _unit_record(world.settings):
        raise ValueError("Invalid world conditions")
    if len(world.events) > 400 or len(world.pending_events) > 1000 or len(world.history) > 240:
        raise ValueError("World history exceeds storage bounds")
    ids = {agent.id for agent in world.agents}
    if len(ids) != len(world.agents) or any(not person_id or len(person_id) >= 80 for person_id in ids):
        raise ValueError("Duplicate or invalid person identifiers")
    if len(set(world.system_ids)) != len(world.system_ids):
        raise ValueError("Duplicate system identifiers")
    for agent in world.agents:
        for record in (agent.traits, agent.initial_traits, agent.values, agent.beliefs, agent.needs, agent.emotions, agent.position):
            if not _unit_record(record):
                raise ValueError(f"Out-of-range state for {agent.id}")
        if not 0 <= agent.public_state.warmth <= 1 or not 0 <= agent.identity.age <= 150:
            raise ValueError("Invalid identity or public state")
        if len(agent.memories) > 82:
            raise ValueError("Memory exceeds storage bounds")
        for other_id, relation in agent.relationships.items():
            if other_id not in ids or not _unit_record(relation):
                raise ValueError("Invalid directed relationship")
    for event in world.events + world.pending_events:
        if any(person_id not in ids for person_id in event.observers):
            raise ValueError("Invalid event observer")
        if event.actor_id is not None and event.actor_id not in ids:
            raise ValueError("Invalid event actor")
        if event.target_id is not None and event.target_id not in ids:
            raise ValueError("Invalid event target")


def dumps(world: World) -> str:
    return json.dumps({"format": "humanity.sh", "version": 1, "world": to_wire(world)}, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def loads(text: str) -> World:
    if not isinstance(text, str) or len(text.encode("utf-8")) >= MAX_SNAPSHOT_BYTES:
        raise ValueError("Snapshot is too large")
    data = json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Invalid constant: {value}")))
    if not isinstance(data, dict) or data.get("format") != "humanity.sh" or data.get("version") != 1:
        raise ValueError("Unsupported snapshot format")
    raw_world = data.get("world")
    if not isinstance(raw_world, dict) or raw_world.get("_projection"):
        raise ValueError("A view projection is not a world snapshot")
    world = _decode(World, raw_world)
    validate_world(world)
    return world


def atomic_write(path: Path, text: str):
    """Replace a save only after its complete contents have reached the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".humanity-", delete=False) as file:
            temporary = Path(file.name)
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
