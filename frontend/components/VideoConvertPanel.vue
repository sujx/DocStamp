<template>
  <div class="card bg-surface border-default">
    <FileUploader
      :accept="'.mp4,.mov,.avi,.mkv'"
      :label="$t('videoConvert.uploadLabel')"
      :hint="$t('videoConvert.sizeHint')"
      @file-selected="onFileSelected"
    />

    <p class="text-xs mt-2 text-tertiary">
      <UIcon name="i-heroicons-information-circle" class="w-3.5 h-3.5 inline" />
      {{ $t("videoConvert.note") }}
    </p>

    <div class="mt-6 flex gap-3">
      <UButton
        color="primary"
        :disabled="!file"
        :loading="converting"
        @click="convert"
      >
        <UIcon name="i-heroicons-video-camera" class="w-4 h-4 mr-1.5" />
        {{ converting ? $t("common.processing") : $t("videoConvert.convert") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const converting = ref(false);

function onFileSelected(f: File) {
  file.value = f;
}

async function convert() {
  if (!file.value) return;
  converting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);

    const resp = await axios.post("/api/v1/video-convert", fd, { responseType: "blob" });
    const base = file.value.name.replace(/\.[^.]+$/, "");
    const url = URL.createObjectURL(resp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${base}.wmv`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    toast.add({ title: e.response?.data?.error || e.message, color: "error" });
  } finally {
    converting.value = false;
  }
}
</script>
