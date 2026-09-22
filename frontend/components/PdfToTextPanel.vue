<template>
  <div class="card bg-surface border-default">
    <FileUploader :accept="'.pdf'" :max-size="100" :label="$t('pdfToText.uploadLabel')" @file-selected="onFileSelected" />
    <UFormGroup v-if="file" :label="$t('pdfToText.pages')" class="mt-4">
      <UInput v-model="pagesInput" :placeholder="$t('pdfToText.pagesHint')" size="sm" />
    </UFormGroup>
    <div class="mt-6 flex gap-3">
      <UButton color="primary" :disabled="!file" :loading="extracting" @click="extract">
        <UIcon name="i-heroicons-document-text" class="w-4 h-4 mr-1.5" />
        {{ extracting ? $t("common.processing") : $t("pdfToText.extract") }}
      </UButton>
      <UButton v-if="result" variant="outline" color="neutral" @click="downloadText">
        <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4 mr-1.5" /> {{ $t("common.download") }}
      </UButton>
      <UButton v-if="result" variant="ghost" color="neutral" @click="copyText">
        <UIcon name="i-heroicons-clipboard" class="w-4 h-4 mr-1.5" /> {{ $t("pdfToText.copy") }}
      </UButton>
      <UButton v-if="result" color="primary" variant="outline" :loading="aiDenoising" @click="aiDenoise">
        <UIcon name="i-heroicons-sparkles" class="w-4 h-4 mr-1.5" />
        {{ aiDenoising ? $t("ai.denoising") : $t("ai.denoise") }}
      </UButton>
    </div>
    <div v-if="result" class="mt-6">
      <div class="text-xs mb-2 text-secondary">{{ $t("pdfToText.pageInfo", { total: result.total_pages, extracted: result.extracted_pages }) }}</div>
      <pre class="result-area">{{ result.text }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
const { t } = useI18n(); const toast = useToast();
const { showError } = useError();
const { denoise: aiDenoiseText, loading: aiDenoising } = useAi();
const file = ref<File | null>(null); const pagesInput = ref(""); const extracting = ref(false);
const result = ref<{ text: string; total_pages: number; extracted_pages: number } | null>(null);
function onFileSelected(f: File) { file.value = f; result.value = null; }
async function extract() {
  if (!file.value) return; extracting.value = true;
  try {
    const fd = new FormData(); fd.append("file", file.value);
    if (pagesInput.value.trim()) fd.append("pages", pagesInput.value.trim());
    const resp = await axios.post("/api/v1/pdf-to-text", fd);
    result.value = resp.data; toast.add({ title: t("pdfToText.success"), color: "success" });
  } catch (e: any) { showError(e); }
  finally { extracting.value = false; }
}
function downloadText() {
  if (!result.value) return;
  const name = (file.value?.name || "document").replace(/\.pdf$/i, "") + ".txt";
  const blob = new Blob([result.value.text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob); const a = document.createElement("a");
  a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url);
}
async function copyText() { if (!result.value) return; await navigator.clipboard.writeText(result.value.text); toast.add({ title: t("pdfToText.copied"), color: "success" }); }
async function aiDenoise() {
  if (!result.value) return;
  try { const r = await aiDenoiseText(result.value.text); if (r.text !== result.value.text) { result.value.text = r.text; toast.add({ title: t("ai.denoised"), color: "success" }); } } catch { /* silent */ }
}
</script>

<style scoped>
.result-area { width: 100%; max-height: 500px; overflow: auto; border: 1px solid; border-radius: 8px; padding: 16px; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; font-family: "JetBrains Mono", "Fira Code", monospace; }
</style>
