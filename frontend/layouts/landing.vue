<template>
  <div class="flex min-h-dvh flex-col bg-page">
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[60] focus:px-4 focus:py-2 focus:rounded-md focus:text-sm focus:font-medium focus:no-underline bg-surface text-brand-600 shadow-elevated"
    >
      {{ $t("a11y.skipToContent") }}
    </a>

    <LandingNav />

    <main id="main-content" class="flex-1">
      <NuxtPage />
    </main>

    <LandingFooter />

    <UNotifications />
  </div>
</template>

<script setup lang="ts">
const route = useRoute();

watch(() => route.fullPath, (path) => {
  trackPageView(path);
}, { immediate: true });

const localeHead = useLocaleHead({ seo: false, dir: false });

useHead({
  titleTemplate: "%s - 鹊随金印",
  htmlAttrs: computed(() => localeHead.value?.htmlAttrs ?? {}),
});
</script>
