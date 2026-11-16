/**
 * 从 Content-Disposition 里取下载名。
 * 优先 RFC 5987 的 `filename*=`：Flask 的 ASCII 兜底 `filename=` 会把中文名剥成空串。
 */
export function filenameFromDisposition(header: string | undefined, fallback: string): string {
  const utf8 = /filename\*=([^;]+)/i.exec(header ?? "")?.[1];
  if (utf8) return decodeURIComponent(utf8.trim().replace(/^[^']*''/, ""));

  const plain = /filename="?([^";]+)"?/i.exec(header ?? "")?.[1];
  return plain?.trim() || fallback;
}
