"""Phase H / H-03 human-readable Markdown rendering for Object Knowledge."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

from sgokb.storage.markdown_repository import MarkdownRenderReadRepository

MARKDOWN_RENDERER_VERSION = "1.0"
DEFAULT_RENDER_ROOT = Path("derived/rendered")


@dataclass(frozen=True, slots=True)
class MarkdownRenderResult:
    object_id: str
    version_id: str
    output_path: str
    sha256: str
    byte_count: int
    renderer_version: str
    derived_state_update: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ObjectMarkdownRenderer:
    """Pure deterministic serializer from a render model / compatible JSON to Markdown."""

    def render(self, value: Mapping[str, Any]) -> str:
        model = self._normalize_model(value)
        obj = model["object"]
        version = model["version"]
        knowledge = model["knowledge"]
        evidence = model.get("evidence", [])
        evidence_numbers = {
            item["evidence_id"]: index
            for index, item in enumerate(evidence, start=1)
            if item.get("evidence_id")
        }

        lines: list[str] = []
        lines.extend(
            [
                "<!-- SGOKB derived artifact: do not edit as canonical Knowledge. -->",
                f"# {self._heading(obj.get('name') or obj['object_id'])}",
                "",
                "> **Derived read-only view.** This Markdown is generated from SGOKB canonical "
                "Object Knowledge. Editing this file does not update the database.",
                "",
                "## Object / Version",
                "",
                f"- Object ID: `{self._code(obj['object_id'])}`",
                f"- Version ID: `{self._code(version.get('version_id', 'unknown'))}`",
            ]
        )
        if version.get("version_number") is not None:
            lines.append(f"- Version number: {version['version_number']}")
        if version.get("base_version_id"):
            lines.append(f"- Base Version: `{self._code(version['base_version_id'])}`")
        if version.get("accepted_at"):
            lines.append(f"- Accepted at: `{self._code(version['accepted_at'])}`")
        if version.get("created_at"):
            lines.append(f"- Created at: `{self._code(version['created_at'])}`")
        if "is_current" in version:
            lines.append(f"- Current: {'yes' if version['is_current'] else 'no'}")
        if knowledge.get("default_language"):
            lines.append(f"- Default language: `{self._code(knowledge['default_language'])}`")

        aliases = obj.get("aliases", [])
        if aliases:
            lines.extend(["", "### Aliases", ""])
            for alias in aliases:
                detail = []
                if alias.get("kind"):
                    detail.append(alias["kind"])
                if alias.get("language"):
                    detail.append(alias["language"])
                suffix = f" ({', '.join(detail)})" if detail else ""
                lines.append(f"- {self._inline(alias.get('value', ''))}{suffix}")

        lines.extend(["", "### Classification", ""])
        classification = version.get("classification", {})
        primary = classification.get("primary")
        if primary:
            label = primary.get("name") or primary.get("key") or primary.get("class_id")
            lines.append(
                f"- Primary: **{self._inline(label)}** "
                f"(`{self._code(primary.get('class_id', ''))}`)"
            )
        else:
            primary_id = classification.get("primary_class_id")
            if primary_id:
                lines.append(f"- Primary: `{self._code(primary_id)}`")
        additional = classification.get("additional", [])
        if additional:
            labels = ", ".join(
                f"**{self._inline(item.get('name') or item.get('key') or item.get('class_id'))}** "
                f"(`{self._code(item.get('class_id', ''))}`)"
                for item in additional
            )
            lines.append(f"- Additional: {labels}")
        elif classification.get("additional_class_ids"):
            labels = ", ".join(
                f"`{self._code(item)}`" for item in classification["additional_class_ids"]
            )
            lines.append(f"- Additional: {labels}")

        lines.extend(["", "## Summary", ""])
        summary = knowledge.get("summary_statements") or knowledge.get("summary") or []
        if summary:
            for statement in summary:
                lines.extend(self._statement_lines(statement, evidence_numbers))
        else:
            lines.append("_No summary statements._")

        lines.extend(["", "## Facets", ""])
        facets = knowledge.get("facets", [])
        if not facets:
            lines.append("_No Facets._")
        for facet in facets:
            title = facet.get("name") or facet.get("key") or facet.get("facet_id") or "Facet"
            lines.extend(
                [
                    f"### {self._heading(title)}",
                    "",
                    f"- Facet ID: `{self._code(facet.get('facet_id', ''))}`",
                    f"- Status: `{self._code(facet.get('status', 'unknown'))}`",
                ]
            )
            if facet.get("description"):
                lines.append(f"- Description: {self._inline(facet['description'])}")
            statements = facet.get("statements", [])
            if statements:
                lines.append("")
                for statement in statements:
                    lines.extend(self._statement_lines(statement, evidence_numbers))
            else:
                lines.extend(["", "_No statements._"])
            lines.append("")

        lines.extend(["## Attributes", ""])
        attributes = knowledge.get("attributes", [])
        if attributes:
            lines.extend(
                [
                    "| Attribute | Status | Value | Temporal scope | Evidence |",
                    "|---|---|---|---|---|",
                ]
            )
            for item in attributes:
                name = item.get("name") or item.get("key") or item.get("attribute_id")
                value = (
                    self._format_value(item.get("value")) if item.get("status") == "known" else "—"
                )
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._cell(f"{name} ({item.get('attribute_id', '')})"),
                            self._cell(item.get("status", "")),
                            self._cell(value),
                            self._cell(self._format_temporal(item.get("temporal_scope"))),
                            self._cell(
                                self._format_evidence_refs(
                                    item.get("evidence", []), evidence_numbers
                                )
                            ),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("_No attributes._")

        lines.extend(["", "## Relations", ""])
        relations = knowledge.get("relations", [])
        if relations:
            lines.extend(
                [
                    "| Subject | Relation | Object | Temporal scope | Evidence |",
                    "|---|---|---|---|---|",
                ]
            )
            for item in relations:
                subject = item.get("subject_name") or item.get("subject_object_id", "")
                relation = (
                    item.get("relation_name")
                    or item.get("relation_key")
                    or item.get("relation_type_id", "")
                )
                target = item.get("object_name") or item.get("object_object_id", "")
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._cell(subject),
                            self._cell(relation),
                            self._cell(target),
                            self._cell(self._format_temporal(item.get("temporal_scope"))),
                            self._cell(
                                self._format_evidence_refs(
                                    item.get("evidence", []), evidence_numbers
                                )
                            ),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("_No relations._")

        review = model.get("review") or {}
        review_has_items = any(
            review.get(key)
            for key in (
                "conflicts",
                "gaps",
                "unresolved_references",
                "registry_proposals",
                "class_extensions",
            )
        )
        if review_has_items or review.get("result_status") not in (None, "complete"):
            lines.extend(["", "## Review metadata", ""])
            if review.get("result_status"):
                lines.append(f"- Result status: `{self._code(review['result_status'])}`")
            for key, title in (
                ("conflicts", "Conflicts"),
                ("gaps", "Gaps"),
                ("unresolved_references", "Unresolved references"),
                ("registry_proposals", "Registry proposals"),
                ("class_extensions", "Class extensions"),
            ):
                items = review.get(key, [])
                if items:
                    lines.extend(["", f"### {title}", ""])
                    for item in items:
                        lines.extend(self._review_item_lines(item, evidence_numbers))

        provenance = model.get("provenance") or {}
        if provenance:
            lines.extend(["", "## Import provenance", ""])
            for label, key in (
                ("Import ID", "import_id"),
                ("Receipt ID", "receipt_id"),
                ("Package ID", "package_id"),
                ("Manifest SHA-256", "manifest_sha256"),
                ("Result SHA-256", "result_sha256"),
                ("Imported at", "imported_at"),
            ):
                if provenance.get(key) is not None:
                    lines.append(f"- {label}: `{self._code(str(provenance[key]))}`")
            if "review_acknowledged" in provenance:
                lines.append(
                    f"- Review acknowledged: {'yes' if provenance['review_acknowledged'] else 'no'}"
                )

        lines.extend(["", "## Evidence", ""])
        if not evidence:
            lines.append("_No Evidence context is present in this render model._")
        for index, item in enumerate(evidence, start=1):
            lines.extend(self._evidence_lines(index, item))

        lines.extend(
            [
                "",
                "---",
                "",
                f"_Generated by SGOKB Markdown Renderer {MARKDOWN_RENDERER_VERSION}. "
                "Canonical data remains in SQLite / structured JSON._",
                "",
            ]
        )
        return "\n".join(lines)

    def _normalize_model(self, value: Mapping[str, Any]) -> dict[str, Any]:
        if "object" in value and "version" in value and "knowledge" in value:
            return dict(value)
        if "object_id" in value and "version_id" in value and "knowledge" in value:
            classification = value.get("classification", {})
            return {
                "schema_version": "sgokb.markdown-render-model/1.0",
                "canonical": False,
                "object": {
                    "object_id": value["object_id"],
                    "name": value.get("name") or value["object_id"],
                    "aliases": value.get("aliases", []),
                },
                "version": {
                    "version_id": value["version_id"],
                    "version_number": value.get("version_number"),
                    "created_at": value.get("version_created_at"),
                    "classification": classification,
                },
                "knowledge": value["knowledge"],
                "review": value.get("review", {}),
                "provenance": value.get("provenance", {}),
                "evidence": value.get("evidence", []),
            }
        raise ValueError("Unsupported Markdown render JSON shape")

    def _statement_lines(
        self, statement: Mapping[str, Any], evidence_numbers: Mapping[str, int]
    ) -> list[str]:
        text = str(statement.get("text", ""))
        lines = [f"- {self._inline(text)}"]
        detail = []
        if statement.get("derivation_kind"):
            detail.append(f"derivation `{self._code(statement['derivation_kind'])}`")
        if statement.get("language"):
            detail.append(f"language `{self._code(statement['language'])}`")
        temporal = self._format_temporal(statement.get("temporal_scope"))
        if temporal:
            detail.append(f"temporal {temporal}")
        attribution = statement.get("attribution")
        if attribution:
            display = (
                attribution.get("display_name")
                or attribution.get("label")
                or attribution.get("source_id")
                or attribution.get("object_id")
            )
            detail.append(
                f"attribution {self._inline(str(display))} "
                f"(`{self._code(attribution.get('kind', ''))}`)"
            )
        evidence = self._format_evidence_refs(statement.get("evidence", []), evidence_numbers)
        if evidence:
            detail.append(f"evidence {evidence}")
        if detail:
            lines.append("  - " + "; ".join(detail))
        return lines

    def _review_item_lines(
        self, item: Mapping[str, Any], evidence_numbers: Mapping[str, int]
    ) -> list[str]:
        label = (
            item.get("description")
            or item.get("rationale")
            or item.get("local_key")
            or item.get("kind")
            or item.get("proposal_kind")
            or "review item"
        )
        lines = [f"- {self._inline(str(label))}"]
        evidence = self._format_evidence_refs(item.get("evidence", []), evidence_numbers)
        if evidence:
            lines.append(f"  - Evidence: {evidence}")
        remaining = {
            key: value
            for key, value in item.items()
            if key not in {"description", "rationale", "evidence"}
        }
        if remaining:
            details = json.dumps(remaining, ensure_ascii=False, sort_keys=True)
            lines.append(f"  - Details: `{self._code(details)}`")
        return lines

    def _evidence_lines(self, index: int, item: Mapping[str, Any]) -> list[str]:
        evidence_id = item.get("evidence_id", "")
        title = item.get("source_label") or item.get("source_id") or evidence_id
        lines = [
            f'<a id="evidence-e{index}"></a>',
            f"### E{index} — {self._heading(title)}",
            "",
            f"- Evidence ID: `{self._code(str(evidence_id))}`",
        ]
        if item.get("source_id"):
            lines.append(f"- Source ID: `{self._code(item['source_id'])}`")
        if item.get("snapshot_id"):
            lines.append(f"- Snapshot ID: `{self._code(item['snapshot_id'])}`")
        if item.get("snapshot_title"):
            lines.append(f"- Snapshot: {self._inline(item['snapshot_title'])}")
        if item.get("language"):
            lines.append(f"- Language: `{self._code(item['language'])}`")
        locators = item.get("locators", [])
        if locators:
            rendered = ", ".join(
                f"{self._inline(locator.get('kind', 'locator'))}: "
                f"{self._inline(locator.get('value', ''))}"
                for locator in locators
            )
            lines.append(f"- Locators: {rendered}")
        locations = item.get("locations", [])
        if locations:
            encoded = json.dumps(locations, ensure_ascii=False, sort_keys=True)
            lines.append(f"- Locations: `{self._code(encoded)}`")
        if item.get("content") is not None:
            content = str(item["content"])
            fence = self._fence(content)
            lines.extend(["", f"{fence}text", content, fence, ""])
        return lines

    @staticmethod
    def _format_temporal(scope: Any) -> str:
        if not scope:
            return ""
        if not isinstance(scope, Mapping):
            return str(scope)
        parts = []
        for key in ("as_of", "valid_from", "valid_to", "label"):
            if scope.get(key) is not None:
                parts.append(f"{key}={scope[key]}")
        if scope.get("context_object_id"):
            context = scope.get("context_object_name") or scope["context_object_id"]
            parts.append(f"context={context}")
        return ", ".join(parts)

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _format_evidence_refs(
        self, references: list[Mapping[str, Any]], evidence_numbers: Mapping[str, int]
    ) -> str:
        rendered = []
        for reference in references:
            evidence_id = str(reference.get("evidence_id", ""))
            role = reference.get("role")
            number = evidence_numbers.get(evidence_id)
            label = (
                f"[E{number}](#evidence-e{number})" if number else f"`{self._code(evidence_id)}`"
            )
            if role:
                label += f" ({self._inline(str(role))})"
            rendered.append(label)
        return ", ".join(rendered)

    @staticmethod
    def _heading(value: Any) -> str:
        return str(value).replace("\r", " ").replace("\n", " ").strip()

    @staticmethod
    def _inline(value: Any) -> str:
        text = str(value).replace("\r", " ").replace("\n", " ")
        return text.replace("\\", "\\\\").replace("`", "\\`")

    @staticmethod
    def _code(value: Any) -> str:
        return str(value).replace("`", "ˋ").replace("\r", " ").replace("\n", " ")

    @staticmethod
    def _cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")

    @staticmethod
    def _fence(content: str) -> str:
        longest = max((len(match.group(0)) for match in re.finditer(r"`+", content)), default=0)
        return "`" * max(3, longest + 1)


class MarkdownRenderService:
    """Render accepted canonical Versions to rebuildable managed Markdown artifacts."""

    def __init__(self, repository, renderer: ObjectMarkdownRenderer | None = None):
        self.repository = repository
        self.renderer = renderer or ObjectMarkdownRenderer()
        self.read_store = MarkdownRenderReadRepository(repository.db)

    def render_version(
        self,
        version_id: str,
        *,
        output_root: str | Path = DEFAULT_RENDER_ROOT,
    ) -> MarkdownRenderResult:
        version = self.repository.version_store.version_by_id(version_id)
        state = self._rendering_state(version.object_id, version_id)
        try:
            model = self.read_store.build_model(version_id)
            markdown = self.renderer.render(model)
            raw = markdown.encode("utf-8")
            output = self._managed_path(output_root, version.object_id, version_id)
            self._atomic_write(output, raw)
        except Exception as exc:
            if state is not None:
                self.repository.version_store.mark_derived_state(
                    version.object_id,
                    "rendering",
                    state["revision"],
                    "failed",
                    error=str(exc),
                )
            raise

        state_update = "not_current"
        if state is not None:
            updated = self.repository.version_store.mark_derived_state(
                version.object_id,
                "rendering",
                state["revision"],
                "ready",
            )
            state_update = "ready" if updated else "superseded"
        return MarkdownRenderResult(
            object_id=version.object_id,
            version_id=version_id,
            output_path=str(output),
            sha256=hashlib.sha256(raw).hexdigest(),
            byte_count=len(raw),
            renderer_version=MARKDOWN_RENDERER_VERSION,
            derived_state_update=state_update,
        )

    def render_json(self, value: Mapping[str, Any]) -> str:
        """Pure JSON-to-Markdown path. It never reads or mutates canonical storage."""

        return self.renderer.render(value)

    def _rendering_state(self, object_id: str, version_id: str) -> dict[str, Any] | None:
        row = self.repository.db.execute(
            """SELECT target_version_id,status,revision FROM object_derived_states
               WHERE object_id=? AND kind='rendering'""",
            (object_id,),
        ).fetchone()
        if not row or row["target_version_id"] != version_id:
            return None
        return dict(row)

    @staticmethod
    def _managed_path(output_root: str | Path, object_id: str, version_id: str) -> Path:
        root = Path(output_root).resolve()
        object_part = quote(object_id, safe="-_.")
        version_part = quote(version_id, safe="-_.")
        return root / object_part / f"{version_part}.md"

    @staticmethod
    def _atomic_write(path: Path, raw: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
