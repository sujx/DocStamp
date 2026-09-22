<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("pdf2img.title") }}</h2>
    <p class="text-sm mb-5 text-pretty text-secondary" >{{ $t("pdf2img.description") }}</p>

    <FileUploader
      accept=".pdf"
      icon="i-heroicons-document"
      @file-selected="onFileSelected"
      @reset="onReset"
    />

    <div v-if="selectedFile" class="p-4 mt-4 rounded-lg bg-surface" >
      <div v-if="pageCount !== null" class="flex items-center gap-3 mb-4 p-3 rounded-md bg-muted" >
        <UIcon name="i-heroicons-document" class="w-5 h-5 shrink-0 text-brand-700"  />
        <span class="text-sm font-medium text-primary" >
          {{ $t("pdf2img.totalPages", { n: pageCount }) }}
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <UFormGroup :label="$t('pdf2img.format')">
          <USelect v-model="format" :options="[{value:'png',label:'PNG'},{value:'jpeg',label:'JPEG'}]" />
        </UFormGroup>
        <UFormGroup :label="$t('pdf2img.dpi')">
          <USelect v-model="dpi" :options="[72,150,200,300].map(d=>({value:d,label:`${d} DPI`}))" />
        </UFormGroup>
      </div>
      <UFormGroup :label="$t('pdf2img.pages')" class="mb-4">
        <UInput v-model="pagesStr" :placeholder="$t('pdf2img.pagesHint')" />
      </UFormGroup>

      <!-- Progress bar -->
      <div v-if="isProcessing" class="mb-4">
        <UProgress :value="progress" :max="pageCount || 1" color="primary" class="mb-2" />
        <p class="text-xs text-center text-secondary" >
          {{ $t("pdf2img.convertingProgress", { current: progress, total: pageCount || '?' }) }}
        </p>
      </div>

      <UButton color="primary" :loading="isProcessing" :disabled="isProcessing" block @click="convert">
        {{ isProcessing ? $t("pdf2img.converting") : $t("pdf2img.convert") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import FileUploader from "./FileUploader.vue";

const { t } = useI18n();
const { downloadBlob } = useDownload();
const { showError } = useApiError();

const selectedFile = ref<File | null>(null);
const pageCount = ref<number | null>(null);
const format = ref("png");
const dpi = ref(200);
const pagesStr = ref("");
const isProcessing = ref(false);
const progress = ref(0);
let progressTimer: ReturnType<typeof setInterval> | null = null;

async function onFileSelected(f: File) {
  selectedFile.value = f;
  pagesStr.value = "";
  // Get page count
  try {
    const fd = new FormData();
    fd.append("file", f);
    const resp = await axios.post("/api/v1/pdf-editor/info", fd);
    pageCount.value = resp.data.total_pages;
  } catch {
    pageCount.value = null;
  }
}

function onReset() {
  selectedFile.value = null;
  pageCount.value = null;
  progress.value = 0;
}

async function convert() {
  if (!selectedFile.value) return;
  isProcessing.value = true;
  progress.value = 0;

  // Simulate progress (conversion is server-side, can't get real-time progress)
  const total = pageCount.value || 1;
  progressTimer = setInterval(() => {
    if (progress.value < total * 0.9) {
      progress.value = Math.min(progress.value + 1, Math.floor(total * 0.9));
    }
  }, 300);

  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("format", format.value);
    fd.append("dpi", String(dpi.value));
    if (pagesStr.value.trim()) fd.append("pages", pagesStr.value.trim());
    const resp = await axios.post("/api/v1/pdf2img", fd, { responseType: "blob" });
    progress.value = total;
    downloadBlob(resp.data, "pdf_images.zip", t("common.success"));
  } catch (e) {
    showError(e);
  } finally {
    isProcessing.value = false;
    if (progressTimer) { clearInterval(progressTimer); progressTimer = null; }
  }
}
</script>
