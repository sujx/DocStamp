<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('pdfMerge.title')" :description="$t('pdfMerge.description')" />

    <div class="card bg-surface border-default" >
      <FileUploader
        :accept="'.pdf'"
        :max-size="100"
        :label="$t('pdfMerge.uploadLabel')"
        @file-selected="onFileSelected"
        @file-rejected="onFileRejected"
      />

      <div v-if="files.length > 0" class="mt-4">
        <div class="text-sm mb-2 text-secondary" >
          {{ $t('pdfMerge.fileCount', { n: files.length }) }}
        </div>
        <p class="text-xs mb-3 text-tertiary" >{{ $t('pdfMerge.dragHint') }}</p>

        <div class="space-y-1.5">
          <div
            v-for="(f, i) in files" :key="f.name"
            class="flex items-center gap-2 rounded-md border border-subtle bg-muted px-3 py-2 text-[13px] text-primary"
          >
            <UIcon name="i-heroicons-bars-3" class="size-4 shrink-0 cursor-move text-tertiary"  />
            <span class="flex-1 truncate">{{ f.name }}</span>
            <button
              :disabled="i === 0"
              class="p-1 rounded hover:bg-raised disabled:opacity-30"
              :aria-label="$t('pdfMerge.moveUp')"
              @click="moveUp(i)"
            >
              <UIcon name="i-heroicons-chevron-up" class="size-4" />
            </button>
            <button
              :disabled="i === files.length - 1"
              class="p-1 rounded hover:bg-raised disabled:opacity-30"
              :aria-label="$t('pdfMerge.moveDown')"
              @click="moveDown(i)"
            >
              <UIcon name="i-heroicons-chevron-down" class="size-4" />
            </button>
            <button
              class="p-1 rounded hover:bg-raised"
              :aria-label="$t('pdfMerge.removeFile')"
              @click="removeFile(i)"
            >
              <UIcon name="i-heroicons-x-mark" class="size-4 text-tertiary"  />
            </button>
          </div>
        </div>

        <div class="mt-6 flex gap-3">
          <UButton
            color="primary"
            :disabled="files.length < 2" :loading="merging"
            @click="merge"
          >
            <UIcon name="i-heroicons-arrows-right-left" class="size-4 mr-1.5" />
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
const toast = useToast();

const files = ref<File[]>([]);
const merging = ref(false);

function onFileSelected(f: File) {
  files.value = [...files.value, f];
}

function onFileRejected(p: { name: string; size: number; maxSizeMb: number }) {
  toast.add({ title: t("common.fileTooLarge", p), color: "warning" });
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

