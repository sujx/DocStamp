<template>
  <div class="flex flex-col items-center justify-center py-16 text-center animate-fade-up">
    <div class="icon-badge !size-16 !rounded-xl mb-4">
      <UIcon :name="icon" class="size-8" />
    </div>
    <h3 class="text-lg font-semibold mb-1 text-balance text-primary">{{ title }}</h3>
    <p class="text-sm mb-6 max-w-md text-secondary leading-relaxed">{{ description }}</p>
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
