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
  gap: 2px;
  border: none;
  border-radius: var(--radius-normal, 6px);
  background: transparent;
  cursor: pointer;
  padding: 4px 5px;
  height: 28px;
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
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
  background: var(--color-muted);
}
.lang-btn.active {
  background: var(--color-brand-soft);
  outline: 1px solid var(--color-brand-700);
  outline-offset: -1px;
}
.flag {
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: var(--color-muted);
  color: var(--color-text-primary);
}
.label {
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
  color: var(--color-text-primary);
}
</style>
