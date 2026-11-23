<template>
  <div>
    <!-- Mode selection cards -->
    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
      <button
        v-for="mode in modes" :key="mode.key"
        class="flex items-center gap-3 rounded-lg border p-5 text-left shadow-card transition-colors"
        :class="activeMode === mode.key
          ? 'border-brand-600 bg-brand-soft'
          : 'border-default bg-surface hover:border-strong'"
        @click="activeMode = mode.key"
      >
        <div class="icon-badge shrink-0" :class="{ 'text-brand-600': activeMode === mode.key }">
          <UIcon :name="mode.icon" class="size-[18px]" />
        </div>
        <span class="text-[13px] font-medium text-primary">{{ mode.title }}</span>
      </button>
    </div>

    <!-- Active content -->
    <Img2PdfTab v-if="activeMode === 'merge'" />
    <PdfToImagesTab v-if="activeMode === 'split'" />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();

const activeMode = ref("merge");

const modes = computed(() => [
  { key: "merge", icon: "i-heroicons-photo", title: t("fileAssembly.imagesToPdf") },
  { key: "split", icon: "i-heroicons-document", title: t("fileAssembly.pdfToImages") },
]);
</script>
