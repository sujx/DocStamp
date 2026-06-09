<template>
  <div>
    <div
      class="border-2 border-dashed rounded-lg p-12 text-center transition-colors duration-150 cursor-pointer"
      :class="isDragover ? 'border-[var(--color-brand-700)]' : 'border-[var(--color-border-default)]'"
      :style="{ backgroundColor: isDragover ? 'var(--color-brand-soft)' : 'var(--color-surface)' }"
      @dragover.prevent="isDragover = true"
      @dragleave.prevent="isDragover = false"
      @drop.prevent="onDrop"
    >
      <UIcon name="i-heroicons-document-text" class="w-12 h-12 mx-auto mb-3" :style="{ color: 'var(--color-text-tertiary)' }" />
      <p class="text-base font-medium mb-1" :style="{ color: 'var(--color-text-primary)' }">{{ $t("format.docxDragText") }}</p>
      <p class="text-sm mb-4" :style="{ color: 'var(--color-text-secondary)' }">{{ $t("format.docxFormats") }}</p>
      <label>
        <UButton color="primary" variant="soft" as="span">{{ $t("format.upload") }}</UButton>
        <input type="file" accept=".docx" class="hidden" @change="onFileSelect" />
      </label>
    </div>

    <div v-if="selectedFile" class="p-4 mt-4 rounded-lg" :style="{ backgroundColor: 'var(--color-surface)', boxShadow: 'var(--shadow-card)' }">
      <div class="flex items-center gap-3 mb-4">
        <UIcon name="i-heroicons-document-text" class="w-5 h-5 shrink-0" :style="{ color: 'var(--color-brand-700)' }" />
        <span class="flex-1 text-sm font-medium truncate" :style="{ color: 'var(--color-text-primary)' }">{{ selectedFile.name }}</span>
        <UButton size="xs" variant="ghost" color="neutral" @click="selectedFile = null">{{ $t("common.reset") }}</UButton>
      </div>
      <UButton color="primary" :loading="isFormatting" block @click="formatFile">
        {{ isFormatting ? $t("format.formatting") : $t("format.downloadDocx") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();
const toast = useToast();
const API = "http://localhost:5000";

const isDragover = ref(false);
const selectedFile = ref<File | null>(null);
const isFormatting = ref(false);

function onDrop(evt: DragEvent) {
  isDragover.value = false;
  const f = evt.dataTransfer?.files?.[0];
  if (f?.name.endsWith(".docx")) selectedFile.value = f;
}
function onFileSelect(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (f) selectedFile.value = f;
}

async function formatFile() {
  if (!selectedFile.value) return;
  isFormatting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    const resp = await fetch(`${API}/api/v1/convert/format-docx`, { method: "POST", body: fd });
    if (!resp.ok) throw new Error((await resp.json()).error || `HTTP ${resp.status}`);
    const json = await resp.json();

    const dlResp = await fetch(`${API}/api/v1/download/${json.download_id}`);
    if (!dlResp.ok) throw new Error(`Download failed: HTTP ${dlResp.status}`);
    const blob = await dlResp.blob();

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = json.filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    toast.add({ title: e.message || "Error", color: "error" });
  } finally {
    isFormatting.value = false;
  }
}
</script>
