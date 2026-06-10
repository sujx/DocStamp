/**
 * AI feature wrappers — text correction, format detection, smart names, denoise.
 *
 * All endpoints gracefully degrade when DOCSTAMP_DEEPSEEK_API_KEY is not set:
 * they return the input unchanged with { changed: false } or empty results.
 */

interface CorrectResult {
  text: string
  changed: boolean
}

interface ClassifyResult {
  is_official: boolean
  confidence: number
}

interface FilenameResult {
  filename: string
}

interface DenoiseResult {
  text: string
}

export function useAi() {
  const loading = ref(false)
  const error = ref("")

  async function _post<T>(url: string, body: Record<string, unknown>): Promise<T> {
    loading.value = true
    error.value = ""
    try {
      return await $fetch<T>(url, { method: "POST", body })
    } catch (e: any) {
      error.value = e.message || "AI request failed"
      throw e
    } finally {
      loading.value = false
    }
  }

  /** Correct typos and punctuation in Markdown text. */
  async function correct(text: string): Promise<CorrectResult> {
    return _post<CorrectResult>("/api/v1/ai/correct", { text })
  }

  /** Detect if text is an official government document. */
  async function classify(text: string): Promise<ClassifyResult> {
    return _post<ClassifyResult>("/api/v1/ai/classify", { text })
  }

  /** Suggest a Chinese filename based on document content. */
  async function suggestFilename(text: string): Promise<FilenameResult> {
    return _post<FilenameResult>("/api/v1/ai/suggest-filename", { text })
  }

  /** Remove header/footer/watermark noise from PDF-extracted text. */
  async function denoise(text: string): Promise<DenoiseResult> {
    return _post<DenoiseResult>("/api/v1/ai/denoise", { text })
  }

  return { correct, classify, suggestFilename, denoise, loading, error }
}
