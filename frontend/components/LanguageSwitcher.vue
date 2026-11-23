<template>
  <div class="lang-switcher" :class="{ collapsed }">
    <button
      class="lang-btn"
      :class="{ active: locale === 'zh-CN' }"
      :aria-label="$t('common.langZh')"
      @click="setLang('zh-CN')"
    >
      <span class="flag">中</span>
      <span v-if="!collapsed" class="label">中文</span>
    </button>
    <button
      class="lang-btn"
      :class="{ active: locale === 'en' }"
      :aria-label="$t('common.langEn')"
      @click="setLang('en')"
    >
      <span class="flag">EN</span>
      <span v-if="!collapsed" class="label">English</span>
    </button>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ collapsed?: boolean }>(), { collapsed: false });
const { locale, setLocale } = useI18n();
function setLang(lang: string) {
  setLocale(lang);
  if (import.meta.client) localStorage.setItem("docstamp_lang", lang);
}
</script>

<style scoped>
.lang-switcher {
  display: flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  overflow: hidden;
}
.lang-switcher.collapsed {
  flex-direction: column;
  gap: 2px;
}
.lang-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  padding: 3px 6px;
  height: 28px;
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  color: var(--color-on-dark-muted);
  transition: background-color 160ms var(--ease-out), color 160ms var(--ease-out);
}
.lang-switcher.collapsed .lang-btn {
  width: 28px;
  height: 28px;
  min-width: 0;
  max-width: 28px;
  flex: none;
  padding: 0;
}
.lang-btn:hover {
  background: var(--color-on-dark-raise);
  color: var(--color-on-dark);
}
.lang-btn.active {
  background: var(--color-on-dark-raise);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.10);
  color: var(--color-on-dark);
}
.flag {
  font-size: 11px;
  font-weight: 500;
  line-height: 1;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
}
.label {
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
  color: inherit;
}
</style>
