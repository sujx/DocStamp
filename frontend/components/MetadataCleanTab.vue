<template>
  <div class="card bg-surface border-default">
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

    <div v-if="result" class="mt-4 text-sm text-secondary">
      {{ $t("metadataClean.fieldsRemoved", { n: result.fields_cleaned }) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

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
    const url = URL.createObjectURL(resp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cleaned_${file.value.name}`;
    a.click();
    URL.revokeObjectURL(url);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    const msg = await e.response?.data?.text?.() || e.message;
    toast.add({ title: msg ? JSON.parse(msg).error || msg : e.message, color: "error" });
  } finally {
    cleaning.value = false;
  }
}
</script>

<style scoped>
.card {
  border: 1px solid;
  border-radius: 10px;
  padding: 24px;
}
</style>
