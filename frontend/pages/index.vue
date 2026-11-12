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
    <PromiseBand
      :kicker="$t('landing.promise.kicker')"
      :title="$t('landing.promise.title')"
      :sub="$t('landing.promise.sub')"
      :items="promiseItems"
      :notes-title="$t('landing.promise.notesTitle')"
      :notes="promiseNotes"
    />
  </div>
</template>

<script setup lang="ts">
import LetterheadHero from "~/components/landing/LetterheadHero.vue";
import ToolShowcase from "~/components/landing/ToolShowcase.vue";
import PromiseBand from "~/components/landing/PromiseBand.vue";
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

const PROMISE_ITEM_KEYS = [
  ["landing.promise.item1Title", "landing.promise.item1Body"],
  ["landing.promise.item2Title", "landing.promise.item2Body"],
  ["landing.promise.item3Title", "landing.promise.item3Body"],
] as const;

const PROMISE_NOTE_KEYS = [
  ["landing.promise.note1Title", "landing.promise.note1Body"],
  ["landing.promise.note2Title", "landing.promise.note2Body"],
  ["landing.promise.note3Title", "landing.promise.note3Body"],
] as const;

const promiseItems = computed(() =>
  PROMISE_ITEM_KEYS.map(([titleKey, bodyKey]) => ({ title: t(titleKey), body: t(bodyKey) })),
);

const promiseNotes = computed(() =>
  PROMISE_NOTE_KEYS.map(([titleKey, bodyKey]) => ({ title: t(titleKey), body: t(bodyKey) })),
);
</script>
