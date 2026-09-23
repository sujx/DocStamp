<template>
  <div
    class="border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer"
    :class="isDragover
      ? 'border-brand-600 bg-brand-soft/60 scale-[1.01]'
      : 'border-default bg-surface hover:border-brand-300 hover:bg-muted/30'"
    @dragover.prevent="isDragover = true"
    @dragleave.prevent="isDragover = false"
    @drop.prevent="onDrop"
  >
    <!-- Empty state -->
    <div v-if="!fileName" class="flex flex-col items-center gap-2">
      <div class="icon-badge mb-1">
        <UIcon :name="icon" class="size-5" />
      </div>
      <p class="text-sm text-secondary">{{ $t("common.uploadHint") }}</p>
      <p v-if="hint" class="text-xs text-pretty text-tertiary">{{ hint }}</p>
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
      <div class="icon-badge !size-10 shrink-0">
        <UIcon :name="fileIcon" class="size-5" />
      </div>
      <div class="flex-1 min-w-0">
        <span class="font-semibold text-sm block truncate text-primary">{{ fileName }}</span>
        <span v-if="fileSize" class="text-xs text-pretty text-tertiary tabular-nums">{{ formatSize(fileSize) }}</span>
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
  maxSize: { type: Number, default: 0 },
});

const emit = defineEmits<{
  "file-selected": [file: File];
  "file-rejected": [reason: string];
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
    webp: "i-heroicons-photo",
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
  if (props.maxSize > 0 && f.size > props.maxSize) {
    emit("file-rejected", `File exceeds ${formatSize(props.maxSize)} limit`);
    return;
  }
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
