<template>
  <div class="animate-pulse rounded bg-muted" :class="[width, height]" />
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  width?: string
  height?: string
}>(), {
  width: 'w-full',
  height: 'h-4',
});
</script>
