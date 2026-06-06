<template>
  <div :class="collapsed ? 'flex-col gap-1' : 'flex gap-1'">
    <UButton
      size="xs"
      :variant="locale === 'zh-CN' ? 'solid' : 'ghost'"
      :color="locale === 'zh-CN' ? 'primary' : 'neutral'"
      :block="!collapsed"
      @click="setLang('zh-CN')"
    >{{ collapsed ? '中' : 'zh-CN' }}</UButton>
    <UButton
      size="xs"
      :variant="locale === 'en' ? 'solid' : 'ghost'"
      :color="locale === 'en' ? 'primary' : 'neutral'"
      :block="!collapsed"
      @click="setLang('en')"
    >{{ collapsed ? 'EN' : 'EN' }}</UButton>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ collapsed?: boolean }>(), { collapsed: false });

const { locale, setLocale } = useI18n();

function setLang(lang: string) {
  setLocale(lang);
  if (import.meta.client) {
    localStorage.setItem("docstamp_lang", lang);
  }
}
</script>
