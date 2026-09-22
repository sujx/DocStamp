<template>
  <div class="min-h-dvh bg-page">
    <!-- Skip-to-content for keyboard users -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[60] focus:px-4 focus:py-2 focus:rounded-md focus:text-sm focus:font-medium focus:no-underline bg-surface text-brand-600 shadow-elevated"
    >
      {{ $t("a11y.skipToContent") }}
    </a>

    <Sidebar />
    <div
      class="min-h-dvh flex flex-col transition-[margin-left] duration-200 ease-out"
      :style="{ marginLeft: shellOffset + 'px' }"
    >
      <main id="main-content" class="flex-1">
        <NuxtPage />
      </main>
      <AppFooter />
    </div>
  </div>
</template>

<script setup lang="ts">
import { trackPageView } from "~/composables/usePageView";

const route = useRoute();
const { shellOffset } = useSidebar();
const { t } = useI18n();

onErrorCaptured((error, instance, info) => {
  console.error("[UI Error]", error, info);
  if (import.meta.client) {
    const toast = useToast();
    toast.add({ title: t("common.pageError"), color: "error" });
  }
  return false;
});

watch(() => route.fullPath, (path) => {
  trackPageView(path);
}, { immediate: true });

useHead({
  titleTemplate: "%s - 鹊随金印",
  meta: [
    { name: "description", content: "鹊随金印 — 一站式文档处理工具箱。MD转公文、文档转MD、PDF编辑、视频转换、Excel合并等13项功能，即开即用。" },
    { name: "theme-color", content: "#3B63D8" },
    { name: "keywords", content: "文档处理,PDF转换,MD转DOCX,视频转换,Excel合并,GB/T 9704" },
    { property: "og:title", content: "鹊随金印 - 文档处理工具箱" },
    { property: "og:description", content: "一站式文档处理，13项功能，即开即用" },
    { property: "og:type", content: "website" },
  ],
  htmlAttrs: { lang: "zh-CN" },
});
</script>
