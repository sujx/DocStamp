<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("watermarkRemove.title") }}</h2>
    <p class="text-sm mb-5 text-pretty text-secondary" >{{ $t("watermarkRemove.description") }}</p>

    <FileUploader
      accept=".pdf,.docx"
      icon="i-heroicons-document-text"
      @file-selected="selectedFile = $event"
      @reset="selectedFile = null"
    />

    <div v-if="selectedFile" class="p-4 mt-4 rounded-lg bg-surface" >
      <UAlert
        color="info"
        :title="selectedFile.name.endsWith('.docx') ? $t('watermarkRemove.docxInfo') : $t('watermarkRemove.pdfInfo')"
        class="mb-4"
      />
      <UButton color="primary" :loading="isProcessing" block @click="remove">
        {{ $t("watermarkRemove.remove") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import FileUploader from "./FileUploader.vue";

const { t } = useI18n();
const { downloadBlob, showError } = useDownload();

const selectedFile = ref<File | null>(null);
const isProcessing = ref(false);

async function remove() {
  if (!selectedFile.value) return;
  isProcessing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    const resp = await axios.post("/api/v1/watermark/remove", fd, { responseType: "blob" });
    downloadBlob(resp.data, `cleaned_${selectedFile.value.name}`, t("common.success"));
  } catch (e) { showError(e); }
  finally { isProcessing.value = false; }
}
</script>
