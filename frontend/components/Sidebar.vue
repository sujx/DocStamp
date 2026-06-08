<template>
  <aside
    class="fixed left-0 top-0 h-full z-40 flex flex-col border-r transition-[width] duration-150 pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)]"
    :class="collapsed ? 'w-16' : 'w-60'"
    :style="{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border-default)', boxShadow: 'var(--shadow-sidebar)' }"
  >
    <!-- Logo -->
    <div
      class="flex items-center h-14 px-4 border-b shrink-0"
      :class="collapsed ? 'justify-center' : 'gap-3'"
      :style="{ borderColor: 'var(--color-border-subtle)' }"
    >
      <img src="/logo.svg" alt="docStamp" class="size-8 shrink-0" />
      <span v-if="!collapsed" class="text-lg font-bold truncate" :style="{ color: 'var(--color-text-primary)' }">docStamp</span>
    </div>

    <!-- Nav items -->
    <nav class="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
      <template v-for="item in navItems" :key="item.key">
        <!-- Standalone item (no children) -->
        <NuxtLink
          v-if="!item.children"
          :to="item.to"
          class="flex items-center h-10 rounded-md text-sm font-medium transition-[background-color,color] duration-150"
          :class="[
            collapsed ? 'justify-center px-2' : 'px-3 gap-3',
            isActive(item.to)
              ? 'bg-brand-soft text-brand-700'
              : 'text-[var(--color-text-primary)] hover:bg-muted'
          ]"
        >
          <UIcon :name="item.icon" class="size-5 shrink-0" />
          <span v-if="!collapsed">{{ item.label }}</span>
        </NuxtLink>

        <!-- Grouped item (with children submenu) -->
        <div
          v-else
          class="relative"
          @mouseenter="hoverGroup = item.key"
          @mouseleave="hoverGroup = null"
        >
          <button
            class="flex items-center w-full h-10 rounded-md text-sm font-medium transition-[background-color,color] duration-150"
            :class="[
              collapsed ? 'justify-center px-2' : 'px-3 gap-3',
              isGroupActive(item)
                ? 'bg-brand-soft text-brand-700'
                : 'text-[var(--color-text-primary)] hover:bg-muted'
            ]"
            @click="collapsed ? (hoverGroup = hoverGroup === item.key ? null : item.key) : null"
            :aria-label="item.label"
          >
            <UIcon :name="item.icon" class="size-5 shrink-0" />
            <span v-if="!collapsed" class="flex-1 text-left">{{ item.label }}</span>
            <UIcon
              v-if="!collapsed"
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
              :class="collapsed ? 'left-full top-0 ml-2' : 'left-2 right-2 top-full mt-1'"
              :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-elevated)' }"
            >
              <NuxtLink
                v-for="child in item.children"
                :key="child.to"
                :to="child.to"
                class="flex items-center gap-2.5 px-3.5 py-2 text-sm rounded-md mx-1 transition-[background-color,color] duration-100"
                :class="isActive(child.to)
                  ? 'bg-brand-soft text-brand-700'
                  : 'text-[var(--color-text-primary)] hover:bg-muted'"
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
      <LanguageSwitcher :collapsed="collapsed" />
      <UButton
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
const collapsed = ref(import.meta.client ? localStorage.getItem("sidebar_collapsed") === "true" : false);
const hoverGroup = ref<string | null>(null);
const route = useRoute();
const { t } = useI18n();

function toggleCollapsed() {
  collapsed.value = !collapsed.value;
  if (import.meta.client) localStorage.setItem("sidebar_collapsed", String(collapsed.value));
}

// Expose collapsed state for layout
provide("sidebarCollapsed", collapsed);

interface NavItem {
  key: string;
  to?: string;
  icon: string;
  label: string;
  children?: { to: string; icon: string; label: string }[];
}

const navItems = computed<NavItem[]>(() => [
  { key: "dashboard", to: "/", icon: "i-heroicons-home", label: t("tabs.dashboard") },
  { key: "md2docx", to: "/md-to-docx", icon: "i-heroicons-arrow-down-tray", label: t("tabs.md2docx") },
  { key: "watermark", to: "/watermark", icon: "i-heroicons-beaker", label: t("tabs.watermarkManagement") },
  {
    key: "office", icon: "i-heroicons-document-text", label: t("tabs.officeTools"),
    children: [
      { to: "/properties", icon: "i-heroicons-document-text", label: t("tabs.properties") },
      { to: "/excel-merge", icon: "i-heroicons-table-cells", label: t("tabs.excelMerge") },
      { to: "/format-docx", icon: "i-heroicons-document-check", label: t("tabs.formatDocx") },
      { to: "/format-convert", icon: "i-heroicons-arrow-path", label: t("tabs.formatConvert") },
      { to: "/metadata-clean", icon: "i-heroicons-shield-exclamation", label: t("tabs.metadataClean") },
    ],
  },
  {
    key: "pdf", icon: "i-heroicons-document", label: t("tabs.pdfTools"),
    children: [
      { to: "/file-assembly", icon: "i-heroicons-arrows-right-left", label: t("tabs.fileAssembly") },
      { to: "/print-split", icon: "i-heroicons-printer", label: t("tabs.printSplit") },
      { to: "/pdf-editor", icon: "i-heroicons-document", label: t("tabs.pdfEditor") },
      { to: "/pdf-to-text", icon: "i-heroicons-document-magnifying-glass", label: t("tabs.pdfToText") },
      { to: "/pdf-merge", icon: "i-heroicons-plus-circle", label: t("tabs.pdfMerge") },
      { to: "/pdf-compress", icon: "i-heroicons-arrows-pointing-in", label: t("tabs.pdfCompress") },
      { to: "/page-decorate", icon: "i-heroicons-document-check", label: t("tabs.pageDecorate") },
      { to: "/image-process", icon: "i-heroicons-photo", label: t("tabs.imageProcess") },
    ],
  },
  { key: "status", to: "/status", icon: "i-heroicons-chart-bar", label: t("tabs.status") },
]);

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
</style>
