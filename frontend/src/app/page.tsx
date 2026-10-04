"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

/**
 * Ana sayfa — Token varsa dashboard'a, yoksa login'e yönlendirir.
 */
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (token) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex flex-1 items-center justify-center min-h-screen">
      <div className="loading-spinner" />
    </div>
  );
}
