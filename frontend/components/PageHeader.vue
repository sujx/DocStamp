<template>
  <div class="mb-6">
    <ULink :to="backTo" class="inline-flex items-center gap-1 text-sm text-secondary hover:text-brand-700 transition-colors duration-150">
      <UIcon name="i-heroicons-arrow-left" class="w-4 h-4" />
      {{ $t("common.back") }}
    </ULink>
    <h1 v-if="title" class="text-2xl font-bold text-primary mt-2">{{ title }}</h1>
    <p v-if="description" class="text-sm text-secondary mt-1 text-pretty">{{ description }}</p>
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
