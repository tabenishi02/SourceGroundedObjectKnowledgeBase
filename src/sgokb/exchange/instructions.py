"""Package-local ChatGPT analysis instructions (Phase G / G-03)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

INSTRUCTIONS_VERSION = "sgokb.object-analysis/1.1"


@dataclass(frozen=True, slots=True)
class AnalysisClassProfile:
    class_id: str
    key: str
    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AnalysisFacetProfile:
    facet_id: str
    key: str
    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AnalysisAttributeProfile:
    attribute_id: str
    key: str
    name: str
    value_type: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AnalysisRelationProfile:
    relation_type_id: str
    key: str
    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class ObjectAnalysisInstructionContext:
    package_id: str
    object_id: str
    object_name: str
    primary_class: AnalysisClassProfile
    ancestor_classes: tuple[AnalysisClassProfile, ...] = ()
    additional_classes: tuple[AnalysisClassProfile, ...] = ()
    effective_facets: tuple[AnalysisFacetProfile, ...] = ()
    allowed_attributes: tuple[AnalysisAttributeProfile, ...] = ()
    allowed_relations: tuple[AnalysisRelationProfile, ...] = ()
    base_version_id: str | None = None
    knowledge_language: str = "ja"


_PRIMARY_OBJECTIVES = {
    "character": (
        "Characterの人物像、価値観、動機、行動傾向、役割、関係、能力、物語上の意味を、"
        "時点・continuity差を保ちながらEvidence-groundedに整理する。"
    ),
    "person": (
        "実在人物について、経歴・役割・活動・関係・思想や評価を時系列とSource attributionを"
        "失わず整理する。"
    ),
    "organization": (
        "組織の目的、構造、活動、所属・関係、歴史的変化を、時点依存性を保って整理する。"
    ),
    "work": (
        "作品の内容、テーマ、世界観、構成、表現上の特徴、登場要素、受容を、作品内描写と"
        "外部評価を混同せず整理する。"
    ),
    "adaptation": (
        "原作・他版との関係を前提に、継承点、変更点、媒体固有要素を区別して整理する。"
    ),
    "work_edition": (
        "版・remake・改訂版として、基底Workとの共通点と版固有差分、時点・edition scopeを整理する。"
    ),
    "series": "複数Work/Componentを束ねるSeriesとして、構成、継続性、共通テーマ・世界観、関係を整理する。",
    "franchise": "媒体横断IP/Franchiseとして、構成作品群、continuity、共有要素、派生関係を整理する。",
    "place": "場所として、位置・構造・機能・利用・歴史・関連Objectを、時間変化を含めて整理する。",
    "world": "World/Universeとして、構造、設定、制度、地理、歴史、continuity境界を整理する。",
    "event": "Eventとして、発生時点、参加者、原因・経過・結果・影響を、推論と明示記述を分離して整理する。",
    "artifact": "個別Artifactとして、由来、構造、機能、利用、所有・関連、状態変化を整理する。",
    "product": "Product/Modelとして、仕様、用途、版・release差、提供状態、関連製品を時点付きで整理する。",
    "taxon": "Taxonとして、定義、分類、特徴、分布・生態、関連TaxonをSourceの分類体系差に注意して整理する。",
    "concept": "Conceptとして、定義、性質、適用範囲、含意、関連概念、用法差を明示記述と解釈に分けて整理する。",
    "theme": "Theme/Motifとして、定義、表現、反復パターン、作品内機能、解釈をEvidence-groundedに整理する。",
    "ideology": "Ideology/Doctrineとして、中心命題、価値、規範、目的、実践、派生・対立概念を帰属付きで整理する。",
    "trait": "Traitとして、意味境界、典型的表れ、条件・例外、関連概念を整理する。",
    "emotion": "Emotionとして、定義、誘因、表出、作用、関連状態を整理する。",
    "motivation": "Motivationとして、目的、誘因、持続条件、行動との関係、競合動機を整理する。",
    "ability": "Abilityとして、効果、発動条件、制約、対象、運用、関連能力を整理する。",
    "skill": "Skillとして、実行内容、前提、習熟・制約、用途、関連技能を整理する。",
    "process": "Processとして、目的、入力、段階、条件、出力、例外を順序関係を保って整理する。",
    "period": "Periodとして、時間境界、特徴、主要Event/Object、前後関係を整理する。",
    "timeline": "Timelineとして、時系列順序、分岐・並行関係、基準時点を明示して整理する。",
    "continuity": "Continuity/World-lineとして、適用範囲、分岐点、共有・非共有設定を混同せず整理する。",
    "system": "Systemとして、目的、構成要素、規則、入出力、相互作用、制約を整理する。",
    "software": "Softwareとして、機能、構成、version/release差、依存関係、運用条件を時点付きで整理する。",
    "service": "Serviceとして、提供機能、対象、運用形態、状態・変更、依存関係を時点付きで整理する。",
    "material": "Materialとして、組成・性質、用途、挙動、条件依存性を整理する。",
    "phenomenon": "Phenomenonとして、定義、発生条件、過程、観測特徴、影響を因果推論と明示記述に分けて整理する。",
    "language": "Languageとして、分類、使用主体、構造、語彙・文法上の特徴、歴史・変種を整理する。",
    "writing_system": "Writing Systemとして、文字体系、対応言語、構造、表記規則、歴史・変種を整理する。",
}


_ANCESTOR_OBJECTIVES = {
    "agent": "Agent familyとして、主体の行為・目的・関係・役割を、単なる外部評価と区別して扱う。",
    "fictional_entity": (
        "FictionalEntityとして、作品内事実・設定と現実世界の事実を混同せず、continuity/edition差を保持する。"
    ),
    "creative_work": (
        "CreativeWork familyとして、作品内容と制作・公開metadata、批評・受容を別のknowledge kindとして区別する。"
    ),
    "work_component": (
        "WorkComponentとして、親Work/Series内での位置、範囲、固有内容と全体への役割を区別する。"
    ),
    "place": "Place familyとして、位置・包含・機能・時間変化を必要に応じて構造化する。",
    "artifact": "Artifact familyとして、物理/人工物のIdentity、機能、状態、所有・関連を区別する。",
    "taxon": "Taxon familyとして、分類階層・分類体系差と個体Objectを混同しない。",
    "concept": "Concept familyとして、定義・用法・解釈・関連概念の境界を明示する。",
    "capability": "Capability familyとして、できること、条件、制約、効果を主体Objectそのものと分離する。",
    "process": "Process familyとして、段階・順序・条件・結果を、単なるEvent instanceと区別する。",
    "temporal_entity": "TemporalEntity familyとして、valid time、前後関係、分岐をVersion作成時刻と分離する。",
    "system": "System familyとして、構成要素・規則・相互作用・境界を個別componentと区別する。",
    "material": "Material familyとして、組成・性質・用途を個別ArtifactのIdentityと区別する。",
    "phenomenon": "Phenomenon familyとして、反復可能な現象型と個別Eventを区別する。",
    "symbolic_system": "SymbolicSystem familyとして、記号体系・規則・使用文脈を利用主体と分離する。",
}


def _template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "object_analysis.md"


def load_object_analysis_template() -> str:
    return _template_path().read_text(encoding="utf-8")


def _inline(value: str) -> str:
    """Render registry/user labels as inert one-line Markdown data."""

    return re.sub(r"\s+", " ", value).strip().replace("`", "'")


def _class_label(profile: AnalysisClassProfile) -> str:
    description = f" — {_inline(profile.description)}" if profile.description else ""
    return f"`{_inline(profile.class_id)}` / {_inline(profile.name)} ({_inline(profile.key)}){description}"


def _target_profile(context: ObjectAnalysisInstructionContext) -> str:
    ancestors = ", ".join(_class_label(item) for item in context.ancestor_classes) or "None"
    additional = ", ".join(_class_label(item) for item in context.additional_classes) or "None"
    base = _inline(context.base_version_id) if context.base_version_id is not None else "null"
    return "\n".join(
        [
            f"- Package ID: `{_inline(context.package_id)}`",
            f"- Target Object ID: `{_inline(context.object_id)}`",
            f"- Target name: `{_inline(context.object_name)}`",
            f"- Primary Class: {_class_label(context.primary_class)}",
            f"- Ancestor Classes: {ancestors}",
            f"- Additional Classes: {additional}",
            f"- Base Knowledge Version: `{base}`",
            f"- Knowledge language: `{_inline(context.knowledge_language)}`",
        ]
    )


def _class_objectives(context: ObjectAnalysisInstructionContext) -> str:
    lines = []
    primary = context.primary_class
    primary_goal = _PRIMARY_OBJECTIVES.get(primary.key)
    if primary_goal is None:
        meaning = _inline(primary.description) if primary.description else _inline(primary.name)
        primary_goal = (
            f"Primary ClassのRegistry意味（{meaning}）に沿って、このObjectをそのClassとして特徴付ける"
            "Evidence-grounded Knowledgeを整理する。"
        )
    lines.append(f"- Primary `{_inline(primary.key)}`: {primary_goal}")

    seen = {primary.key}
    for ancestor in context.ancestor_classes:
        if ancestor.key in seen:
            continue
        seen.add(ancestor.key)
        goal = _ANCESTOR_OBJECTIVES.get(ancestor.key)
        if goal:
            lines.append(f"- Ancestor `{_inline(ancestor.key)}`: {goal}")

    for additional in context.additional_classes:
        if additional.key in seen:
            continue
        seen.add(additional.key)
        goal = _ANCESTOR_OBJECTIVES.get(additional.key)
        if goal:
            lines.append(f"- Additional `{_inline(additional.key)}`: {goal}")
        else:
            meaning = _inline(additional.description) if additional.description else _inline(additional.name)
            lines.append(
                f"- Additional `{_inline(additional.key)}`: Cross-cutting classificationとして"
                f"「{meaning}」の意味境界を追加し、Primary Classを置換しない。"
            )
    return "\n".join(lines)


def _facet_profile(context: ObjectAnalysisInstructionContext) -> str:
    if not context.effective_facets:
        return "- None. The Package contract has no effective Facet for this Object."
    lines = []
    for facet in context.effective_facets:
        description = f" — {_inline(facet.description)}" if facet.description else ""
        lines.append(
            f"- `{_inline(facet.facet_id)}` / {_inline(facet.name)} ({_inline(facet.key)}){description}"
        )
    return "\n".join(lines)


def _attribute_profile(context: ObjectAnalysisInstructionContext) -> str:
    if not context.allowed_attributes:
        return "- None. Do not invent Attribute IDs."
    lines = []
    for attribute in context.allowed_attributes:
        description = f" — {_inline(attribute.description)}" if attribute.description else ""
        lines.append(
            f"- `{_inline(attribute.attribute_id)}` / {_inline(attribute.name)} "
            f"({ _inline(attribute.key) }; type=`{_inline(attribute.value_type)}`){description}"
        )
    return "\n".join(lines)


def _relation_profile(context: ObjectAnalysisInstructionContext) -> str:
    if not context.allowed_relations:
        return "- None. Do not invent Relation Type IDs."
    lines = []
    for relation in context.allowed_relations:
        description = f" — {_inline(relation.description)}" if relation.description else ""
        lines.append(
            f"- `{_inline(relation.relation_type_id)}` / {_inline(relation.name)} "
            f"({_inline(relation.key)}){description}"
        )
    return "\n".join(lines)


def _update_mode(context: ObjectAnalysisInstructionContext) -> str:
    if context.base_version_id is None:
        return (
            "**Mode: new Knowledge generation.** `base_version_id` is `null`; "
            "`current_object.json` must not be assumed to exist."
        )
    return (
        f"**Mode: full-snapshot update from base `{_inline(context.base_version_id)}`.** "
        "Evaluate `current_object.json` against all included carry-forward and newly retrieved Evidence."
    )


def _validate_context(context: ObjectAnalysisInstructionContext) -> None:
    required = {
        "package_id": context.package_id,
        "object_id": context.object_id,
        "object_name": context.object_name,
        "primary_class.class_id": context.primary_class.class_id,
        "primary_class.key": context.primary_class.key,
        "primary_class.name": context.primary_class.name,
        "knowledge_language": context.knowledge_language,
    }
    for field, value in required.items():
        if not value or not value.strip():
            raise ValueError(f"Object analysis instruction context requires {field}")

    for label, values in (
        ("Facet", [item.facet_id for item in context.effective_facets]),
        ("Attribute", [item.attribute_id for item in context.allowed_attributes]),
        ("Relation Type", [item.relation_type_id for item in context.allowed_relations]),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {label} ID in instruction context")


def render_object_analysis_instructions(context: ObjectAnalysisInstructionContext) -> str:
    """Render the finalized Package-local `instructions.md` for one Object."""

    _validate_context(context)
    rendered = load_object_analysis_template()
    replacements = {
        "@@INSTRUCTIONS_VERSION@@": INSTRUCTIONS_VERSION,
        "@@TARGET_PROFILE@@": _target_profile(context),
        "@@CLASS_OBJECTIVES@@": _class_objectives(context),
        "@@FACET_PROFILE@@": _facet_profile(context),
        "@@ATTRIBUTE_PROFILE@@": _attribute_profile(context),
        "@@RELATION_PROFILE@@": _relation_profile(context),
        "@@UPDATE_MODE@@": _update_mode(context),
    }
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)

    unresolved = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", rendered)))
    if unresolved:
        raise RuntimeError(f"Unresolved object analysis instruction markers: {unresolved}")
    return rendered.rstrip() + "\n"
