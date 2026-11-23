<template>
  <div>
    <div
      class="cursor-pointer rounded-xl border border-dashed p-8 text-center transition-colors"
      :class="isDragover ? 'border-brand-600 bg-brand-soft' : 'border-default bg-surface hover:border-strong'"
      @dragover.prevent="isDragover = true"
      @dragleave.prevent="isDragover = false"
      @drop.prevent="onDrop"
    >
      <div class="icon-badge mx-auto mb-3">
        <UIcon name="i-heroicons-document-text" class="size-[18px]" />
      </div>
      <p class="mb-1 text-[15px] font-medium text-primary">{{ $t("format.docxDragText") }}</p>
      <p class="mb-4 text-[13px] text-secondary">{{ $t("format.docxFormats") }}</p>
      <label>
        <UButton color="primary" variant="soft" as="span">{{ $t("format.upload") }}</UButton>
        <input type="file" accept=".docx" class="hidden" @change="onFileSelect" />
      </label>
    </div>

    <div v-if="selectedFile" class="card mt-4">
      <div class="mb-4 flex items-center gap-3">
        <UIcon name="i-heroicons-document-text" class="size-[18px] shrink-0 text-secondary" />
        <span class="flex-1 truncate text-[13px] font-medium text-primary">{{ selectedFile.name }}</span>
        <UButton size="xs" variant="ghost" color="neutral" @click="selectedFile = null">{{ $t("common.reset") }}</UButton>
      </div>
      <UButton color="primary" :loading="isFormatting" block @click="formatFile">
        {{ isFormatting ? $t("format.formatting") : $t("format.downloadDocx") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const { showError } = useApiError();
const { downloadBlob } = useDownload();

const isDragover = ref(false);
const selectedFile = ref<File | null>(null);
const isFormatting = ref(false);

function onDrop(evt: DragEvent) {
  isDragover.value = false;
  const f = evt.dataTransfer?.files?.[0];
  if (f?.name.endsWith(".docx")) selectedFile.value = f;
}
function onFileSelect(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (f) selectedFile.value = f;
}

async function formatFile() {
  if (!selectedFile.value) return;
  isFormatting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);

    // Step 1: Convert
    const resp = await axios.post("/api/v1/convert/doc2md", fd);
    const { download_id, filename } = resp.data;

    // Step 2: Download
    const dlResp = await axios.get(`/api/v1/download/${download_id}`, { responseType: "blob" });
    downloadBlob(dlResp.data, filename, t("common.success"));
  } catch (e: any) {
    showError(e);
  } finally {
    isFormatting.value = false;
  }
}
</script>
