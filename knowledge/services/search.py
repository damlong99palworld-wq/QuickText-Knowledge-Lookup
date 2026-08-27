from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.knowledge import KnowledgeEntry

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None
    import difflib


@dataclass
class SearchHit:
    entry: KnowledgeEntry
    score: float


class KnowledgeSearch:
    """Searches KnowledgeEntry objects using exact and fuzzy matching."""
    def __init__(self, cutoff: float = 55.0):
        self.cutoff = cutoff

    def search(self, entries: list[KnowledgeEntry], query: str) -> list[SearchHit]:
        q = (query or "").strip()
        if not q:
            return [SearchHit(e, 100.0) for e in entries]

        hits: list[SearchHit] = []
        q_lower = q.lower()
        tokens = [t for t in q_lower.replace("/", " ").replace("_", " ").split() if t]

        for entry in entries:
            score = self._score_entry(entry, q_lower, tokens)
            if score >= self.cutoff or self._contains_all_tokens(entry, tokens):
                hits.append(SearchHit(entry, score))

        hits.sort(key=lambda h: (-h.score, h.entry.name.lower()))
        return hits

    def _contains_all_tokens(self, entry: KnowledgeEntry, tokens: list[str]) -> bool:
        blob = entry.searchable_text().lower()
        return all(token in blob for token in tokens)

    def _score_entry(self, entry: KnowledgeEntry, query: str, tokens: list[str]) -> float:
        fields = [
            (entry.name, 100.0),
            (" ".join(entry.aliases), 92.0),
            (entry.category, 70.0),
            (" ".join(entry.tags), 75.0),
            (entry.short_description, 60.0),
        ]
        for prop in entry.properties:
            fields.append((prop.name, 68.0))
            fields.append((prop.value, 55.0))

        best = 0.0
        for text, weight in fields:
            if not text:
                continue
            raw = self._ratio(query, text.lower())
            token_boost = 0.0
            lower = text.lower()
            if query in lower:
                token_boost = 25.0
            elif all(t in lower for t in tokens):
                token_boost = 15.0
            best = max(best, min(100.0, raw * (weight / 100.0) + token_boost))
        return best

    def _ratio(self, query: str, text: str) -> float:
        if not query or not text:
            return 0.0
        if fuzz is not None:
            return float(
                max(
                    fuzz.WRatio(query, text),
                    fuzz.partial_ratio(query, text),
                    fuzz.token_set_ratio(query, text),
                )
            )
        # difflib fallback
        ratio = difflib.SequenceMatcher(None, query, text).ratio() * 100.0
        if query in text:
            ratio = max(ratio, 80.0)
        return ratio
