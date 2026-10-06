"""Versioned lossless key compression; canonical storage remains unchanged."""

from copy import deepcopy

from jsonschema import Draft202012Validator

KEYS = {
    "fragments": "f",
    "assessments": "a",
    "entity_candidates": "c",
    "subject": "s",
    "facet": "t",
    "epistemic_type": "e",
    "evidence_strength": "h",
    "asserted_by": "b",
    "temporal_context": "v",
    "resolved_statement": "r",
    "atomic_claim": "m",
    "evidence_ids": "i",
    "conflict_group": "g",
    "quote_id": "q",
    "evidence_id": "d",
    "discard_reason": "x",
    "story_phase": "p",
    "valid_from": "u",
    "valid_to": "w",
    "work_context": "k",
    "temporal_note": "n",
    "name": "l",
    "type": "y",
    "aliases": "z",
}


def rename(value, mapping):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            target = mapping.get(key, key)
            if target in result:
                raise ValueError("Transport key collision")
            result[target] = rename(item, mapping)
        return result
    if isinstance(value, list):
        return [rename(item, mapping) for item in value]
    return value


def compact_schema(schema):
    result = deepcopy(schema)
    if "properties" in result:
        result["properties"] = {
            KEYS.get(k, k): compact_schema(v) for k, v in result["properties"].items()
        }
    if "required" in result:
        result["required"] = [KEYS.get(k, k) for k in result["required"]]
    if isinstance(result.get("items"), dict):
        result["items"] = compact_schema(result["items"])
    return result


def decode(value, schema):
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        raise ValueError("Invalid compact transport at " + "/".join(map(str, errors[0].path)))
    return rename(value, {v: k for k, v in KEYS.items()})


def instructions():
    return (
        "\nTransport compact-keys-v1: return the exact wire schema. "
        "Use these short keys instead of canonical keys; values and meanings are unchanged: "
        + ", ".join(f"{v}={k}" for k, v in KEYS.items())
    )
