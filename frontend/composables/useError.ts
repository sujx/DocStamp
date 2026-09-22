/** Canonical API error extraction and toast, shared by every tool component. */
export function useError() {
  /** Pull a human-readable message out of an axios error.
   *
   * Error bodies arrive either as parsed JSON (plain requests) or as a Blob
   * (requests made with `responseType: "blob"`), so both shapes are handled.
   */
  async function extractError(e: any, fallback = "Unknown error"): Promise<string> {
    const data = e?.response?.data;

    if (typeof data === "string" && data) {
      const parsed = parseMessage(data);
      if (parsed) return parsed;
    } else if (data && typeof data.text === "function") {
      try {
        const parsed = parseMessage(await data.text());
        if (parsed) return parsed;
      } catch { /* unreadable body — fall through to the generic message */ }
    } else if (data && typeof data === "object") {
      const msg = data.error || data.msg || data.message;
      if (typeof msg === "string" && msg) return msg;
    }

    return e?.message || fallback;
  }

  async function showError(e: any) {
    const msg = await extractError(e);
    if (import.meta.client) {
      useToast().add({ title: msg, color: "error" });
    }
  }

  return { extractError, showError };
}

/** Parse a raw error body: JSON envelope first, plain text as fallback. */
function parseMessage(raw: string): string {
  const text = raw.trim();
  if (!text || text.startsWith("<")) return "";
  try {
    const body = JSON.parse(text);
    const msg = body?.error || body?.msg || body?.message;
    return typeof msg === "string" ? msg : "";
  } catch {
    return text;
  }
}
