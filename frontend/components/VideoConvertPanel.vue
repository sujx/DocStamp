<template>
  <div class="card bg-surface border-default">
    <!-- Step 1: Upload / Converting -->
    <template v-if="!done">
      <div
        class="border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-150 cursor-pointer"
        :class="converting ? 'border-brand-400 bg-brand-soft' : 'border-default bg-surface'"
        @dragover.prevent
        @drop.prevent="onDrop"
      >
        <template v-if="!converting">
          <UIcon name="i-heroicons-video-camera" class="w-10 h-10 mx-auto text-tertiary" />
          <p class="text-sm mt-3 text-secondary">{{ $t("videoConvert.uploadLabel") }}</p>
          <p class="text-xs mt-1 text-tertiary">{{ $t("videoConvert.sizeHint") }}</p>
          <label class="cursor-pointer mt-3 inline-block">
            <span class="px-5 py-2.5 rounded-md text-sm font-medium text-white bg-brand-700 hover:bg-brand-800 transition-colors duration-150">
              {{ $t("common.upload") }}
            </span>
            <input type="file" accept=".mp4,.mov,.avi,.mkv" class="hidden" @change="onFileInput" />
          </label>
        </template>
        <template v-else>
          <UIcon name="i-heroicons-arrow-path" class="w-10 h-10 mx-auto animate-spin text-brand-700" />
          <p class="text-sm mt-4 text-secondary">{{ $t("videoConvert.converting") }}</p>
          <p class="text-xs mt-1 text-tertiary truncate max-w-xs mx-auto">{{ fileName }}</p>
        </template>
      </div>
    </template>

    <!-- Step 2: Done → show WMV + download -->
    <template v-if="done">
      <p class="text-sm font-semibold text-primary mb-3">{{ $t("videoConvert.resultPreview") }}</p>
      <video
        :src="resultUrl"
        class="w-full rounded-lg"
        style="max-height:360px; background:#000;"
        controls
      />
      <p class="text-xs mt-2 text-tertiary">{{ resultName }} &middot; {{ resultSizeFmt }}</p>
      <div class="mt-4 flex gap-3">
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-md text-sm font-medium text-white bg-brand-700 hover:bg-brand-800 cursor-pointer transition-colors duration-150"
          @click="download"
        >
          <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4" />
          {{ $t("common.download") }}
        </button>
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-md text-sm font-medium text-secondary border border-default bg-surface hover:bg-muted cursor-pointer transition-colors duration-150"
          @click="resetState"
        >
          {{ $t("videoConvert.convertAnother") }}
        </button>
      </div>
    </template>

    <!-- Error fallback -->
    <div v-if="errorMsg" class="mt-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 flex items-start gap-2">
      <UIcon name="i-heroicons-exclamation-triangle" class="w-4 h-4 shrink-0 mt-0.5" />
      <div class="flex-1">
        <p class="font-medium">{{ $t("common.error") }}</p>
        <p class="text-xs mt-0.5">{{ errorMsg }}</p>
      </div>
      <button type="button" class="text-red-400 hover:text-red-600" @click="errorMsg = ''">✕</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();

const converting = ref(false);
const done = ref(false);
const fileName = ref("");
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
  if (f) startConvert(f);
}

function onDrop(evt: DragEvent) {
  const f = evt.dataTransfer?.files?.[0];
  if (f) startConvert(f);
}

async function startConvert(f: File) {
  errorMsg.value = "";
  fileName.value = f.name;
  converting.value = true;
  done.value = false;

  try {
    const fd = new FormData();
    fd.append("file", f);
    const resp = await axios.post("/api/v1/video-convert", fd, { responseType: "blob" });

    resultBlob.value = resp.data;
    resultName.value = f.name.replace(/\.[^.]+$/, "") + ".wmv";
    resultSizeFmt.value = fmtSize(resp.data.size);
    resultUrl.value = URL.createObjectURL(resp.data);
    done.value = true;
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
  converting.value = false;
  done.value = false;
  fileName.value = "";
  resultUrl.value = "";
  resultBlob.value = null;
  resultName.value = "";
  resultSizeFmt.value = "";
  errorMsg.value = "";
}
</script>
