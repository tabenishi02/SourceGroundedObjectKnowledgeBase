"""Model-isolated cosine search, reciprocal-rank merge and replaceable simple reranker."""

import math

from .domain import EmbeddingSpace, SearchFilter, validate_vectors


class SQLiteCosineIndex:
    version = "brute-cosine-v1"

    def search(self, vector, rows, limit):
        length = math.sqrt(sum(v * v for v in vector))
        results = []
        for row in rows:
            other = row["vector"]
            if len(other) != len(vector):
                raise ValueError("Stored embedding dimension mismatch")
            score = sum(a * b for a, b in zip(vector, other)) / (
                length * math.sqrt(sum(v * v for v in other))
            )
            results.append(dict(row, semantic_score=score))
        results.sort(key=lambda x: (-x["semantic_score"], x["target_id"]))
        return [dict(r, semantic_rank=i + 1) for i, r in enumerate(results[:limit])]


def merge_candidates(lexical, semantic, k=60):
    merged = {}
    for channel, rows in [("lexical", lexical), ("semantic", semantic)]:
        for row in rows:
            key = (row["kind"], row["target_id"])
            rank = row[channel + "_rank"]
            if key not in merged:
                merged[key] = dict(row, score=0, channels=[])
                merged[key].pop("vector", None)
            merged[key]["score"] += 1 / (k + rank)
            merged[key]["channels"].append(channel)
            merged[key].update(
                {name: value for name, value in row.items() if name.startswith(channel + "_")}
            )
    return list(merged.values())


class SimpleReranker:
    version = "rrf60-literal-v1"

    def rank(self, query, candidates, limit):
        result = [
            dict(
                r,
                rerank_score=r["score"]
                + (0.005 if query.casefold() in r["content"].casefold() else 0),
            )
            for r in candidates
        ]
        return sorted(result, key=lambda x: (-x["rerank_score"], x["target_id"]))[:limit]


class HybridSearch:
    def __init__(self, repository, embedder=None, vector_index=None, reranker=None):
        self.repository, self.embedder = repository, embedder
        self.vector_index = vector_index or SQLiteCosineIndex()
        self.reranker = reranker or SimpleReranker()

    def search(self, query, filters=SearchFilter(), limit=10, mode="hybrid"):
        if not query.strip() or not 1 <= limit <= 1000:
            raise ValueError("Nonempty query and limit 1..1000 required")
        eligible = self.repository.candidates(filters)
        lexical = (
            self.repository.lexical(query, eligible, max(50, limit)) if mode != "semantic" else []
        )
        semantic = []
        if mode != "lexical":
            if self.embedder is None:
                raise ValueError("Semantic/hybrid search requires an embedder")
            vectors = self.embedder.embed([query], query=True)
            dimension = validate_vectors(vectors, 1)
            space = EmbeddingSpace(
                self.embedder.model, self.embedder.revision, dimension, self.embedder.configuration
            )
            stored = self.repository.vector_rows(space, eligible)
            if eligible and not stored:
                raise ValueError(
                    "No embeddings in this model/revision/configuration space; run embed"
                )
            semantic = self.vector_index.search(vectors[0], stored, max(50, limit))
        return self.reranker.rank(query, merge_candidates(lexical, semantic), limit)
