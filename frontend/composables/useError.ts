/**
 * Unified API error extraction utility.
 *
 * Usage:
 *   } catch (e: any) {
 *     const msg = await extractError(e);
 *     toast.add({ title: msg, color: "error" });
 *   }
 *
 * Handles both JSON responses (e.response.data.error) and Blob responses
 * (where error body is a Blob needing .text() + JSON.parse).
 */

export async function extractError(e: any): Promise<string> {
  // JSON response (most endpoints)
  if (e.response?.data?.error) {
    return e.response.data.error;
  }

  // Blob response — need to extract text first
  if (e.response?.data instanceof Blob) {
    try {
      const text = await e.response.data.text();
      const parsed = JSON.parse(text);
      return parsed.error || parsed.msg || text;
    } catch {
      return "Request failed";
    }
  }

  // Network error or other
  return e.message || "Unknown error";
}
