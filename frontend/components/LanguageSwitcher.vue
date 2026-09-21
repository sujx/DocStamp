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
  gap: 3px;
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
  gap: 3px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  padding: 3px 6px;
  height: 28px;
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  transition: all 0.2s cubic-bezier(.16, 1, .3, 1);
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
  background: rgba(255, 255, 255, 0.08);
}
.lang-btn.active {
  background: rgba(76, 125, 240, 0.22);
  border-color: rgba(76, 125, 240, 0.40);
}
.flag {
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.12);
  color: #8FA0C8;
  transition: all 0.2s cubic-bezier(.16, 1, .3, 1);
}
.lang-btn.active .flag {
  background: #4C7DF0;
  color: #fff;
}
.label {
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
  color: #8FA0C8;
}
.lang-btn.active .label {
  color: #fff;
}
</style>
