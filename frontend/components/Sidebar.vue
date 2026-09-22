<template>
  <!-- Hamburger toggle (mobile only) -->
  <button
    class="fixed top-4 left-4 z-50 lg:hidden flex items-center justify-center size-10 rounded-xl transition-all duration-200 cursor-pointer bg-surface shadow-elevated hover:shadow-md"
    :aria-label="mobileOpen ? '关闭导航' : '打开导航'"
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
      class="fixed inset-0 z-30 bg-black/30 backdrop-blur-sm lg:hidden"
      @click="mobileOpen = false"
    />
  </Transition>

  <!-- Sidebar: dark aurora floating panel -->
  <aside
    class="sidebar-panel fixed z-40 flex flex-col transition-[width,transform] duration-200 overflow-hidden"
    :class="[
      collapsed && !isMobile ? 'w-[72px]' : 'w-64',
      isMobile && !mobileOpen ? '-translate-x-full' : 'translate-x-0',
    ]"
  >
    <!-- Aurora light spots overlay -->
    <div class="aurora-overlay" />

    <!-- Content layer -->
    <div class="relative z-10 flex flex-col h-full">
      <!-- Logo area -->
      <div
        class="flex items-center h-14 px-3 shrink-0"
        :class="collapsed && !isMobile ? 'justify-center' : 'gap-2.5'"
      >
        <div class="seal-icon shrink-0">印</div>
        <div v-if="!(collapsed && !isMobile)" class="flex flex-col min-w-0">
          <span class="text-white font-bold text-base leading-tight tracking-wide">鹊随金印</span>
          <span class="text-[10px] text-sidebar-sub font-medium tracking-wider">DOCSTAMP</span>
        </div>
      </div>

      <!-- Divider -->
      <div class="mx-3 h-px bg-white/10" />

      <!-- Nav items -->
      <nav class="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto scrollbar-thin">
        <template v-for="item in navItems" :key="item.key">
          <!-- Group label (shown before group items) -->

          <!-- Standalone item -->
          <NuxtLink
            v-if="!item.children"
            :to="item.to"
            class="nav-item group relative flex items-center min-h-[42px] rounded-lg text-[14px] font-medium transition-all duration-150 cursor-pointer"
            :class="[
              collapsed && !isMobile ? 'justify-center px-1.5' : 'px-2.5 gap-2.5',
              isActive(item.to)
                ? 'nav-item--active'
                : 'text-sidebar-text hover:bg-white/[.06] hover:text-white'
            ]"
            @click="mobileOpen = false"
          >
            <UIcon :name="item.icon" class="size-[22px] shrink-0" />
            <span v-if="!(collapsed && !isMobile)" class="truncate">{{ item.label }}</span>
          </NuxtLink>

          <!-- Grouped item (with children submenu) -->
          <div
            v-else
            class="relative"
            @mouseenter="hoverGroup = item.key"
            @mouseleave="hoverGroup = null"
          >
            <button
              class="nav-item group relative flex items-center w-full min-h-[42px] rounded-lg text-[14px] font-medium transition-all duration-150 cursor-pointer"
              :class="[
                collapsed && !isMobile ? 'justify-center px-1.5' : 'px-2.5 gap-2.5',
                isGroupActive(item)
                  ? 'nav-item--active'
                  : 'text-sidebar-text hover:bg-white/[.06] hover:text-white'
              ]"
              @click="hoverGroup = hoverGroup === item.key ? null : item.key"
              :aria-label="item.label"
            >
              <UIcon :name="item.icon" class="size-[22px] shrink-0" />
              <span v-if="!(collapsed && !isMobile)" class="flex-1 text-left truncate">{{ item.label }}</span>
              <UIcon
                v-if="!(collapsed && !isMobile)"
                name="i-heroicons-chevron-right"
                class="size-3.5 shrink-0 transition-transform duration-200 text-sidebar-sub"
                :class="hoverGroup === item.key && 'rotate-90'"
              />
            </button>

            <!-- Submenu popup -->
            <Transition name="submenu-fade">
              <div
                v-if="hoverGroup === item.key"
                class="absolute z-50 py-1.5 rounded-xl min-w-[180px] bg-surface border border-default shadow-elevated"
                :class="(collapsed && !isMobile) ? 'left-full top-0 ml-2' : 'left-2 right-2 top-full mt-1'"
              >
                <NuxtLink
                  v-for="child in item.children"
                  :key="child.to"
                  :to="child.to"
                  class="flex items-center gap-2.5 px-3 py-1.5 text-[13px] rounded-lg mx-1.5 transition-all duration-150 cursor-pointer"
                  :class="isActive(child.to)
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : 'text-primary hover:bg-muted'"
                  @click="mobileOpen = false"
                >
                  <UIcon :name="child.icon" class="size-4 shrink-0" />
                  <span>{{ child.label }}</span>
                </NuxtLink>
              </div>
            </Transition>
          </div>
        </template>
      </nav>

      <!-- Bottom: language + collapse -->
      <div class="px-2 py-2 space-y-1.5 shrink-0 border-t border-white/10">
        <LanguageSwitcher :collapsed="collapsed && !isMobile" />
        <button
          v-if="!isMobile"
          class="flex items-center justify-center w-full min-h-[32px] rounded-lg text-[11px] font-medium text-sidebar-sub transition-all duration-150 cursor-pointer hover:bg-white/[.06] hover:text-white"
          :class="collapsed && 'px-1.5'"
          :aria-label="collapsed ? '展开侧边栏' : '折叠侧边栏'"
          @click="toggleCollapsed"
        >
          <UIcon
            :name="collapsed ? 'i-heroicons-chevron-right' : 'i-heroicons-chevron-left'"
            class="size-3.5"
          />
          <span v-if="!(collapsed && !isMobile)" class="ml-2">收起侧边栏</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { SIDEBAR_GROUPS } from "~/composables/tools.config";

