<template>
  <p class="text-[13px] font-semibold uppercase tracking-[0.18em] text-inherit">{{ text }}</p>
</template>

<script setup lang="ts">
defineProps<{ text: string }>();
</script>
