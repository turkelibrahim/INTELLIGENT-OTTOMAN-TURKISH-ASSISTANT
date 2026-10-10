import asyncio

async def main():
    print("--- SEGMENTATION BENCHMARK METHODOLOGY ---")
    print("Segmentasyon kalitesini test etmek için crop'lar yetersizdir.")
    print("Çünkü crop zaten segmentasyon sonucudur.")
    print("Tam sayfa (Full Page) bir resim üzerinde EasyOCR detect() çalıştırılıp,")
    print("bulunan bbox'lar insan tarafından doğrulanmış GT bbox'larıyla IoU (Intersection over Union) ile karşılaştırılacaktır.")
    print("Metrikler:")
    print("- Ground Truth Lines: X")
    print("- Detected Lines: Y")
    print("- Missing: (GT var, ancak tespit edilmedi)")
    print("- Merged: (Birden fazla GT satırı tek bbox içinde birleştirildi)")
    print("- Split: (Tek GT satırı birden fazla bbox'a bölündü)")
    print("- Duplicated: (Aynı alan birden fazla kez tespit edildi)")
    print("\nBu test, GT koordinat veri seti tamamlandığında otomatik olarak çalıştırılacaktır.")

if __name__ == "__main__":
    asyncio.run(main())
