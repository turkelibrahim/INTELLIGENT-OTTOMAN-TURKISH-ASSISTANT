'use client';

import Image from 'next/image';
import React, { useEffect, useMemo, useState } from 'react';
import {
  ApiError,
  groundTruthApi,
  type GroundTruthDataset,
  type GroundTruthLine,
  type GroundTruthPage,
  type GroundTruthProgress,
} from '@/lib/api';

function bboxText(values: number[]) {
  return values.map((value) => Math.round(value)).join(',');
}

function parseBbox(value: string) {
  const parsed = value.split(',').map((item) => Number(item.trim()));
  return parsed.length === 4 && parsed.every((item) => Number.isFinite(item)) ? parsed : [0, 0, 0, 0];
}

export default function AnnotationStudio() {
  const [datasets, setDatasets] = useState<GroundTruthDataset[]>([]);
  const [pages, setPages] = useState<GroundTruthPage[]>([]);
  const [lines, setLines] = useState<GroundTruthLine[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [selectedPageId, setSelectedPageId] = useState<number | null>(null);
  const [selectedLineIndex, setSelectedLineIndex] = useState(0);
  const [progress, setProgress] = useState<GroundTruthProgress | null>(null);
  const [pageImage, setPageImage] = useState<{ pageId: number; url: string } | null>(null);
  const [zoom, setZoom] = useState(0.36);
  const [fitMode, setFitMode] = useState<'page' | 'width'>('page');
  const [draftText, setDraftText] = useState('');
  const [bboxValue, setBboxValue] = useState('');
  const [textChecked, setTextChecked] = useState(false);
  const [bboxChecked, setBboxChecked] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  const selectedDataset = useMemo(
    () => datasets.find((dataset) => dataset.id === selectedDatasetId) || null,
    [datasets, selectedDatasetId],
  );
  const selectedPage = useMemo(
    () => pages.find((page) => page.id === selectedPageId) || null,
    [pages, selectedPageId],
  );
  const selectedLine = lines[selectedLineIndex] || null;
  const pageImageUrl = pageImage && pageImage.pageId === selectedPage?.id ? pageImage.url : '';
  const isLocked = selectedDataset?.status === 'LOCKED' || selectedPage?.annotation_status === 'LOCKED';

  async function refreshDataset(datasetId?: number) {
    const result = await groundTruthApi.listDatasets();
    if (result.length === 0 && !datasetId) {
      const imported = await groundTruthApi.importPilotDraft();
      setNotice(imported.created ? 'Pilot review dataseti hazirlandi' : 'Pilot review dataseti zaten hazir');
      return refreshDataset(imported.dataset.id);
    }
    setDatasets(result);
    const nextDatasetId = datasetId || selectedDatasetId || result[0]?.id || null;
    setSelectedDatasetId(nextDatasetId);
    if (nextDatasetId) {
      const [pageResult, progressResult] = await Promise.all([
        groundTruthApi.listPages(nextDatasetId),
        groundTruthApi.getProgress(nextDatasetId),
      ]);
      setPages(pageResult);
      setProgress(progressResult);
      const nextPageId = selectedPageId || pageResult[0]?.id || null;
      setSelectedPageId(nextPageId);
      if (nextPageId) {
        const lineResult = await groundTruthApi.listLines(nextPageId);
        setLines(lineResult);
        setSelectedLineIndex(0);
      }
    }
  }

  async function preparePilot() {
    setSaving(true);
    setError('');
    try {
      const result = await groundTruthApi.importPilotDraft();
      setNotice(result.created ? 'Pilot review dataseti hazirlandi' : 'Pilot review dataseti zaten hazir');
      await refreshDataset(result.dataset.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Pilot veri hazirlanamadi');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refreshDataset().catch(() => {
        preparePilot().catch((err) => {
          setError(err instanceof ApiError ? err.detail : 'Review verisi yuklenemedi');
        });
      });
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedPageId) return;
    groundTruthApi.listLines(selectedPageId)
      .then((result) => {
        setLines(result);
        setSelectedLineIndex(0);
      })
      .catch((err) => setError(err instanceof ApiError ? err.detail : 'Satirlar yuklenemedi'));
  }, [selectedPageId]);

  useEffect(() => {
    let revokeUrl = '';
    let cancelled = false;
    if (!selectedPage?.id) return undefined;
    groundTruthApi.getPageImageBlobUrl(selectedPage.id)
      .then((url) => {
        revokeUrl = url;
        if (!cancelled) setPageImage({ pageId: selectedPage.id, url });
      })
      .catch(() => setPageImage(null));
    return () => {
      cancelled = true;
      if (revokeUrl) URL.revokeObjectURL(revokeUrl);
    };
  }, [selectedPage?.id]);

  useEffect(() => {
    if (!selectedLine) return;
    const timer = window.setTimeout(() => {
      setDraftText(selectedLine.text_content);
      setBboxValue(bboxText(selectedLine.bounding_box));
      setTextChecked(Boolean(selectedLine.text_reviewed));
      setBboxChecked(Boolean(selectedLine.bbox_reviewed));
      setDirty(false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [selectedLine]);

  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [dirty]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setSelectedLineIndex((index) => Math.min(index + 1, lines.length - 1));
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        setSelectedLineIndex((index) => Math.max(index - 1, 0));
      }
      if (event.key === '+' || event.key === '=') setZoom((value) => Math.min(value + 0.08, 1.4));
      if (event.key === '-') setZoom((value) => Math.max(value - 0.08, 0.18));
      if (event.key === 'Escape' && selectedLine) {
        setDraftText(selectedLine.text_content);
        setBboxValue(bboxText(selectedLine.bounding_box));
        setDirty(false);
      }
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        void saveReview(true);
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  async function saveReview(goNext = false) {
    if (!selectedLine?.id || isLocked) return;
    setSaving(true);
    setError('');
    try {
      const response = await groundTruthApi.reviewLine(selectedLine.id, {
        text_content: draftText,
        bounding_box: parseBbox(bboxValue),
        text_reviewed: textChecked,
        bbox_reviewed: bboxChecked,
      });
      setProgress(response.progress);
      const updated = [...lines];
      updated[selectedLineIndex] = response.line;
      setLines(updated);
      setDirty(false);
      setNotice('Satir kaydedildi');
      if (goNext) setSelectedLineIndex((index) => Math.min(index + 1, lines.length - 1));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Satir kaydedilemedi');
    } finally {
      setSaving(false);
    }
  }

  async function readyAndLock() {
    if (!selectedDatasetId) return;
    setSaving(true);
    setError('');
    try {
      await groundTruthApi.readyToLock(selectedDatasetId);
      const locked = await groundTruthApi.lockDataset(selectedDatasetId);
      setNotice(`Review tamamlandi, dataset kilitlendi. Evaluation job #${locked.job_id} baslatildi.`);
      await refreshDataset(selectedDatasetId);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Dataset kilitlenemedi');
    } finally {
      setSaving(false);
    }
  }

  const selectedLineBox = selectedLine?.bounding_box || [0, 0, 0, 0];
  const riskyLines = new Set([
    'page_001:0', 'page_001:4', 'page_001:5', 'page_001:10', 'page_001:14', 'page_001:17', 'page_001:20', 'page_001:21',
    'page_002:1', 'page_002:3', 'page_002:7', 'page_002:9', 'page_002:11', 'page_002:12', 'page_002:15', 'page_002:18', 'page_002:19', 'page_002:20',
    'page_003:0', 'page_003:3', 'page_003:6', 'page_003:10', 'page_003:11', 'page_003:14', 'page_003:15', 'page_003:16', 'page_003:19', 'page_003:20', 'page_003:22', 'page_003:23', 'page_003:24',
  ]);
  const sourcePageId = selectedPage?.metadata_json?.source_page_id as string | undefined;
  const risky = sourcePageId ? riskyLines.has(`${sourcePageId}:${selectedLineIndex}`) : false;

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--text-primary)]">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 lg:h-screen">
        <header className="ota-page-header">
          <div>
            <h1 className="text-2xl font-semibold">Ground Truth Human Review</h1>
            <p className="text-sm text-[var(--text-secondary)]">AI destekli taslak - insan dogrulamasi gereklidir</p>
          </div>
          <div className="flex flex-wrap gap-2 text-sm">
            <button className="btn-secondary" onClick={preparePilot} disabled={saving}>Pilot Veriyi Hazirla</button>
            <button className="btn-secondary" onClick={() => setFitMode('width')}>Fit Width</button>
            <button className="btn-secondary" onClick={() => setFitMode('page')}>Fit Page</button>
            <button className="btn-secondary" onClick={() => setZoom((value) => Math.max(value - 0.08, 0.18))}>-</button>
            <button className="btn-secondary" onClick={() => setZoom((value) => Math.min(value + 0.08, 1.4))}>+</button>
            <button className="btn-danger" onClick={readyAndLock} disabled={saving || isLocked || !progress || progress.pending > 0}>
              Review tamamlandi ve dataset kilitlendi
            </button>
          </div>
        </header>

        {(notice || error) && (
          <div className={`border px-3 py-2 text-sm ${error ? 'border-red-300 bg-red-50 text-red-800' : 'border-emerald-300 bg-emerald-50 text-emerald-800'}`}>
            {error || notice}
          </div>
        )}

        <section className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[260px_minmax(0,1fr)_390px]">
          <aside className="space-y-3 overflow-y-auto border-r border-[var(--border)] pr-3">
            <div className="border border-[var(--border)] bg-white p-3 text-sm">
              <h2 className="font-semibold">Review Progress</h2>
              <p className="mt-1 text-3xl font-semibold">{progress?.percent ?? 0}%</p>
              <div className="mt-2 space-y-1 text-xs text-[var(--text-secondary)]">
                <p>Toplam satir: {progress?.total_lines ?? 0}</p>
                <p>Metin kontrol: {progress?.text_reviewed ?? 0}/73</p>
                <p>Kutu kontrol: {progress?.bbox_reviewed ?? 0}/73</p>
                <p>Duzeltilen: {progress?.corrected ?? 0}</p>
                <p>Bekleyen: {progress?.pending ?? 0}</p>
                <p>Dataset: {selectedDataset?.status || '-'}</p>
              </div>
            </div>
            <div className="space-y-2">
              {datasets.map((dataset) => (
                <button key={dataset.id} className={`w-full border px-3 py-2 text-left text-sm ${dataset.id === selectedDatasetId ? 'border-[var(--accent)] bg-white' : 'border-[var(--border)]'}`} onClick={() => refreshDataset(dataset.id)}>
                  <span className="block font-medium">{dataset.name}</span>
                  <span className="text-xs text-[var(--text-secondary)]">{dataset.status}</span>
                </button>
              ))}
            </div>
            <div className="space-y-2">
              {pages.map((page, pageIndex) => (
                <button key={page.id} className={`w-full border px-3 py-2 text-left text-sm ${page.id === selectedPageId ? 'border-[var(--accent)] bg-white' : 'border-[var(--border)]'}`} onClick={() => setSelectedPageId(page.id)}>
                  <span className="block font-medium">Sayfa {pageIndex + 1} - {page.split_type}</span>
                  <span className="text-xs text-[var(--text-secondary)]">{page.annotation_status}</span>
                </button>
              ))}
            </div>
          </aside>

          <section className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-2">
            <div className="flex flex-wrap gap-2 border border-[var(--border)] bg-white p-2 text-xs">
              <span>Yukari/Asagi: satir</span>
              <span>Ctrl+Enter: kaydet ve sonraki</span>
              <span>Esc: iptal</span>
              <span>+/-: zoom</span>
            </div>
            <div className="relative overflow-auto border border-[var(--border)] bg-neutral-100">
              {pageImageUrl && selectedPage ? (
                <div className="relative mx-auto" style={{ width: fitMode === 'width' ? '100%' : selectedPage.image_width ? selectedPage.image_width * zoom : 900 }}>
                  <div className="relative" style={{ width: selectedPage.image_width ? selectedPage.image_width * zoom : 900, height: selectedPage.image_height ? selectedPage.image_height * zoom : 1200 }}>
                    <Image src={pageImageUrl} alt="Review page" fill unoptimized className="object-contain" />
                    {lines.map((line, index) => {
                      const [x1, y1, x2, y2] = line.bounding_box;
                      const active = index === selectedLineIndex;
                      return (
                        <button
                          key={line.id || index}
                          className={`absolute border-2 ${active ? 'border-red-500 bg-red-500/10' : line.text_reviewed && line.bbox_reviewed ? 'border-emerald-500/80' : 'border-amber-500/80'}`}
                          style={{ left: x1 * zoom, top: y1 * zoom, width: (x2 - x1) * zoom, height: (y2 - y1) * zoom }}
                          onClick={() => setSelectedLineIndex(index)}
                          title={`Satir ${index + 1}`}
                        />
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="flex h-full items-center justify-center p-6 text-[var(--text-secondary)]">Sayfa gorseli yukleniyor</div>
              )}
            </div>
          </section>

          <aside className="flex min-h-0 flex-col gap-3 border-l border-[var(--border)] pl-3">
            <div className="border border-[var(--border)] bg-white p-3 text-sm">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Satir {selectedLineIndex + 1}</h2>
                <span className="text-xs text-[var(--text-secondary)]">{selectedLine?.status || '-'}</span>
              </div>
              {risky && <p className="mt-2 border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800">Bu satir ozellikle yeniden okunmali.</p>}
              <p className="mt-2 text-xs text-[var(--text-secondary)]">EasyOCR tahmini gosterilmez. Bu metin yalniz paket taslagidir.</p>
            </div>

            <div className="min-h-0 flex-1 space-y-3 overflow-y-auto">
              <label className="block text-xs font-semibold">Kaydedilmis taslak</label>
              <pre className="whitespace-pre-wrap border border-[var(--border)] bg-white p-3 text-right text-lg" dir="rtl">{selectedLine?.draft_text || selectedLine?.text_content || ''}</pre>

              <label className="block text-xs font-semibold">Osmanlica RTL transkripsiyon</label>
              <textarea
                className="input min-h-32 text-right text-lg"
                dir="rtl"
                value={draftText}
                readOnly={isLocked}
                onChange={(event) => {
                  setDraftText(event.target.value);
                  setDirty(true);
                }}
              />

              <label className="block text-xs font-semibold">Satir kutusu x1,y1,x2,y2</label>
              <input
                className="input font-mono text-xs"
                value={bboxValue}
                readOnly={isLocked}
                onChange={(event) => {
                  setBboxValue(event.target.value);
                  setDirty(true);
                }}
              />
              <p className="text-xs text-[var(--text-secondary)]">Secili kutu: {bboxText(selectedLineBox)}</p>

              <div className="space-y-2 text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={textChecked} disabled={isLocked} onChange={(event) => { setTextChecked(event.target.checked); setDirty(true); }} />
                  Metni kontrol ettim
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={bboxChecked} disabled={isLocked} onChange={(event) => { setBboxChecked(event.target.checked); setDirty(true); }} />
                  Satir kutusunu kontrol ettim
                </label>
              </div>

              <div className="border border-[var(--border)] bg-white p-3 text-xs">
                <p className="font-semibold">Onceki / yeni farki</p>
                <p>Metin degisti: {selectedLine && selectedLine.draft_text !== draftText ? 'Evet' : 'Hayir'}</p>
                <p>Kutu degisti: {selectedLine && bboxText(selectedLine.bounding_box) !== bboxValue ? 'Evet' : 'Hayir'}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-[var(--border)] pt-3">
              <button className="btn-secondary" onClick={() => setSelectedLineIndex((index) => Math.max(index - 1, 0))}>Onceki</button>
              <button className="btn-primary" onClick={() => saveReview(false)} disabled={saving || isLocked || !selectedLine?.id}>Kaydet</button>
              <button className="btn-primary" onClick={() => saveReview(true)} disabled={saving || isLocked || !selectedLine?.id}>Kaydet ve Sonraki</button>
              <button className="btn-secondary" onClick={() => setSelectedLineIndex((index) => Math.min(index + 1, lines.length - 1))}>Sonraki</button>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
