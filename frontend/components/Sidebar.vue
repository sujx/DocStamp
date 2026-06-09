<template>
  <!-- Hamburger toggle (mobile only) -->
  <button
    class="fixed top-3 left-3 z-50 lg:hidden flex items-center justify-center size-11 rounded-lg transition-[background-color] duration-150 cursor-pointer"
    :style="{ backgroundColor: 'var(--color-surface)', boxShadow: 'var(--shadow-elevated)' }"
    :aria-label="mobileOpen ? '关闭导航' : '打开导航'"
    @click="mobileOpen = !mobileOpen"
  >
    <UIcon
      :name="mobileOpen ? 'i-heroicons-x-mark' : 'i-heroicons-bars-3'"
      class="size-5"
      :style="{ color: 'var(--color-text-primary)' }"
    />
  </button>

  <!-- Backdrop (mobile only) -->
  <Transition name="backdrop-fade">
    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-30 bg-black/30 lg:hidden"
      @click="mobileOpen = false"
    />
  </Transition>

  <!-- Sidebar -->
  <aside
    class="fixed left-0 top-0 h-full z-40 flex flex-col border-r transition-[width,transform] duration-150 pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)]"
    :class="[
      collapsed && !isMobile ? 'w-16' : 'w-60',
      isMobile && !mobileOpen ? '-translate-x-full' : 'translate-x-0',
    ]"
    :style="{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border-default)', boxShadow: 'var(--shadow-sidebar)' }"
  >
    <!-- Logo -->
    <div
      class="flex items-center h-14 px-4 border-b shrink-0"
      :class="collapsed && !isMobile ? 'justify-center' : 'gap-3'"
      :style="{ borderColor: 'var(--color-border-subtle)' }"
    >
      <img src="/logo.svg" alt="鹊随金印" class="size-8 shrink-0" />
      <span v-if="!(collapsed && !isMobile)" class="brand-title truncate">鹊随金印</span>
    </div>

    <!-- Nav items -->
    <nav class="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
      <template v-for="item in navItems" :key="item.key">
        <!-- Standalone item (no children) -->
        <NuxtLink
          v-if="!item.children"
          :to="item.to"
          class="flex items-center min-h-[44px] rounded-md text-sm font-medium transition-[background-color,color] duration-150 cursor-pointer"
          :class="[
            collapsed && !isMobile ? 'justify-center px-2' : 'px-3 gap-3',
            isActive(item.to)
              ? 'bg-brand-soft text-brand-700'
              : 'text-[var(--color-text-primary)] hover:bg-muted'
          ]"
          @click="mobileOpen = false"
        >
          <UIcon :name="item.icon" class="size-5 shrink-0" />
          <span v-if="!(collapsed && !isMobile)">{{ item.label }}</span>
        </NuxtLink>

        <!-- Grouped item (with children submenu) -->
        <div
          v-else
          class="relative"
          @mouseenter="hoverGroup = item.key"
          @mouseleave="hoverGroup = null"
        >
          <button
            class="flex items-center w-full min-h-[44px] rounded-md text-sm font-medium transition-[background-color,color] duration-150 cursor-pointer"
            :class="[
              collapsed && !isMobile ? 'justify-center px-2' : 'px-3 gap-3',
              isGroupActive(item)
                ? 'bg-brand-soft text-brand-700'
                : 'text-[var(--color-text-primary)] hover:bg-muted'
            ]"
            @click="hoverGroup = hoverGroup === item.key ? null : item.key"
            :aria-label="item.label"
          >
            <UIcon :name="item.icon" class="size-5 shrink-0" />
            <span v-if="!(collapsed && !isMobile)" class="flex-1 text-left">{{ item.label }}</span>
            <UIcon
              v-if="!(collapsed && !isMobile)"
              :name="hoverGroup === item.key ? 'i-heroicons-chevron-down' : 'i-heroicons-chevron-right'"
              class="size-3.5 shrink-0 transition-transform duration-150"
              :style="{ color: 'var(--color-text-tertiary)' }"
            />
          </button>

          <!-- Submenu popup -->
          <Transition name="submenu-fade">
            <div
              v-if="hoverGroup === item.key"
              class="absolute z-50 py-1.5 rounded-lg min-w-[168px]"
              :class="(collapsed && !isMobile) ? 'left-full top-0 ml-2' : 'left-2 right-2 top-full mt-1'"
              :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-elevated)' }"
            >
              <NuxtLink
                v-for="child in item.children"
                :key="child.to"
                :to="child.to"
                class="flex items-center gap-2.5 px-3.5 py-2 text-sm rounded-md mx-1 transition-[background-color,color] duration-100 cursor-pointer"
                :class="isActive(child.to)
                  ? 'bg-brand-soft text-brand-700'
                  : 'text-[var(--color-text-primary)] hover:bg-muted'"
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
    <div class="px-2 py-2.5 border-t space-y-1.5 shrink-0 overflow-hidden" :style="{ borderColor: 'var(--color-border-subtle)' }">
      <LanguageSwitcher :collapsed="collapsed && !isMobile" />
      <UButton
        v-if="!isMobile"
        size="sm" variant="ghost" color="neutral"
        :icon="collapsed ? 'i-heroicons-chevron-right' : 'i-heroicons-chevron-left'"
        :block="!collapsed"
        :aria-label="collapsed ? '展开侧边栏' : '折叠侧边栏'"
        @click="toggleCollapsed"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { SIDEBAR_GROUPS } from "~/composables/tools.config";

const collapsed = ref(import.meta.client ? localStorage.getItem("sidebar_collapsed") === "true" : false);
const hoverGroup = ref<string | null>(null);
const mobileOpen = ref(false);
const isMobile = ref(false);
const route = useRoute();
const { t } = useI18n();

// Media query for mobile detection
onMounted(() => {
  const mq = window.matchMedia("(max-width: 1023px)");
  isMobile.value = mq.matches;
  mq.addEventListener("change", (e) => { isMobile.value = e.matches; });
});

// Watch route changes on mobile — close sidebar after navigation
watch(() => route.path, () => {
  if (isMobile.value) mobileOpen.value = false;
});

function toggleCollapsed() {
  collapsed.value = !collapsed.value;
  if (import.meta.client) localStorage.setItem("sidebar_collapsed", String(collapsed.value));
}

// Expose effective sidebar width for layout margin
const sidebarWidth = computed(() => {
  if (isMobile.value) return 0;
  return collapsed.value ? 64 : 240;
});
provide("sidebarWidth", sidebarWidth);

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
.submenu-fade-enter-active { transition: opacity 100ms ease-out, transform 100ms ease-out; }
.submenu-fade-leave-active { transition: opacity 80ms ease-in, transform 80ms ease-in; }
.submenu-fade-enter-from { opacity: 0; transform: translateY(-4px); }
.submenu-fade-leave-to { opacity: 0; transform: translateY(-4px); }

.backdrop-fade-enter-active { transition: opacity 150ms ease-out; }
.backdrop-fade-leave-active { transition: opacity 150ms ease-in; }
.backdrop-fade-enter-from,
.backdrop-fade-leave-to { opacity: 0; }
</style>
