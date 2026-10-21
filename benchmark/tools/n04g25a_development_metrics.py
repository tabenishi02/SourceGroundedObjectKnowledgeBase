"""Development-only G-25A metrics; no final-confirmation input path exists."""

from __future__ import annotations

from collections import Counter

ROLES = {
    "SOURCE_FACT_CONTENT": "source_fact",
    "INTERPRETATION_CONTENT": "interpretation",
    "CREATIVE_CONTENT": "creative_addition",
    "CONTEXT_LIMIT_CONTENT": "context_limit",
}


def model_inputs(rows):
    return [row["text"] for row in rows]


def predict_labels(probabilities, classes, policy):
    labels = []
    for vector in probabilities:
        if len(vector) != len(classes) or len(vector) < 2:
            raise ValueError("Invalid probability/class mapping")
        if any(not 0 <= p <= 1 for p in vector) or abs(sum(vector) - 1) > 1e-4:
            raise ValueError("Invalid normalized probabilities")
        ranked = sorted(range(len(vector)), key=lambda i: (-vector[i], i))
        top, second = ranked[:2]
        labels.append(
            "AMBIGUOUS"
            if vector[top] < policy["min_confidence"]
            or vector[top] - vector[second] < policy["min_margin"]
            else classes[top]
        )
    return labels


def metrics(task, rows, predictions, classes):
    if len(rows) != len(predictions) or any(p not in classes for p in predictions):
        raise ValueError("Missing/malformed predictions")
    confusion, families = Counter(), {}
    critical = required = 0
    for row, pred in zip(rows, predictions):
        gold = row["label"]
        confusion[gold, pred] += 1
        bucket = families.setdefault(row["family_id"], Counter())
        bucket[f"{gold}->{pred}"] += 1
        if task == "atomicity":
            critical += bool(
                row["critical_for_safety"] and gold == "NON_ATOMIC" and pred == "ATOMIC"
            )
            required += bool(row["required"] and gold == "ATOMIC" and pred != "ATOMIC")
        elif task == "content_type":
            role = ROLES.get(pred)
            critical += bool(
                row["critical_for_safety"] and role in row["critical_incompatible_expected_roles"]
            )
            required += (
                sum(role != expected for expected in row["compatible_expected_roles"])
                if row["required"]
                else 0
            )
        else:
            raise ValueError("Unknown task")
    recalls, f1 = {}, []
    for label in classes:
        tp = confusion[label, label]
        actual = sum(v for (g, _), v in confusion.items() if g == label)
        predicted = sum(v for (_, p), v in confusion.items() if p == label)
        recalls[label] = tp / actual if actual else 0.0
        f1.append(2 * tp / (actual + predicted) if actual + predicted else 0.0)
    nonamb = [p for r, p in zip(rows, predictions) if r["label"] != "AMBIGUOUS"]
    return {
        "critical_false_pass": critical,
        "required_valid_false_reject": required,
        "per_class_recall": recalls,
        "macro_f1": sum(f1) / len(f1),
        "mean_class_recall": sum(recalls.values()) / len(recalls),
        "ambiguity_rate": predictions.count("AMBIGUOUS") / len(rows),
        "nonambiguous_ambiguity_rate": nonamb.count("AMBIGUOUS") / len(nonamb),
        "confusion": {f"{g}->{p}": n for (g, p), n in sorted(confusion.items())},
        "confusion_by_family": {k: dict(v) for k, v in families.items()},
    }


def fit_policy(task, rows, probabilities, classes, manifest):
    if not rows or any(r["split"] != "validation" for r in rows):
        raise ValueError("Policy fitting requires validation only")
    best = None
    for confidence in manifest["abstention"]["min_confidence_grid"]:
        for margin in manifest["abstention"]["min_margin_grid"]:
            policy = {"min_confidence": confidence, "min_margin": margin}
            result = metrics(
                task,
                rows,
                predict_labels(probabilities, classes, policy),
                manifest["tasks"][task]["output_classes"],
            )
            key = (
                result["critical_false_pass"],
                result["required_valid_false_reject"],
                -result["macro_f1"],
                confidence,
                margin,
            )
            if best is None or key < best[0]:
                best = key, policy, result
    return {"policy": best[1], "validation_metrics": best[2], "fit_partition": "validation"}


def repeatability(rows, repeats):
    if len(repeats) != 3 or any(len(preds) != len(rows) for preds in repeats):
        raise ValueError("Three complete repeats required")
    return sum(
        len({preds[i] for preds in repeats}) != 1
        for i, row in enumerate(rows)
        if row["required"] or row["critical_for_safety"]
    )
