/**
 * Unified API error extraction.
 *
 * Handles both JSON responses (e.response.data.error) and Blob responses
 * (where the error body is a Blob needing .text() + JSON.parse).
 */
export async function extractError(e: any): Promise<string> {
  if (e.response?.data?.error) {
    return e.response.data.error;
  }

  if (e.response?.data instanceof Blob) {
    try {
      const text = await e.response.data.text();
      const parsed = JSON.parse(text);
      return parsed.error || parsed.msg || text;
    } catch {
      return "Request failed";
    }
  }

  return e.message || "Unknown error";
}