const { collapsed, isMobile, toggleCollapsed } = useSidebar();

const hoverGroup = ref<string | null>(null);
const mobileOpen = ref(false);
const route = useRoute();
const { t } = useI18n();

watch(() => route.path, () => {
  if (isMobile.value) mobileOpen.value = false;
});

interface NavChild {
  to: string; icon: string; label: string;
}
interface NavItem {
  key: string;
  to?: string;
  icon: string;
  label: string;
  children?: NavChild[];
}

const navItems = computed<NavItem[]>(() =>
  SIDEBAR_GROUPS.map(item => {
    if ("tools" in item) {
      return {
        key: item.key,
        icon: item.icon,
        label: t(item.label),
        children: item.tools.map(tool => ({ to: tool.to, icon: tool.icon, label: t(tool.label) })),
      }
    }
    return { key: item.key, to: item.to, icon: item.icon, label: t(item.label) }
  })
);

function isActive(href: string): boolean {
  if (href === "/") return route.path === "/";
  return route.path.startsWith(href);
}

function isGroupActive(item: NavItem): boolean {
  return item.children?.some(c => isActive(c.to)) ?? false;
}
</script>

<style scoped>
/* ── Dark aurora floating panel ── */
.sidebar-panel {
  top: 12px;
  left: 12px;
  bottom: 12px;
  background: linear-gradient(168deg, #2A2166 0%, #23337A 30%, #1E4E7E 55%, #17646B 80%, #4A3D20 100%);
  border-radius: 16px;
  box-shadow: 0 12px 22px -4px rgba(26, 43, 79, 0.18), 0 6px 10px -4px rgba(26, 43, 79, 0.10);
}

.aurora-overlay {
  position: absolute;
  inset: -30%;
  pointer-events: none;
  background:
    radial-gradient(40% 26% at 30% 6%, rgba(126, 159, 227, 0.30), transparent 60%),
    radial-gradient(45% 30% at 72% 42%, rgba(147, 207, 233, 0.18), transparent 60%),
    radial-gradient(50% 28% at 38% 94%, rgba(241, 226, 182, 0.16), transparent 60%);
  filter: blur(40px);
  z-index: 0;
}

/* ── Seal icon (brand accent) ── */
.seal-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--color-seal-red);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 8px rgba(192, 57, 43, 0.35);
  flex: none;
}

/* ── Nav item active state (no left accent bar, SynTime style) ── */
.nav-item--active {
  background: rgba(76, 125, 240, 0.22);
  color: #ffffff;
  font-weight: 600;
}

/* ── Sidebar text colors ── */
.text-sidebar-text {
  color: #8FA0C8;
}
.text-sidebar-sub {
  color: #8496C4;
}

/* ── Transitions ── */
.submenu-fade-enter-active { transition: opacity 150ms ease-out, transform 150ms ease-out; }
.submenu-fade-leave-active { transition: opacity 100ms ease-in, transform 100ms ease-in; }
.submenu-fade-enter-from { opacity: 0; transform: translateY(-4px) scale(0.98); }
.submenu-fade-leave-to { opacity: 0; transform: translateY(-4px) scale(0.98); }

.backdrop-fade-enter-active { transition: opacity 200ms ease-out; }
.backdrop-fade-leave-active { transition: opacity 150ms ease-in; }
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
