<template>
  <NuxtLink
    :to="to"
    class="card card-interactive group flex gap-5 p-5"
  >
    <div class="icon-badge shrink-0 !size-12">
      <UIcon :name="icon" class="size-6" />
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="text-[15px] font-semibold text-primary leading-tight mb-1.5">{{ title }}</h3>
      <p class="text-[13px] text-secondary leading-relaxed line-clamp-2">{{ description }}</p>
    </div>
    <UIcon
      name="i-heroicons-arrow-right"
      class="size-5 shrink-0 self-center text-tertiary opacity-0 -translate-x-1 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-brand-600"
    />
  </NuxtLink>
</template>

<script setup lang="ts">
defineProps<{ icon: string; title: string; description: string; to: string }>();
</script>
