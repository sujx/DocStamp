<template>
  <div class="min-h-dvh" :style="{ backgroundColor: 'var(--color-page)' }">
    <!-- Skip-to-content for keyboard users -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[60] focus:px-4 focus:py-2 focus:rounded-md focus:text-sm focus:font-medium focus:no-underline"
      :style="{ backgroundColor: 'var(--color-surface)', color: 'var(--color-brand-700)', boxShadow: 'var(--shadow-elevated)' }"
    >
      {{ $t("a11y.skipToContent") }}
    </a>

    <Sidebar />
    <div
      class="min-h-dvh flex flex-col transition-[margin-left] duration-150"
      :style="{ marginLeft: sidebarWidth + 'px' }"
    >
      <main id="main-content" class="flex-1">
        <NuxtPage />
      </main>
      <AppFooter />
    </div>
  </div>
</template>

<script setup lang="ts">
const sidebarWidth = inject("sidebarWidth", ref(240));

useHead({
  titleTemplate: "%s - 鹊随金印",
  meta: [
    { name: "description", content: "鹊随金印 文档处理工具箱" },
    { name: "theme-color", content: "#008a3d" },
  ],
  htmlAttrs: { lang: "zh-CN" },
});
</script>

<style scoped>
/* Layout shell — all visual styles live in child components */
</style>
