<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('metadataClean.title')" :description="$t('metadataClean.description')" />

    <div class="card bg-surface border-default" >
      <FileUploader
        :accept="'.docx,.xlsx,.pptx,.pdf'"
        :max-size="100"
        :label="$t('common.upload')"
        @file-selected="onFileSelected"
      />

      <div class="mt-6 flex gap-3">
        <UButton color="primary" :disabled="!file" :loading="cleaning" @click="clean">
          <UIcon name="i-heroicons-shield-exclamation" class="w-4 h-4 mr-1.5" />
          {{ cleaning ? $t("common.processing") : $t("metadataClean.clean") }}
        </UButton>
      </div>

      <div v-if="result" class="mt-4 text-sm text-secondary" >
        {{ $t("metadataClean.fieldsRemoved", { n: result.fields_cleaned }) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const { showError } = useApiError();
const { downloadBlob } = useDownload();

const file = ref<File | null>(null);
const cleaning = ref(false);
const result = ref<{ fields_cleaned: number } | null>(null);

function onFileSelected(f: File) {
  file.value = f;
  result.value = null;
}

async function clean() {
  if (!file.value) return;
  cleaning.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);

    const resp = await axios.post("/api/v1/metadata-clean", fd, { responseType: "blob" });
    result.value = { fields_cleaned: Number(resp.headers["x-fields-cleaned"] || 0) };

    downloadBlob(resp.data, `cleaned_${file.value.name}`, t("common.success"));
  } catch (e: any) {
    showError(e);
  } finally {
    cleaning.value = false;
  }
}
</script>

