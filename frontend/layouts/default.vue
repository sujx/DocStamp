<template>
  <div class="min-h-dvh" :style="{ backgroundColor: 'var(--color-page)' }">
    <Sidebar />
    <div class="min-h-dvh flex flex-col transition-all duration-200" :style="{ marginLeft: collapsed ? '64px' : '240px' }">
      <main class="flex-1">
        <NuxtPage />
      </main>
      <AppFooter />
    </div>
  </div>
</template>

<script setup lang="ts">
const collapsed = inject<Ref<boolean>>("sidebarCollapsed", ref(false));

if (import.meta.client) {
  useHead({
    titleTemplate: "%s - docStamp",
    meta: [
      { name: "description", content: "" },
      { name: "theme-color", content: "#008a3d" },
    ],
    htmlAttrs: { lang: "zh-CN" },
  });
}
</script>
