<template>
  <p class="kicker">{{ text }}</p>
</template>

<script setup lang="ts">
defineProps<{ text: string }>();
</script>
