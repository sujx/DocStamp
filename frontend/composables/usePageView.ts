/**
 * Track page views via a lightweight beacon POST.
 * Call once per navigation — swallowed silently on failure.
 */
export function trackPageView(page: string) {
  if (!import.meta.client) return;
  try {
    navigator.sendBeacon
      ? navigator.sendBeacon("/api/v1/track", JSON.stringify({ page }))
      : fetch("/api/v1/track", {
          method: "POST",
          body: JSON.stringify({ page }),
          headers: { "Content-Type": "application/json" },
          keepalive: true,
        }).catch(() => {});
  } catch {
    // Analytics must never break the app
  }
}
