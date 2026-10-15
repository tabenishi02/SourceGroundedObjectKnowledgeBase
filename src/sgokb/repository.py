"""Canonical SQLite bootstrap and responsibility-specific stores."""

import sqlite3
from pathlib import Path

from .storage import (
    EmbeddingRepository,
    ObjectRepository,
    SemanticRepository,
    SourceRepository,
    VersionRepository,
)


class Repository:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=5000")
        try:
            self.migrate()
            self.db.execute("PRAGMA journal_mode=WAL")
        except Exception:
            self.db.close()
            raise
        self.embedding_store = EmbeddingRepository(self.db)
        self.object_store = ObjectRepository(self.db)
        self.semantic_store = SemanticRepository(self.db)
        self.source_store = SourceRepository(self.db)
        self.version_store = VersionRepository(self.db)

    def close(self):
        self.db.close()

    def migrate(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)")
        self.db.commit()
        applied = {row[0] for row in self.db.execute("SELECT version FROM schema_migrations")}
        if applied & {1, 2}:
            raise ValueError(
                "Prototype DB rejected (migration version 1/2); "
                "create a fresh canonical DB. No automatic upgrade is supported."
            )
        for file in sorted(Path(__file__).with_name("migrations").glob("*.sql")):
            version = int(file.name.split("_")[0])
            if version < 3:
                raise ValueError("Prototype migration is not allowed in the canonical chain")
            if version not in applied:
                try:
                    self.db.executescript(
                        "BEGIN;\n"
                        + file.read_text(encoding="utf-8")
                        + f"\nINSERT INTO schema_migrations VALUES({version});\nCOMMIT;"
                    )
                except Exception:
                    self.db.rollback()
                    raise

    def one(self, sql, parameters=()):
        result = self.db.execute(sql, parameters).fetchone()
        return dict(result) if result else None

    def rows(self, sql, parameters=()):
        return [dict(row) for row in self.db.execute(sql, parameters)]
