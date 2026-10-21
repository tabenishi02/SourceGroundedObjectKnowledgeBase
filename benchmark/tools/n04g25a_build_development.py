"""Build independent, design-reviewed neutral development families; no confirmation data access."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROLES = ("source_fact", "interpretation", "creative_addition", "context_limit")
COMPATIBLE = dict(
    zip(
        (
            "SOURCE_FACT_CONTENT",
            "INTERPRETATION_CONTENT",
            "CREATIVE_CONTENT",
            "CONTEXT_LIMIT_CONTENT",
        ),
        ROLES,
    )
)
# Each source bank is independent and belongs to exactly one partition. All its
# lexical variants, cross-task uses and minimal-pair derivatives stay there.
BANKS = {
    "train": [
        "ceramic valve|closed|copper pipe|laboratory|metal|round",
        "linen banner|folded|wooden pole|gallery|fabric|narrow",
        "brass compass|stationary|glass lens|observatory|instrument|small",
        "oak crate|empty|iron trolley|warehouse|container|square",
        "paper ledger|sealed|wax stamp|archive|record|heavy",
        "clay jug|intact|stone basin|pottery room|vessel|tall",
        "rubber belt|loose|steel pulley|workshop|component|wide",
        "marble token|polished|felt pouch|museum|object|smooth",
        "wool cover|dry|leather strap|storeroom|textile|soft",
        "tin whistle|silent|reed flute|music room|instrument|short",
    ],
    "validation": [
        "aluminum latch|locked|bronze hinge|boathouse|fitting|slender",
        "bamboo screen|upright|silk cord|conservatory|partition|light",
        "porcelain dial|blank|silver needle|clock room|display|broad",
        "felt sleeve|open|plastic tube|packing room|cover|thick",
        "maple tray|level|granite tile|kitchen|utensil|flat",
        "velvet ribbon|knotted|nickel clasp|costume room|fastener|long",
        "resin prism|clear|ceramic bead|optics room|specimen|angular",
        "canvas panel|taut|teak frame|studio|surface|large",
        "cork stopper|damp|amber bottle|cellar|seal|porous",
        "pewter bell|cracked|hemp rope|tower|sounder|hollow",
    ],
    "selection": [
        "slate marker|tilted|birch stake|garden|sign|dark",
        "cotton sail|furled|ash mast|dock|rigging|white",
        "quartz plate|clean|mica sheet|inspection bay|sample|thin",
        "nylon net|tangled|alloy ring|equipment shed|mesh|coarse",
        "willow basket|full|flax mat|market stall|carrier|woven",
        "ebony handle|detached|ivory knob|repair bay|grip|curved",
        "acrylic shield|transparent|foam pad|test chamber|barrier|rigid",
        "platinum pin|bent|jade brooch|jewelry bench|ornament|tiny",
        "silicone gasket|compressed|titanium rim|assembly room|seal|flexible",
        "parchment scroll|unrolled|obsidian weight|reading room|document|pale",
    ],
}
# Each entry is a separately reviewed semantic construction, not an arbitrary
# transformation with an inherited label. Ten domain variants per family is a cap.
ATOMIC = [
    ("single_state", "{s} is {state}.", "One direct state proposition."),
    (
        "contact_relation",
        "{s} touches {o}.",
        "One relation; the second participant is not a second assertion.",
    ),
    ("negative_property", "{s} is not transparent.", "Negation leaves one factual proposition."),
    ("event_with_time", "{s} moved at noon.", "One event with a temporal modifier."),
    (
        "category_membership",
        "{s} belongs to the {kind} category.",
        "One category-membership claim.",
    ),
    (
        "interpretive_conclusion",
        "This pattern suggests an imbalance in the {place} workflow.",
        "One conclusion; factual premises are not restated.",
    ),
    (
        "invented_state",
        "In a new fictional scene, {s} can become invisible.",
        "One newly invented capability, one policy.",
    ),
    (
        "context_absence",
        "The supplied note gives no color for {obj}.",
        "One context-availability proposition.",
    ),
    (
        "compound_name",
        "{s} has a self-locking release catch.",
        "Compound noun identifies one asserted feature.",
    ),
    (
        "joint_participants",
        "The distance between {obj} and {other} is two meters.",
        "One relation jointly involving two participants.",
    ),
    ("negative_relation", "{s} does not overlap {o}.", "One negated spatial relation."),
    (
        "passive_event",
        "{s} was photographed yesterday.",
        "One passive event, with time as modifier.",
    ),
    ("sole_count", "Exactly three copies of {obj} exist.", "One quantified count proposition."),
    (
        "single_comparison",
        "{s} is heavier than {o}.",
        "One comparative relation, not two absolute weights.",
    ),
    ("existence", "A replacement for {obj} exists.", "One existential proposition."),
    ("event_not_occurred", "{s} did not move during the inspection.", "One negated event."),
    ("measured_value", "{s} weighs four kilograms.", "One measured property."),
    ("relative_position", "{s} lies beneath {o}.", "One spatial relationship."),
    (
        "assigned_identity",
        "The identifier assigned to {obj} is R-17.",
        "One identifier-assignment claim.",
    ),
    (
        "single_receipt",
        "{s} arrived with the morning delivery.",
        "One arrival event; delivery modifies its circumstances.",
    ),
]
NON_ATOMIC = [
    (
        "independent_states",
        "{s} is {state}, and {o} is missing.",
        "Two independently judgeable states.",
    ),
    (
        "fact_and_cause",
        "{s} is {state} because a motor failed.",
        "A state plus a causal/event assertion.",
    ),
    (
        "premise_and_conclusion",
        "{s} is {state}, so the {place} is inefficient.",
        "Factual premise plus an interpretive conclusion.",
    ),
    (
        "two_events",
        "{s} arrived yesterday and departed today.",
        "Two independently judgeable events.",
    ),
    (
        "world_and_context",
        "{s} is {state}, but the supplied note omits its weight.",
        "Source-world fact and availability meta claim use different policies.",
    ),
    (
        "world_and_invention",
        "{s} is {state}; in a new story it can sing.",
        "Source-world state plus invented capability.",
    ),
    (
        "interpretation_and_extra_fact",
        "This suggests poor scheduling; {o} was replaced on Tuesday.",
        "Interpretation plus an independently asserted event.",
    ),
    (
        "ordered_events",
        "After {s} rotated, {o} fell.",
        "Both sequence events can receive independent support verdicts.",
    ),
    (
        "two_relations",
        "{s} touches {o} and stands beside the door.",
        "Two independent spatial relations.",
    ),
    (
        "creative_and_context",
        "In a new fable {s} flies, while the supplied note names no pilot.",
        "Invention and bounded-context availability differ in policy.",
    ),
    (
        "two_measurements",
        "{s} weighs four kilograms and measures two meters.",
        "Two independent measurements.",
    ),
    (
        "negative_plus_positive",
        "{s} is not transparent, but {o} is polished.",
        "Independent negative and positive properties.",
    ),
    (
        "appended_identity_event",
        "{s} has identifier R-17; it was repaired last week.",
        "Identity assignment and repair event are separable.",
    ),
    (
        "two_invented_events",
        "In an original scene {s} escapes the {place} and later returns.",
        "Two separate creative events despite one fictional policy.",
    ),
    (
        "inference_and_context",
        "This implies redundant work, though the supplied excerpt has no timing data.",
        "Conclusion plus context-availability proposition.",
    ),
    (
        "fact_and_interpretive_value",
        "{s} moved at noon, which makes the procedure needlessly elaborate.",
        "An event plus evaluative interpretation.",
    ),
    (
        "separate_counts",
        "There are three copies of {obj} and five of {other}.",
        "Independent counts of separate objects.",
    ),
    (
        "existence_and_location",
        "A spare {obj} exists and is stored in the {place}.",
        "Existence and storage location can receive different verdicts.",
    ),
    (
        "contrast_of_states",
        "{s} is {state}, whereas {o} is damaged.",
        "Two contrasted factual states.",
    ),
    (
        "nested_causal_events",
        "{s} fell when {o} struck it.",
        "A fall and an independently evaluable striking event.",
    ),
]
CONTENT = {
    "SOURCE_FACT_CONTENT": [
        ("direct_property", "{s} is {state}."),
        ("negative_fact", "{s} is not transparent."),
        ("general_category", "A {obj} is a kind of {kind}."),
        ("unlikely_assertion", "{s} has existed for ten thousand years."),
        ("object_relation", "{s} touches {o}."),
        ("dated_event", "{s} arrived on Monday."),
        ("passive_world_event", "{s} was photographed in the {place}."),
        ("measured_world_property", "{s} weighs four kilograms."),
        ("world_comparison", "{s} is heavier than {o}."),
        ("quantified_world_fact", "There are exactly three copies of {obj}."),
    ],
    "INTERPRETATION_CONTENT": [
        ("suggested_conclusion", "This suggests a coordination problem in the {place}."),
        (
            "contrast_conclusion",
            "The contrast indicates a different approach to managing the {place}.",
        ),
        (
            "tentative_evaluation",
            "Taken together, these details make the {place} procedure seem overly cautious.",
        ),
        (
            "causal_reading",
            "A reasonable reading is that the {place} delay reflects conflicting priorities.",
        ),
        ("synthesis", "Overall, the pattern points toward redundancy in the {place} process."),
        (
            "comparative_inference",
            "These observations imply that the {place} favors stability over speed.",
        ),
        (
            "interpretive_tradeoff",
            "The most plausible trade-off is reduced flexibility in the {place}.",
        ),
        (
            "evaluative_implication",
            "The implication is a fragile balance of responsibilities in the {place}.",
        ),
        (
            "abstract_inference",
            "The evidence can be read as a sign of organizational inertia in the {place}.",
        ),
        (
            "inferred_priority",
            "It appears that continuity matters more than convenience in the {place}.",
        ),
    ],
    "CREATIVE_CONTENT": [
        ("new_entity", "For an original tale, invent a talking {obj} called Vela."),
        ("new_state", "Imagine a newly invented {obj} that becomes invisible at dusk."),
        ("new_event", "In this new fictional episode, {s} flies out of the {place}."),
        ("fictional_continuation", "As an invented continuation, {s} discovers a hidden moon."),
        ("hypothetical_invention", "Let our new fantasy version of {obj} whisper forgotten songs."),
        (
            "original_character",
            "Create an original character: a wandering {obj} with a clockwork heart.",
        ),
        ("imagined_motive", "In a newly composed fable, {s} longs to see the ocean."),
        ("new_dialogue", "For a new scene, give {s} the line: 'I will find the dawn.'"),
        ("invented_change", "In the story we are inventing, {s} transforms into a bird."),
        ("new_plot", "Our original plot begins when {s} steals a star from the sky."),
    ],
    "CONTEXT_LIMIT_CONTENT": [
        ("absent_property", "The supplied note gives no weight for {obj}."),
        ("unidentified_answer", "The available excerpt does not identify who made {obj}."),
        ("bounded_insufficiency", "This context is insufficient to determine the age of {obj}."),
        ("missing_description", "No color of {obj} is specified in the supplied description."),
        ("evidence_silence", "The provided evidence is silent about the location of {obj}."),
        (
            "unavailable_relationship",
            "We cannot establish ownership of {obj} from this excerpt alone.",
        ),
        (
            "limited_scope",
            (
                "Only the supplied material is available, and it does not establish"
                " the price of {obj}."
            ),
        ),
        (
            "bounded_confirmation",
            "Whether {obj} was repaired cannot be confirmed from the given record.",
        ),
        ("context_omission", "The current context omits the delivery date of {obj}."),
        (
            "unanswerable_from_input",
            "With the provided passage alone, the dimensions of {obj} remain undetermined.",
        ),
    ],
    "MIXED_CONTENT": [
        ("fact_inference", "{s} is {state}. This suggests poor management in the {place}."),
        ("fact_invention", "{s} is {state}; in a new fictional sequel it becomes a dragon."),
        ("fact_context", "{s} is {state}, but the supplied context omits its size."),
        (
            "inference_invention",
            "This suggests disorder in the {place}; in a newly invented scene {s} learns to dance.",
        ),
        (
            "inference_context",
            (
                "The pattern implies caution in the {place}, although the supplied "
                "record gives no dates."
            ),
        ),
        (
            "invention_context",
            "Imagine a new flying {obj}; the supplied excerpt says nothing about its color.",
        ),
        ("premise_embedded_conclusion", "{s} moved at noon, so the {place} seems inefficient."),
        (
            "invention_fact",
            "In our original fable {s} reads minds; in the actual {place} it is {state}.",
        ),
        ("context_world", "The supplied record names no maker, but {s} weighs four kilograms."),
        (
            "three_policies",
            "{s} is {state}; that implies neglect, so invent a new singing replacement.",
        ),
    ],
}
AMBIGUOUS_A = [
    (
        "coordination_scope",
        "{s} and {o} with a handle moved.",
        "Unclear modifier scope and whether movement is joint or independent.",
    ),
    (
        "appositive_materiality",
        "{s}, the restored one, moved.",
        "Restoration may be identifying background or an independent material claim.",
    ),
    (
        "elliptical_coordination",
        "{s} near {o}, then away.",
        "Ellipsis leaves one relation versus separate events unresolved.",
    ),
    (
        "explanatory_modifier",
        "{s} moved in a repair-related incident.",
        "Modifier may add an independent repair assertion or only classify the event.",
    ),
    (
        "relative_scope",
        "{s} that replaced {o} moved.",
        "Restrictive identification versus independent replacement event is underdetermined.",
    ),
]
AMBIGUOUS_C = [
    (
        "hypothetical_status",
        "Suppose {s} begins to glow.",
        "Unspecified whether analytical hypothesis, invention or instruction.",
    ),
    (
        "deictic_instruction",
        "Let {s} move next.",
        "Could be world-directed instruction or newly invented plot.",
    ),
    (
        "unmarked_fragment",
        "{s}: a promising beginning.",
        "Fragment does not settle factual description versus evaluation/story framing.",
    ),
    (
        "unmarked_future",
        "Perhaps {s} will find a way out.",
        "Epistemic prediction versus invented continuation cannot be settled from this text.",
    ),
    (
        "quoted_meta",
        "'{s}' is the missing element.",
        "The subject may refer to a wording gap or a world object; content type is unresolved.",
    ),
]


def partition(index: int, count: int) -> str:
    if index < count * 0.6:
        return "train"
    if index < count * 0.8:
        return "validation"
    return "selection"


def seed_fields(line: str) -> dict[str, str]:
    obj, state, other, place, kind, shape = line.split("|")
    return dict(
        obj=obj,
        state=state,
        other=other,
        place=place,
        kind=kind,
        shape=shape,
        s="The " + obj,
        o="the " + other,
    )


def build() -> tuple[dict[str, list[dict]], list[dict]]:
    rows: dict[str, list[dict]] = {"atomicity": [], "content_type": []}
    families: list[dict] = []

    def add(task, label, index, count, name, template, reason):
        split = partition(index, count)
        family_id = f"{task}.{label.lower()}.{name}"
        rationale = (
            reason
            or {
                "SOURCE_FACT_CONTENT": (
                    "World-directed factual assertion; truth/support are out of scope."
                ),
                "INTERPRETATION_CONTENT": (
                    "One inferential/evaluative conclusion without asserted "
                    "factual-premise restatement."
                ),
                "CREATIVE_CONTENT": (
                    "Explicitly newly invented entity/state/event, not source-world authority."
                ),
                "CONTEXT_LIMIT_CONTENT": (
                    "Only availability/limitations of the supplied input are asserted."
                ),
                "MIXED_CONTENT": (
                    "At least two semantic policies are present; compatibility is fail-closed."
                ),
            }[label]
        )
        families.append(
            dict(
                family_id=family_id,
                task=task,
                label=label,
                split=split,
                template=template,
                rationale=rationale,
                variant_count=10,
                review="Design-derived semantic family review; not independent human adjudication.",
            )
        )
        for j, line in enumerate(BANKS[split]):
            fields = seed_fields(line)
            row = dict(
                case_id=f"{family_id}.{j:02}",
                text=template.format(**fields),
                label=label,
                family_id=family_id,
                lineage_id=f"neutral-bank.{split}.{j:02}",
                split_group=f"neutral-bank.{split}.{j:02}",
                split=split,
                source="synthetic_design_family",
                required=label != "AMBIGUOUS",
                critical_for_safety=(
                    label == "NON_ATOMIC" if task == "atomicity" else label != "AMBIGUOUS"
                ),
                rationale=rationale,
                training_target=label != "AMBIGUOUS",
            )
            if task == "content_type":
                good = [COMPATIBLE[label]] if label in COMPATIBLE else []
                row["compatible_expected_roles"] = good
                row["critical_incompatible_expected_roles"] = (
                    [r for r in ROLES if r not in good] if label != "AMBIGUOUS" else []
                )
            rows[task].append(row)

    for label, patterns in [
        ("ATOMIC", ATOMIC),
        ("NON_ATOMIC", NON_ATOMIC),
        ("AMBIGUOUS", AMBIGUOUS_A),
    ]:
        for i, (name, template, reason) in enumerate(patterns):
            add("atomicity", label, i, len(patterns), name, template, reason)
    for label, patterns in CONTENT.items():
        for i, (name, template) in enumerate(patterns):
            add("content_type", label, i, len(patterns), name, template, None)
    for i, (name, template, reason) in enumerate(AMBIGUOUS_C):
        add("content_type", "AMBIGUOUS", i, len(AMBIGUOUS_C), name, template, reason)
    return rows, families


def main() -> None:
    rows, families = build()
    hashes = {}
    for task, suffix in [("atomicity", "atomicity"), ("content_type", "content-type")]:
        p = ROOT / "benchmark" / f"n04g25a-{suffix}-development-v1.jsonl"
        p.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows[task]
            ),
            encoding="utf-8",
        )
        hashes[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    split = dict(
        schema_version="sgokb.g25a.split/1",
        status="frozen_for_development",
        policy=(
            "Pattern-family holdout plus independent neutral-domain lineage "
            "grouping; no random row split."
        ),
        partitions=["train", "validation", "selection"],
        families={f["family_id"]: f["split"] for f in families},
        lineages={f"neutral-bank.{s}.{j:02}": s for s in BANKS for j in range(10)},
        cases={row["case_id"]: row["split"] for task in rows.values() for row in task},
    )
    p = ROOT / "benchmark/n04g25a-split-manifest-v1.json"
    p.write_text(json.dumps(split, indent=2) + "\n", encoding="utf-8")
    hashes[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = dict(
        schema_version="sgokb.g25a.development/1",
        status="frozen_for_development",
        authority="G-23F / E5 and G-25A execution plan",
        confirmation_data_access=(
            "prohibited; no seed/paraphrase/similarity input from historical confirmation data"
        ),
        corpora=hashes,
        family_review=(
            "100 distinct reviewed constructions, ten neutral-domain variants "
            "per construction. Labels are design-derived and frozen before "
            "classifier execution; human adjudication is not claimed."
        ),
        families=families,
        distributions={
            task: dict(
                total=len(values),
                labels=dict(Counter(r["label"] for r in values)),
                splits=dict(Counter(r["split"] for r in values)),
            )
            for task, values in rows.items()
        },
        ambiguous_policy=(
            "AMBIGUOUS controls are excluded from hard supervised targets; used"
            " for validation/uncertainty and held-out evaluation only."
        ),
    )
    (ROOT / "benchmark/n04g25a-development-manifest-v1.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["distributions"], indent=2))


if __name__ == "__main__":
    main()
