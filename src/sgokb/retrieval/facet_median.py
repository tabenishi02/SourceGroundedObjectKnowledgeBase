"""Source-bounded canonical Facet median scoring for R2 overall Similarity."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, fields

from sgokb.domain import ObjectSimilarityEvidence


@dataclass(frozen=True, slots=True)
class _ClusterSummary:
    facet: str
    source_membership_id: str
    candidate_membership_id: str
    source_representation_id: str
    candidate_representation_id: str
    raw_facet_cosine: float
    bounded_facet_cosine: float
    statement_mean: float | None
    statement_observation_count: int
    cluster_score: float
    median_support: bool


@dataclass(frozen=True, slots=True)
class _MedianExplanation:
    eligible_shared_facet_count: int
    clusters: tuple[_ClusterSummary, ...]
    median_support_facets: tuple[str, ...]
    detail_median: float
    overview_contribution: float
    detail_contribution: float


@dataclass(frozen=True, slots=True)
class _MedianEvidence(ObjectSimilarityEvidence):
    # Additive explanation inside the existing evidence container; v1 is unchanged.
    facet_median: _MedianExplanation | None = None


class FacetMedianScorer:
    """One operation's pinned-generation scorer; performs no candidate acquisition."""

    def __init__(self, owner, source, generation, facets, statements, weights):
        self.owner = owner
        self.generation_id = generation.generation_id
        self.source = source
        self.weights = weights
        self.facets = {row["facet"]: row for row in facets}
        self.vectors = {}
        # Statement source selection can mention Facets outside the eight Facet ANN queries.
        for statement in statements:
            facet = statement["facet"]
            if facet in self.facets:
                continue
            rows = owner.repository.rows(
                """SELECT m.id AS membership_id,m.representation_id,m.facet_id,f.key AS facet
                   FROM knowledge_search_representation_memberships m
                   JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
                   JOIN facet_definitions f ON f.id=m.facet_id
                   WHERE gm.generation_id=? AND m.object_id=? AND m.version_id=?
                     AND m.target_kind='facet' AND m.facet_id=?""",
                (
                    self.generation_id,
                    source["object_id"],
                    source["version_id"],
                    statement["facet_id"],
                ),
            )
            if len(rows) > 1:
                raise RuntimeError("Duplicate source Facet membership in active generation")
            if rows:
                self.facets[facet] = dict(rows[0])

    def _vector(self, representation_id):
        if representation_id not in self.vectors:
            self.vectors[representation_id] = self.owner._embedding(representation_id)
        return self.vectors[representation_id]

    def _anchor(self, source_facet, candidate, hits):
        rows = self.owner.repository.rows(
            """SELECT m.id AS membership_id,m.representation_id,m.facet_id,f.key AS facet
               FROM knowledge_search_representation_memberships m
               JOIN knowledge_search_generation_memberships gm ON gm.membership_id=m.id
               JOIN object_version_lifecycle l ON l.version_id=m.version_id AND l.state='accepted'
               JOIN objects o ON o.id=m.object_id AND o.current_version_id=m.version_id
               JOIN facet_definitions f ON f.id=m.facet_id
               WHERE gm.generation_id=? AND m.object_id=? AND m.version_id=?
                 AND m.target_kind='facet' AND m.facet_id=?""",
            (
                self.generation_id,
                candidate["object_id"],
                candidate["version_id"],
                source_facet["facet_id"],
            ),
        )
        if len(rows) > 1:
            raise RuntimeError("Duplicate candidate Facet membership in active generation")
        if not rows:
            return None
        row = dict(rows[0])
        ann = next(
            (
                hit
                for hit in hits
                if hit.component == "facet"
                and hit.source["membership_id"] == source_facet["membership_id"]
                and hit.candidate["membership_id"] == row["membership_id"]
            ),
            None,
        )
        if ann is not None:
            raw = ann.raw_score
        else:
            left = self._vector(source_facet["representation_id"])
            right = self._vector(row["representation_id"])
            if len(left) != self.owner.space.dimension or len(right) != len(left):
                raise RuntimeError("Facet embedding dimension mismatch")
            denominator = math.sqrt(sum(v * v for v in left)) * math.sqrt(sum(v * v for v in right))
            if denominator == 0:
                raise RuntimeError("Facet embedding has zero norm")
            raw = sum(a * b for a, b in zip(left, right)) / denominator
        if not math.isfinite(raw):
            raise RuntimeError("Facet similarity is not finite")
        return row, raw

    def score(self, hits):
        candidate = hits[0].candidate
        overview = next((hit for hit in hits if hit.component == "overview"), None)
        # Retain one best point per selected source query and candidate Object.
        best = {}
        for hit in hits:
            if hit.component != "statement":
                continue
            key = hit.source["membership_id"]
            if key not in best or self.owner._hit_sort_key(hit) < self.owner._hit_sort_key(
                best[key]
            ):
                best[key] = hit
        clusters = []
        detail_weight = self.weights["facet"] + self.weights["statement"]
        for facet, source_facet in self.facets.items():
            anchor = self._anchor(source_facet, candidate, hits)
            if anchor is None:
                continue
            target, raw = anchor
            observations = sorted(
                (hit for hit in best.values() if hit.source["facet"] == facet),
                key=lambda hit: (hit.source["membership_id"], hit.candidate["membership_id"]),
            )
            mean = (
                math.fsum(self.owner._bounded_cosine(hit.raw_score) for hit in observations)
                / len(observations)
                if observations
                else None
            )
            bounded = self.owner._bounded_cosine(raw)
            score = (
                (self.weights["facet"] * bounded + self.weights["statement"] * mean) / detail_weight
                if mean is not None
                else bounded
            )
            clusters.append((facet, source_facet, target, raw, mean, score, observations))
        clusters.sort(key=lambda row: (row[5], row[0]))
        count = len(clusters)
        support = (
            clusters[count // 2 : count // 2 + 1]
            if count % 2
            else clusters[max(0, count // 2 - 1) : count // 2 + 1]
        )
        median = statistics.median([row[5] for row in clusters]) if clusters else 0.0
        overview_contribution = (
            self.weights["overview"] * self.owner._bounded_cosine(overview.raw_score)
            if overview
            else 0.0
        )
        detail_contribution = detail_weight * median
        evidence = []
        if overview:
            evidence.append(self._evidence(overview, overview_contribution))
        for facet, source_facet, target, raw, mean, _, observations in support:
            factor = detail_weight / len(support)
            facet_factor = self.weights["facet"] / detail_weight if observations else 1.0
            evidence.append(
                ObjectSimilarityEvidence(
                    "facet",
                    source_facet["representation_id"],
                    source_facet["membership_id"],
                    target["representation_id"],
                    target["membership_id"],
                    "facet",
                    facet,
                    None,
                    None,
                    raw,
                    "cosine_similarity",
                    factor * facet_factor * self.owner._bounded_cosine(raw),
                )
            )
            for hit in observations:
                contribution = (
                    factor
                    * self.weights["statement"]
                    / detail_weight
                    * self.owner._bounded_cosine(hit.raw_score)
                    / len(observations)
                )
                evidence.append(self._evidence(hit, contribution))
        if not evidence:
            # Discovery membership is identity/provenance only, never statement-only detail.
            evidence.append(self._evidence(hits[0], 0.0, component="discovery"))
        support_facets = tuple(row[0] for row in support)
        summary = _MedianExplanation(
            count,
            tuple(
                _ClusterSummary(
                    facet,
                    src["membership_id"],
                    dst["membership_id"],
                    src["representation_id"],
                    dst["representation_id"],
                    raw,
                    self.owner._bounded_cosine(raw),
                    mean,
                    len(obs),
                    score,
                    facet in support_facets,
                )
                for facet, src, dst, raw, mean, score, obs in clusters
            ),
            support_facets,
            median,
            overview_contribution,
            detail_contribution,
        )
        evidence[0] = _MedianEvidence(
            **{
                field.name: getattr(evidence[0], field.name)
                for field in fields(ObjectSimilarityEvidence)
            },
            facet_median=summary,
        )
        return overview_contribution + detail_contribution, tuple(evidence)

    @staticmethod
    def _evidence(hit, contribution, *, component=None):
        return ObjectSimilarityEvidence(
            component or hit.component,
            hit.source["representation_id"],
            hit.source["membership_id"],
            hit.candidate["representation_id"],
            hit.candidate["membership_id"],
            hit.candidate["target_kind"],
            hit.candidate.get("facet"),
            hit.source.get("statement_id"),
            hit.candidate.get("statement_id"),
            hit.raw_score,
            "cosine_similarity",
            contribution,
        )
