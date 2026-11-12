<template>
  <header class="sticky top-0 z-50 border-b border-default bg-surface/95 backdrop-blur">
    <div class="mx-auto flex h-14 max-w-5xl items-center gap-2 px-3 sm:gap-6 sm:px-6">
      <NuxtLink to="/" class="flex min-h-[44px] items-center gap-2.5 no-underline">
        <span class="seal-dot">印</span>
        <!-- 320px 下「印章 + 四字品牌 + 药丸 + CTA」横排放不下（实测英文 CTA 124px），
             品牌字会折成两行撑破顶栏；窄屏只留印章，文字 sr-only 保住可访问名。 -->
        <span class="sr-only font-official text-lg font-bold text-primary sm:not-sr-only">鹊随金印</span>
      </NuxtLink>

      <nav class="ml-auto flex items-center gap-2 sm:gap-3 md:gap-5" :aria-label="$t('landing.nav.ariaLabel')">
        <a
          v-for="anchor in anchors"
          :key="anchor.href"
          :href="anchor.href"
          class="hidden min-h-[44px] items-center text-sm text-secondary no-underline transition-colors duration-150 hover:text-brand-600 sm:inline-flex"
        >{{ anchor.label }}</a>

        <!-- 响应式 display 类必须挂在普通 div 上：LanguageSwitcher 根节点的
             scoped 规则 .lang-switcher[data-v] 是 (0,2,0)，会压过 .hidden /
             .md:hidden 的 (0,1,0)，直接写在组件上两份实例会同时可见。 -->
        <div class="lang-pill rounded-lg bg-brand-900 px-1.5">
          <div class="md:hidden"><LanguageSwitcher collapsed /></div>
          <div class="hidden md:block"><LanguageSwitcher /></div>
        </div>

        <NuxtLink
          to="/tools"
          class="inline-flex min-h-[44px] items-center whitespace-nowrap rounded-lg bg-brand-500 px-3 text-sm font-semibold text-white no-underline transition-colors duration-200 hover:bg-brand-600 sm:px-4"
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

/* collapsed 变体（md 以下那一份）在子组件里是「竖排 28px 方块」，它的
   .lang-switcher.collapsed .lang-btn[data-v] 与上面那条同为 (0,4,0)，靠源序
   就能赢回 28px；这里多一级选择器压过它。同时改回横排：两颗 44px 按钮竖排
   = 90px，会撑破 h-14（56px）的顶栏。
   完整标签那份放到 md 才出现：640–767px 英文下「品牌 + 三锚点 + 完整药丸
   + CTA」实测需 ~705px，sm 就换完整药丸会让 CTA 折行。 */
.lang-pill :deep(.lang-switcher.collapsed) {
  flex-direction: row;
}

.lang-pill :deep(.lang-switcher.collapsed .lang-btn) {
  width: auto;
  max-width: none;
  height: 44px;
  padding: 0 10px;
}
</style>
