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

    <UNotifications />
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

const localeHead = useLocaleHead({ seo: false, dir: false });

useHead({
  titleTemplate: "%s - 鹊随金印",
  meta: [
    { name: "description", content: "鹊随金印 — 一站式文档处理工具箱。Markdown 转 GB/T 9704 公文、PDF 脱敏打码、Word 格式规范、PDF 合并压缩页码、Excel 合并、属性清理，即开即用。" },
    { name: "theme-color", content: "#3B63D8" },
    { name: "keywords", content: "文档处理,公文格式,GB/T 9704,Markdown转公文,PDF脱敏,PDF合并,PDF压缩,Word格式规范,Excel合并" },
    { property: "og:title", content: "鹊随金印 - 文档处理工具箱" },
    { property: "og:description", content: "一站式文档处理，14项功能，即开即用" },
    { property: "og:type", content: "website" },
  ],
  htmlAttrs: computed(() => localeHead.value?.htmlAttrs ?? {}),
});
</script>
