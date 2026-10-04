import type { Metadata } from "next";
import { Geist, Geist_Mono, Noto_Naskh_Arabic } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const notoNaskhArabic = Noto_Naskh_Arabic({
  variable: "--font-noto-naskh-arabic",
  subsets: ["arabic"],
  weight: ["400", "600", "700"],
});

export const metadata: Metadata = {
  title: "Osmanlıca Belge Asistanıı — Yapay Zekâ Destekli Dijital Arşiv",
  description:
    "Taranmış Osmanlı Türkçesi belgelerini OCR, transliterasyon, modernleştirme, NER ve belge sohbeti ile işleyen yapay zekâ destekli dijital arşiv asistanı.",
  keywords: ["Osmanlıca", "OCR", "NER", "belge asistanı", "dijital arşiv", "yapay zekâ"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} ${notoNaskhArabic.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
