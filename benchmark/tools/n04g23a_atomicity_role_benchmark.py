"""Run the N-04G-23A Atomicity / Role Gold Benchmark against local LM Studio.

This diagnostic intentionally evaluates only V2-style atomicity and semantic-role
classification. It does not invoke retrieval, MiniCheck, source-fact entailment,
material sufficiency, or rendering.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ATOMICITY_VERDICTS = {"ATOMIC", "NON_ATOMIC", "INDETERMINATE"}
ROLE_VERDICTS = {"ROLE_VALID", "ROLE_VIOLATION", "INDETERMINATE"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _substitute(template: str, case: dict[str, Any]) -> str:
    result = template
    for key in ("text", "semantic_role", "purpose", "presentation_role"):
        result = result.replace("${" + key + "}", str(case.get(key, "")))
    return result


def _post_json(endpoint: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer lm-studio"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"LM Studio request failed: {exc}") from exc
    return json.loads(raw)


def _message_content(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LM Studio response does not contain choices[0].message.content") from exc
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected message content type: {type(content).__name__}")
    return content


def _chat_call(
    *,
    endpoint: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response_format: dict[str, Any],
    temperature: float,
    max_tokens: int,
    seed: int,
    timeout: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "seed": seed,
        "stream": False,
        "response_format": response_format,
    }
    started = time.perf_counter()
    response = _post_json(endpoint, payload, timeout)
    elapsed = time.perf_counter() - started
    content = _message_content(response)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Structured response was not JSON: {content!r}") from exc
    return {
        "request": payload,
        "response_content": content,
        "parsed": parsed,
        "elapsed_seconds": elapsed,
        "usage": response.get("usage"),
    }


def _validate_joint(parsed: dict[str, Any]) -> tuple[str, str]:
    atomicity = parsed.get("atomicity_verdict")
    role = parsed.get("role_boundary_verdict")
    if atomicity not in ATOMICITY_VERDICTS:
        raise RuntimeError(f"Unexpected atomicity verdict: {atomicity!r}")
    if role not in ROLE_VERDICTS:
        raise RuntimeError(f"Unexpected role verdict: {role!r}")
    return atomicity, role


def _run_joint(
    *,
    case: dict[str, Any],
    profile: dict[str, Any],
    endpoint: str,
    model: str,
    runtime: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    call = _chat_call(
        endpoint=endpoint,
        model=model,
        system_prompt=profile["system_prompt"],
        user_prompt=_substitute(profile["user_prompt_template"], case),
        response_format=profile["response_format"],
        temperature=float(runtime["temperature"]),
        max_tokens=int(runtime["max_tokens"]),
        seed=int(runtime["seed"]),
        timeout=timeout,
    )
    atomicity, role = _validate_joint(call["parsed"])
    call["atomicity_verdict"] = atomicity
    call["role_boundary_verdict"] = role
    return call


def _run_split(
    *,
    case: dict[str, Any],
    profile: dict[str, Any],
    endpoint: str,
    model: str,
    runtime: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    atomic_profile = profile["atomicity"]
    role_profile = profile["role"]
    atomic_call = _chat_call(
        endpoint=endpoint,
        model=model,
        system_prompt=atomic_profile["system_prompt"],
        user_prompt=_substitute(atomic_profile["user_prompt_template"], case),
        response_format=atomic_profile["response_format"],
        temperature=float(runtime["temperature"]),
        max_tokens=int(runtime["max_tokens"]),
        seed=int(runtime["seed"]),
        timeout=timeout,
    )
    role_call = _chat_call(
        endpoint=endpoint,
        model=model,
        system_prompt=role_profile["system_prompt"],
        user_prompt=_substitute(role_profile["user_prompt_template"], case),
        response_format=role_profile["response_format"],
        temperature=float(runtime["temperature"]),
        max_tokens=int(runtime["max_tokens"]),
        seed=int(runtime["seed"]),
        timeout=timeout,
    )
    atomicity = atomic_call["parsed"].get("atomicity_verdict")
    role = role_call["parsed"].get("role_boundary_verdict")
    if atomicity not in ATOMICITY_VERDICTS:
        raise RuntimeError(f"Unexpected atomicity verdict: {atomicity!r}")
    if role not in ROLE_VERDICTS:
        raise RuntimeError(f"Unexpected role verdict: {role!r}")
    return {
        "atomicity_call": atomic_call,
        "role_call": role_call,
        "atomicity_verdict": atomicity,
        "role_boundary_verdict": role,
        "elapsed_seconds": atomic_call["elapsed_seconds"] + role_call["elapsed_seconds"],
    }


def _confusion(results: list[dict[str, Any]], gold_key: str, observed_key: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        expected = result["gold"][gold_key]
        for repeat in result["repeats"]:
            observed = repeat[observed_key]
            counts[f"{expected}->{observed}"] += 1
    return dict(sorted(counts.items()))


def _score(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    critical_atomicity_false_pass: list[str] = []
    critical_role_false_pass: list[str] = []
    required_atomicity_false_reject: list[str] = []
    required_role_false_reject: list[str] = []
    repeatability_failures: list[str] = []
    required_repeatability_failures: list[str] = []
    exact_match_failures: list[str] = []
    total_predictions = 0
    indeterminate_predictions = 0

    for result in case_results:
        expected_atomicity = result["gold"]["atomicity"]
        expected_role = result["gold"]["role_boundary"]
        repeats = result["repeats"]
        atomicity_values = [item["atomicity_verdict"] for item in repeats]
        role_values = [item["role_boundary_verdict"] for item in repeats]

        total_predictions += 2 * len(repeats)
        indeterminate_predictions += sum(value == "INDETERMINATE" for value in atomicity_values)
        indeterminate_predictions += sum(value == "INDETERMINATE" for value in role_values)

        unstable = len(set(atomicity_values)) != 1 or len(set(role_values)) != 1
        if unstable:
            repeatability_failures.append(result["case_id"])
            if result["required"]:
                required_repeatability_failures.append(result["case_id"])

        if any(value != expected_atomicity for value in atomicity_values) or any(
            value != expected_role for value in role_values
        ):
            exact_match_failures.append(result["case_id"])

        if result["critical_for_safety"] and expected_atomicity == "NON_ATOMIC":
            if any(value == "ATOMIC" for value in atomicity_values):
                critical_atomicity_false_pass.append(result["case_id"])
        if result["critical_for_safety"] and expected_role == "ROLE_VIOLATION":
            if any(value == "ROLE_VALID" for value in role_values):
                critical_role_false_pass.append(result["case_id"])

        if result["required"] and expected_atomicity == "ATOMIC":
            if any(value != "ATOMIC" for value in atomicity_values):
                required_atomicity_false_reject.append(result["case_id"])
        if result["required"] and expected_role == "ROLE_VALID":
            if any(value != "ROLE_VALID" for value in role_values):
                required_role_false_reject.append(result["case_id"])

    safety_gate = not critical_atomicity_false_pass and not critical_role_false_pass
    required_valid_gate = not required_atomicity_false_reject and not required_role_false_reject
    repeatability_gate = not required_repeatability_failures

    return {
        "critical_atomicity_false_pass_cases": critical_atomicity_false_pass,
        "critical_role_false_pass_cases": critical_role_false_pass,
        "required_atomicity_false_reject_cases": required_atomicity_false_reject,
        "required_role_false_reject_cases": required_role_false_reject,
        "repeatability_failure_cases": repeatability_failures,
        "required_repeatability_failure_cases": required_repeatability_failures,
        "exact_match_failure_cases": exact_match_failures,
        "indeterminate_rate": (indeterminate_predictions / total_predictions if total_predictions else 0.0),
        "atomicity_confusion": _confusion(case_results, "atomicity", "atomicity_verdict"),
        "role_confusion": _confusion(case_results, "role_boundary", "role_boundary_verdict"),
        "gates": {
            "safety_gate": safety_gate,
            "required_valid_gate": required_valid_gate,
            "repeatability_gate": repeatability_gate,
            "candidate_viable": safety_gate and required_valid_gate and repeatability_gate,
        },
    }


def _profile_by_id(profile_set: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for profile in profile_set.get("profiles", []):
        if profile.get("profile_id") == profile_id:
            return profile
    raise ValueError(f"Unknown profile_id: {profile_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234/v1/chat/completions")
    parser.add_argument("--model", default="sgokb-n04-phi4")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    if args.repeats < 1:
        raise ValueError("--repeats must be >= 1")

    corpus = _load_json(args.corpus)
    profile_set = _load_json(args.profiles)
    profile = _profile_by_id(profile_set, args.profile_id)
    if profile.get("status") != "ready":
        raise RuntimeError(
            f"Profile {args.profile_id!r} is not ready: {profile.get('status')!r}. "
            "Import exact evidence before running this profile."
        )

    runtime = profile_set["runtime"]
    case_results: list[dict[str, Any]] = []
    started = time.time()

    for case in corpus.get("cases", []):
        repeats: list[dict[str, Any]] = []
        for repeat_index in range(args.repeats):
            if profile["mode"] == "joint":
                observed = _run_joint(
                    case=case,
                    profile=profile,
                    endpoint=args.endpoint,
                    model=args.model,
                    runtime=runtime,
                    timeout=args.timeout,
                )
            elif profile["mode"] == "split":
                observed = _run_split(
                    case=case,
                    profile=profile,
                    endpoint=args.endpoint,
                    model=args.model,
                    runtime=runtime,
                    timeout=args.timeout,
                )
            else:
                raise RuntimeError(f"Unsupported profile mode: {profile['mode']!r}")
            observed["repeat_index"] = repeat_index + 1
            repeats.append(observed)

        case_results.append(
            {
                "case_id": case["case_id"],
                "origin": case.get("origin"),
                "required": bool(case.get("required")),
                "critical_for_safety": bool(case.get("critical_for_safety")),
                "gold": case["gold"],
                "repeats": repeats,
            }
        )

    result = {
        "schema_version": "sgokb.n04g23a-atomicity-role-result/1",
        "benchmark_id": corpus.get("benchmark_id"),
        "profile_set_id": profile_set.get("profile_set_id"),
        "profile_id": args.profile_id,
        "corpus_path": args.corpus.as_posix(),
        "corpus_sha256": _sha256(args.corpus),
        "profiles_path": args.profiles.as_posix(),
        "profiles_sha256": _sha256(args.profiles),
        "model": args.model,
        "runtime": runtime,
        "repeats": args.repeats,
        "started_epoch": started,
        "finished_epoch": time.time(),
        "cases": case_results,
        "metrics": _score(case_results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
