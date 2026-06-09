<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <UIcon :name="icon" class="w-16 h-16 mb-4"  />
    <h3 class="text-lg font-semibold mb-1 text-balance" >{{ title }}</h3>
    <p class="text-sm mb-6 max-w-md" >{{ description }}</p>
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
