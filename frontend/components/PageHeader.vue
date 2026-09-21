<template>
  <div class="mb-6">
    <ULink
      :to="backTo"
      class="inline-flex items-center gap-1.5 text-xs font-medium text-tertiary hover:text-brand-600 transition-colors duration-150 mb-2"
    >
      <UIcon name="i-heroicons-arrow-left" class="size-3.5" />
      {{ $t("common.back") }}
    </ULink>
    <h1 v-if="title" class="text-xl font-bold text-primary tracking-tight">{{ title }}</h1>
    <p v-if="description" class="text-sm text-secondary mt-1 leading-relaxed text-pretty">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  backTo?: string
  title?: string
  description?: string
}>(), {
  backTo: "/",
});
</script>
