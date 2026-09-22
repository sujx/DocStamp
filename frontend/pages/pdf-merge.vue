<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pdfMerge.title')" :description="$t('pdfMerge.description')" />

    <div class="card bg-surface border-default" >
      <FileUploader
        :accept="'.pdf'"
        :max-size="100"
        :multiple="true"
        :label="$t('pdfMerge.uploadLabel')"
        @files-selected="onFilesSelected"
      />

      <div v-if="files.length > 0" class="mt-4">
        <div class="text-sm mb-2 text-secondary" >
          {{ $t('pdfMerge.fileCount', { n: files.length }) }}
        </div>
        <p class="text-xs mb-3 text-tertiary" >{{ $t('pdfMerge.dragHint') }}</p>

        <div class="space-y-1.5">
          <div
            v-for="(f, i) in files" :key="f.name"
            class="flex items-center gap-2 px-3 py-2 rounded-md text-sm border"
            :style="{ backgroundColor: 'var(--color-muted)', borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }"
          >
            <UIcon name="i-heroicons-bars-3" class="w-4 h-4 shrink-0 cursor-move text-tertiary"  />
            <span class="flex-1 truncate">{{ f.name }}</span>
            <button
              :disabled="i === 0"
              class="p-1 rounded hover:bg-[var(--color-border-subtle)] disabled:opacity-30"
              :aria-label="$t('pdfMerge.moveUp')"
              @click="moveUp(i)"
            >
              <UIcon name="i-heroicons-chevron-up" class="w-3.5 h-3.5" />
            </button>
            <button
              :disabled="i === files.length - 1"
              class="p-1 rounded hover:bg-[var(--color-border-subtle)] disabled:opacity-30"
              :aria-label="$t('pdfMerge.moveDown')"
              @click="moveDown(i)"
            >
              <UIcon name="i-heroicons-chevron-down" class="w-3.5 h-3.5" />
            </button>
            <button
              class="p-1 rounded hover:bg-[var(--color-border-subtle)]"
              :aria-label="$t('pdfMerge.removeFile')"
              @click="removeFile(i)"
            >
              <UIcon name="i-heroicons-x-mark" class="w-3.5 h-3.5 text-tertiary"  />
            </button>
          </div>
        </div>

        <div class="mt-6 flex gap-3">
          <UButton
            color="primary"
            :disabled="files.length < 2" :loading="merging"
            @click="merge"
          >
            <UIcon name="i-heroicons-arrows-right-left" class="w-4 h-4 mr-1.5" />
            {{ merging ? $t("common.processing") : $t("pdfMerge.merge") }}
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const { showError } = useApiError();
const { downloadBlob } = useDownload();

const files = ref<File[]>([]);
const merging = ref(false);

function onFilesSelected(newFiles: File[]) {
  files.value = [...files.value, ...newFiles];
}

function moveUp(i: number) {
  if (i > 0) {
    const arr = [...files.value];
    [arr[i - 1], arr[i]] = [arr[i], arr[i - 1]];
    files.value = arr;
  }
}

function moveDown(i: number) {
  if (i < files.value.length - 1) {
    const arr = [...files.value];
    [arr[i], arr[i + 1]] = [arr[i + 1], arr[i]];
    files.value = arr;
  }
}

function removeFile(i: number) {
  files.value = files.value.filter((_, idx) => idx !== i);
}

async function merge() {
  if (files.value.length < 2) return;
  merging.value = true;
  try {
    const fd = new FormData();
    for (const f of files.value) {
      fd.append("files", f);
    }
    fd.append("filename", "merged.pdf");

    const resp = await axios.post("/api/v1/pdf-merge", fd, { responseType: "blob" });
    downloadBlob(resp.data, "merged.pdf", t("common.success"));
  } catch (e: any) {
    showError(e);
  } finally {
    merging.value = false;
  }
}
</script>

