<template>
  <div
    class="card-base"
    :style="{ borderRadius: `var(--radius-${radius})` }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  radius?: "sm" | "md" | "lg";
}>(), {
  radius: "md",
});
</script>

<style scoped>
.card-base {
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  padding: 1rem;
}
</style>
