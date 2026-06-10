<template>
  <div
    class="border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-150 cursor-pointer"
    :style="isDragover
      ? { borderColor: 'var(--color-brand-700)', backgroundColor: 'var(--color-brand-soft)' }
      : { borderColor: 'var(--color-border-default)', backgroundColor: 'var(--color-surface)' }"
    @dragover.prevent="isDragover = true"
    @dragleave.prevent="isDragover = false"
    @drop.prevent="onDrop"
  >
    <!-- Empty state -->
    <div v-if="!fileName" class="flex flex-col items-center gap-2">
      <UIcon :name="icon" class="w-8 h-8 text-tertiary"  />
      <p class="text-sm text-secondary" >{{ $t("common.uploadHint") }}</p>
      <p v-if="hint" class="text-xs text-pretty text-tertiary" >{{ hint }}</p>
      <label class="cursor-pointer">
        <UButton color="primary" variant="soft" as="span">
          {{ $t("common.upload") }}
        </UButton>
        <input
          type="file"
          :accept="accept"
          v-bind="$attrs"
          class="hidden"
          @change="onFileInput"
        />
      </label>
    </div>

    <!-- File selected -->
    <div v-else class="flex items-center gap-3 text-left">
      <UIcon :name="fileIcon" class="w-6 h-6 shrink-0 text-tertiary"  />
      <div class="flex-1 min-w-0">
        <span class="font-semibold text-sm block truncate text-primary" >{{ fileName }}</span>
        <span v-if="fileSize" class="text-xs text-pretty text-tertiary" >{{ formatSize(fileSize) }}</span>
      </div>
      <UButton size="xs" variant="ghost" color="neutral" @click="reset">
        {{ $t("common.reset") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  icon: { type: String, default: "i-heroicons-arrow-up-tray" },
  hint: { type: String, default: "" },
  accept: { type: String, default: "" },
});

const emit = defineEmits<{
  "file-selected": [file: File];
  reset: [];
}>();

const isDragover = ref(false);
const fileName = ref("");
const fileSize = ref(0);
const file = ref<File | null>(null);

const fileIcon = computed(() => {
  const ext = (fileName.value || "").split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    docx: "i-heroicons-document-text",
    xlsx: "i-heroicons-table-cells",
    pptx: "i-heroicons-presentation-chart-bar",
    pdf: "i-heroicons-document",
    png: "i-heroicons-photo",
    jpg: "i-heroicons-photo",
    jpeg: "i-heroicons-photo",
    tiff: "i-heroicons-photo",
    tif: "i-heroicons-photo",
    csv: "i-heroicons-table-cells",
  };
  return map[ext] || "i-heroicons-document";
});

function onFileInput(evt: Event) {
  const target = evt.target as HTMLInputElement;
  const f = target.files?.[0];
  if (f) setFile(f);
}

function onDrop(evt: DragEvent) {
  isDragover.value = false;
  const f = evt.dataTransfer?.files?.[0];
  if (f) setFile(f);
}

function setFile(f: File) {
  file.value = f;
  fileName.value = f.name;
  fileSize.value = f.size;
  emit("file-selected", f);
}

function reset() {
  file.value = null;
  fileName.value = "";
  fileSize.value = 0;
  emit("reset");
}

function formatSize(bytes: number): string {
  if (!bytes) return "";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

defineExpose({ setFile });
</script>
