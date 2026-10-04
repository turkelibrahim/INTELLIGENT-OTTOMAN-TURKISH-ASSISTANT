"use client";

import { useEffect, useState } from "react";
import { fetchAuthenticatedBlobUrl } from "@/lib/api";

export function AuthImage({
  src,
  alt,
  className,
  onLoad,
}: {
  src: string;
  alt: string;
  className?: string;
  onLoad?: (event: React.SyntheticEvent<HTMLImageElement>) => void;
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!src) return;
    let mounted = true;
    let url: string | null = null;

    void fetchAuthenticatedBlobUrl(src)
      .then((nextUrl) => {
        url = nextUrl;
        if (mounted) setBlobUrl(nextUrl);
      })
      .catch(() => {
        if (mounted) setError(true);
      });

    return () => {
      mounted = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [src]);

  if (error) {
    return <div className="db-empty-state">Görsel yüklenemedi</div>;
  }

  if (!blobUrl) {
    return (
      <div className="db-empty-state">
        <div className="db-spinner" />
      </div>
    );
  }

  // eslint-disable-next-line @next/next/no-img-element
  return <img src={blobUrl} alt={alt} className={className} onLoad={onLoad} />;
}
