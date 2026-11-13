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
    <section id="resources" class="scroll-mt-20 py-14">
      <div class="mx-auto max-w-5xl px-4 sm:px-6">
        <div class="text-brand-600">
          <SectionKicker :text="$t('landing.resource.kicker')" />
        </div>
        <h2 class="font-official mb-2 mt-2 text-[30px] font-extrabold tracking-wide text-primary">
          {{ $t("landing.resource.title") }}
        </h2>
        <p class="mb-9 max-w-xl text-secondary">{{ $t("landing.resource.note") }}</p>

        <div class="stagger-children grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <a
            href="/GBT9704-2012.pdf"
            target="_blank"
            rel="noopener"
            class="card card-interactive block no-underline"
          >
            <h3 class="mb-1.5 text-[15px] font-semibold text-primary">{{ $t("landing.footer.standard") }}</h3>
            <p class="text-[13px] leading-relaxed text-secondary">{{ $t("landing.resource.standardDesc") }}</p>
          </a>

          <NuxtLink to="/tools" class="card card-interactive block no-underline">
            <h3 class="mb-1.5 text-[15px] font-semibold text-primary">{{ $t("landing.footer.allTools") }}</h3>
            <p class="text-[13px] leading-relaxed text-secondary">{{ $t("landing.resource.toolsDesc") }}</p>
          </NuxtLink>

          <NuxtLink to="/status" class="card card-interactive block no-underline">
            <h3 class="mb-1.5 text-[15px] font-semibold text-primary">{{ $t("landing.footer.stats") }}</h3>
            <p class="text-[13px] leading-relaxed text-secondary">{{ $t("landing.resource.statsDesc") }}</p>
          </NuxtLink>

          <NuxtLink to="/guide/pdf-redact" class="card card-interactive block no-underline">
            <h3 class="mb-1.5 text-[15px] font-semibold text-primary">{{ $t("landing.resource.guideTitle") }}</h3>
            <p class="text-[13px] leading-relaxed text-secondary">{{ $t("landing.resource.guideDesc") }}</p>
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import LetterheadHero from "~/components/landing/LetterheadHero.vue";
import ToolShowcase from "~/components/landing/ToolShowcase.vue";
import PromiseBand from "~/components/landing/PromiseBand.vue";
import SectionKicker from "~/components/landing/SectionKicker.vue";
import { TOOLS, LANDING_GROUPS, LANDING_FLAGS, type ToolDef } from "~/composables/tools.config";

definePageMeta({ layout: "landing" });

const { t } = useI18n();

useHead({
  title: computed(() => t("landing.meta.title")),
  meta: [
    { name: "description", content: computed(() => t("landing.meta.description")) },
    { name: "keywords", content: computed(() => t("landing.meta.keywords")) },
    { property: "og:title", content: computed(() => t("landing.meta.title")) },
    { property: "og:description", content: computed(() => t("landing.meta.description")) },
    { property: "og:type", content: "website" },
    { property: "og:url", content: "https://doc.sujx.net/" },
    { property: "og:image", content: "https://doc.sujx.net/og.png" },
    { name: "twitter:card", content: "summary_large_image" },
    { name: "twitter:title", content: computed(() => t("landing.meta.title")) },
    { name: "twitter:description", content: computed(() => t("landing.meta.description")) },
    { name: "twitter:image", content: "https://doc.sujx.net/og.png" },
  ],
});

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
  ["landing.promise.note4Title", "landing.promise.note4Body"],
] as const;

const promiseItems = computed(() =>
  PROMISE_ITEM_KEYS.map(([titleKey, bodyKey]) => ({ title: t(titleKey), body: t(bodyKey) })),
);

const promiseNotes = computed(() =>
  PROMISE_NOTE_KEYS.map(([titleKey, bodyKey]) => ({ title: t(titleKey), body: t(bodyKey) })),
);
</script>
