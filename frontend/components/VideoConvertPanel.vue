<template>
  <div class="card bg-surface border-default">
    <!-- Upload -->
    <div
      v-if="!file"
      class="border-2 border-dashed rounded-lg p-6 sm:p-8 text-center transition-colors duration-150 cursor-pointer border-default bg-surface"
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

    <!-- File ready: preview + Convert button -->
    <div v-if="file && !converting && !done" class="mt-6 space-y-4">
      <div class="flex items-center gap-3 p-3 rounded-lg bg-muted">
        <UIcon name="i-heroicons-video-camera" class="w-6 h-6 text-brand-700 shrink-0" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate text-primary">{{ file.name }}</p>
          <p class="text-xs text-tertiary">{{ fmtSize(file.size) }}</p>
        </div>
        <button type="button" class="text-sm text-tertiary hover:text-red-600" @click="resetState">✕</button>
      </div>

      <video
        v-if="sourceUrl"
        :src="sourceUrl"
        class="w-full rounded-lg"
        style="max-height:300px; background:#000;"
        controls
        preload="metadata"
      />

      <UButton color="primary" block class="min-h-[44px]" @click="startConvert">
        <UIcon name="i-heroicons-video-camera" class="w-4 h-4 mr-1.5" />
        {{ $t("videoConvert.convert") }}
      </UButton>
    </div>

    <!-- Converting: progress bar + message -->
    <div v-if="converting" class="mt-6 space-y-4">
      <div class="flex items-center gap-3 p-3 rounded-lg bg-muted">
        <UIcon name="i-heroicons-video-camera" class="w-6 h-6 text-brand-700 shrink-0" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate text-primary">{{ file?.name }}</p>
          <p class="text-xs text-tertiary">{{ progressMessage || $t("videoConvert.converting") }}</p>
        </div>
      </div>

      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin text-brand-700 mx-auto" />
    </div>

    <!-- Done -->
    <div v-if="done" class="mt-6 space-y-4">
      <div class="p-6 rounded-lg bg-brand-soft border border-default text-center">
        <UIcon name="i-heroicons-check-circle" class="w-10 h-10 mx-auto text-brand-700" />
        <p class="text-sm font-semibold mt-3 text-primary">{{ $t("common.success") }}</p>
        <p class="text-xs mt-1 text-tertiary">{{ resultName }} &middot; {{ resultSizeFmt }}</p>
        <p class="text-xs mt-2 text-tertiary">{{ $t("videoConvert.note") }}</p>
      </div>
      <div class="flex flex-col sm:flex-row gap-3">
        <UButton color="primary" class="flex-1 min-h-[44px]" @click="download">
          <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4 mr-1.5" />
          {{ $t("common.download") }}
        </UButton>
        <UButton variant="outline" color="neutral" class="flex-1 min-h-[44px]" @click="resetState">
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
const { extractError } = useApiError();
const { downloadBlob } = useDownload();

const file = ref<File | null>(null);
const sourceUrl = ref("");
const converting = ref(false);
const done = ref(false);
const resultBlob = ref<Blob | null>(null);
const resultName = ref("");
const resultSizeFmt = ref("");
const errorMsg = ref("");
const progress = ref(0);
const progressMessage = ref("");

let eventSource: EventSource | null = null;

function connectSSE(taskId: string) {
  closeSSE();
  eventSource = new EventSource(`/api/v1/tasks/${encodeURIComponent(taskId)}/stream`);

  eventSource.onmessage = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      if (data.progress !== undefined) progress.value = data.progress;
      if (data.status) {
        if (data.status === "success") onTaskSuccess(data.result_data ? JSON.parse(data.result_data) : null);
        else if (data.status === "failure") onTaskFail(data.error_message || "Conversion failed");
      }
      if (data.progress_message) progressMessage.value = data.progress_message;
    } catch { /* ignore parse errors */ }
  };

  eventSource.onerror = () => {
    if (done.value) closeSSE();
  };
}

function closeSSE() {
  if (eventSource) { eventSource.close(); eventSource = null; }
}

onUnmounted(() => closeSSE());

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function onFileInput(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (f) setFile(f);
}

function onDrop(evt: DragEvent) {
  const f = evt.dataTransfer?.files?.[0];
  if (f) setFile(f);
}

const MAX_VIDEO_SIZE = 100 * 1024 * 1024; // 100 MB

function setFile(f: File) {
  if (f.size > MAX_VIDEO_SIZE) {
    errorMsg.value = `File exceeds ${fmtSize(MAX_VIDEO_SIZE)} limit`;
    return;
  }
  resetState();
  file.value = f;
  sourceUrl.value = URL.createObjectURL(f);
}

async function startConvert() {
  if (!file.value) return;
  errorMsg.value = "";
  converting.value = true;
  progress.value = 0;
  progressMessage.value = t("videoConvert.converting");

  try {
    const fd = new FormData();
    fd.append("file", file.value);
    const resp = await axios.post("/api/v1/video-convert", fd);
    connectSSE(resp.data.task_id);
  } catch (err: any) {
    errorMsg.value = await extractError(err, "Upload failed");
    converting.value = false;
  }
}

async function onTaskSuccess(result: Record<string, unknown> | null) {
  closeSSE();
  progress.value = 100;

  if (result?.download_id) {
    try {
      const dlResp = await axios.get(`/api/v1/download/${result.download_id}`, { responseType: "blob" });
      resultBlob.value = dlResp.data;
    } catch { /* download failed but conversion succeeded */ }
  }

  resultName.value = (result?.filename as string) || file.value?.name?.replace(/\.[^.]+$/, "") + ".wmv" || "";
  if (result?.size) resultSizeFmt.value = fmtSize(result.size as number);

  converting.value = false;
  done.value = true;
}

function onTaskFail(err: string) {
  closeSSE();
  converting.value = false;
  errorMsg.value = err || "Conversion failed";
}

function download() {
  if (!resultBlob.value) return;
  downloadBlob(resultBlob.value, resultName.value);
}

function resetState() {
  closeSSE();
  if (sourceUrl.value) { URL.revokeObjectURL(sourceUrl.value); sourceUrl.value = ""; }
  file.value = null;
  converting.value = false;
  done.value = false;
  resultBlob.value = null;
  resultName.value = "";
  resultSizeFmt.value = "";
  errorMsg.value = "";
  progress.value = 0;
  progressMessage.value = "";
}
</script>
