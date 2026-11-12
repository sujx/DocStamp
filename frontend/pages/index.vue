<template>
  <div>
    <LetterheadHero
      :no="$t('landing.hero.no')"
      :title="$t('landing.hero.title')"
      :sub="$t('landing.hero.sub')"
      :lede="$t('landing.hero.lede')"
      primary-to="/tools"
      :primary-label="$t('landing.hero.primary')"
      secondary-to="/pdf-redact"
      :secondary-label="$t('landing.hero.secondary')"
    />
    <ToolShowcase :groups="groups" />
  </div>
</template>

<script setup lang="ts">
import LetterheadHero from "~/components/landing/LetterheadHero.vue";
import ToolShowcase from "~/components/landing/ToolShowcase.vue";
import { TOOLS, LANDING_GROUPS, LANDING_FLAGS, type ToolDef } from "~/composables/tools.config";

definePageMeta({ layout: "landing" });

const { t } = useI18n();

const groups = computed(() =>
  LANDING_GROUPS.map((group) => ({
    label: t(group.labelKey),
    items: group.keys
      .map((key) => TOOLS.find((x) => x.key === key))
      .filter((tool): tool is ToolDef & { desc: string } => Boolean(tool?.desc))
      .map((tool) => {
        const flagKey = LANDING_FLAGS[tool.key];
        return {
          to: tool.to,
          icon: tool.icon,
          title: t(tool.label),
          description: t(tool.desc),
          flag: flagKey ? t(flagKey) : undefined,
        };
      }),
  })),
);
</script>
