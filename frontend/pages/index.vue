<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <div class="mb-10 flex items-center">
      <DigitalClock />
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <ToolCard
        v-for="tool in tools" :key="tool.to"
        :icon="tool.icon"
        :title="tool.title"
        :description="tool.description"
        :to="tool.to"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();

const tools = computed(() => [
  { to: "/md-to-docx", icon: "i-heroicons-document-text", title: t("tabs.md2docx"), description: t("md2docx.description") },
  { to: "/watermark", icon: "i-heroicons-beaker", title: t("tabs.watermarkManagement"), description: t("watermark.description") },
  { to: "/properties", icon: "i-heroicons-document-text", title: t("tabs.properties"), description: t("properties.description") },
  { to: "/excel-merge", icon: "i-heroicons-table-cells", title: t("tabs.excelMerge"), description: t("excelMerge.description") },
  { to: "/format-docx", icon: "i-heroicons-document-check", title: t("tabs.formatDocx"), description: t("format.description") },
  { to: "/file-assembly", icon: "i-heroicons-arrows-right-left", title: t("tabs.fileAssembly"), description: t("img2pdf.description") },
  { to: "/print-split", icon: "i-heroicons-printer", title: t("tabs.printSplit"), description: t("printSplit.description") },
  { to: "/pdf-editor", icon: "i-heroicons-document", title: t("tabs.pdfEditor"), description: t("pdfEditor.description") },
]);
</script>
