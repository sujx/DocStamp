<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <!-- Hero -->
    <div class="relative overflow-hidden rounded-xl border border-brand-200/60 bg-gradient-to-br from-brand-50 via-white to-brand-50/30 shadow-sm mb-8 px-5 py-5 animate-fade-up">
      <div class="relative z-10 flex items-start gap-4">
        <div class="icon-badge shrink-0 !size-12">
          <UIcon name="i-heroicons-sparkles" class="size-6" />
        </div>
        <div>
          <h1 class="text-xl font-bold gradient-text mb-1">{{ t("dashboard.heroTitle") }}</h1>
          <p class="text-sm text-secondary leading-relaxed">{{ t("dashboard.heroSubtitle") }}</p>
        </div>
      </div>
      <div class="absolute -right-8 -top-8 size-32 rounded-full bg-brand-100/40 blur-2xl" />
      <div class="absolute -right-4 -bottom-10 size-24 rounded-full bg-brand-200/20 blur-xl" />
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

const CONVERT_KEYS = ["md2docx", "format-docx"];
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
