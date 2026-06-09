<template>
  <div class="max-w-3xl mx-auto px-6 py-8">
    <PageHeader :title="$t('pdfCompress.title')" :description="$t('pdfCompress.description')" />

    <div class="card" >
      <FileUploader
        :accept="'.pdf'"
        :max-size="100"
        :label="$t('common.upload')"
        @file-selected="onFileSelected"
      />

      <UFormGroup v-if="file" :label="$t('pdfCompress.quality')" class="mt-4">
        <div class="flex gap-3">
          <label v-for="q in qualities" :key="q.key" class="flex items-center gap-1.5 cursor-pointer text-sm" >
            <input v-model="quality" type="radio" :value="q.key" class="accent-brand-700" />
            {{ q.label }}
          </label>
        </div>
      </UFormGroup>

      <div class="mt-6 flex gap-3">
        <UButton color="primary" :disabled="!file" :loading="compressing" @click="compress">
          <UIcon name="i-heroicons-arrows-pointing-in" class="w-4 h-4 mr-1.5" />
          {{ compressing ? $t("common.processing") : $t("pdfCompress.compress") }}
        </UButton>
      </div>

      <div v-if="stats" class="mt-6 p-4 rounded-lg border" >
        <div class="text-sm space-y-1">
          <div >
            {{ $t("pdfCompress.originalSize") }}: <strong>{{ formatSize(stats.original_size) }}</strong>
          </div>
          <div >
            {{ $t("pdfCompress.compressedSize") }}: <strong>{{ formatSize(stats.compressed_size) }}</strong>
          </div>
          <div >
            {{ $t("pdfCompress.ratio") }}: <strong>{{ stats.ratio }}%</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const quality = ref("medium");
const compressing = ref(false);
const stats = ref<{ original_size: number; compressed_size: number; ratio: number } | null>(null);

const qualities = [
  { key: "low", label: t("pdfCompress.low") },
  { key: "medium", label: t("pdfCompress.medium") },
  { key: "high", label: t("pdfCompress.high") },
];

function onFileSelected(f: File) {
  file.value = f;
  stats.value = null;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function compress() {
  if (!file.value) return;
  compressing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    fd.append("quality", quality.value);

    const resp = await axios.post("/api/v1/pdf-compress", fd, { responseType: "blob" });
    stats.value = {
      original_size: Number(resp.headers["x-original-size"]),
      compressed_size: Number(resp.headers["x-compressed-size"]),
      ratio: Number(resp.headers["x-compression-ratio"]),
    };

    const url = URL.createObjectURL(resp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `compressed_${file.value.name}`;
    a.click();
    URL.revokeObjectURL(url);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    const msg = await e.response?.data?.text?.() || e.message;
    toast.add({ title: msg ? JSON.parse(msg).error || msg : e.message, color: "error" });
  } finally {
    compressing.value = false;
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
