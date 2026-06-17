<template>
  <div class="card bg-surface border-default">
    <FileUploader
      :accept="'.mp4,.mov,.avi,.mkv'"
      :label="$t('videoConvert.uploadLabel')"
      :hint="$t('videoConvert.sizeHint')"
      @file-selected="onFileSelected"
    />

    <!-- Source video preview -->
    <div v-if="file && !converted && !converting" class="mt-6">
      <p class="text-sm font-semibold text-primary mb-3">{{ $t("videoConvert.sourcePreview") }}</p>
      <video
        ref="sourceVideo"
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

    <!-- Converting spinner -->
    <div v-if="converting" class="mt-6 flex flex-col items-center justify-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="w-10 h-10 animate-spin text-brand-700" />
      <p class="mt-4 text-sm text-secondary">{{ $t("videoConvert.converting") }}</p>
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

    <!-- Convert button (before conversion) -->
    <div v-if="file && !converted && !converting" class="mt-6 flex gap-3">
      <UButton color="primary" type="button" @click="convert">
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
    toast.add({ title: e.response?.data?.error || e.message, color: "error" });
  } finally {
    converting.value = false;
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
