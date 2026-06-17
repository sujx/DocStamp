<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
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
import { DASHBOARD_TOOLS } from "~/composables/tools.config";

const { t } = useI18n();

const tools = computed(() =>
  DASHBOARD_TOOLS.map(tool => ({
    to: tool.to,
    icon: tool.icon,
    title: t(tool.label),
    description: t(tool.desc!),
  }))
);
</script>
