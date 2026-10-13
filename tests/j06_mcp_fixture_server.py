"""Deterministic stdio MCP fixture used by J-06 transport acceptance tests."""

from __future__ import annotations

from sgokb.application_read import APPLICATION_READ_CONTRACT_VERSION
from sgokb.mcp import MCPReadAdapter
from sgokb.mcp.server import create_read_server, run_stdio_server


class AcceptanceApplication:
    contract_version = APPLICATION_READ_CONTRACT_VERSION

    @staticmethod
    def _object(object_id: str, *, version_id: str | None = None) -> dict:
        resolved = version_id or f"version:{object_id}:current"
        return {
            "contract_version": APPLICATION_READ_CONTRACT_VERSION,
            "object_id": object_id,
            "name": f"Object {object_id}",
            "aliases": [],
            "object_status": "active",
            "requested_version_id": version_id,
            "resolved_version_id": resolved,
            "is_current": version_id is None,
            "primary_class": {"id": "class:character", "key": "character", "name": "Character"},
            "additional_classes": [],
            "requested_scope": {},
            "knowledge": {
                "default_language": "ja",
                "result_status": "complete",
                "summary": [],
                "facets": [],
                "attributes": [],
                "relations": [],
            },
            "warnings": [],
        }

    def search_objects(self, query: str, *, mode="hybrid", **kwargs):
        del kwargs
        mode_value = getattr(mode, "value", mode)
        return {
            "query": query,
            "mode": mode_value,
            "results": [
                {
                    "object_id": "object:alpha",
                    "name": "Alpha",
                    "primary_class": "character",
                    "version_id": "version:alpha:current",
                    "rank": 1,
                    "fused_score": 1.0,
                    "score_type": "semantic" if mode_value == "semantic" else "hybrid",
                    "exact_identity": None,
                    "channels": [mode_value],
                    "matched_facets": [],
                    "matches": [],
                }
            ],
            "degraded_channels": [],
        }

    def find_similar_objects(self, object_id: str, *, facet=None, cross_class=False, **kwargs):
        del kwargs
        return {
            "source_object_id": object_id,
            "source_name": "Alpha",
            "source_primary_class": "character",
            "source_version_id": "version:alpha:current",
            "source_representation_id": "representation:alpha",
            "facet": facet,
            "cross_class": cross_class,
            "results": [
                {
                    "object_id": "object:beta",
                    "name": "Beta",
                    "version_id": "version:beta:current",
                    "score": 0.91,
                }
            ],
        }

    def get_object(self, object_id: str, *, version_id=None, **kwargs):
        del kwargs
        return self._object(object_id, version_id=version_id)

    def get_objects(self, object_ids, *, version_ids=None, **kwargs):
        del kwargs
        versions = version_ids or {}
        return {
            "contract_version": APPLICATION_READ_CONTRACT_VERSION,
            "objects": [
                self._object(object_id, version_id=versions.get(object_id))
                for object_id in object_ids
            ],
        }

    def get_object_relations(self, object_id: str, *, version_id=None, **kwargs):
        del kwargs
        return {
            "contract_version": APPLICATION_READ_CONTRACT_VERSION,
            "object_id": object_id,
            "resolved_version_id": version_id or f"version:{object_id}:current",
            "is_current": version_id is None,
            "relations": [],
            "warnings": [],
        }

    def get_object_evidence(self, object_id: str, *, semantic=None, **kwargs):
        del kwargs
        return {
            "contract_version": APPLICATION_READ_CONTRACT_VERSION,
            "object_id": object_id,
            "name": "Alpha",
            "scope": "effective",
            "semantic": bool(semantic),
            "candidate_count": 0,
            "candidates": [],
        }

    def get_evidence(self, evidence_id: str):
        return {
            "contract_version": APPLICATION_READ_CONTRACT_VERSION,
            "evidence": {"evidence_id": evidence_id, "content": "fixture"},
            "snapshot": {},
            "source": {},
            "raw_artifact_ids": [],
            "context": {},
        }

    def build_context(
        self,
        object_ids,
        *,
        purpose="general",
        version_ids=None,
        max_characters=12000,
        **kwargs,
    ):
        del kwargs
        versions = version_ids or {}
        objects = [
            self._object(object_id, version_id=versions.get(object_id)) for object_id in object_ids
        ]
        return {
            "context_contract_version": "sgokb.context-builder.v1",
            "purpose": purpose,
            "selection_policy": {
                "budget_metric": "serialized_json_characters",
                "budget_strategy": "equal_share_per_object",
            },
            "objects": objects,
            "budget": {
                "metric": "serialized_json_characters",
                "limit_characters": max_characters,
                "used_characters": min(max_characters, 100 * len(objects)),
                "omitted_items": 0,
                "truncated": False,
            },
            "warnings": [],
        }

    def search_evidence(self, query: str, *, mode="hybrid", include_historical=False, **kwargs):
        del kwargs
        return {
            "query": query,
            "mode": mode,
            "results": [],
            "degraded_channels": [],
            "include_historical": include_historical,
        }


async def main() -> None:
    adapter = MCPReadAdapter(AcceptanceApplication())
    await run_stdio_server(create_read_server(adapter))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
