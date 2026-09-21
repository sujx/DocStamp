<template>
  <NuxtLink
    :to="to"
    class="card card-interactive group flex gap-4 p-4"
  >
    <div class="icon-badge shrink-0">
      <UIcon :name="icon" class="size-5" />
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="text-sm font-semibold text-primary leading-tight mb-1">{{ title }}</h3>
      <p class="text-xs text-secondary leading-relaxed line-clamp-2">{{ description }}</p>
    </div>
    <UIcon
      name="i-heroicons-arrow-right"
      class="size-4 shrink-0 self-center text-tertiary opacity-0 -translate-x-1 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-brand-600"
    />
  </NuxtLink>
</template>

<script setup lang="ts">
defineProps<{ icon: string; title: string; description: string; to: string }>();
</script>
