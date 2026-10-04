from pathlib import Path

path = Path("app/services/historical_rag/qdrant_store.py")
text = path.read_text(encoding="utf-8-sig")

old = '''    def lexical_search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:

        q = self._sparse_vector(
            query,
            query=True,
        )

        results = self.client.query_points(
            collection_name=self.COLLECTION,
            query=q,
            using="lexical",
            limit=limit,
            with_payload=True,
        ).points
'''

new = '''    def lexical_search(
        self,
        query: str,
        limit: int = 5,
        verified_only: bool = True,
    ) -> List[Dict[str, Any]]:

        q = self._sparse_vector(
            query,
            query=True,
        )

        query_filter = None

        if verified_only:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="verified",
                        match=models.MatchValue(
                            value=True
                        )
                    )
                ]
            )

        results = self.client.query_points(
            collection_name=self.COLLECTION,
            query=q,
            using="lexical",
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points
'''

if old not in text:
    raise SystemExit("LEXICAL_SEARCH_BLOCK_NOT_FOUND")

text = text.replace(old, new)

insert_before = '''    def close(self):
        self.client.close()
'''

replacement = '''    def delete(self, item_ids: List[int]) -> None:
        if not item_ids:
            return

        self.client.delete(
            collection_name=self.COLLECTION,
            points_selector=models.PointIdsList(
                points=item_ids
            ),
            wait=True,
        )

    def close(self):
        self.client.close()
'''

if insert_before not in text:
    raise SystemExit("CLOSE_BLOCK_NOT_FOUND")

text = text.replace(insert_before, replacement)

path.write_text(text, encoding="utf-8")

print("HISTORICAL_RAG_VERIFIED_FILTER_PATCHED")
