<template>
  <div class="max-w-3xl mx-auto px-6 py-8">
    <PageHeader :title="$t('formatConvert.title')" :description="$t('formatConvert.description')" />

    <div class="card" :style="{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border-default)' }">
      <FileUploader
        :accept="'.docx,.html,.htm'"
        :max-size="100"
        :label="$t('common.upload')"
        @file-selected="onFileSelected"
      />

      <div v-if="file" class="mt-4 p-3 rounded-md text-sm border" :style="{ backgroundColor: 'var(--color-muted)', borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-secondary)' }">
        {{ $t("formatConvert.sourceFormat") }}: <strong>{{ sourceFormat }}</strong>
        &rarr; {{ $t("formatConvert.targetFormat") }}: <strong>PDF</strong>
      </div>

      <div class="mt-6 flex gap-3">
        <UButton color="primary" :disabled="!file" :loading="converting" @click="convert">
          <UIcon name="i-heroicons-arrow-path" class="w-4 h-4 mr-1.5" />
          {{ converting ? $t("common.processing") : $t("formatConvert.convert") }}
        </UButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const converting = ref(false);

const sourceFormat = computed(() => {
  if (!file.value) return "";
  const ext = file.value.name.split(".").pop()?.toLowerCase();
  return ext === "docx" ? "DOCX" : ext === "html" || ext === "htm" ? "HTML" : ext?.toUpperCase() || "";
});

function onFileSelected(f: File) {
  file.value = f;
}

async function convert() {
  if (!file.value) return;
  converting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    fd.append("target_format", "pdf");

    const resp = await axios.post("/api/convert/format", fd, { responseType: "blob" });
    const url = URL.createObjectURL(resp.data);
    const baseName = file.value.name.replace(/\.\w+$/, "");
    const a = document.createElement("a");
    a.href = url;
    a.download = `${baseName}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    const msg = await e.response?.data?.text?.() || e.message;
    toast.add({ title: msg ? JSON.parse(msg).error || msg : e.message, color: "error" });
  } finally {
    converting.value = false;
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
