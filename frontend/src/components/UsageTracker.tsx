"use client";

import { useEffect } from "react";
import { trackPageView } from "@/lib/api";

export default function UsageTracker() {
  useEffect(() => {
    void trackPageView();
  }, []);

  return null;
}
