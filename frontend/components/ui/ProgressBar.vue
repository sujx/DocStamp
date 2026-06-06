<template>
  <div
    class="progress-bar-wrapper"
    role="progressbar"
    :aria-valuenow="value"
    aria-valuemin="0"
    aria-valuemax="100"
    :aria-label="label"
  >
    <div class="progress-bar-track">
      <div
        class="progress-bar-fill"
        :style="{ width: `${Math.min(100, Math.max(0, value))}%` }"
      />
    </div>
    <span v-if="showLabel" class="progress-bar-label">{{ label || `${value}%` }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  value: number;
  label?: string;
  showLabel?: boolean;
}>(), {
  showLabel: true,
});
</script>

<style scoped>
.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar-track {
  flex: 1;
  height: 8px;
  background: var(--color-muted, #f4f2e4);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-brand-700);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-bar-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

@media (prefers-contrast: high) {
  .progress-bar-track {
    border: 1px solid var(--color-border-default);
  }
}
</style>
