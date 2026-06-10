<template>
  <NuxtLink
    :to="to"
    class="block p-6 rounded-lg border border-transparent transition-[box-shadow,transform] duration-200 hover:-translate-y-0.5 group cursor-pointer bg-surface shadow-card"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  >
    <div
      class="w-12 h-12 rounded-full flex items-center justify-center mb-4 transition-colors duration-150"
      :style="{ backgroundColor: hover ? 'var(--color-brand-700)' : 'var(--color-brand-soft)' }"
    >
      <UIcon
        :name="icon"
        class="w-6 h-6 transition-colors duration-150"
        :style="{ color: hover ? '#fff' : 'var(--color-brand-700)' }"
      />
    </div>
    <h3 class="text-lg font-semibold mb-1 text-balance text-primary">{{ title }}</h3>
    <p class="text-sm text-pretty text-secondary">{{ description }}</p>
  </NuxtLink>
</template>

<script setup lang="ts">
defineProps<{ icon: string; title: string; description: string; to: string }>();
const hover = ref(false);
</script>
