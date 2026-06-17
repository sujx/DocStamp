<template>
  <div class="card bg-surface border-default">
    <!-- Upload -->
    <div
      class="border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-150 cursor-pointer border-default bg-surface"
      @dragover.prevent
      @drop.prevent="onDrop"
    >
      <UIcon name="i-heroicons-video-camera" class="w-10 h-10 mx-auto text-tertiary" />
      <p class="text-sm mt-3 text-secondary">{{ $t("videoConvert.uploadLabel") }}</p>
      <p class="text-xs mt-1 text-tertiary">{{ $t("videoConvert.sizeHint") }}</p>
      <label class="cursor-pointer mt-3 inline-block">
        <span class="px-5 py-2.5 rounded-md text-sm font-medium text-white bg-brand-700 hover:bg-brand-800 transition-colors duration-150">
          {{ $t("common.upload") }}
        </span>
        <input type="file" accept=".mp4,.mov,.avi,.mkv" class="hidden" @change="onFileInput" />
      </label>
    </div>

    <!-- File ready + Convert button -->
    <div v-if="file && !converting && !done" class="mt-6 space-y-4">
      <div class="flex items-center gap-3 p-3 rounded-lg bg-muted">
        <UIcon name="i-heroicons-video-camera" class="w-6 h-6 text-brand-700 shrink-0" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate text-primary">{{ file.name }}</p>
          <p class="text-xs text-tertiary">{{ fmtSize(file.size) }}</p>
        </div>
        <button type="button" class="text-sm text-tertiary hover:text-red-600" @click="resetState">✕</button>
      </div>

      <UButton color="primary" block :loading="converting" @click="doConvert">
        <UIcon name="i-heroicons-video-camera" class="w-4 h-4 mr-1.5" />
        {{ $t("videoConvert.convert") }}
      </UButton>
    </div>

    <!-- Converting -->
    <div v-if="converting" class="mt-6 flex flex-col items-center py-10">
      <UIcon name="i-heroicons-arrow-path" class="w-10 h-10 animate-spin text-brand-700" />
      <p class="mt-4 text-sm text-secondary">{{ $t("videoConvert.converting") }}</p>
    </div>

    <!-- Done -->
    <div v-if="done" class="mt-6 space-y-4">
      <p class="text-sm font-semibold text-primary">{{ $t("videoConvert.resultPreview") }}</p>
      <video :src="resultUrl" class="w-full rounded-lg" style="max-height:360px; background:#000;" controls />
      <p class="text-xs text-tertiary">{{ resultName }} &middot; {{ resultSizeFmt }}</p>
      <div class="flex gap-3">
        <UButton color="primary" class="flex-1" @click="download">
          <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4 mr-1.5" />
          {{ $t("common.download") }}
        </UButton>
        <UButton variant="outline" color="neutral" class="flex-1" @click="resetState">
          {{ $t("videoConvert.convertAnother") }}
        </UButton>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="mt-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 flex items-start gap-2">
      <UIcon name="i-heroicons-exclamation-triangle" class="w-4 h-4 shrink-0 mt-0.5" />
      <span class="flex-1">{{ errorMsg }}</span>
      <button type="button" class="text-red-400 hover:text-red-600 shrink-0" @click="errorMsg = ''">✕</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const converting = ref(false);
const done = ref(false);
const resultUrl = ref("");
const resultBlob = ref<Blob | null>(null);
const resultName = ref("");
const resultSizeFmt = ref("");
const errorMsg = ref("");

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function onFileInput(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (f) {
    resetState();
    file.value = f;
  }
}

function onDrop(evt: DragEvent) {
  const f = evt.dataTransfer?.files?.[0];
  if (f) {
    resetState();
    file.value = f;
  }
}

async function doConvert() {
  if (!file.value) return;
  errorMsg.value = "";
  converting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    const resp = await axios.post("/api/v1/video-convert", fd, { responseType: "blob" });

    resultBlob.value = resp.data;
    resultName.value = file.value.name.replace(/\.[^.]+$/, "") + ".wmv";
    resultSizeFmt.value = fmtSize(resp.data.size);
    resultUrl.value = URL.createObjectURL(resp.data);
    done.value = true;
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    let msg = e.message || "Unknown error";
    try {
      if (e.response?.data instanceof Blob) {
        const text = await e.response.data.text();
        msg = JSON.parse(text).error || text;
      } else if (e.response?.data?.error) {
        msg = e.response.data.error;
      }
    } catch { /* keep e.message */ }
    errorMsg.value = msg;
  } finally {
    converting.value = false;
  }
}

function download() {
  if (!resultBlob.value) return;
  const url = URL.createObjectURL(resultBlob.value);
  const a = document.createElement("a");
  a.href = url;
  a.download = resultName.value;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
}

function resetState() {
  if (resultUrl.value) URL.revokeObjectURL(resultUrl.value);
  file.value = null;
  converting.value = false;
  done.value = false;
  resultUrl.value = "";
  resultBlob.value = null;
  resultName.value = "";
  resultSizeFmt.value = "";
  errorMsg.value = "";
}
</script>
