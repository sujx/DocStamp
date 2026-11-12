<template>
  <header class="sticky top-0 z-50 border-b border-default bg-surface/95 backdrop-blur">
    <div class="mx-auto flex h-14 max-w-5xl items-center gap-3 px-4 sm:gap-6 sm:px-6">
      <NuxtLink to="/" class="flex items-center gap-2.5 no-underline">
        <span class="seal-dot">印</span>
        <span class="font-official text-lg font-bold text-primary">鹊随金印</span>
      </NuxtLink>

      <nav class="ml-auto flex items-center gap-3 sm:gap-5" :aria-label="$t('landing.nav.ariaLabel')">
        <a
          v-for="anchor in anchors"
          :key="anchor.href"
          :href="anchor.href"
          class="hidden min-h-[44px] items-center text-sm text-secondary no-underline transition-colors duration-150 hover:text-brand-600 sm:inline-flex"
        >{{ anchor.label }}</a>

        <div class="lang-pill hidden rounded-lg bg-sidebar px-1.5 sm:block">
          <LanguageSwitcher />
        </div>

        <NuxtLink
          to="/tools"
          class="inline-flex min-h-[44px] items-center rounded-lg bg-brand-500 px-4 text-sm font-semibold text-white no-underline transition-colors duration-200 hover:bg-brand-600"
        >{{ $t("landing.nav.cta") }}</NuxtLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
const { t } = useI18n();

const anchors = computed(() => [
  { href: "#tools", label: t("landing.nav.tools") },
  { href: "#promise", label: t("landing.nav.promise") },
  { href: "#resources", label: t("landing.nav.resources") },
]);
</script>

<style scoped>
/* LanguageSwitcher 自带 28px 按钮（为深色侧栏设计）。共享组件不动，
   在这里提到 44px：选择器比子组件的 scoped 规则多一级，稳定胜出。 */
.lang-pill :deep(.lang-switcher .lang-btn) {
  height: 44px;
  padding: 0 10px;
}
</style>