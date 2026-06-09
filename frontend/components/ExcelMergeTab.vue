<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("excelMerge.title") }}</h2>
    <p class="text-sm mb-5 text-pretty" :style="{ color: 'var(--color-text-secondary)' }">{{ $t("excelMerge.description") }}</p>

    <label class="block mb-4">
      <UButton color="primary" variant="soft" as="span">
        <UIcon name="i-heroicons-table-cells" class="w-4 h-4 mr-1" />
        {{ $t("excelMerge.selectFiles") }}
      </UButton>
      <input type="file" multiple accept=".xlsx,.csv" class="hidden" @change="onFilesSelected" />
    </label>

    <div v-if="files.length" class="p-3 rounded-md mb-4" style="background:#fff; border:1px solid #e8e6d8;">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold" :style="{ color: 'var(--color-text-secondary)' }">{{ $t("excelMerge.fileCount", { n: files.length }) }}</span>
        <UButton size="xs" variant="ghost" color="neutral" @click="files=[]">{{ $t("common.reset") }}</UButton>
      </div>
      <div
        v-for="(f, idx) in files" :key="f.id"
        class="flex items-center gap-2 py-2 border-t"
        style="border-color:#e8e6d8;"
      >
        <UIcon name="i-heroicons-table-cells" class="w-4 h-4 shrink-0" :style="{ color: 'var(--color-text-tertiary)' }" />
        <span class="flex-1 text-sm truncate" :style="{ color: 'var(--color-text-primary)' }">{{ f.name }}</span>
        <span v-if="f.rowCount !== null" class="text-xs shrink-0" :style="{ color: 'var(--color-text-tertiary)' }">{{ $t("excelMerge.rowsCount", { n: f.rowCount }) }}</span>
        <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-x-mark" :aria-label="$t('common.removeFile')" @click="files.splice(idx,1)" />
      </div>
    </div>

    <div v-if="files.length >= 2" class="p-4 rounded-lg" :style="{ backgroundColor: 'var(--color-surface)' }">
      <UFormGroup :label="$t('excelMerge.outputFilename')" class="mb-4">
        <UInput v-model="outputFilename" :placeholder="defaultFilename" />
      </UFormGroup>
      <UButton color="primary" :loading="isProcessing" block @click="merge">
        {{ $t("excelMerge.merge") }}
      </UButton>
    </div>

    <UAlert
      v-else-if="files.length === 1"
      color="warning"
      :title="$t('excelMerge.needMoreFiles')"
      variant="soft"
      class="mt-4"
    />
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const { downloadBlob, showError } = useDownload();

let idCounter = 0;

const files = ref<{id:number;name:string;file:File;rowCount:number|null}[]>([]);
const isProcessing = ref(false);
const outputFilename = ref("");

const defaultFilename = computed(() => "merged.xlsx");

function onFilesSelected(evt: Event) {
  const fileList = (evt.target as HTMLInputElement).files;
  if (!fileList) return;
  for (const f of fileList) {
    const ext = f.name.toLowerCase().split(".").pop();
    if (ext !== "xlsx" && ext !== "csv") continue;
    files.value.push({ id: ++idCounter, name: f.name, file: f, rowCount: null });
  }
}

async function merge() {
  if (files.value.length < 2) return;
  isProcessing.value = true;
  try {
    const fd = new FormData();
    for (const f of files.value) fd.append("files", f.file);
    const fname = outputFilename.value.trim() || defaultFilename.value;
    fd.append("filename", fname);
    const resp = await axios.post("/api/v1/excel-merge", fd, { responseType: "blob" });
    downloadBlob(resp.data, fname, t("common.success"));
  } catch (e) { showError(e); }
  finally { isProcessing.value = false; }
}
</script>
