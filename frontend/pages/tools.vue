<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
    <!-- Page title -->
    <div class="mb-8 animate-fade-up">
      <h1 class="text-[28px] font-medium leading-tight text-primary">{{ t("dashboard.heroTitle") }}</h1>
      <p class="mt-2 max-w-xl text-[15px] leading-relaxed text-secondary">{{ t("dashboard.heroSubtitle") }}</p>
    </div>

    <!-- Tool grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
      <ToolCard
        v-for="tool in cards"
        :key="tool.to"
        :icon="tool.icon"
        :title="tool.title"
        :description="tool.description"
        :to="tool.to"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { TOOLS } from "~/composables/tools.config";

const { t } = useI18n();

useHead({
  title: computed(() => t("dashboard.metaTitle")),
  meta: [{ name: "description", content: computed(() => t("dashboard.metaDescription")) }],
});

const CONVERT_KEYS = ["md2docx", "format-docx", "meeting-minutes"];
const PDF_KEYS = ["file-assembly", "print-split", "pdf-editor", "pdf-tools", "pdf-merge", "pdf-redact"];
const OFFICE_KEYS = ["properties", "excel-merge"];

function mapTool(key: string) {
  const tool = TOOLS.find(t => t.key === key)!;
  return {
    to: tool.to,
    icon: tool.icon,
    title: t(tool.label),
    description: t(tool.desc!),
  };
}

const REST_KEYS = TOOLS
  .filter(t => t.key !== "dashboard" && t.key !== "status"
    && !CONVERT_KEYS.includes(t.key)
    && !PDF_KEYS.includes(t.key)
    && !OFFICE_KEYS.includes(t.key))
  .sort((a, b) => a.order - b.order)
  .map(t => t.key);

const cards = computed(() =>
  [...CONVERT_KEYS, ...PDF_KEYS, ...OFFICE_KEYS, ...REST_KEYS].map(mapTool),
);
</script>
