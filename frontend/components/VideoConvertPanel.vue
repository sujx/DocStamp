<template>
  <div class="card bg-surface border-default">
    <FileUploader
      :accept="'.mp4,.mov,.avi,.mkv'"
      :label="$t('videoConvert.uploadLabel')"
      :hint="$t('videoConvert.sizeHint')"
      @file-selected="onFileSelected"
      @reset="() => {}"
    />

    <!-- Source video preview (stays visible during conversion) -->
    <div v-if="file && !converted" class="mt-6 relative">
      <p class="text-sm font-semibold text-primary mb-3">{{ $t("videoConvert.sourcePreview") }}</p>

      <!-- Converting overlay -->
      <div
        v-if="converting"
        class="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-lg"
        style="background: rgba(0,0,0,0.75);"
      >
        <UIcon name="i-heroicons-arrow-path" class="w-10 h-10 animate-spin text-white" />
        <p class="mt-4 text-sm text-white">{{ $t("videoConvert.converting") }}</p>
      </div>

      <video
        :src="sourceUrl"
        class="w-full rounded-lg"
        style="max-height:320px; background:#000;"
        controls
        preload="metadata"
      />
      <p class="text-xs mt-2 text-tertiary">
        {{ file.name }} &middot; {{ formatSize(file.size) }}
      </p>
    </div>

    <!-- Result: WMV preview + download -->
    <div v-if="converted" class="mt-6">
      <p class="text-sm font-semibold text-primary mb-3">{{ $t("videoConvert.resultPreview") }}</p>
      <video
        :src="resultUrl"
        class="w-full rounded-lg"
        style="max-height:320px; background:#000;"
        controls
        preload="metadata"
      />
      <p class="text-xs mt-2 text-tertiary">
        {{ resultFilename }} &middot; {{ formatSize(resultSize) }}
      </p>

      <div class="mt-4 flex gap-3">
        <UButton color="primary" @click="download">
          <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4 mr-1.5" />
          {{ $t("common.download") }}
        </UButton>
        <UButton variant="outline" color="neutral" @click="resetAll">
          {{ $t("videoConvert.convertAnother") }}
        </UButton>
      </div>
    </div>

    <!-- Convert button -->
    <div v-if="file && !converted" class="mt-6 flex gap-3">
      <UButton color="primary" type="button" :disabled="converting" :loading="converting" @click="convert">
        <UIcon name="i-heroicons-video-camera" class="w-4 h-4 mr-1.5" />
        {{ $t("videoConvert.convert") }}
      </UButton>
    </div>

    <p v-if="!file" class="text-xs mt-2 text-tertiary">
      <UIcon name="i-heroicons-information-circle" class="w-3.5 h-3.5 inline" />
      {{ $t("videoConvert.note") }}
    </p>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const sourceUrl = ref("");
const converting = ref(false);
const converted = ref(false);
const resultUrl = ref("");
const resultBlob = ref<Blob | null>(null);
const resultFilename = ref("");
const resultSize = ref(0);

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function onFileSelected(f: File) {
  if (sourceUrl.value) URL.revokeObjectURL(sourceUrl.value);
  if (resultUrl.value) URL.revokeObjectURL(resultUrl.value);

  file.value = f;
  sourceUrl.value = URL.createObjectURL(f);
  converted.value = false;
  resultUrl.value = "";
  resultBlob.value = null;
}

async function convert() {
  if (!file.value) return;
  converting.value = true;
  const startTime = Date.now();
  try {
    const fd = new FormData();
    fd.append("file", file.value);

    const resp = await axios.post("/api/v1/video-convert", fd, { responseType: "blob" });
    resultBlob.value = resp.data;

    const base = file.value.name.replace(/\.[^.]+$/, "");
    resultFilename.value = `${base}.wmv`;
    resultSize.value = resp.data.size;
    resultUrl.value = URL.createObjectURL(resp.data);
    converted.value = true;
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    let msg = e.message;
    try {
      // Blob error body — need .text() to extract server message
      if (e.response?.data instanceof Blob) {
        const text = await e.response.data.text();
        msg = JSON.parse(text).error || text;
      } else if (e.response?.data?.error) {
        msg = e.response.data.error;
      }
    } catch { /* keep e.message */ }
    toast.add({ title: msg, color: "error" });
  } finally {
    // Keep spinner visible for at least 300ms so user can see it
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, 300 - elapsed);
    setTimeout(() => { converting.value = false; }, remaining);
  }
}

function download() {
  if (!resultBlob.value) return;
  const url = URL.createObjectURL(resultBlob.value);
  const a = document.createElement("a");
  a.href = url;
  a.download = resultFilename.value;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
}

function resetAll() {
  if (sourceUrl.value) URL.revokeObjectURL(sourceUrl.value);
  if (resultUrl.value) URL.revokeObjectURL(resultUrl.value);
  file.value = null;
  sourceUrl.value = "";
  converted.value = false;
  resultUrl.value = "";
  resultBlob.value = null;
  resultFilename.value = "";
  resultSize.value = 0;
}
</script>
