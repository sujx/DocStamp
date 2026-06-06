<template>
  <div>
    <!-- Mode selection cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
      <button
        v-for="mode in modes" :key="mode.key"
        class="text-left p-5 rounded-lg border-2 transition-all duration-150"
        :class="activeMode === mode.key
          ? 'border-[var(--color-brand-700)] bg-[var(--color-brand-soft)]'
          : 'border-[var(--color-border-default)] bg-[var(--color-surface)] hover:border-[var(--color-brand-400)]'"
        :style="{ boxShadow: 'var(--shadow-card)' }"
        @click="activeMode = mode.key"
      >
        <div class="flex items-center gap-3 mb-2">
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors duration-150"
            :class="activeMode === mode.key ? 'bg-[var(--color-brand-700)] text-white' : 'bg-[var(--color-brand-soft)] text-[var(--color-brand-700)]'"
          >
            <UIcon :name="mode.icon" class="w-5 h-5" />
          </div>
          <span class="font-semibold" :style="{ color: 'var(--color-text-primary)' }">{{ mode.title }}</span>
        </div>
        <p class="text-sm pl-[52px]" :style="{ color: 'var(--color-text-secondary)' }">{{ mode.desc }}</p>
      </button>
    </div>

    <!-- Active content -->
    <WatermarkTab v-if="activeMode === 'add'" />
    <RemoveWatermarkTab v-if="activeMode === 'remove'" />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();

const activeMode = ref("add");

const modes = computed(() => [
  { key: "add", icon: "i-heroicons-beaker", title: t("watermarkManagement.addWatermark"), desc: t("watermark.description") },
  { key: "remove", icon: "i-heroicons-beaker", title: t("watermarkManagement.removeWatermark"), desc: t("watermarkRemove.description") },
]);
</script>
