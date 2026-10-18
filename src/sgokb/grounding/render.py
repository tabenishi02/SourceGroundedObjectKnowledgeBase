"""Deterministic renderer for validated grounded-generation units."""

from __future__ import annotations

from typing import Any


class DeterministicRenderer:
    """Render only validated unit text; never invent or paraphrase content."""

    _DEFAULT_LABELS = {
        "interpretation": "Interpretation",
        "creative": "Creative addition",
        "context_limit": "Context limit",
    }

    def render(
        self,
        output: dict[str, Any],
        validation: dict[str, Any],
    ) -> str:
        if validation.get("verdict") != "PASS":
            raise ValueError("Only validation PASS output may be rendered")
        if validation.get("output") != output:
            raise ValueError("Renderer output does not match the validated output envelope")

        validated_ids = {
            item["unit_id"]
            for item in validation.get("unit_results", [])
            if item.get("grounding_disposition")
            in {"supported", "derived_supported", "not_applicable"}
        }
        output_ids = {
            unit["unit_id"]
            for block in output.get("blocks", [])
            for unit in block.get("units", [])
        }
        if validated_ids != output_ids:
            raise ValueError("Every rendered unit must have a successful validation result")

        rendered_blocks: list[str] = []
        for block in output["blocks"]:
            body = " ".join(unit["text"].strip() for unit in block["units"]).strip()
            role = block["presentation_role"]
            label = block.get("label")
            if role == "main":
                rendered = body
            else:
                visible_label = label.strip() if isinstance(label, str) and label.strip() else None
                visible_label = visible_label or self._DEFAULT_LABELS[role]
                rendered = f"{visible_label}\n{body}"
            rendered_blocks.append(rendered)

        return "\n\n".join(rendered_blocks).strip()
