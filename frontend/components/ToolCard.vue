<template>
  <NuxtLink
    :to="to"
    class="card card-interactive group flex items-start gap-4"
  >
    <div class="icon-badge shrink-0">
      <UIcon :name="icon" class="size-[18px]" />
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="text-[15px] font-medium leading-tight text-primary">{{ title }}</h3>
      <p class="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-secondary">{{ description }}</p>
      <p v-if="flag" class="mt-2 text-[12px] leading-relaxed text-tertiary">{{ flag }}</p>
    </div>
    <UIcon
      name="i-heroicons-arrow-right"
      class="mt-2 size-[18px] shrink-0 text-tertiary transition-colors group-hover:text-brand-600"
    />
  </NuxtLink>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon: string;
  title: string;
  description: string;
  to: string;
  flag?: string;
}>(), {
  flag: undefined,
});
</script>
