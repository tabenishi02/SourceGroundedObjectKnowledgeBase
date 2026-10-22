"""Exact R2 object_overview size diagnostic for an accepted N-05 sample database.

The source database is opened read-only and backed up to a temporary working copy
before Repository migrations/building are allowed to run. The tool does not embed,
truncate, rebuild Qdrant, or mutate the supplied benchmark database. It builds the
deterministic R2 object_overview in memory and tokenizes it with the frozen Harrier
model tokenizer at the frozen revision.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path

from sgokb.repository import Repository
from sgokb.retrieval.embedding import (
    DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_REVISION,
)
from sgokb.retrieval.search_representation import SearchRepresentationBuilder

R2_OVERVIEW_ENGINEERING_TARGET_TOKENS = 4096
N05_LARGE_EXPECTED_STATEMENT_COUNT = 1200
N05_LARGE_OBJECT_ID = "object-n05-large"


def _resolve_version(repo: Repository, object_id: str, version_id: str | None) -> str:
    if version_id is not None:
        row = repo.one(
            """SELECT v.id,l.state FROM object_versions v
               JOIN object_version_lifecycle l ON l.version_id=v.id
               WHERE v.id=? AND v.object_id=?""",
            (version_id, object_id),
        )
        if row is None:
            raise ValueError("Requested Version does not belong to the requested Object")
        if row["state"] != "accepted":
            raise ValueError("R2 overview diagnostic requires an accepted Version")
        return version_id

    current = repo.version_store.current_version_id(object_id)
    if current is None:
        raise ValueError("Object has no accepted current Version")
    return current


def _build_overview_from_read_only_copy(
    database: Path,
    *,
    object_id: str,
    version_id: str | None,
    require_large_fixture: bool,
):
    database = database.resolve()
    if not database.is_file():
        raise ValueError(f"Database does not exist: {database}")

    with tempfile.TemporaryDirectory(prefix="sgokb-r2-overview-") as temporary:
        copied_database = Path(temporary) / "diagnostic.sqlite"
        source = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
        destination = sqlite3.connect(copied_database)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        repo = Repository(copied_database)
        try:
            resolved_version = _resolve_version(repo, object_id, version_id)
            statement_count = repo.one(
                "SELECT count(*) AS n FROM knowledge_statements WHERE version_id=?",
                (resolved_version,),
            )["n"]
            facet_statement_count = repo.one(
                """SELECT count(*) AS n FROM knowledge_statements
                   WHERE version_id=? AND facet_id IS NOT NULL""",
                (resolved_version,),
            )["n"]
            summary_statement_count = statement_count - facet_statement_count
            content_facet_count = repo.one(
                """SELECT count(*) AS n FROM object_version_facets
                   WHERE version_id=? AND status='content'""",
                (resolved_version,),
            )["n"]

            if require_large_fixture and statement_count != N05_LARGE_EXPECTED_STATEMENT_COUNT:
                raise ValueError(
                    "Expected the frozen N-05 Large fixture with exactly "
                    f"{N05_LARGE_EXPECTED_STATEMENT_COUNT} Statements; got {statement_count}"
                )

            overview = SearchRepresentationBuilder(repo).build_object_overview(resolved_version)
        finally:
            repo.close()

    return (
        resolved_version,
        statement_count,
        summary_statement_count,
        facet_statement_count,
        content_facet_count,
        overview,
    )


def diagnose(
    database: Path,
    *,
    object_id: str = N05_LARGE_OBJECT_ID,
    version_id: str | None = None,
    cache_folder: Path | None = None,
    require_large_fixture: bool = True,
) -> dict:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Exact Harrier token diagnostic requires the local-embedding/transformers runtime"
        ) from exc

    (
        resolved_version,
        statement_count,
        summary_statement_count,
        facet_statement_count,
        content_facet_count,
        overview,
    ) = _build_overview_from_read_only_copy(
        database,
        object_id=object_id,
        version_id=version_id,
        require_large_fixture=require_large_fixture,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        DEFAULT_EMBEDDING_MODEL,
        revision=DEFAULT_EMBEDDING_REVISION,
        cache_dir=None if cache_folder is None else str(cache_folder),
        local_files_only=True,
    )
    input_ids = tokenizer(
        overview.content,
        add_special_tokens=True,
        padding=False,
        truncation=False,
    )["input_ids"]
    token_count = len(input_ids)

    return {
        "diagnostic": "N05D04R2 object_overview exact token count",
        "database": str(database.resolve()),
        "source_database_mutated": False,
        "object_id": object_id,
        "version_id": resolved_version,
        "representation_kind": overview.kind.value,
        "builder_key": overview.builder_key,
        "builder_version": overview.builder_version,
        "content_hash": overview.content_hash,
        "content_characters": len(overview.content),
        "content_utf8_bytes": len(overview.content.encode("utf-8")),
        "statement_count": statement_count,
        "summary_statement_count": summary_statement_count,
        "facet_statement_count": facet_statement_count,
        "content_facet_count": content_facet_count,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "embedding_revision": DEFAULT_EMBEDDING_REVISION,
        "provider_max_sequence_length": DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH,
        "tokenizer_add_special_tokens": True,
        "tokenizer_truncation": False,
        "object_overview_token_count": token_count,
        "engineering_target_tokens": R2_OVERVIEW_ENGINEERING_TARGET_TOKENS,
        "engineering_target_pass": token_count <= R2_OVERVIEW_ENGINEERING_TARGET_TOKENS,
        "provider_limit_pass": token_count <= DEFAULT_EMBEDDING_MAX_SEQUENCE_LENGTH,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--object-id", default=N05_LARGE_OBJECT_ID)
    parser.add_argument("--version-id")
    parser.add_argument("--cache-folder", type=Path)
    parser.add_argument(
        "--allow-non-large",
        action="store_true",
        help="Allow diagnostics against a non-1200-Statement accepted Version.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = diagnose(
        args.database,
        object_id=args.object_id,
        version_id=args.version_id,
        cache_folder=args.cache_folder,
        require_large_fixture=not args.allow_non_large,
    )
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["engineering_target_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
