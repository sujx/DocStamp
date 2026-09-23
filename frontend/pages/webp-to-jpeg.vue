<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('webpToJpeg.title')" :description="$t('webpToJpeg.description')" />

    <div class="card bg-surface border-default">
      <FileUploader
        accept=".webp"
        icon="i-heroicons-photo"
        :hint="$t('webpToJpeg.hint')"
        @file-selected="onFileSelected"
        @reset="onReset"
      />

      <div v-if="file" class="mt-6">
        <UButton color="primary" :loading="converting" @click="convert">
          <UIcon name="i-heroicons-arrow-down-tray" class="w-4 h-4 mr-1.5" />
          {{ converting ? $t("common.processing") : $t("webpToJpeg.convert") }}
        </UButton>
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
const converting = ref(false);

function onFileSelected(f: File) {
  file.value = f;
}

function onReset() {
  file.value = null;
}

async function convert() {
  if (!file.value) return;
  converting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);
    const resp = await axios.post("/api/v1/webp-to-jpeg", fd, { responseType: "blob" });
    const name = file.value.name.replace(/\.webp$/i, "") + ".jpg";
    downloadBlob(resp.data, name, t("common.success"));
  } catch (e: any) {
    showError(e);
  } finally {
    converting.value = false;
  }
}
</script>
