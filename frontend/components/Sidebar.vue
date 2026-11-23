<template>
  <!-- Hamburger toggle (mobile only) -->
  <button
    class="fixed top-4 left-4 z-50 lg:hidden flex items-center justify-center size-11 rounded-xl cursor-pointer bg-surface shadow-md"
    :aria-label="mobileOpen ? $t('a11y.closeNav') : $t('a11y.openNav')"
    @click="mobileOpen = !mobileOpen"
  >
    <UIcon
      :name="mobileOpen ? 'i-heroicons-x-mark' : 'i-heroicons-bars-3'"
      class="size-5 text-primary"
    />
  </button>

  <!-- Backdrop (mobile only) -->
  <Transition name="backdrop-fade">
    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-30 bg-black/40 lg:hidden"
      @click="mobileOpen = false"
    />
  </Transition>

  <!-- Sidebar: 单色深面板，层次靠表面台阶与细线 -->
  <aside
    class="sidebar-panel fixed z-40 flex flex-col transition-[width,transform] duration-200 overflow-hidden"
    :class="[
      collapsed && !isMobile ? 'w-[72px]' : 'w-64',
      isMobile && !mobileOpen ? '-translate-x-full' : 'translate-x-0',
    ]"
  >
    <div class="relative flex flex-col h-full">
      <!-- Logo area -->
      <div
        class="flex items-center h-14 px-4 shrink-0"
        :class="collapsed && !isMobile ? 'justify-center' : 'gap-2.5'"
      >
        <span class="seal-dot seal-dot--solid shrink-0">印</span>
        <div v-if="!(collapsed && !isMobile)" class="flex flex-col min-w-0">
          <span class="wordmark">鹊随金印</span>
          <span class="wordmark-sub">DOCSTAMP</span>
        </div>
      </div>

      <!-- Divider -->
      <div class="mx-4 h-px panel-hairline" />

      <!-- Nav items -->
      <nav class="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto scrollbar-thin">
        <NuxtLink
          v-for="item in navItems"
          :key="item.key"
          :to="item.to"
          class="nav-item group relative flex items-center min-h-[44px] lg:min-h-[36px] rounded-md text-[14px] cursor-pointer"
          :class="[
            collapsed && !isMobile ? 'justify-center px-1' : 'px-2.5 gap-2.5',
            isActive(item.to) ? 'nav-item--active' : 'nav-item--idle',
          ]"
          @click="mobileOpen = false"
        >
          <UIcon :name="item.icon" class="size-[18px] shrink-0" />
          <span v-if="!(collapsed && !isMobile)" class="truncate">{{ item.label }}</span>
        </NuxtLink>
      </nav>

      <!-- Bottom: language + collapse -->
      <div class="px-2 py-2 space-y-1 shrink-0 panel-hairline-top">
        <LanguageSwitcher :collapsed="collapsed && !isMobile" />
        <button
          v-if="!isMobile"
          class="collapse-btn flex items-center justify-center w-full min-h-[32px] rounded-md text-xs cursor-pointer"
          :class="collapsed && 'px-1'"
          :aria-label="collapsed ? $t('a11y.expandSidebar') : $t('a11y.collapseSidebar')"
          @click="toggleCollapsed"
        >
          <UIcon
            :name="collapsed ? 'i-heroicons-chevron-right' : 'i-heroicons-chevron-left'"
            class="size-[18px]"
          />
          <span v-if="!(collapsed && !isMobile)" class="ml-2">{{ $t('a11y.collapseSidebar') }}</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { SIDEBAR_ITEMS } from "~/composables/tools.config";

const { collapsed, isMobile, toggleCollapsed } = useSidebar();

const mobileOpen = ref(false);
const route = useRoute();
const { t } = useI18n();

watch(() => route.path, () => {
  if (isMobile.value) mobileOpen.value = false;
});

const navItems = computed(() =>
  SIDEBAR_ITEMS.map(tool => ({
    key: tool.key,
    to: tool.to,
    icon: tool.icon,
    label: t(tool.label),
  }))
);

function isActive(href: string): boolean {
  return route.path.startsWith(href);
}
</script>

<style scoped>
/* ── 单色深面板 ── */
.sidebar-panel {
  top: 12px;
  left: 12px;
  bottom: 12px;
  background: var(--color-sidebar);
  border-radius: var(--radius-xl);
  border: 1px solid rgba(238, 240, 245, 0.08);
  box-shadow: var(--shadow-sidebar);
}

.panel-hairline {
  background: rgba(238, 240, 245, 0.08);
}

.panel-hairline-top {
  border-top: 1px solid rgba(238, 240, 245, 0.08);
}

/* ── 品牌锁定：名称用主字族，标记只有印章 ── */
.wordmark {
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  color: var(--color-on-dark);
}

.wordmark-sub {
  font-size: 11px;
  font-weight: 400;
  line-height: 16px;
  color: var(--color-on-dark-muted);
}

/* ── 导航行：中性表面台阶即选中态，不加粗、不发亮 ── */
.nav-item {
  transition: background-color 160ms var(--ease-out), color 160ms var(--ease-out);
}

.nav-item--idle {
  color: var(--color-on-dark-muted);
}

.nav-item--idle:hover {
  background: var(--color-on-dark-raise);
  color: var(--color-on-dark);
}

.nav-item--active {
  background: var(--color-on-dark-raise);
  color: var(--color-on-dark);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);
}

.collapse-btn {
  color: var(--color-on-dark-muted);
  transition: background-color 160ms var(--ease-out), color 160ms var(--ease-out);
}

.collapse-btn:hover {
  background: var(--color-on-dark-raise);
  color: var(--color-on-dark);
}

/* ── Transitions ── */
.backdrop-fade-enter-active,
.backdrop-fade-leave-active {
  transition: opacity 200ms var(--ease-out);
}
.backdrop-fade-enter-from,
.backdrop-fade-leave-to { opacity: 0; }

/* ── Scrollbar ── */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}
</style>
