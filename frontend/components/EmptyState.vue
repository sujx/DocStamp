<template>
  <div class="flex flex-col items-center justify-center py-16 text-center animate-fade-up">
    <div class="icon-badge mb-4">
      <UIcon :name="icon" class="size-[18px]" />
    </div>
    <h3 class="mb-1 text-[15px] font-medium text-balance text-primary">{{ title }}</h3>
    <p class="mb-6 max-w-md text-[13px] leading-relaxed text-secondary">{{ description }}</p>
    <UButton v-if="actionTo" color="primary" :to="actionTo">{{ actionLabel }}</UButton>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string;
  title: string;
  description: string;
  actionLabel?: string;
  actionTo?: string;
}>();
</script>
