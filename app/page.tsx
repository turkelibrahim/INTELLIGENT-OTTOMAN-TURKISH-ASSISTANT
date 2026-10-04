"use client";

import { useState } from "react";

export default function OsmanliAsistani() {
    // TypeScript için değişken tipleri (string, null) eklendi
    const [yuklenenResim, setYuklenenResim] = useState<string | null>(null);
    const [ocrCevirisi, setOcrCevirisi] = useState<string>("");
    const [yapayZekaRaporu, setYapayZekaRaporu] = useState<string>("");
    const [islemDurumu, setIslemDurumu] = useState<string>("Bekleniyor...");

    // TypeScript hata vermesin diye 'e: any' eklendi
    const handleResimYukle = async (e: any) => {
        const file = e.target.files[0];
        if (!file) return;

        setYuklenenResim(URL.createObjectURL(file));
        setIslemDurumu("Kendi OCR Modelin Belgeyi Okuyor...");

        try {
            const formData = new FormData();
            formData.append("dosya", file);

            const ocrResponse = await fetch(
                "http://127.0.0.1:8000/api/ocr",
                {
                    method: "POST",
                    body: formData,
                }
            );

            if (!ocrResponse.ok) {
                throw new Error("OCR İşlemi Başarısız Oldu!");
            }

            const ocrData = await ocrResponse.json();
            const cevrilenMetin = ocrData.ocr_metni;

            setOcrCevirisi(cevrilenMetin);

            await yapayZekayaGonder(cevrilenMetin);

        } catch (error) {
            console.error("OCR Bağlantı Hatası:", error);
            setIslemDurumu(
                "OCR Sunucusuna Bağlanılamadı! (Python API açık mı?)"
            );
        }
    };

    // metin parametresine ': string' tipi eklendi
    const yapayZekayaGonder = async (metin: string) => {
        setIslemDurumu("Osmanlı Tarihçisi Analiz Ediyor...");

        try {
            const response = await fetch(
                "http://127.0.0.1:8000/api/belge-analiz",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        belge_metni: metin,
                    }),
                }
            );

            const data = await response.json();

            setYapayZekaRaporu(data.analiz_raporu);
            setIslemDurumu("İşlem Tamamlandı!");

        } catch (error) {
            console.error("API Bağlantı Hatası:", error);
            setIslemDurumu(
                "Yapay Zeka Sunucusuna Bağlanılamadı! (Python API açık mı?)"
            );
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8 font-sans">

            <h1 className="text-3xl font-bold text-center mb-8 text-amber-900">
                Akıllı Osmanlı Türkçesi Asistanı
            </h1>

            <div className="max-w-xl mx-auto mb-8 bg-white p-6 rounded-lg shadow">
                <input
                    type="file"
                    accept="image/*"
                    onChange={handleResimYukle}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100"
                />

                <p className="text-center mt-4 text-sm text-gray-600 font-medium">
                    Durum:{" "}
                    <span className="text-blue-600">
                        {islemDurumu}
                    </span>
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto">

                <div className="bg-white p-6 rounded-lg shadow h-96 overflow-auto">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2 text-gray-800">
                        Orijinal Belge
                    </h2>

                    {yuklenenResim ? (
                        <img
                            src={yuklenenResim}
                            alt="Yüklenen Belge"
                            className="w-full h-auto rounded"
                        />
                    ) : (
                        <p className="text-gray-400 italic">
                            Henüz belge yüklenmedi...
                        </p>
                    )}
                </div>

                <div className="bg-white p-6 rounded-lg shadow h-96 overflow-auto border-t-4 border-blue-500">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2 text-gray-800">
                        Güncel Türkçe Çeviri (OCR)
                    </h2>

                    <p className="text-gray-700 leading-relaxed">
                        {ocrCevirisi || (
                            <span className="text-gray-400 italic">
                                Bekleniyor...
                            </span>
                        )}
                    </p>
                </div>

                <div className="bg-white p-6 rounded-lg shadow h-96 overflow-auto border-t-4 border-amber-500">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2 text-gray-800">
                        Tarihsel Analiz Raporu
                    </h2>

                    <p className="text-gray-700 leading-relaxed">
                        {yapayZekaRaporu || (
                            <span className="text-gray-400 italic">
                                Bekleniyor...
                            </span>
                        )}
                    </p>
                </div>

            </div>
        </div>
    );
}