<template>
  <div class="pt-3">
    <h2 class="text-[28px] font-medium leading-tight text-balance text-primary">{{ $t("excelMerge.title") }}</h2>
    <p class="mb-6 mt-2 max-w-xl text-[15px] text-pretty leading-relaxed text-secondary">{{ $t("excelMerge.description") }}</p>

    <label class="block mb-4">
      <UButton color="primary" variant="soft" as="span">
        <UIcon name="i-heroicons-table-cells" class="size-4 mr-1" />
        {{ $t("excelMerge.selectFiles") }}
      </UButton>
      <input type="file" multiple accept=".xlsx,.csv" class="hidden" @change="onFilesSelected" />
    </label>

    <div v-if="files.length" class="p-3 rounded-md mb-4 bg-surface border border-default">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[12px] font-medium text-secondary">{{ $t("excelMerge.fileCount", { n: files.length }) }}</span>
        <UButton size="xs" variant="ghost" color="neutral" @click="files=[]">{{ $t("common.reset") }}</UButton>
      </div>
      <div
        v-for="(f, idx) in files" :key="f.id"
        class="flex items-center gap-2 py-2 border-t border-subtle"
      >
        <UIcon name="i-heroicons-table-cells" class="size-4 shrink-0 text-tertiary"  />
        <span class="flex-1 text-sm truncate text-primary" >{{ f.name }}</span>
        <span v-if="f.rowCount !== null" class="text-xs shrink-0 text-tertiary" >{{ $t("excelMerge.rowsCount", { n: f.rowCount }) }}</span>
        <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-x-mark" :aria-label="$t('a11y.removeFile')" @click="files.splice(idx,1)" />
      </div>
    </div>

    <div v-if="files.length >= 2" class="p-4 rounded-lg bg-surface" >
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
const { downloadBlob } = useDownload();
const { showError } = useApiError();

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
