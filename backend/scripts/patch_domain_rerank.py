from pathlib import Path

path = Path("app/services/historical_rag/qdrant_store.py")
text = path.read_text(encoding="utf-8-sig")

# Gerekli importlar
if "import re\n" not in text:
    text = text.replace(
        "import os\n",
        "import os\nimport re\nimport unicodedata\n"
    )

marker = '''    def count(self) -> int:
'''

new_methods = r'''    @staticmethod
    def _normalize_search_text(value: str) -> str:
        """
        Turkish/Ottoman-friendly lightweight normalization
        used only for deterministic retrieval reranking.
        """
        value = str(value or "").casefold()

        value = unicodedata.normalize(
            "NFKD",
            value
        )

        value = "".join(
            char
            for char in value
            if not unicodedata.combining(char)
        )

        replacements = {
            "ı": "i",
            "ş": "s",
            "ğ": "g",
            "ç": "c",
            "ö": "o",
            "ü": "u",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value
        )

        return " ".join(value.split())

    def search(
        self,
        query: str,
        limit: int = 5,
        verified_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Domain-aware historical retrieval.

        Stage 1:
            BM25 no-stem candidate retrieval.

        Stage 2:
            Deterministic reranking using curated
            title / aliases / keywords metadata.

        This does NOT let an LLM alter retrieval scores.
        """

        candidate_limit = max(
            limit * 4,
            12,
        )

        candidates = self.lexical_search(
            query=query,
            limit=candidate_limit,
            verified_only=verified_only,
        )

        normalized_query = self._normalize_search_text(
            query
        )

        reranked = []

        for item in candidates:

            bm25_score = float(
                item.get("score", 0.0)
            )

            title = self._normalize_search_text(
                item.get("title", "")
            )

            aliases = [
                self._normalize_search_text(alias)
                for alias in item.get(
                    "aliases",
                    []
                )
                if alias
            ]

            keywords = [
                self._normalize_search_text(keyword)
                for keyword in item.get(
                    "keywords",
                    []
                )
                if keyword
            ]

            title_match = (
                1
                if title
                and title in normalized_query
                else 0
            )

            alias_matches = sum(
                1
                for alias in aliases
                if alias
                and alias in normalized_query
            )

            keyword_matches = sum(
                1
                for keyword in keywords
                if keyword
                and keyword in normalized_query
            )

            # Curated metadata is intentionally stronger
            # than small BM25 score differences.
            domain_boost = (
                title_match * 5.0
                + alias_matches * 4.0
                + keyword_matches * 2.5
            )

            final_score = (
                bm25_score
                + domain_boost
            )

            enriched = dict(item)

            enriched["bm25_score"] = bm25_score
            enriched["title_match"] = title_match
            enriched["alias_matches"] = alias_matches
            enriched["keyword_matches"] = keyword_matches
            enriched["domain_boost"] = domain_boost
            enriched["retrieval_score"] = final_score

            reranked.append(enriched)

        reranked.sort(
            key=lambda item: (
                item["retrieval_score"],
                item["bm25_score"],
            ),
            reverse=True,
        )

        return reranked[:limit]

'''

if marker not in text:
    raise SystemExit("COUNT_METHOD_MARKER_NOT_FOUND")

if "def _normalize_search_text" in text:
    raise SystemExit("DOMAIN_RERANK_ALREADY_INSTALLED")

text = text.replace(
    marker,
    new_methods + marker
)

path.write_text(
    text,
    encoding="utf-8"
)

print("DOMAIN_AWARE_RERANK_INSTALLED")
