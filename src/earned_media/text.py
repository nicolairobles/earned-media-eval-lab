from __future__ import annotations

import math
import re
from collections import Counter

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "in", "is", "it", "its", "of", "on", "or", "said", "that", "the",
    "their", "this", "to", "was", "were", "will", "with", "we", "our", "they",
}

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-\.]*")


def tokenize(text: str, drop_stopwords: bool = True) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    if drop_stopwords:
        tokens = [t for t in tokens if t not in _STOPWORDS]
    return tokens


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def shingles(tokens: list[str], size: int) -> set[tuple[str, ...]]:
    if len(tokens) < size:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class TfIdfIndex:
    """Deterministic lexical-semantic similarity used as the offline embedding
    stand-in. Production would swap this for a hosted embedding model behind
    the same interface."""

    def __init__(self, corpus: dict[str, str]):
        self._tf: dict[str, Counter] = {}
        df: Counter = Counter()
        for doc_id, text in corpus.items():
            counts = Counter(tokenize(text))
            self._tf[doc_id] = counts
            df.update(counts.keys())
        n = max(len(corpus), 1)
        self._idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        self._vecs = {doc_id: self._vector(counts) for doc_id, counts in self._tf.items()}

    def _vector(self, counts: Counter) -> dict[str, float]:
        vec = {t: c * self._idf.get(t, 1.0) for t, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def similarity(self, doc_a: str, doc_b: str) -> float:
        va, vb = self._vecs[doc_a], self._vecs[doc_b]
        if len(vb) < len(va):
            va, vb = vb, va
        return sum(v * vb.get(t, 0.0) for t, v in va.items())


class BM25:
    def __init__(self, corpus: dict[str, str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self._docs = {doc_id: tokenize(text) for doc_id, text in corpus.items()}
        self._doc_len = {d: len(t) for d, t in self._docs.items()}
        self._avg_len = (sum(self._doc_len.values()) / len(self._docs)) if self._docs else 0.0
        df: Counter = Counter()
        for tokens in self._docs.values():
            df.update(set(tokens))
        n = len(self._docs)
        self._idf = {
            t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()
        }
        self._tf = {d: Counter(t) for d, t in self._docs.items()}

    def score(self, query: str, doc_id: str) -> float:
        q_tokens = tokenize(query)
        tf = self._tf[doc_id]
        dl = self._doc_len[doc_id]
        score = 0.0
        for t in q_tokens:
            if t not in tf:
                continue
            idf = self._idf.get(t, 0.0)
            freq = tf[t]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / (self._avg_len or 1.0))
            score += idf * freq * (self.k1 + 1) / denom
        return score

    def rank(self, query: str, top_k: int) -> list[tuple[str, float]]:
        scored = [(d, self.score(query, d)) for d in self._docs]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[:top_k]
