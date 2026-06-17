<template>
  <div class="card bg-surface border-default">
    <!-- Step 1: Upload -->
    <div
      v-if="!state.file"
      class="border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-150 cursor-pointer border-default bg-surface"
      @dragover.prevent
      @drop.prevent="onDrop"
    >
      <UIcon name="i-heroicons-video-camera" class="w-8 h-8 mx-auto text-tertiary" />
      <p class="text-sm mt-2 text-secondary">{{ $t("videoConvert.uploadLabel") }}</p>
      <p class="text-xs mt-1 text-tertiary">{{ $t("videoConvert.sizeHint") }}</p>
      <label class="cursor-pointer mt-3 inline-block">
        <span class="px-4 py-2 rounded-md text-sm font-medium text-white bg-brand-700 hover:bg-brand-800 transition-colors duration-150">
          {{ $t("common.upload") }}
        </span>
        <input type="file" accept=".mp4,.mov,.avi,.mkv" class="hidden" @change="onFileInput" />
      </label>
    </div>

    <!-- Step 2: File ready, preview -->
    <div v-if="state.file && state.step === 'ready'" class="space-y-4">
      <div class="flex items-center gap-3 p-3 rounded-lg bg-muted">
        <UIcon name="i-heroicons-video-camera" class="w-6 h-6 text-brand-700 shrink-0" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate text-primary">{{ state.fileName }}</p>
          <p class="text-xs text-tertiary">{{ state.fileSizeFmt }}</p>
        </div>
        <button type="button" class="text-sm text-secondary hover:text-red-600 transition-colors duration-150" @click="resetState">✕</button>
      </div>

      <button
        type="button"
        class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-md text-sm font-medium text-white bg-brand-700 hover:bg-brand-800 cursor-pointer transition-colors duration-150"
        @click="doConvert"
      >
        <UIcon name="i-heroicons-video-camera" class="w-4 h-4" />
        {{ $t("videoConvert.convert") }}
      </button>
    </div>

    <!-- Step 3: Converting -->
    <div v-if="state.step === 'converting'" class="flex flex-col items-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="w-10 h-10 animate-spin text-brand-700" />
      <p class="mt-4 text-sm text-secondary">{{ $t("videoConvert.converting") }}</p>
    </div>

    <!-- Step 4: Done -->
    <div v-if="state.step === 'done'" class="space-y-4">
      <div class="p-4 rounded-lg bg-brand-soft text-center">
        <UIcon name="i-heroicons-check-circle" class="w-8 h-8 mx-auto text-brand-700" />
        <p class="text-sm font-medium mt-2 text-primary">{{ $t("common.success") }}</p>
        <p class="text-xs mt-1 text-tertiary">{{ state.resultName }}</p>
      </div>
      <div class="flex gap-3">
        <button type="button" class="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-md text-sm font-medium text-white bg-brand-700 hover:bg-brand-800 cursor-pointer transition-colors duration-150" @click="doDownload">
          <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4" />
          {{ $t("common.download") }}
        </button>
        <button type="button" class="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-md text-sm font-medium text-secondary border border-default bg-surface hover:bg-muted cursor-pointer transition-colors duration-150" @click="resetState">
          {{ $t("videoConvert.convertAnother") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

interface State {
  step: "upload" | "ready" | "converting" | "done";
  file: File | null;
  fileName: string;
  fileSizeFmt: string;
  resultBlob: Blob | null;
  resultName: string;
}

const state = reactive<State>({
  step: "upload",
  file: null,
  fileName: "",
  fileSizeFmt: "",
  resultBlob: null,
  resultName: "",
});

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function setFile(f: File) {
  state.file = f;
  state.fileName = f.name;
  state.fileSizeFmt = fmtSize(f.size);
  state.step = "ready";
  state.resultBlob = null;
  state.resultName = "";
}

function onFileInput(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (f) setFile(f);
}

function onDrop(evt: DragEvent) {
  const f = evt.dataTransfer?.files?.[0];
  if (f) setFile(f);
}

async function doConvert() {
  if (!state.file) return;
  state.step = "converting";
  try {
    const fd = new FormData();
    fd.append("file", state.file);
    const resp = await axios.post("/api/v1/video-convert", fd, { responseType: "blob" });
    state.resultBlob = resp.data;
    state.resultName = state.fileName.replace(/\.[^.]+$/, "") + ".wmv";
    state.step = "done";
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    let msg = e.message;
    try {
      if (e.response?.data instanceof Blob) {
        const text = await e.response.data.text();
        msg = JSON.parse(text).error || text;
      } else if (e.response?.data?.error) {
        msg = e.response.data.error;
      }
    } catch { /* keep e.message */ }
    toast.add({ title: msg, color: "error" });
    state.step = "ready";
  }
}

function doDownload() {
  if (!state.resultBlob) return;
  const url = URL.createObjectURL(state.resultBlob);
  const a = document.createElement("a");
  a.href = url;
  a.download = state.resultName;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
}

function resetState() {
  state.step = "upload";
  state.file = null;
  state.fileName = "";
  state.fileSizeFmt = "";
  state.resultBlob = null;
  state.resultName = "";
}
</script>
