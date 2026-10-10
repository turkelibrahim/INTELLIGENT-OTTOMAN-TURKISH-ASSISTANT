"use client";

import { useRef, useState } from "react";
import type { PageResponse, OCRPipelineLine } from "@/lib/api";
import { Icons } from "@/components/Icons";
import { AuthImage } from "./AuthImage"; // I'll extract AuthImage from page.tsx
import { FileText } from 'lucide-react';


const LINE_COLORS = [
  "#2ed8b6", "#4ea3ff", "#9a6cff", "#f4c84d", "#ff914d",
  "#f472b6", "#36d3c0", "#74d66d", "#8067dc", "#5aa7ff",
];

function getLineBox(line: OCRPipelineLine) {
  const bbox = line.bbox;
  if (!bbox) return null;
  if (Array.isArray(bbox)) {
    if (bbox.length < 4) return null;
    return { x: bbox[0], y: bbox[1], width: bbox[2], height: bbox[3] };
  }
  return bbox;
}

export default function OriginalDocumentPanel({
  pages,
  selectedPage,
  setSelectedPage,
  imageUrl,
  ocrLines,
  highlightedLine,
  setHighlightedLine,
  onDownload,
}: {
  pages: PageResponse[];
  selectedPage: PageResponse | null;
  setSelectedPage: (page: PageResponse) => void;
  imageUrl: string;
  ocrLines: OCRPipelineLine[];
  highlightedLine: number | null;
  setHighlightedLine: (index: number | null) => void;
  onDownload?: () => void;
}) {
  const [zoom, setZoom] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [rotation, setRotation] = useState(0);
  const viewerRef = useRef<HTMLDivElement>(null);
  const [imageLayout, setImageLayout] = useState({ width: 0, height: 0, naturalWidth: 0, naturalHeight: 0 });

  const handleZoomIn = () => setZoom((z) => Math.min(250, z + 25));
  const handleZoomOut = () => setZoom((z) => Math.max(50, z - 25));
  const handleZoomReset = () => setZoom(100);
  const handleRotate = () => setRotation((r) => (r + 90) % 360);
  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      viewerRef.current?.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  return (
    <div className="db-panel">
      <div className="db-panel-header">
        <h2 className="db-panel-title">
          <span className="db-panel-icon"><FileText className="w-5 h-5 inline-block mr-1 align-text-bottom" /></span>
          Orijinal Belge
        </h2>
        <div className="db-panel-actions">
          <button className="db-icon-btn" onClick={handleFullscreen} title="Tam Ekran">⛶</button>
        </div>
      </div>
      
      <div className="db-panel-content document-viewer-content" ref={viewerRef} style={{ background: isFullscreen ? '#000' : '' }}>
        {selectedPage ? (
          <div className="document-stage-wrapper">
             <div 
                className="document-image-stage" 
                style={{ 
                  transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                  transformOrigin: 'center center',
                  transition: 'transform 0.2s ease-out'
                }}
             >
              <AuthImage
                src={imageUrl}
                alt={`Sayfa ${selectedPage.page_no}`}
                className="document-image"
                onLoad={(event) => {
                  const image = event.target as HTMLImageElement;
                  setImageLayout({
                    width: image.clientWidth,
                    height: image.clientHeight,
                    naturalWidth: image.naturalWidth,
                    naturalHeight: image.naturalHeight,
                  });
                }}
              />
              {imageLayout.naturalWidth > 0 && ocrLines.some((line) => getLineBox(line)) && (
                <div className="bbox-layer">
                  {ocrLines.map((line, index) => {
                    const box = getLineBox(line);
                    if (!box || box.width <= 0 || box.height <= 0) return null;
                    const active = highlightedLine === index;
                    return (
                      <button
                        type="button"
                        key={`${line.text}-${index}`}
                        className={`bbox-box ${active ? "active" : ""}`}
                        style={{
                          left: `${(box.x / imageLayout.naturalWidth) * 100}%`,
                          top: `${(box.y / imageLayout.naturalHeight) * 100}%`,
                          width: `${(box.width / imageLayout.naturalWidth) * 100}%`,
                          height: `${(box.height / imageLayout.naturalHeight) * 100}%`,
                          borderColor: LINE_COLORS[index % LINE_COLORS.length],
                        }}
                        onClick={() => setHighlightedLine(index)}
                        aria-label={`OCR satiri ${index + 1}`}
                      />
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="db-empty-state">Görüntü bulunamadı.</div>
        )}
      </div>

      <div className="db-panel-footer viewer-controls">
         <div className="zoom-controls">
           <button onClick={handleZoomOut}>−</button>
           <span className="zoom-level">%{zoom}</span>
           <button onClick={handleZoomIn}>+</button>
         </div>
         <div className="action-controls">
           <button onClick={handleFullscreen} title="Tam Ekran">⛶</button>
           <button onClick={handleRotate} title="Döndür">↻</button>
           <button onClick={onDownload} title="İndir">↓</button>
         </div>
      </div>
    </div>
  );
}
