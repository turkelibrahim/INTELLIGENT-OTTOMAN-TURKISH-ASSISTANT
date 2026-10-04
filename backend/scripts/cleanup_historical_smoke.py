from qdrant_client import QdrantClient, models

DB_PATH = r"C:\ottoman_ai_data\qdrant"
COLLECTION = "ottoman_historical_knowledge_v1"

client = QdrantClient(path=DB_PATH)

try:
    client.delete(
        collection_name=COLLECTION,
        points_selector=models.PointIdsList(
            points=[10001, 10002]
        ),
        wait=True,
    )

    count = client.count(
        collection_name=COLLECTION,
        exact=True
    ).count

    print("SMOKE_POINTS_REMOVED")
    print("REMAINING_POINTS:", count)

finally:
    client.close()
